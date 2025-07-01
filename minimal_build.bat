@echo off
echo Starting minimal build...

:: Basic cleanup
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
del /s /q *.pyc 2>nul

:: Activate venv if exists
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
    if errorlevel 1 (
        echo Failed to activate virtual environment
        pause
        exit /b 1
    )
)

:: Simple PyInstaller command
echo Building executable...
pyinstaller --noconfirm --clean --onefile ^
    --name "MNITJFlowMeter" ^
    --add-data "gui_flow_extractor_full.py;." ^
    --add-data "realtime_analysis.py;." ^
    --add-data "images;images" ^
    --hidden-import PyQt6.QtWebEngineWidgets ^
    --hidden-import PyQt6.QtWebEngineCore ^
    --hidden-import PyQt6.QtWebEngineQuick ^
    --hidden-import scapy ^
    --hidden-import dash ^
    --hidden-import plotly ^
    --hidden-import flask ^
    --hidden-import dash_bootstrap_components ^
    --hidden-import dash_daq ^
    --hidden-import flask_compress ^
    "MNITJFlowMeter_gui.py"

if exist "dist\MNITJFlowMeter.exe" (
    echo.
    echo ====== BUILD SUCCESSFUL ======
    echo Executable created at: %CD%\dist\MNITJFlowMeter.exe
    start "" "dist"
) else (
    echo.
    echo ====== BUILD FAILED ======
    echo Check for error messages above
)

pause
