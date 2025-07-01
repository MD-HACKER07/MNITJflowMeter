#!/bin/bash
echo "Building CICFlowMeter..."
echo "======================="

# Install required packages
echo "Installing required packages..."
pip3 install -r requirements.txt

# Create icon if it doesn't exist
if [ ! -f icon.ico ]; then
    echo "Creating application icon..."
    python3 create_icon.py
fi

# Build the executable using PyInstaller
echo "Building executable..."
python3 -m PyInstaller --clean --noconfirm --windowed --onefile \
    --icon=icon.ico \
    --name=CICFlowMeter \
    --add-data="icon.ico:." \
    cicflowmeter_gui_new.py

echo ""
echo "Build complete!"
echo "The executable is available in the 'dist' folder as 'CICFlowMeter'."
