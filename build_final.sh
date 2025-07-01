#!/bin/bash

# Create a clean build directory
BUILD_DIR="/tmp/cicflowmeter_final_build"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy necessary files to the build directory
cp cicflowmeter_gui_new.py "$BUILD_DIR/"
cp icon.ico "$BUILD_DIR/"
cp requirements.txt "$BUILD_DIR/"

# Create a new virtual environment in the build directory
cd "$BUILD_DIR"
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install required packages
pip install --upgrade pip
pip install -r requirements.txt
pip install PyQt6-WebEngine

# Create a wrapper script that sets up the environment and runs the application
cat > run_cicflowmeter.sh << 'EOL'
#!/bin/bash
# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set the Qt plugin path
export QT_DEBUG_PLUGINS=1
export QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox"

# Run the application
"$SCRIPT_DIR/dist/CICFlowMeter" "$@"
EOL

chmod +x run_cicflowmeter.sh

# Build the application with PyInstaller
pyinstaller \
    --clean \
    --noconfirm \
    --windowed \
    --onefile \
    --icon=icon.ico \
    --name=CICFlowMeter \
    --add-data="icon.ico:." \
    --hidden-import="PyQt6.QtWebEngineWidgets" \
    --hidden-import="PyQt6.QtWebEngineCore" \
    --hidden-import="PyQt6.QtWebEngineQuick" \
    --exclude-module="_tkinter" \
    --exclude-module="matplotlib.tests" \
    --exclude-module="numpy.random._examples" \
    cicflowmeter_gui_new.py

# Copy the final executable to the project directory
cp "$BUILD_DIR/dist/CICFlowMeter" "/home/avinash-awasthi/Pictures/new/MNITJFlowMeter (2)/CICFlowMeter_final"

# Make the final executable executable
chmod +x "/home/avinash-awasthi/Pictures/new/MNITJFlowMeter (2)/CICFlowMeter_final"

echo "Build complete! The final executable is available as CICFlowMeter_final in your project directory."
