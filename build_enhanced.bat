@echo off
setlocal enabledelayedexpansion

:: Set the project directory and log file
set "PROJECT_DIR=%~dp0"
set "LOG_FILE=%PROJECT_DIR%build.log"
cd /d "%PROJECT_DIR%"

:: Clear previous log
echo New build started: %date% %time% > "%LOG_FILE%"

echo ==============================
echo    MNITJFlowMeter Build Tool
echo ==============================

echo Logging to: %LOG_FILE%

:: Function to log messages
:log
    echo [%time%] %~1 >> "%LOG_FILE%"
    echo [%time%] %~1
goto :eof

:: Start logging
echo Building MNITJFlowMeter - %date% %time% > "%LOG_FILE%"
call :log "Starting build process..."

:: Clean up previous build artifacts
call :log "[1/5] Cleaning up previous build artifacts..."

:: Simple cleanup - ignore errors
@echo off
rmdir /s /q "build" 2>nul
rmdir /s /q "dist" 2>nul
rmdir /s /q "__pycache__" 2>nul
del /s /q *.pyc 2>nul
@echo on

call :log "Cleanup complete"

:: Check Python
call :log "[2/5] Checking Python installation..."
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    call :log "ERROR: Python not found. Please install Python 3.8+ and add it to PATH"
    pause
    exit /b 1
)

:: Check for virtual environment
call :log "[3/5] Setting up virtual environment..."
if not exist "venv\Scripts\python.exe" (
    call :log "Creating new virtual environment..."
    python -m venv venv
    if errorlevel 1 (
        call :log "ERROR: Failed to create virtual environment"
        pause
        exit /b 1
    )
    
    call "venv\Scripts\activate.bat"
    if errorlevel 1 (
        call :log "ERROR: Failed to activate new virtual environment"
        pause
        exit /b 1    
    )
    
    call :log "Installing required packages..."
    python -m pip install --upgrade pip
    if exist "requirements.txt" (
        pip install -r requirements.txt
    ) else (
        pip install pyinstaller PyQt6 scapy pandas numpy psutil pyqtgraph dash plotly flask dash-bootstrap-components dash-daq flask-compress
    )
) else (
    call "venv\Scripts\activate.bat"
    if errorlevel 1 (
        call :log "ERROR: Failed to activate existing virtual environment"
        pause
        exit /b 1
    )
)

:: Install/update pip
call :log "Upgrading pip..."
python -m pip install --upgrade pip >> "%LOG_FILE%" 2>&1

:: Install requirements
call :log "Installing requirements..."
if exist "requirements.txt" (
    pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        call :log "ERROR: Failed to install requirements"
        pause
        exit /b 1
    )
) else (
    call :log "WARNING: requirements.txt not found"
)

:: Install PyInstaller if not installed
call :log "Checking for PyInstaller..."
pip list | findstr /i "pyinstaller" >nul
if %ERRORLEVEL% neq 0 (
    call :log "Installing PyInstaller..."
    pip install pyinstaller >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        call :log "ERROR: Failed to install PyInstaller"
        pause
        exit /b 1
    )
)

:: Build the executable
call :log "[4/5] Starting PyInstaller build..."

set "PY_CMD=pyinstaller"
set "PY_OPTS=--noconfirm --clean --onefile --windowed"
set "PY_OPTS=%PY_OPTS% --name "MNITJFlowMeter""
set "PY_OPTS=%PY_OPTS% --add-data "gui_flow_extractor_full.py;.""
set "PY_OPTS=%PY_OPTS% --add-data "realtime_analysis.py;.""

:: Add images if directory exists
if exist "images" (
    set "PY_OPTS=%PY_OPTS% --add-data "images;images""
)

:: Add icon if exists
if exist "icon.ico" (
    set "PY_OPTS=%PY_OPTS% --icon "icon.ico""
)

:: Add hidden imports
set "HIDDEN_IMPORTS=PyQt6.QtWebEngineWidgets PyQt6.QtWebEngineCore PyQt6.QtWebEngineQuick"
set "HIDDEN_IMPORTS=%HIDDEN_IMPORTS% scapy numpy pandas psutil pyqtgraph dash plotly flask"
set "HIDDEN_IMPORTS=%HIDDEN_IMPORTS% werkzeug dash_bootstrap_components dash_daq flask_compress"

for %%i in (%HIDDEN_IMPORTS%) do (
    set "PY_OPTS=!PY_OPTS! --hidden-import %%i"
)

:: Add exclusions
set "PY_OPTS=%PY_OPTS% --exclude-module _tkinter --exclude-module matplotlib"

:: Build the command
set "FULL_CMD=%PY_CMD% %PY_OPTS% "MNITJFlowMeter_gui.py""

call :log "Running: %FULL_CMD%"
%FULL_CMD% >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    call :log "ERROR: Build failed. Check build.log for details."
    echo.
    echo ====== BUILD FAILED ======
    type "%LOG_FILE%" | findstr /i "error fail"
    pause
    exit /b 1
)

:: Verify the executable was created
if exist "%PROJECT_DIR%dist\MNITJFlowMeter.exe" (
    call :log "[5/5] Build successful!"
    echo.
    echo ====== BUILD SUCCESSFUL ======
    echo Executable created at: %PROJECT_DIR%dist\MNITJFlowMeter.exe
    echo.
    timeout /t 3 >nul
    start "" "%PROJECT_DIR%dist"
) else (
    call :log "ERROR: Executable was not created"
    echo.
    echo ====== BUILD FAILED ======
    echo Check build.log for details
    pause
    exit /b 1
)

echo.
echo Build completed at: %date% %time%
echo Log file: %LOG_FILE%
pause
exit /b 0
