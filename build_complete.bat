@echo off
setlocal enabledelayedexpansion

:: Configuration
set "APP_NAME=MNITJFlowMeter"
set "VENV_DIR=venv"
set "REQUIREMENTS=requirements.txt"
set "MAIN_SCRIPT=MNITJFlowMeter_gui.py"
set "ICON_FILE=icon.ico"
set "DIST_DIR=dist"

:: Clear screen and show header
echo ===================================
echo    MNITJFlowMeter - Complete Build
 ===================================
echo.

:: Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Please install Python 3.8+ and add it to PATH
    pause
    exit /b 1
)

:: Clean up
echo [1/5] Cleaning up previous builds...
if exist "build" rmdir /s /q "build"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "__pycache__" rmdir /s /q "__pycache__"
del /s /q *.pyc 2>nul

:: Setup virtual environment
echo [2/5] Setting up virtual environment...
if not exist "%VENV_DIR%" (
    python -m venv "%VENV_DIR%"
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Activate and install requirements
call "%VENV_DIR%\Scripts\activate.bat"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

:: Install required packages
echo [3/5] Installing required packages...
python -m pip install --upgrade pip
if exist "%REQUIREMENTS%" (
    pip install -r "%REQUIREMENTS%"
) else (
    pip install pyinstaller PyQt6 scapy pandas numpy psutil pyqtgraph dash plotly flask dash-bootstrap-components dash-daq flask-compress
)

:: Build the executable
echo [4/5] Building executable with PyInstaller...
set "PYINSTALLER_CMD=pyinstaller --noconfirm --clean --onefile --windowed"
set "PYINSTALLER_CMD=%PYINSTALLER_CMD% --name "%APP_NAME%""
set "PYINSTALLER_CMD=%PYINSTALLER_CMD% --add-data "gui_flow_extractor_full.py;.""
set "PYINSTALLER_CMD=%PYINSTALLER_CMD% --add-data "realtime_analysis.py;.""
set "PYINSTALLER_CMD=%PYINSTALLER_CMD% --add-data "images;images""

:: Add hidden imports and collect data files
set "HIDDEN_IMPORTS=PyQt6.QtWebEngineWidgets PyQt6.QtWebEngineCore PyQt6.QtWebEngineQuick"
set "HIDDEN_IMPORTS=%HIDDEN_IMPORTS% scapy numpy pandas psutil pyqtgraph dash plotly flask"
set "HIDDEN_IMPORTS=%HIDDEN_IMPORTS% werkzeug dash_bootstrap_components dash_daq flask_compress"
set "HIDDEN_IMPORTS=%HIDDEN_IMPORTS% flask_compress.gzip"

for %%i in (%HIDDEN_IMPORTS%) do (
    set "PYINSTALLER_CMD=!PYINSTALLER_CMD! --hidden-import %%i"
)

:: Add data files
set "DATA_FILES=gui_flow_extractor_full.py realtime_analysis.py requirements.txt"
set "DATA_DIRS=images"

for %%f in (%DATA_FILES%) do (
    if exist "%%f" (
        set "PYINSTALLER_CMD=!PYINSTALLER_CMD! --add-data "%%f;.""
    )
)

for %%d in (%DATA_DIRS%) do (
    if exist "%%d" (
        set "PYINSTALLER_CMD=!PYINSTALLER_CMD! --add-data "%%d;%%d""
    )
)

:: Add icon if exists
if exist "%ICON_FILE%" (
    set "PYINSTALLER_CMD=%PYINSTALLER_CMD% --icon "%ICON_FILE%""
)

:: Execute PyInstaller
echo Executing: %PYINSTALLER_CMD% "%MAIN_SCRIPT%"
%PYINSTALLER_CMD% "%MAIN_SCRIPT%"

:: Verify build
echo [5/5] Verifying build...
if exist "%DIST_DIR%\%APP_NAME%.exe" (
    echo.
    echo ===================================
    echo    BUILD SUCCESSFUL!
    echo ===================================
    echo.
    echo Executable created at: %~dp0%DIST_DIR%\%APP_NAME%.exe
    echo.
    echo Starting the application...
    timeout /t 2 >nul
    start "" "%DIST_DIR%\%APP_NAME%.exe"
) else (
    echo.
    echo ===================================
    echo    BUILD FAILED
    echo ===================================
    echo.
    echo Check for error messages above
)

echo.
pause
