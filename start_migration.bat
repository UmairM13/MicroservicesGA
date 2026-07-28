@echo off
echo Starting migration services...

docker compose up -d kafka
timeout /t 5 /nobreak > nul

start "migration (8301)" cmd /k "cd Services\migration && set NUM_ISLANDS=24 && uvicorn main:app --port 8301"

echo Kafka started (container); migration started (local uvicorn).