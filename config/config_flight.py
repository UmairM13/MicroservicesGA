import csv
import json
import time
import os
import subprocess
import concurrent.futures
from pathlib import Path
from datetime import datetime
import sys

import httpx


#### CONFIG

ORCH_BASE_PORT = 8202
ORCH_DIR = "Services/orchestrator"
HEALTH_TIMEOUT = 30
KAFKA_CONTAINER = "kafka"
KAFKA_SETTLE_SECONDS = 12
REQUEST_TIMEOUT = 300.0
TOPOLOGY = "ring"         

# ---- FLIGHT service URLs (8011-8014); selection shared on 8201 ----
FITNESS_URL   = "http://127.0.0.1:8011"
GENERATOR_URL = "http://127.0.0.1:8012"
CROSSOVER_URL = "http://127.0.0.1:8013"
MUTATION_URL  = "http://127.0.0.1:8014"
SELECTOR_URL  = "http://127.0.0.1:8201"

# ---- FLIGHT context ----
NUM_FLIGHTS = 24
NUM_GATES = 6
FLIGHTS = [
    {"flight_id":0,"arrival":81,"departure":128,"passengers":32},
    {"flight_id":1,"arrival":223,"departure":278,"passengers":134},
    {"flight_id":2,"arrival":355,"departure":442,"passengers":72},
    {"flight_id":3,"arrival":588,"departure":675,"passengers":299},
    {"flight_id":4,"arrival":75,"departure":142,"passengers":36},
    {"flight_id":5,"arrival":205,"departure":250,"passengers":131},
    {"flight_id":6,"arrival":339,"departure":411,"passengers":33},
    {"flight_id":7,"arrival":542,"departure":594,"passengers":299},
    {"flight_id":8,"arrival":28,"departure":96,"passengers":162},
    {"flight_id":9,"arrival":156,"departure":244,"passengers":101},
    {"flight_id":10,"arrival":393,"departure":460,"passengers":194},
    {"flight_id":11,"arrival":555,"departure":604,"passengers":130},
    {"flight_id":12,"arrival":13,"departure":58,"passengers":214},
    {"flight_id":13,"arrival":130,"departure":192,"passengers":196},
    {"flight_id":14,"arrival":329,"departure":385,"passengers":42},
    {"flight_id":15,"arrival":503,"departure":577,"passengers":83},
    {"flight_id":16,"arrival":10,"departure":85,"passengers":170},
    {"flight_id":17,"arrival":225,"departure":304,"passengers":205},
    {"flight_id":18,"arrival":437,"departure":489,"passengers":55},
    {"flight_id":19,"arrival":554,"departure":636,"passengers":136},
    {"flight_id":20,"arrival":10,"departure":64,"passengers":71},
    {"flight_id":21,"arrival":172,"departure":229,"passengers":252},
    {"flight_id":22,"arrival":370,"departure":433,"passengers":103},
    {"flight_id":23,"arrival":540,"departure":602,"passengers":127}
]

ISLAND_COUNTS = [1, 4, 8, 16]
SEEDS = [ 1, 2, 3, 4, 5, 67, 76, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
TOTAL_POPULATION = 1600
MAX_GENERATIONS = 100
MIGRATION_INTERVAL = 10
NUM_MIGRANTS = 3
STALE_THRESHOLD = 20
MUTATION_RATE = 0.2        # flight used 0.2, not Sudoku's 0.06
POPULATION_MODES = ["fixed_total"]

MIGRATION_URL = "http://127.0.0.1:8301"
OUTPUT_DIR = Path("experiments") / datetime.now().strftime("flight_results_%Y%m%d_%H%M%S")


def reset_kafka():
    print("Resetting Kafka...")
    subprocess.run(["docker", "restart", KAFKA_CONTAINER], check=True, capture_output=True)
    time.sleep(KAFKA_SETTLE_SECONDS)


def build_payload(island_id, num_islands, base_seed, population_mode):
    if population_mode == "fixed_total":
        pop_per_island = TOTAL_POPULATION // num_islands
    else:
        pop_per_island = TOTAL_POPULATION

    payload = {
        "context": {
            "num_flights": NUM_FLIGHTS,
            "num_gates": NUM_GATES,
            "flights": FLIGHTS,
        },
        "island_id": island_id,
        "base_seed": base_seed,
        "population_size": pop_per_island,
        "max_generations": MAX_GENERATIONS,
        "elitism_count": 5,
        "mutation_rate": MUTATION_RATE,
        "crossover_rate": 1.0,
        "selection_rate": 0.85,
        "tournament_size": 2,
        "stale_threshold": STALE_THRESHOLD,
        "migration_interval": MIGRATION_INTERVAL,
        "num_migrants": NUM_MIGRANTS,
    }
    if num_islands > 1:
        payload["migration_url"] = MIGRATION_URL
        payload["num_islands"] = num_islands
        payload["topology"] = TOPOLOGY
    return payload


def run_one_island(island_id, num_islands, base_seed, population_mode):
    port = ORCH_BASE_PORT + island_id
    url = f"http://127.0.0.1:{port}/run"
    payload = build_payload(island_id, num_islands, base_seed, population_mode)
    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        res = client.post(url, json=payload)
        res.raise_for_status()
        return res.json()


def launch_orchestrators(num_islands):
    procs = []
    env = os.environ.copy()
    env.update({
        "FITNESS_URL": FITNESS_URL,
        "GENERATOR_URL": GENERATOR_URL,
        "CROSSOVER_URL": CROSSOVER_URL,
        "MUTATION_URL": MUTATION_URL,
        "SELECTOR_URL": SELECTOR_URL,
    })
    for i in range(num_islands):
        port = ORCH_BASE_PORT + i
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", str(port)],
            cwd=ORCH_DIR,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        procs.append(proc)
    return procs


def wait_for_healthy(num_islands):
    deadline = time.time() + HEALTH_TIMEOUT
    for i in range(num_islands):
        port = ORCH_BASE_PORT + i
        url = f"http://127.0.0.1:{port}/health"
        while True:
            try:
                if httpx.get(url, timeout=2).status_code == 200:
                    break
            except Exception:
                pass
            if time.time() > deadline:
                raise RuntimeError(f"Orchestrator on port {port} never became healthy")
            time.sleep(0.5)


def teardown_orchestrators(procs):
    for p in procs:
        p.terminate()
    for p in procs:
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()


def run_config(num_islands, base_seed, population_mode):
    if num_islands > 1:
        reset_kafka()
        try:
            httpx.post(f"{MIGRATION_URL}/reset", timeout=10)
        except Exception as e:
            print(f"  reset flag failed: {e}")

    procs = launch_orchestrators(num_islands)
    try:
        wait_for_healthy(num_islands)
        start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_islands) as pool:
            futures = {
                pool.submit(run_one_island, i, num_islands, base_seed, population_mode): i
                for i in range(num_islands)
            }
            results = {}
            for fut in concurrent.futures.as_completed(futures):
                results[futures[fut]] = fut.result()
        wall = time.perf_counter() - start
        ordered = [results[i] for i in range(num_islands)]
        return ordered, wall
    finally:
        teardown_orchestrators(procs)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / "results.csv"
    all_histories = {}
    writer = None
    f = open(csv_path, "w", newline="")

    for population_mode in POPULATION_MODES:
        for num_islands in ISLAND_COUNTS:
            for seed in SEEDS:
                label = f"{TOPOLOGY}_{population_mode}_islands_{num_islands}_seed_{seed}"
                print(f"Running configuration: {label}")
                try:
                    results, wall = run_config(num_islands, seed, population_mode)
                except Exception as e:
                    print(f"Error running configuration {label}: {e}")
                    continue

                config_best = max(r["best_fitness"] for r in results)
                solved = config_best >= 1.0
                config_rows = []
                for island_id, r in enumerate(results):
                    config_rows.append({
                        "num_islands": num_islands,
                        "base_seed": seed,
                        "island_id": island_id,
                        "population_mode": population_mode,
                        "pop_per_island": build_payload(island_id, num_islands, seed, population_mode)["population_size"],
                        "best_fitness": r["best_fitness"],
                        "generations": r["generations"],
                        "status": r["status"],
                        "solved": r["best_fitness"] >= 1.0,
                        "config_best_fitness": config_best,
                        "config_solved": solved,
                        "wall_clock_seconds": round(wall, 2),
                        "topology": TOPOLOGY,
                    })
                    all_histories[f"{TOPOLOGY}_{population_mode}_{num_islands}_{seed}_{island_id}"] = r["history"]

                if writer is None:
                    writer = csv.DictWriter(f, fieldnames=list(config_rows[0].keys()))
                    writer.writeheader()
                writer.writerows(config_rows)
                f.flush()
                print(f" best={config_best:.4f}, solved={solved}, wall={wall:.1f}s")

    f.close()
    with open(OUTPUT_DIR / "history.json", "w") as hf:
        json.dump(all_histories, hf)
    print("Experiment completed.")


if __name__ == "__main__":
    main()