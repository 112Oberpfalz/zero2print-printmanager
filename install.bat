@echo off
title Zero2Print PrintManager Installation

cd /d "%~dp0"

echo.
echo ==============================================
echo  Zero2Print PrintManager - Installation
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

echo Python gefunden.
echo.
echo Aktualisiere pip...
echo.

python -m pip install --upgrade pip

echo.
echo Installiere Abhaengigkeiten...
echo.

python -m pip install -r requirements.txt

echo.
echo Installation fertig.
echo.
echo Starten mit:
echo   start.bat
echo.
pause