@echo off
cd /d "%~dp0backend"
call myenv\Scripts\activate

echo Starting server...
start /b python -m uvicorn main:app --host 0.0.0.0 --port 8000

:wait
timeout /t 1 /nobreak >nul
curl.exe -s -o nul http://localhost:8000 && goto ready
goto wait

:ready
echo Server is ready.
start "" http://localhost:8000

:: Keep window open so uvicorn stays running
cmd /k
