@echo off
echo Starting migration services...

docker compose up -d
timeout /t 5 /nobreak > nul

start "migration (8301)" cmd /k "cd Services\migration && uvicorn main:app --port 8301"

echo Kafka and migration service started.