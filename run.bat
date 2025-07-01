@echo off
REM MNITJFlowMeter - Windows Launcher
REM This batch file sets up and runs MNITJFlowMeter on Windows

setlocal enabledelayedexpansion

REM Set colors
set RED=91
set GREEN=92
set YELLOW=93
set BLUE=94
set NC=0

REM Function to print colored text
:colorEcho
echo off
set message=%~1
set color=%~2
if not defined color set color=%GREEN%

powershell -Command "Write-Host '%message%' -ForegroundColor %color%"

goto :eof

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    call :colorEcho "Python is not installed or not in PATH. Please install Python 3.8 or higher." %RED%
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2 del==. " %%v in ('python -c "import sys; print('PYTHON_VERSION =', sys.version_info[0], '.', sys.version_info[1])" 2^>nul') do (
    set PYTHON_MAJOR=%%v
    set PYTHON_MINOR=%%w
)

if "%PYTHON_MAJOR%" neq "3" (
    call :colorEcho "Python 3 is required. Found Python %PYTHON_MAJOR%.%PYTHON_MINOR%" %RED%
    pause
    exit /b 1
) else if "%PYTHON_MINOR%" lss "8" (
    call :colorEcho "Python 3.8 or higher is required. Found Python %PYTHON_MAJOR%.%PYTHON_MINOR%" %RED%
    pause
    exit /b 1
)

REM Set up virtual environment
if not exist "venv\" (
    call :colorEcho "Creating virtual environment..." %BLUE%
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        call :colorEcho "Failed to create virtual environment." %RED%
        pause
        exit /b 1
    )
    
    call :colorEcho "Installing dependencies..." %BLUE%
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    if exist requirements.txt (
        pip install -r requirements.txt
    ) else (
        pip install PyQt6 pyqtgraph pandas numpy scapy python-dateutil pytz tzdata matplotlib
        pip install dash dash-bootstrap-components dash-daq plotly
    )
    
    REM Install the package in development mode
    pip install -e .
) else (
    call venv\Scripts\activate.bat
)

REM Find an available port
set PORT=8050
:port_loop
netstat -ano | find " :%PORT% " >nul
if %ERRORLEVEL% EQU 0 (
    set /a PORT+=1
    if %PORT% GTR 9000 (
        call :colorEcho "Could not find an available port." %RED%
        pause
        exit /b 1
    )
    goto :port_loop
)

REM Start the server
start "MNITJFlowMeter Server" cmd /k "venv\Scripts\python.exe realtime_analysis.py --port %PORT%"

REM Set the port for the GUI
set DASH_SERVER_PORT=%PORT%

REM Start the GUI
call :colorEcho "Starting MNITJFlowMeter GUI..." %GREEN%
call :colorEcho "Server running on port %PORT%" %BLUE%
call :colorEcho "Press Ctrl+C in this window to stop the server." %YELLOW%

start "MNITJFlowMeter GUI" /b cmd /c "venv\Scripts\python.exe MNITJFlowMeter_gui.py %*"

REM Keep the window open
pause
