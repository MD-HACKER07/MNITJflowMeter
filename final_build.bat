@echo off
setlocal enabledelayedexpansion

:: Configuration
set "APP_NAME=MNITJFlowMeter"
set "VENV_DIR=venv"
set "REQUIREMENTS=requirements.txt"
set "MAIN_SCRIPT=MNITJFlowMeter_gui.py"
set "ICON_FILE=icon.ico"
set "DIST_DIR=dist"
set "BUILD_SPEC=final_build.spec"

:: Clear screen and show header
echo ===================================
echo    MNITJFlowMeter - Final Build
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
echo [1/6] Cleaning up previous builds...
if exist "build" rmdir /s /q "build"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "__pycache__" rmdir /s /q "__pycache__"
del /s /q *.pyc 2>nul

:: Create spec file
echo [2/6] Creating build configuration...
echo ^# -*- mode: python ; coding: utf-8 -*- > "%BUILD_SPEC%"
echo. >> "%BUILD_SPEC%"
echo block_cipher = None >> "%BUILD_SPEC%"
echo. >> "%BUILD_SPEC%"
echo a = Analysis( >> "%BUILD_SPEC%"
echo     ['%MAIN_SCRIPT%'], >> "%BUILD_SPEC%"
echo     pathex=[], >> "%BUILD_SPEC%"
echo     binaries=[], >> "%BUILD_SPEC%"
echo     datas=[ >> "%BUILD_SPEC%"
echo         ('gui_flow_extractor_full.py', '.'), >> "%BUILD_SPEC%"
echo         ('realtime_analysis.py', '.'), >> "%BUILD_SPEC%"
echo         ('requirements.txt', '.'), >> "%BUILD_SPEC%"
echo         ('images', 'images') >> "%BUILD_SPEC%"
echo     ], >> "%BUILD_SPEC%"
echo     hiddenimports=[ >> "%BUILD_SPEC%"
echo         'PyQt6.QtWebEngineWidgets', >> "%BUILD_SPEC%"
echo         'PyQt6.QtWebEngineCore', >> "%BUILD_SPEC%"
echo         'PyQt6.QtWebEngineQuick', >> "%BUILD_SPEC%"
echo         'scapy', 'scapy.packet', 'scapy.fields', 'scapy.layers.inet', 'scapy.layers.l2', 'scapy.layers.dns', >> "%BUILD_SPEC%"
echo         'numpy', 'pandas', 'psutil', 'pyqtgraph', >> "%BUILD_SPEC%"
echo         'dash', 'plotly', 'flask', 'werkzeug', 'flask_compress', 'flask_compress.gzip', >> "%BUILD_SPEC%"
echo         'dash_bootstrap_components', 'dash_daq' >> "%BUILD_SPEC%"
echo     ], >> "%BUILD_SPEC%"
echo     hookspath=[], >> "%BUILD_SPEC%"
echo     hooksconfig={}, >> "%BUILD_SPEC%"
echo     runtime_hooks=[], >> "%BUILD_SPEC%"
echo     excludes=['_tkinter', 'matplotlib'], >> "%BUILD_SPEC%"
echo     noarchive=False, >> "%BUILD_SPEC%"
echo ) >> "%BUILD_SPEC%"
echo. >> "%BUILD_SPEC%"
echo pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher) >> "%BUILD_SPEC%"
echo. >> "%BUILD_SPEC%"
echo exe = EXE( >> "%BUILD_SPEC%"
echo     pyz, >> "%BUILD_SPEC%"
echo     a.scripts, >> "%BUILD_SPEC%"
echo     a.binaries, >> "%BUILD_SPEC%"
echo     a.zipfiles, >> "%BUILD_SPEC%"
echo     a.datas, >> "%BUILD_SPEC%"
echo     [], >> "%BUILD_SPEC%"
echo     name='%APP_NAME%', >> "%BUILD_SPEC%"
echo     debug=False, >> "%BUILD_SPEC%"
echo     bootloader_ignore_signals=False, >> "%BUILD_SPEC%"
echo     strip=False, >> "%BUILD_SPEC%"
echo     upx=True, >> "%BUILD_SPEC%"
echo     upx_exclude=[], >> "%BUILD_SPEC%"
echo     runtime_tmpdir=None, >> "%BUILD_SPEC%"
echo     console=False, >> "%BUILD_SPEC%"
echo     disable_windowed_traceback=False, >> "%BUILD_SPEC%"
echo     argv_emulation=False, >> "%BUILD_SPEC%"
echo     target_arch=None, >> "%BUILD_SPEC%"
echo     codesign_identity=None, >> "%BUILD_SPEC%"
echo     entitlements_file=None, >> "%BUILD_SPEC%"
if exist "%ICON_FILE%" (
    echo     icon='%ICON_FILE%'^) >> "%BUILD_SPEC%"
) else (
    echo     icon=None^) >> "%BUILD_SPEC%"
)

:: Setup virtual environment
echo [3/6] Setting up virtual environment...
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
echo [4/6] Installing required packages...
python -m pip install --upgrade pip
if exist "%REQUIREMENTS%" (
    pip install -r "%REQUIREMENTS%"
) else (
    pip install pyinstaller PyQt6 scapy pandas numpy psutil pyqtgraph dash plotly flask dash-bootstrap-components dash-daq flask-compress
)

:: Build the executable
echo [5/6] Building executable with PyInstaller...
pyinstaller "%BUILD_SPEC%" --clean

:: Verify build
echo [6/6] Verifying build...
if exist "%DIST_DIR%\%APP_NAME%\%APP_NAME%.exe" (
    echo.
    echo ===================================
    echo    BUILD SUCCESSFUL!
    echo ===================================
    echo.
    echo Executable created at: %~dp0%DIST_DIR%\%APP_NAME%\%APP_NAME%.exe
    echo.
    echo Starting the application...
    timeout /t 2 >nul
    start "" "%DIST_DIR%\%APP_NAME%\%APP_NAME%.exe"
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
