@echo off
title MMO LLM Adapter for PlayerBots
cd /d "%~dp0"

rem Do not open another console if the adapter is already listening.
netstat -ano | findstr /R /C:":8080 .*LISTENING" >nul
if not errorlevel 1 (
    echo MMO LLM Adapter is already running on port 8080.
    exit /b 0
)

echo ============================================================
echo   MMO LLM Adapter for PlayerBots
echo   Universal Local LLM Cognitive Layer
echo ============================================================
echo.

"%~dp0.venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8080
