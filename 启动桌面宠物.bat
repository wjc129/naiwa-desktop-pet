@echo off
cd /d "%~dp0"
if exist "奶娃桌面宠物.exe" (
    start "" "奶娃桌面宠物.exe"
    exit /b
)
where conda >nul 2>nul
if not errorlevel 1 call conda activate beijing
start "" pythonw desktop_pet_qt.py
