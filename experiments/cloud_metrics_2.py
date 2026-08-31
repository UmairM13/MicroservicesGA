"""
Find experiment windows automatically from the orchestrator pod count,
then pull per-pod CPU, memory and network metrics for each one.

No hand-entered run timestamps: give it a broad search period and it
locates the stable plateaus itself.

Prerequisites:
    kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090

"""

from pathlib import Path
from datetime import datetime, timezone, timedelta
import requests
import pandas as pd

# ----------------------------------------------------------------- CONFIG

PROM = "http://localhost:9090"
NAMESPACE = "ga-pipeline"
STEP = "15s"    
# your local offset from UTC            
TZ_OFFSET_HOURS = 1          

# Broad period to search. Local wall-clock.
SEARCH_START = "2026-08-16 11:00:00"
SEARCH_END   = "2026-08-16 15:15:43"

# just used for labelling the output
BUDGET_LABEL = 1600          
TOPOLOGY = "ring"

# island counts actually ran
VALID_COUNTS = {1, 4, 8, 16}   
MIN_PLATEAU_S = 240            
TRIM_S = 60                    

OUT_CSV = Path("cloud_metrics_auto.csv")

# -------------------------------------------------------------------------


def to_unix(s):
    dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    return dt.replace(tzinfo=timezone.utc).timestamp() - TZ_OFFSET_HOURS * 3600


def to_local(ts):
    dt = datetime.fromtimestamp(ts, tz=timezone.utc) + timedelta(hours=TZ_OFFSET_HOURS)
    return dt.strftime("%H:%M:%S")


def query_range(expr, start, end, step=STEP):
    r = requests.get(f"{PROM}/api/v1/query_range", params={
        "query": expr, "start": start, "end": end, "step": step,
    }, timeout=90)
    r.raise_for_status()
    p = r.json()
    if p["status"] != "success":
        raise RuntimeError(p)
    return p["data"]["result"]


def find_plateaus(start, end):
    """Return [(count, t_start, t_end)] for each stable stretch."""
    expr = (f'count(container_memory_working_set_bytes'
            f'{{namespace="{NAMESPACE}", pod=~"orchestrator.*", container!=""}})')
    res = query_range(expr, start, end)
    if not res:
        raise SystemExit("No orchestrator pods found. Check NAMESPACE, "
                         "TZ_OFFSET_HOURS and the search period.")
    pts = sorted((float(t), int(float(v))) for t, v in res[0]["values"])

    segments, cur, seg_start = [], pts[0][1], pts[0][0]
    for t, v in pts[1:]:
        if v != cur:
            segments.append((cur, seg_start, t))
            cur, seg_start = v, t
    segments.append((cur, seg_start, pts[-1][0]))

    print("Detected segments:")
    keep = []
    for c, a, b in segments:
        dur = b - a
        ok = c in VALID_COUNTS and dur >= MIN_PLATEAU_S
        print(f"  {c:>3} pods  {to_local(a)} -> {to_local(b)}  "
              f"({dur:5.0f}s){'  KEEP' if ok else ''}")
        if ok:
            keep.append((c, a + TRIM_S, b - TRIM_S))
    return keep


QUERIES = {
    "cpu_cores": ('sum by (pod) (rate(container_cpu_usage_seconds_total'
                  '{{namespace="{ns}", container!=""}}[1m]))'),
    "mem_bytes": ('sum by (pod) (container_memory_working_set_bytes'
                  '{{namespace="{ns}", container!=""}})'),
    "net_tx_bps": ('sum by (pod) (rate(container_network_transmit_bytes_total'
                   '{{namespace="{ns}"}}[1m]))'),
}


def role_of(pod):
    return "orchestrator" if pod.startswith("orchestrator") else pod.split("-")[0]


def main():
    plateaus = find_plateaus(to_unix(SEARCH_START), to_unix(SEARCH_END))
    if not plateaus:
        raise SystemExit("No usable plateaus. Widen the search period or "
                         "lower MIN_PLATEAU_S.")

    rows = []
    for idx, (islands, start, end) in enumerate(plateaus, 1):
        label = f"seg{idx:02d}_i{islands}"
        print(f"\n{label}: {to_local(start)} -> {to_local(end)}")

        frames = {}
        for name, tmpl in QUERIES.items():
            res = query_range(tmpl.format(ns=NAMESPACE), start, end, "5s")
            if res:
                frames[name] = pd.DataFrame([
                    {"pod": s["metric"].get("pod", "?"), "t": float(t), name: float(v)}
                    for s in res for t, v in s["values"]
                ])
        if not frames:
            print("  no metrics"); continue

        n_steps = max(f["t"].nunique() for f in frames.values())
        for pod in sorted(set().union(*[set(f["pod"]) for f in frames.values()])):
            presence = max(f[f["pod"] == pod]["t"].nunique() / n_steps
                           for f in frames.values())
            if presence < 0.9:
                continue
            row = {"label": label, "islands": islands, "topology": TOPOLOGY,
                   "budget": BUDGET_LABEL, "pod": pod, "role": role_of(pod)}
            for name, f in frames.items():
                v = f[f["pod"] == pod][name]
                if len(v):
                    row[f"{name}_mean"], row[f"{name}_peak"] = v.mean(), v.max()
            rows.append(row)

        n_orch = sum(1 for r in rows
                     if r["label"] == label and r["role"] == "orchestrator")
        status = "OK" if n_orch == islands else "MISMATCH"
        print(f"  orchestrator pods retained: {n_orch} ({status})")

    df = pd.DataFrame(rows)
    df["mem_MiB_mean"] = df["mem_bytes_mean"] / 1024 ** 2
    df["mem_MiB_peak"] = df["mem_bytes_peak"] / 1024 ** 2
    df.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {OUT_CSV}")

    print("\n--- Per configuration ---")
    print(df.groupby(["label", "islands"]).agg(
        pods=("pod", "nunique"),
        cpu_total_mean=("cpu_cores_mean", "sum"),
        cpu_total_peak=("cpu_cores_peak", "sum"),
        mem_total_MiB=("mem_MiB_mean", "sum"),
    ).round(3).to_string())

    print("\n--- By role (mean CPU cores) ---")
    print(df.pivot_table(index="role", columns="label",
                         values="cpu_cores_mean", aggfunc="sum"
                         ).round(3).to_string())


if __name__ == "__main__":
    main()