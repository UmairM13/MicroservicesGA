@echo off
@echo off
echo Stopping all services...
docker compose down

for %%P in (8001 8002 8003 8004 8201 8202 8203 8204 8205 8301) do (
    for /f "tokens=5" %%A in ('netstat -ano ^| findstr :%%P ^| findstr LISTENING') do (
        taskkill /PID %%A /F 2>nul
    )
)
echo All services stopped.