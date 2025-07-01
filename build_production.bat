@echo off
setlocal enabledelayedexpansion

:: Set application name
set APP_NAME=MNITJFlowMeter

:: Create a clean build directory
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
pip install pyinstaller PyQt6-WebEngine

:: Create icon if it doesn't exist
if not exist icon.ico (
    echo Creating application icon...
    python create_icon.py
)

:: Build the executable
echo Building %APP_NAME%...

pyinstaller --noconfirm --clean --windowed --onefile ^
    --name="%APP_NAME%" ^
    --icon=icon.ico ^
    --add-data="icon.ico;." ^
    --add-data="images;images" ^
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
    --exclude-module="_tkinter" ^
    --exclude-module="matplotlib.tests" ^
    --exclude-module="numpy.random._examples" ^
    MNITJFlowMeter_gui.py

:: Create a clean distribution folder
echo Creating distribution package...
if exist "dist\%APP_NAME%" rmdir /s /q "dist\%APP_NAME%"
mkdir "dist\%APP_NAME%"

:: Copy necessary files to distribution folder
xcopy /Y /E /I "dist\%APP_NAME%.exe" "dist\%APP_NAME%\"
xcopy /Y /E /I "requirements.txt" "dist\%APP_NAME%\"
xcopy /Y /E /I "README.md" "dist\%APP_NAME%\"

:: Create a batch file to run the application
(
    echo @echo off
    echo echo Starting %APP_NAME%...
    echo %~dp0%APP_NAME%.exe
    echo pause
) > "dist\%APP_NAME%\Run_%APP_NAME%.bat"

echo.
echo =========================================
echo Build complete!
echo The application is ready in the 'dist\%APP_NAME%' folder.
echo Run 'Run_%APP_NAME%.bat' to start the application.
echo =========================================
pause
