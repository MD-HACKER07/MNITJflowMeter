@echo off
setlocal enabledelayedexpansion

:: Set the project directory
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo [*] Cleaning up previous build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"

:: Remove any .pyc files
for /r . %%i in (*.pyc) do (
    if exist "%%i" del /f /q "%%i"
)

echo [*] Activating virtual environment...
if exist "venv\Scripts\activate" (
    call "venv\Scripts\activate.bat"
) else (
    echo [ERROR] Virtual environment not found. Please create one using 'python -m venv venv'
    pause
    exit /b 1
)

echo [*] Installing required packages...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install required packages
    pause
    exit /b 1
)

echo [*] Building executable...
pyinstaller --noconfirm --clean --windowed --onefile ^
    --name "MNITJFlowMeter" ^
    --icon "icon.ico" ^
    --add-data "gui_flow_extractor_full.py;." ^
    --add-data "realtime_analysis.py;." ^
    --add-data "requirements.txt;." ^
    --add-data "images;images" ^
    --hidden-import "PyQt6.QtWebEngineWidgets" ^
    --hidden-import "PyQt6.QtWebEngineCore" ^
    --hidden-import "PyQt6.QtWebEngineQuick" ^
    --hidden-import "scapy" ^
    --hidden-import "numpy" ^
    --hidden-import "pandas" ^
    --hidden-import "psutil" ^
    --hidden-import "pyqtgraph" ^
    --hidden-import "dash" ^
    --hidden-import "plotly" ^
    --hidden-import "flask" ^
    --hidden-import "werkzeug" ^
    --hidden-import "dash_bootstrap_components" ^
    --hidden-import "dash_daq" ^
    --hidden-import "flask_compress" ^
    --exclude-module "_tkinter" ^
    --exclude-module "matplotlib" ^
    "MNITJFlowMeter_gui.py"

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo [*] Build completed successfully!
echo [*] Executable location: %PROJECT_DIR%dist\MNITJFlowMeter.exe

:: Open the output directory in Explorer
start "" "%PROJECT_DIR%dist"

pause
