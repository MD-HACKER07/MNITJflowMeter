#!/usr/bin/env python3
"""
Build script for creating CICFlowMeter GUI executable
"""
import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

def check_dependencies():
    """Check if required tools are installed"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def install_dependencies():
    """Install required Python packages"""
    print("Installing required dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def create_spec_file():
    """Create PyInstaller spec file"""
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['cicflowmeter_gui_new.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'scapy',
        'scapy.packet',
        'scapy.fields',
        'scapy.layers.inet',
        'scapy.layers.l2',
        'scapy.sendrecv',
        'scapy.utils',
        'pandas',
        'numpy',
        'pyqtgraph',
        'pyqtgraph.graphicsItems',
        'pyqtgraph.graphicsItems.PlotItem',
        'pyqtgraph.graphicsItems.ViewBox',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

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
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'
)
"""
    with open("CICFlowMeter.spec", "w") as f:
        f.write(spec_content)

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building executable...")
    
    # Create dist and build directories if they don't exist
    os.makedirs("dist", exist_ok=True)
    os.makedirs("build", exist_ok=True)
    
    # Build the executable
    subprocess.check_call([
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "--windowed",
        "--onefile",
        "--icon=icon.ico",
        "--name=CICFlowMeter",
        "--add-data=icon.ico;.",
        "cicflowmeter_gui_new.py"
    ])

def create_installer():
    """Create an installer (Windows only)"""
    if platform.system() != "Windows":
        print("Skipping installer creation (only supported on Windows)")
        return
        
    print("Creating installer...")
    try:
        import PyInstaller.__main__
        
        # Create NSIS installer
        subprocess.check_call([
            "makensis",
            f"-DVERSION={get_version()}",
            "installer.nsi"
        ])
    except Exception as e:
        print(f"Error creating installer: {e}")

def get_version():
    """Get version from the code"""
    try:
        with open("cicflowmeter_gui_new.py", "r") as f:
            for line in f:
                if line.startswith("VERSION ="):
                    return line.split("=")[1].strip().strip('"\'')
    except Exception:
        pass
    return "1.0.0"

def main():
    """Main function"""
    print("CICFlowMeter Build Tool")
    print("======================")
    
    # Check if running on Windows
    if platform.system() != "Windows":
        print("Warning: This build script is optimized for Windows. Some features may not work on other platforms.")
    
    # Check if PyInstaller is installed
    if not check_dependencies():
        print("PyInstaller not found. Installing required dependencies...")
        install_dependencies()
    
    try:
        # Create spec file
        create_spec_file()
        
        # Build the executable
        build_executable()
        
        # Create installer (Windows only)
        if platform.system() == "Windows":
            create_installer()
            
        print("\nBuild completed successfully!")
        print(f"Executable location: {os.path.abspath('dist/CICFlowMeter')}")
        
    except Exception as e:
        print(f"Error during build: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
