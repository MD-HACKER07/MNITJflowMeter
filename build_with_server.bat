@echo off
setlocal enabledelayedexpansion

:: Set application name
set APP_NAME=MNITJFlowMeter

:: Clean previous builds
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install required packages
echo Installing required packages...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller PyQt6-WebEngine dash dash-bootstrap-components plotly

:: Create icon if it doesn't exist
if not exist icon.ico (
    echo Creating application icon...
    python create_icon.py
)

:: Build the single executable
echo Building %APP_NAME% with server support...

pyinstaller --noconfirm --clean --windowed --onefile ^
    --name="%APP_NAME%" ^
    --icon=icon.ico ^
    --add-data="icon.ico;." ^
    --add-data="images;images" ^
    --add-data="venv/Lib/site-packages/dash;dash" ^
    --add-data="venv/Lib/site-packages/dash_bootstrap_components;dash_bootstrap_components" ^
    --add-data="venv/Lib/site-packages/plotly;plotly" ^
    --hidden-import="PyQt6.QtWebEngineWidgets" ^
    --hidden-import="PyQt6.QtWebEngineCore" ^
    --hidden-import="PyQt6.QtWebEngineQuick" ^
    --hidden-import="attack_detection" ^
    --hidden-import="flow_session_integration" ^
    --hidden-import="gui_flow_extractor" ^
    --hidden-import="export_packets" ^
    --hidden-import="enhanced_flow_extractor" ^
    --hidden-import="process_pcap" ^
    --hidden-import="realtime_analysis" ^
    --hidden-import="simple_flow_analyzer" ^
    --hidden-import="simple_flow_extractor" ^
    --hidden-import="test_flow_extractor" ^
    --hidden-import="fix_server_imports" ^
    --hidden-import="dash" ^
    --hidden-import="dash_bootstrap_components" ^
    --hidden-import="plotly" ^
    --hidden-import="flask" ^
    --hidden-import="werkzeug" ^
    --exclude-module="_tkinter" ^
    --exclude-module="matplotlib.tests" ^
    --exclude-module="numpy.random._examples" ^
    MNITJFlowMeter_gui.py

echo.
echo =========================================
echo Build complete with server support!
echo The standalone executable is available in the 'dist' folder as '%APP_NAME%.exe'
echo =========================================
pause
