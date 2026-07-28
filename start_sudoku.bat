@echo off
echo Starting Sudoku GA pipeline...

start "fitness-sudoku (8001)" cmd /k "cd Services\fitness-sudoku && uvicorn main:app --port 8001"
start "generator-sudoku (8002)" cmd /k "cd Services\generator\generator-sudoku && uvicorn main:app --port 8002"
start "crossover-sudoku (8003)" cmd /k "cd Services\crossover\crossover-sudoku && uvicorn main:app --port 8003"
start "mutation-sudoku (8004)" cmd /k "cd Services\mutation\mutation-sudoku && uvicorn main:app --port 8004"
start "selection (8201)" cmd /k "cd Services\selection && uvicorn main:app --port 8201"

@REM timeout /t 3 /nobreak > nul

@REM start "orchestrator (8202)" cmd /k "cd Services\orchestrator && uvicorn main:app --port 8202"

echo All Sudoku services started.