@echo off
echo Starting Flight Scheduling GA pipeline...

start "fitness-flight (8011)" cmd /k "cd Services\fitness-flight && uvicorn main:app --port 8011"
start "generator-flight (8012)" cmd /k "cd Services\generator\generator-flight && uvicorn main:app --port 8012"
start "crossover-flight (8013)" cmd /k "cd Services\crossover\crossover-flight && uvicorn main:app --port 8013"
start "mutation-flight (8014)" cmd /k "cd Services\mutation\mutation-flight && uvicorn main:app --port 8014"
start "selection (8201)" cmd /k "cd Services\selection && uvicorn main:app --port 8201"

timeout /t 3 /nobreak > nul

set FITNESS_URL=http://127.0.0.1:8011
set GENERATOR_URL=http://127.0.0.1:8012
set CROSSOVER_URL=http://127.0.0.1:8013
set MUTATION_URL=http://127.0.0.1:8014
@REM start "orchestrator (8202)" cmd /k "cd Services\orchestrator && set FITNESS_URL=http://127.0.0.1:8011 && set GENERATOR_URL=http://127.0.0.1:8012 && set CROSSOVER_URL=http://127.0.0.1:8013 && set MUTATION_URL=http://127.0.0.1:8014 && uvicorn main:app --port 8202"

echo All Flight services started.