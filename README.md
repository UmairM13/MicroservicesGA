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
- Helm (for the monitoring stack)

## Running locally

<!-- TODO: -->

```bash
# 1. Ensure Docker is running locally
./start_sudoku.bat or ./start_flight.bat


```

Experiment parameters (island counts, seeds, population budget, topology) are set
in the config block at the top of each runner script.

## Running on AWS

<!-- TODO: fill in -->

Cluster used for the reported results: one m7i-flex.large control-plane node and
two t3.small agent nodes, running k3s, in the EU (London) region. Images are
distributed via Docker Hub so any node pulls the same artefact.

```bash
# Deploy

```

Two things to watch:

- Orchestrators must reach the migration service by **cluster DNS**
  (`http://migration:8000`), not localhost. A localhost address resolves to the
  pod's own loopback, so migration silently never happens.
- Kafka must be restarted between configurations. The broker retains messages
  after delivery, so migrants from one run would otherwise leak into the next.

## Analysis

| Script | Purpose |
|---|---|
| `ga_results.py` | Summary statistics, significance tests and figures from `results.csv` |
| `cloud_metrics.py` | Pulls per-pod CPU, memory and network from Prometheus for each run window |

Requires a port-forward to Prometheus:

```bash
kubectl -n monitoring port-forward svc/<prometheus-svc> 9090:9090
```

## Repository layout

<!-- TODO: adjust to match -->

```
Services/          the seven microservices, one directory each
config/            experiment runner scripts, one per domain
k8s/               base manifests and Kustomize overlays per island count
Results/           experiment output and analysis scripts
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

<!-- TODO: choose one, e.g. MIT -->

Note that the Sudoku implementation this work derives from carries a copyright
notice but no licence, so its original terms are reserved to its author. Any
licence applied here covers only the original work in this repository.