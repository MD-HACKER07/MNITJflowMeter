#!/bin/bash

# Create a clean build directory
BUILD_DIR="/tmp/cicflowmeter_complete_build"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy all Python files and necessary resources to the build directory
cp *.py "$BUILD_DIR/" 2>/dev/null || true
cp *.ico "$BUILD_DIR/" 2>/dev/null || true
cp requirements.txt "$BUILD_DIR/"

# Create a new virtual environment in the build directory
cd "$BUILD_DIR"
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install required packages
pip install --upgrade pip
pip install -r requirements.txt
pip install PyQt6-WebEngine

# Create a spec file that includes all Python files
cat > cicflowmeter.spec << 'EOL'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['cicflowmeter_gui_new.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineQuick',
        'attack_detection',
        'flow_session_integration',
        'gui_flow_extractor',
        'export_packets',
        'enhanced_flow_extractor',
        'process_pcap',
        'realtime_analysis',
        'simple_flow_analyzer',
        'simple_flow_extractor',
        'test_flow_extractor',
    ],
    hookspath=[],
    hooksconfig={},
    excludes=['_tkinter', 'matplotlib.tests', 'numpy.random._examples'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add all Python files as data files
for file in *.py; do
    if [ "$file" != "cicflowmeter_gui_new.py" ]; then
        a.datas += [(file, '.', 'DATA')]
    fi
done

# Add icon if it exists
if [ -f "icon.ico" ]; then
    a.datas += [('icon.ico', '.', 'DATA')]
fi

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CICFlowMeter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
EOL

# Build the application with PyInstaller
pyinstaller --clean --noconfirm cicflowmeter.spec

# Create a wrapper script that sets up the environment
cat > run_cicflowmeter.sh << 'EOL2'
#!/bin/bash
# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set the Qt plugin path
export QT_DEBUG_PLUGINS=1
export QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox"

# Copy all Python files to the current directory
for file in "$SCRIPT_DIR"/*.py; do
    if [ -f "$file" ]; then
        cp "$file" "./"
    fi
done

# Run the application
"$SCRIPT_DIR/dist/CICFlowMeter" "$@"
EOL2

chmod +x run_cicflowmeter.sh

# Copy the final executable to the project directory
cp "$BUILD_DIR/dist/CICFlowMeter" "/home/avinash-awasthi/Pictures/new/MNITJFlowMeter (2)/CICFlowMeter_complete"

# Make the final executable executable
chmod +x "/home/avinash-awasthi/Pictures/new/MNITJFlowMeter (2)/CICFlowMeter_complete"

echo "Build complete! The final executable is available as CICFlowMeter_complete in your project directory."
