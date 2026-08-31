import csv
import json
import time
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

PUZZLE = [
    [0,3,0,0,7,0,0,5,0],
    [5,0,0,1,0,6,0,0,9],
    [0,0,1,0,0,0,4,0,0],
    [0,9,0,0,5,0,0,6,0],
    [6,0,0,4,0,2,0,0,7],
    [0,4,0,0,1,0,0,3,0],
    [0,0,2,0,0,0,8,0,0],
    [9,0,0,3,0,5,0,0,2],
    [0,1,0,0,2,0,0,7,0],
]



### ISLAND and Seed configuration

ISLAND_COUNTS = [1, 4, 8, 16]
SEEDS = [ 1, 2, 3, 4, 5, 67, 76, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
TOTAL_POPULATION = 1600
MAX_GENERATIONS = 100
MIGRATION_INTERVAL = 10
NUM_MIGRANTS = 3
STALE_THRESHOLD = 20
POPULATION_MODES = ["fixed_total"]
MIGRATION_RATE = 0.05
ELITISM_RATE = 0.05

MIGRATION_URL = "http://127.0.0.1:8301"

OUTPUT_DIR = Path("experiments") / datetime.now().strftime("results_%Y%m%d_%H%M%S")



### HELPER FUNCTIONS

def reset_kafka():
    """Reset Kafka by deleting all topics and restarting the container."""
    print("Resetting Kafka...")
    subprocess.run(["docker", "restart", KAFKA_CONTAINER],
                   check=True, capture_output=True)
    time.sleep(KAFKA_SETTLE_SECONDS)


def build_payload(island_id, num_islands, base_seed, population_mode):
    """ Build the payload for the orchestrator run request. """
    if population_mode == "fixed_total":
        pop_per_island = TOTAL_POPULATION // num_islands
    else:
        pop_per_island = TOTAL_POPULATION
    
    payload = {
        "context": {
            "puzzle": PUZZLE
        },
        "island_id": island_id,
        "base_seed": base_seed,
        "population_size": pop_per_island,
        "max_generations": MAX_GENERATIONS,
        "elitism_rate": ELITISM_RATE,
        "mutation_rate": 0.06,
        "crossover_rate": 1.0,
        "selection_rate": 0.85,
        "tournament_size": 2,
        "stale_threshold": STALE_THRESHOLD,
        "migration_interval": MIGRATION_INTERVAL,
    }
    if num_islands > 1: 
        payload["migration_url"] = MIGRATION_URL
        payload["num_islands"] = num_islands
        payload["topology"] = TOPOLOGY
        payload["migration_rate"] = MIGRATION_RATE
    return payload


def run_one_island(island_id, num_islands, base_seed, population_mode):
    """Run one island and return the result."""
    port = ORCH_BASE_PORT + island_id
    url = f"http://127.0.0.1:{port}/run"
    payload = build_payload(island_id, num_islands, base_seed, population_mode)
    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        res = client.post(url, json=payload)
        res.raise_for_status()
        return res.json()



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
                island_id = futures[fut]
                results[island_id] = fut.result()
        wall = time.perf_counter() - start

        ordered = [results[i] for i in range(num_islands)]
        return ordered, wall
    finally:
        teardown_orchestrators(procs)

def launch_orchestrators(num_islands):
    procs = []
    for i in range(num_islands):
        port = ORCH_BASE_PORT + i
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", str(port)],
            cwd=ORCH_DIR,
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



### Main


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
                    all_histories[f"{population_mode}_{num_islands}_{seed}_{island_id}"] = r["history"]

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