@echo off
setlocal enabledelayedexpansion

:: Install required packages
py -m pip install -r requirements.txt
py -m pip install pyinstaller PyQt6-WebEngine

:: Create the executable using PyInstaller
py -m PyInstaller ^
    --name="MNITJFlowMeter" ^
    --onefile ^
    --windowed ^
    --icon=icon.ico ^
    --add-data "icon.ico;." ^
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
    MNITJFlowMeter_gui.py

echo.
echo Build complete! The executable is in the 'dist' folder.
pause
