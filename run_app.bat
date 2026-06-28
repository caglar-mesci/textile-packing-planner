@echo off
setlocal
cd /d "%~dp0"
if not exist "work" mkdir "work"
set QT_QPA_PLATFORM=
".venv\Scripts\python.exe" -m app.main > "work\app_output.log" 2> "work\app_error.log"
if errorlevel 1 (
    echo Uygulama acilamadi. Hata kaydi:
    type "work\app_error.log"
    pause
)
