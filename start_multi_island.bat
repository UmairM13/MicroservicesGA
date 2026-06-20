@echo off
echo Starting additional island orchestrators with migration...

echo Make sure Kafka is running (start_migration.bat) and one pipeline is already started.
echo.

set /p PROBLEM="Which problem? (sudoku/flight): "

if "%PROBLEM%"=="sudoku" (
    set F_URL=http://localhost:8001
    set G_URL=http://localhost:8002
    set C_URL=http://localhost:8003
    set M_URL=http://localhost:8004
) else (
    set F_URL=http://localhost:8011
    set G_URL=http://localhost:8012
    set C_URL=http://localhost:8013
    set M_URL=http://localhost:8014
)

start "orchestrator-island1 (8203)" cmd /k "cd Services\orchestrator && set FITNESS_URL=%F_URL% && set GENERATOR_URL=%G_URL% && set CROSSOVER_URL=%C_URL% && set MUTATION_URL=%M_URL% && set SELECTION_URL=http://localhost:8201 && set MIGRATION_URL=http://localhost:8301 && uvicorn main:app --port 8203"

start "orchestrator-island2 (8204)" cmd /k "cd Services\orchestrator && set FITNESS_URL=%F_URL% && set GENERATOR_URL=%G_URL% && set CROSSOVER_URL=%C_URL% && set MUTATION_URL=%M_URL% && set SELECTION_URL=http://localhost:8201 && set MIGRATION_URL=http://localhost:8301 && uvicorn main:app --port 8204"

start "orchestrator-island3 (8205)" cmd /k "cd Services\orchestrator && set FITNESS_URL=%F_URL% && set GENERATOR_URL=%G_URL% && set CROSSOVER_URL=%C_URL% && set MUTATION_URL=%M_URL% && set SELECTION_URL=http://localhost:8201 && set MIGRATION_URL=http://localhost:8301 && uvicorn main:app --port 8205"

echo Islands 1-3 started. Island 0 should already be running from start_sudoku or start_flight.