# Cloud-Based Microservice Genetic Algorithm with Island-Based Evolution

A genetic algorithm decomposed into independently deployable microservices and run
under an island model, deployed on Kubernetes both locally and on AWS.

MSc Advanced Computer Science dissertation, University of Leeds, 2026.
Supervised by Professor Leandro Soares Indrusiak.

## What this is

Most GA implementations are monolithic, so individual operators cannot be scaled
independently and the fitness function cannot be swapped without redeploying the
whole system. This project decomposes the GA pipeline into seven services and runs
them under an island model, then measures what that costs and what it buys.

The system is evaluated on two structurally dissimilar problems:

- **Sudoku** — constraint satisfaction, grid encoding, single known optimum
- **Flight-gate scheduling** — combinatorial optimisation, flat-list encoding, no known optimum

Experiments vary island count (1, 4, 8, 16), migration topology (ring, fully
connected) and total population budget (1600, 3200), with 20 seeds per
configuration locally and 5 on the cloud.

## Services

| Service | Domain-aware | Role |
|---|---|---|
| Orchestrator | No | Drives the generational loop, holds population and run state |
| Generator | Yes | Builds the initial population |
| Selection | No | Tournament selection; reads fitness values only |
| Crossover | Yes | Cycle crossover (Sudoku) / two-point (flight-gate) |
| Mutation | Yes | Constraint-preserving swap (Sudoku) / random reassignment (flight-gate) |
| Fitness | Yes | Objective evaluation |
| Migration | No | Routes migrants by topology, holds the run-level solved flag |

## Requirements

- Python 3.11+
- Docker
- k3d (local) or k3s (cloud)
- kubectl, Kustomize
- Helm (for the monitoring stack on cloud)

## Running locally (windows)

Requires Docker Desktop to be running. Services are launcehd as separate `uvicorn` processes via `.bat` scripts. Each opens in its own console window. There are two ways to run the system: an automated harness for experimental sweeps, and a manual mode for sending individual requests on postman.

### Automated (experiment sweeps)

The Python runner launches and tears down the island orchestrators itself, so only the operator services, Kafka and the migration service need to be started first.

```bash
./start_sudoku.bat
./start_migration.bat
python config/config.py

```

```bash
./stop_all.bat
```
This stops all the consoles and kills the processes.

Experiment parameters (island counts, seeds, population budget, topology) are set
in the config block at the top of each runner script.

### Manual (postman)
To drive a single orchestrator by hand instead of through the harness, start
the operator services and the migration service as above, then start one
orchestrator manually. In `start_sudoku.bat` (or `start_flight.bat`), uncomment
the `orchestrator (8202)` line before running it, which launches an orchestrator
wired to the operator service URLs. Requests can then be sent to the
orchestrator at `http://127.0.0.1:8202`.

To add further islands for a manual multi-island run, use `start_islands.bat`,
which prompts for the problem (sudoku or flight) and starts orchestrators on
ports 8203 to 8205, all pointed at the shared migration service. Island 0 is
the orchestrator started above.

### Service URLs

| Service | Sudoku | Flight |
|---|---|---|
| Fitness | 8001 | 8011 |
| Generator | 8002 | 8012 |
| Crossover | 8003 | 8013 |
| Mutation | 8004 | 8014 |
| Selection | 8201 | 8201 (shared) |
| Migration | 8301 | 8301 (shared) |
| Orchestrator (island 0) | 8202 | 8202 |
| Orchestrators (islands 1-3, manual) | 8203-8205 | 8203-8205 |


### Example request (Postman)

With the operator services, migration service and a manual orchestrator running
(see above), send a `POST` to the orchestrator's `/run` endpoint:

Body (a single-island Sudoku run):

```json
{
    "context": {
        "puzzle": [
            [0,3,0,0,7,0,0,5,0],
            [5,0,0,1,0,6,0,0,9],
            [0,0,1,0,0,0,4,0,0],
            [0,9,0,0,5,0,0,6,0],
            [6,0,0,4,0,2,0,0,7],
            [0,4,0,0,1,0,0,3,0],
            [0,0,2,0,0,0,8,0,0],
            [9,0,0,3,0,5,0,0,2],
            [0,1,0,0,2,0,0,7,0]
        ]
    },
    "island_id": 0,
    "base_seed": 67,
    "population_size": 1600,
    "max_generations": 100,
    "elitism_rate": 0.05,
    "mutation_rate": 0.06,
    "crossover_rate": 1.0,
    "selection_rate": 0.85,
    "tournament_size": 2,
    "stale_threshold": 15,
    "migration_interval": 10,
    "migration_rate": 0.05
}
```

The response reports the run's status, the best fitness reached, the generation
it stopped at, and the best solution found. For a solved puzzle the best fitness
is `1.0`.

The `context` object is the only problem-specific field; everything else is
domain-agnostic. To run the flight-gate domain instead, point the orchestrator
at the flight operator services and replace `context` with the flight instance
(`num_flights`, `num_gates`, `flights`).

To run more than one island, add `"num_islands"`, `"topology"` (`ring` or
`fully_connected`) and start the additional orchestrators with
`start_islands.bat`.

| Field | Meaning |
|---|---|
| `context` | Problem instance; the only domain-specific field |
| `island_id` | Identifier for this island; seeds are derived from it |
| `base_seed` | Seed for the run; the same seed reproduces the run exactly |
| `population_size` | Individuals in this island's sub-population |
| `max_generations` | Generation cap |
| `elitism_rate` | Fraction of the population preserved unchanged each generation |
| `mutation_rate` | Base mutation rate; adapted at runtime on stagnation |
| `crossover_rate` | Probability of recombining a parent pair |
| `selection_rate` | Probability the fitter tournament competitor is chosen |
| `tournament_size` | Competitors per selection tournament |
| `stale_threshold` | Generations without improvement before reinitialisation |
| `migration_interval` | Generations between migration events |
| `migration_rate` | Fraction of the sub-population sent as migrants |

## Running on AWS


Cluster used for the reported results: one m7i-flex.large control-plane node and
two t3.small agent nodes, running k3s, in the EU (London) region. Images are
distributed via Docker Hub so any node pulls the same artefact.

### Build and push images

From a machine with Docker and push access to the Docker Hub account, build and
push all eleven service images:

```bash
./build_push.sh
```

This builds the orchestrator, migration and selection services once each, and
the fitness, generator, crossover and mutation services once per domain, tagging
each `umair121/<service>:latest` and pushing to Docker Hub.

### Cluster prerequisites

- k3s installed across the three nodes, with the agents joined to the server.
- The monitoring stack, if resource metrics are to be collected:

```bash
helm install monitoring prometheus-community/kube-prometheus-stack 
```

  Prometheus, Grafana and the operator components are pinned to the control-plane
  node via node selectors so the monitoring stack does not consume the agents'
  limited resources; only node-exporter runs on every node.

### Run a configuration

Island count is set by applying a Kustomize overlay, which patches the
orchestrator StatefulSet's replica count. `cloud_run.sh` applies an overlay,
waits for the orchestrators and Kafka to become ready, sets up port-forwards,
runs the sweep and cleans up:

```bash
# ./cloud_run.sh <island_count> <overlay_name>
./cloud_run.sh 1  one-island
./cloud_run.sh 4  four-island
./cloud_run.sh 8  eight-island
./cloud_run.sh 16 sixteen-island
```

Each invocation:

1. Applies the overlay (`k3s/overlays/<overlay_name>`) to scale the orchestrators.
2. Waits for `orchestrator-0` through `orchestrator-(N-1)` to become ready.
3. Restarts Kafka so no migrants carry over from a previous run, then waits for
   the broker to come back.
4. Port-forwards each orchestrator (host ports 8202 upward) and the migration
   service (8301).
5. Runs the sweep via `config/cloud_config.py`.
6. Tears down the port-forwards.

Experiment parameters (seeds, population budget, topology) are set in the config
block of `cloud_config.py`.

### Notes

- **Migration must use cluster DNS, not localhost.** Inside the cluster the
  orchestrators reach the migration service at its service DNS name, whereas the
  experiment harness on the host reaches individual orchestrators over the
  forwarded localhost ports. Supplying an orchestrator with the host-side address
  produces a system that runs without error while migration silently never
  happens, because the failed requests are caught and logged rather than raised.
- **Elastic IPs.** Stopping and starting an EC2 instance changes its public IP
  unless an Elastic IP is assigned.
- **Image caching.** In k3s (containerd), if images are loaded manually rather
  than pulled, they must be imported with
  `docker save <image> | sudo k3s ctr images import -`. Distributing via Docker
  Hub, as `build_push.sh` does, avoids this.

Two things to watch:

- Orchestrators must reach the migration service by **cluster DNS**
  (`http://migration:8000`), not localhost. A localhost address resolves to the
  pod's own loopback, so migration silently never happens.
- Kafka must be restarted between configurations. The broker retains messages
  after delivery, so migrants from one run would otherwise leak into the next.

## Analysis

| Script | Purpose |
|---|---|
| `analyse_sudoku.py` | Summary statistics, significance tests and figures from `results.csv` |
| `analyse_flight.py` | Summary statistics, significance tests and figures from `results.csv` |
| `cloud_metrics.py` | Pulls per-pod CPU, memory and network from Prometheus for each run window |

Requires a port-forward to Prometheus:

```bash
kubectl -n monitoring port-forward svc/<prometheus-svc> 9090:9090
```

## Repository layout


```
experiments/             scripts to run experiments and collect results
Services/
  fitness-sudoku/              domain sudoku services
  fitness-flight/              domain flight services
  generator/
    generator-sudoku/    generator-flight/
  crossover/
    crossover-sudoku/    crossover-flight/
  mutation/
    mutation-sudoku/     mutation-flight/
  selection/             shared, domain-agnostic
  migration/             shared, holds the solved flag
  orchestrator/          one process per island
config/                  experiment runner scripts, one per domain
k3s/                     base manifests and Kustomize overlays per island count
Results/                 experiment output and analysis scripts
*.bat                    local launch scripts (Windows)
```

## Attribution

The Sudoku domain derives from a genetic algorithm implementation by
**Christian T. Jacobs**, originally produced as coursework for the CS3M6
Evolutionary Computation module at the University of Reading
(Copyright © 2009, 2017 Christian Thomas Jacobs).

The candidate generator, cycle crossover, constraint-preserving swap mutation and
column-by-block fitness formulation follow that implementation. The modifications
made here are structural rather than algorithmic: the operators were
re-implemented as stateless pure functions rather than as methods mutating object
state, so that they could be deployed as independent services; the global random
seed was replaced with explicit generator injection; and bounded retry loops and
mutation-rate-dependent swap counts were added.

The flight-gate scheduling domain is original to this project.

## Licence

<!-- TODO: MIT -->

Note that the Sudoku implementation this work derives from carries a copyright
notice but no licence, so its original terms are reserved to its author. Any
licence applied here covers only the original work in this repository.