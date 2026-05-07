@echo off
cd /d "%~dp0"
set POLYSPACE_PORT=8000
set POLYSPACE_DATA_DIR=%LOCALAPPDATA%\PolySpace\data
if not exist "%POLYSPACE_DATA_DIR%" mkdir "%POLYSPACE_DATA_DIR%"
uv run uvicorn app.main:app --host 127.0.0.1 --port %POLYSPACE_PORT% --app-dir backend