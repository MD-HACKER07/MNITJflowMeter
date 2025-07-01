#!/usr/bin/env python3
"""
Build script for creating MNITJFlowMeter Windows executable with logo
"""
import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
from PIL import Image

def print_header():
    print("=" * 50)
    print("  MNITJFlowMeter - Executable Builder")
    print("  Platform: " + platform.system() + " " + platform.machine())
    print("=" * 50)

def check_dependencies():
    required = ['PyInstaller', 'Pillow']
    missing = []
    
    for package in required:
        try:
            __import__(package.lower())
        except ImportError:
            missing.append(package)
    
    return missing

def install_dependencies():
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "Pillow"])

def convert_logo_to_ico():
    """Convert PNG logo to ICO format for Windows"""
    logo_path = Path("images/Logo.png")
    ico_path = Path("images/icon.ico")
    
    if not logo_path.exists():
        print(f"Error: Logo not found at {logo_path}")
        return False
    
    try:
        img = Image.open(logo_path)
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        # Save as ICO
        img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        print(f"Created icon file at: {ico_path}")
        return True
    except Exception as e:
        print(f"Error converting logo to ICO: {e}")
        return False

def build_executable():
    print("\nBuilding CICFlowMeter executable...")
    
    # Paths
    base_dir = Path(__file__).parent
    build_dir = base_dir / "build"
    dist_dir = base_dir / "dist"
    icon_path = base_dir / "images" / "icon.ico"
    
    # Clean previous builds
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # Convert logo to ICO if needed
    if not icon_path.exists():
        if not convert_logo_to_ico():
            print("Warning: Could not create icon file. Building without custom icon.")
            icon_path = None
    
    # Main application script
    main_script = "MNITJFlowMeter_gui.py"
    if not os.path.exists(main_script):
        print(f"Error: Main script not found at {main_script}")
        return False
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "MNITJFlowMeter",
        "--add-data", f"{base_dir / 'src/mnitjflowmeter'}{os.pathsep}mnitjflowmeter",
        "--add-data", f"{base_dir / 'images'}{os.pathsep}images",
    ]
    
    # Add icon if available
    if icon_path and icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    # Add hidden imports
    hidden_imports = [
        'scapy', 'pandas', 'numpy', 'PyQt6', 'pyqtgraph',
        'dash', 'dash_bootstrap_components', 'dash_daq', 'plotly',
        'matplotlib', 'python_dateutil', 'pytz', 'tzdata', 'pyshark',
        'scapy.layers.l2', 'scapy.layers.inet', 'scapy.layers.inet6'
    ]
    
    for imp in hidden_imports:
        cmd.extend(['--hidden-import', imp])
    
    # Add main script
    cmd.append(str(main_script))
    
    # Run PyInstaller
    try:
        subprocess.check_call(cmd, cwd=str(base_dir))
    except subprocess.CalledProcessError as e:
        print(f"Error during PyInstaller execution: {e}")
        return False
    
    # Create distribution package
    dist_dir = base_dir / "dist" / "MNITJFlowMeter"
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    exe_name = "MNITJFlowMeter.exe" if sys.platform == 'win32' else "MNITJFlowMeter"
    exe_src = base_dir / "dist" / exe_name
    if exe_src.exists():
        shutil.copy(exe_src, dist_dir / exe_name)
    
    # Copy additional files
    files_to_copy = [
        ("README.md", "README.txt"),
        ("LICENSE", "LICENSE.txt")
    ]
    
    for src, dst in files_to_copy:
        src_path = base_dir / src
        if src_path.exists():
            shutil.copy(src_path, dist_dir / dst)
    
    # Create a batch file for Windows
    if sys.platform == 'win32':
        with open(dist_dir / "run.bat", "w") as f:
            f.write('@echo off\n')
            f.write('start "" "%~dp0MNITJFlowMeter.exe" %*\n')
    else:
        # Create a shell script for Linux/macOS
        with open(dist_dir / "run.sh", "w") as f:
            f.write('#!/bin/bash\n')
            f.write('cd "$(dirname "$0")"\n')
            f.write('./MNITJFlowMeter "$@"\n')
        os.chmod(dist_dir / "run.sh", 0o755)
    
    print("\nBuild completed successfully!")
    print(f"The executable is available in: {dist_dir.absolute()}")
    return True

def main():
    print_header()
    
    # Check for missing dependencies
    missing = check_dependencies()
    if missing:
        print(f"Missing required packages: {', '.join(missing)}")
        try:
            install_dependencies()
        except Exception as e:
            print(f"Error installing dependencies: {e}")
            return 1
    
    # Build the executable
    try:
        if not build_executable():
            return 1
    except Exception as e:
        print(f"Error building executable: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
