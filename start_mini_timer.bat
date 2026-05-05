@echo off
title Zero2Print Mini-Timer

cd /d "%~dp0"

echo.
echo ==============================================
echo  Zero2Print Mini-Timer
echo ==============================================
echo.
echo Wichtig:
echo Der Zero2Print PrintManager muss bereits laufen.
echo.
echo Starte Mini-Timer...
echo.

python mini_timer.py

echo.
echo Mini-Timer wurde geschlossen.
pause