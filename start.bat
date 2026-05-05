@echo off
title Zero2Print PrintManager
echo Starte Zero2Print PrintManager...
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
@echo off
title Zero2Print PrintManager

cd /d "%~dp0"

echo.
echo ==============================================
echo  Zero2Print PrintManager
echo ==============================================
echo.
echo Pruefe Python...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Python wurde nicht gefunden.
    echo Bitte Python installieren und "Add Python to PATH" aktivieren.
    echo.
    pause
    exit /b
)

echo Python gefunden.
echo.
echo Pruefe Abhaengigkeiten...
echo.

python -m pip install -r requirements.txt

echo.
echo Starte Zero2Print PrintManager...
echo.

python run_server.py

echo.
echo Server wurde beendet.
pause