@echo off
REM Build script for MNITJFlowMeter (Optimized Version)

setlocal enabledelayedexpansion

:: Configuration
set APP_NAME=MNITJFlowMeter_Optimized
set BUILD_DIR=build\%APP_NAME%
set DIST_DIR=dist
set SPEC_FILE=%APP_NAME%.spec

:: Clean previous builds
echo Cleaning previous builds...
if exist %BUILD_DIR% rmdir /s /q %BUILD%
if exist %DIST_DIR% rmdir /s /q %DIST_DIR%
if exist %SPEC_FILE% del %SPEC_FILE%

:: Ensure required directories exist
if not exist %BUILD_DIR% mkdir %BUILD_DIR%
if not exist %DIST_DIR% mkdir %DIST_DIR%

:: Install PyInstaller if not present
echo Checking for PyInstaller...
python -m pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install PyInstaller
        pause
        exit /b 1
    )
)

:: Create the executable
echo Creating executable...
python -m PyInstaller ^
    --name %APP_NAME% ^
    --onefile ^
    --windowed ^
    --add-data "optimized_flow_extractor.py;." ^
    --distpath %DIST_DIR% ^
    --workpath %BUILD_DIR% ^
    --specpath . ^
    --hidden-import="scapy" ^
    --hidden-import="scapy.utils" ^
    --hidden-import="scapy.layers.inet" ^
    --hidden-import="scapy.layers.l2" ^
    --hidden-import="scapy.packet" ^
    --hidden-import="PyQt6" ^
    --hidden-import="PyQt6.QtCore" ^
    --hidden-import="PyQt6.QtWidgets" ^
    --hidden-import="PyQt6.QtGui" ^
    --hidden-import="pyqtgraph" ^
    --hidden-import="pandas" ^
    --hidden-import="numpy" ^
    --hidden-import="psutil" ^
    --icon=icon.ico ^
    optimized_gui.py

if %ERRORLEVEL% NEQ 0 (
    echo Build failed with error %ERRORLEVEL%
    pause
    exit /b 1
)

:: Create a ZIP archive of the distribution
echo Creating distribution package...
powershell -command "Compress-Archive -Path %DIST_DIR%\%APP_NAME% -DestinationPath %DIST_DIR%\%APP_NAME%.zip -Force"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================
    echo Build completed successfully!
    echo Executable: %DIST_DIR%\%APP_NAME%\%APP_NAME%.exe
    echo Package: %DIST_DIR%\%APP_NAME%.zip
    echo =======================================
) else (
    echo Failed to create distribution package
    pause
    exit /b 1
)

pause
