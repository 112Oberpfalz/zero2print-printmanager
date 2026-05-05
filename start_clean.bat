@echo off
title Zero2Print PrintManager

cd /d "%~dp0"

echo.
echo ==============================================
echo  Zero2Print PrintManager - Normaler Start
echo ==============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Python wurde nicht gefunden.
    echo Bitte Python installieren und "Add Python to PATH" aktivieren.
    echo.
    pause
    exit /b
)

python -m pip install -r requirements.txt

echo.
echo Starte Server...
echo.

python run_server_clean.py

echo.
echo Server wurde beendet.
pause