@echo off
REM Batch file to run the optimized MNITJFlowMeter

echo Starting MNITJFlowMeter (Optimized Version)...
echo =======================================

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking required packages...
python -c "import PyQt6, scapy, pandas, pyqtgraph" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing required packages...
    pip install -r requirements_optimized.txt
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install required packages
        pause
        exit /b 1
    )
)

REM Run the optimized MNITJFlowMeter
echo Starting application...
python optimized_gui.py

if %ERRORLEVEL% NEQ 0 (
    echo An error occurred while running MNITJFlowMeter
    pause
    exit /b 1
)

exit /b 0
