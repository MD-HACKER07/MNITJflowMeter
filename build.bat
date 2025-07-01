@echo off
echo Building CICFlowMeter...
echo =======================

:: Install required packages
echo Installing required packages...
pip install -r requirements.txt

:: Create icon if it doesn't exist
if not exist icon.ico (
    echo Creating application icon...
    python create_icon.py
)

:: Build the executable using PyInstaller
echo Building executable...
python -m PyInstaller --clean --noconfirm --windowed --onefile \
    --icon=icon.ico \
    --name=CICFlowMeter \
    --add-data="icon.ico;." \
    cicflowmeter_gui_new.py

echo.
echo Build complete!
echo The executable is available in the 'dist' folder as 'CICFlowMeter.exe'.
pause
