#!/bin/bash
# Usage: ./cloud_run.sh <island_count> <overlay_name>
# e.g: ./clound_run.sh 4 four-island

set -e
N=$1
OVERLAY=$2
NS=ga-pipeline

echo "=== Scaling to $N islands ($OVERLAY) ==="
sudo kubectl apply -k /home/MicroservicesGA/k3s/overlays/$OVERLAY

echo "=== Waiting for orchestrator-0..$((N-1)) ready ==="

for i in $(seq 0 $((N-1))); do
   sudo kubectl wait --for=condition=ready pod/orchestrator-$i -n $NS --timeout=300s
done

echo "=== Restarting Kafka ==="
sudo kubectl delete pods -n $NS -l app=kafka
sudo kubectl wait --for=condition=ready pod -l app=kafka -n $NS --timeout=180s
sleep 10


echo "=== Port-frowarding orchs + migration ==="
PIDS=()
for i in $(seq 0 $((N-1))); do
  sudo kubectl port-forward -n $NS orchestrator-$i $((8202+i)):8000 >/dev/null 2>&1 &
  PIDS+=($!)
done
sudo kubectl port-forward -n $NS service/migration 8301:8000 >/dev/null 2>&1 &
PIDS+=($!)
sleep 8


echo "=== Running experiment for $N islands ==="
cd /home/MicroservicesGA/config
python3 cloud_config.py $N || true


echo "=== Cleaning ==="
for pid in "${PIDS[@]}"; do kill $pid 2>/dev/null || true; done
sleep 2
echo "=== Done $N islands ==="
