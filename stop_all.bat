@echo off
echo Stopping all services...
taskkill /FI "WindowTitle eq fitness-*" /F 2>nul
taskkill /FI "WindowTitle eq generator-*" /F 2>nul
taskkill /FI "WindowTitle eq crossover-*" /F 2>nul
taskkill /FI "WindowTitle eq mutation-*" /F 2>nul
taskkill /FI "WindowTitle eq selection*" /F 2>nul
taskkill /FI "WindowTitle eq orchestrator*" /F 2>nul
taskkill /FI "WindowTitle eq migration*" /F 2>nul
docker compose down
echo All services stopped.