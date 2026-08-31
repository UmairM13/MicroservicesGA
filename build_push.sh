#!/bin/bash
set -e
USER=umair121
ROOT=/home/MicroservicesGA/Services

# name : dockerfile-directory
build_push () {
  local name=$1
  local dir=$2
  echo "=== Building $name from $dir ==="
  docker build -t $USER/$name:latest "$dir"
  echo "=== Pushing $name ==="
  docker push $USER/$name:latest
  echo ""
}

build_push orchestrator      $ROOT/orchestrator
build_push fitness-sudoku    $ROOT/fitness-sudoku
build_push generator-sudoku  $ROOT/generator/generator-sudoku
build_push crossover-sudoku  $ROOT/crossover/crossover-sudoku
build_push mutation-sudoku   $ROOT/mutation/mutation-sudoku
build_push selection         $ROOT/selection
build_push migration         $ROOT/migration
build_push fitness-flight    $ROOT/fitness-flight
build_push generator-flight  $ROOT/generator/generator-flight
build_push crossover-flight  $ROOT/crossover/crossover-flight
build_push mutation-flight   $ROOT/mutation/mutation-flight

echo "=== All images built and pushed to Docker Hub (umair121) ==="
