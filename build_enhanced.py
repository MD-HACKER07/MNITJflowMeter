#!/usr/bin/env python3
"""
Enhanced build script for MNITJFlowMeter Windows executable
"""
import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

def print_header():
    print("=" * 50)
    print("  MNITJFlowMeter - Enhanced Executable Builder")
    print("  Platform: " + platform.system() + " " + platform.machine())
    print("=" * 50)

def install_requirements():
    print("\nInstalling required packages...")
    requirements = [
        "pyinstaller>=5.0",
        "PyQt6>=6.0.0",
        "PyQt6-WebEngine>=6.0.0",
        "pandas",
        "numpy",
        "scapy",
        "pyqtgraph",
        "python-dateutil",
        "pytz"
    ]
    
    for package in requirements:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def build_executable():
    print("\nBuilding CICFlowMeter executable...")
    
    # Paths
    base_dir = Path(__file__).parent
    build_dir = base_dir / "build"
    dist_dir = base_dir / "dist"
    
    # Clean previous builds
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "MNITJFlowMeter",
        "--icon", str(base_dir / "icon.ico") if (base_dir / "icon.ico").exists() else "",
        "--add-data", f"{base_dir / 'images'}{os.pathsep}images",
        "--add-data", f"{base_dir / 'src'}{os.pathsep}src",
    ]
    
    # Filter out any empty strings from the command
    cmd = [arg for arg in cmd if arg]
    
    # Add hidden imports
    hidden_imports = [
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineQuick',
        'scapy',
        'pandas',
        'numpy',
        'pyqtgraph',
        'python_dateutil',
        'pytz'
    ]
    
    for imp in hidden_imports:
        cmd.extend(['--hidden-import', imp])
    
    # Add main script
    cmd.append(str(base_dir / "MNITJFlowMeter_gui.py"))
    
    # Run PyInstaller
    try:
        subprocess.check_call(cmd, cwd=str(base_dir))
        print("\nBuild completed successfully!")
        print(f"The executable is available in: {dist_dir.absolute()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError during PyInstaller execution: {e}")
        return False

def main():
    print_header()
    
    try:
        # Install requirements
        install_requirements()
        
        # Build the executable
        if not build_executable():
            return 1
            
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
