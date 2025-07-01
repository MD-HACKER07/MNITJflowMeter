@echo off
setlocal enabledelayedexpansion

:: Configuration
set "APP_NAME=MNITJFlowMeter"
set "DIST_DIR=dist"
set "BUILD_DIR=build"
set "WORK_DIR=build_work"
set "SPEC_FILE=%APP_NAME%.spec"
set "ICON_FILE=icon.ico"

:: Clean up
echo [1/5] Cleaning up...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%WORK_DIR%" rmdir /s /q "%WORK_DIR%"
if exist "%SPEC_FILE%" del "%SPEC_FILE%"

:: Create spec file
echo [2/5] Creating build configuration...
echo ^# -*- mode: python ; coding: utf-8 -*- > "%SPEC_FILE%"
echo. >> "%SPEC_FILE%"
echo block_cipher = None >> "%SPEC_FILE%"
echo. >> "%SPEC_FILE%"
echo a = Analysis( >> "%SPEC_FILE%"
echo     ['MNITJFlowMeter_gui.py'], >> "%SPEC_FILE%"
echo     pathex=[], >> "%SPEC_FILE%"
echo     binaries=[], >> "%SPEC_FILE%"
echo     datas=[ >> "%SPEC_FILE%"
echo         ('gui_flow_extractor_full.py', '.'), >> "%SPEC_FILE%"
echo         ('realtime_analysis.py', '.'), >> "%SPEC_FILE%"
echo         ('requirements.txt', '.'), >> "%SPEC_FILE%"
echo         ('images', 'images') >> "%SPEC_FILE%"
echo     ], >> "%SPEC_FILE%"
echo     hiddenimports=[ >> "%SPEC_FILE%"
echo         'PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineCore', 'PyQt6.QtWebEngineQuick', >> "%SPEC_FILE%"
echo         'scapy', 'scapy.packet', 'scapy.fields', 'scapy.layers.inet', 'scapy.layers.l2', 'scapy.layers.dns', >> "%SPEC_FILE%"
echo         'numpy', 'pandas', 'psutil', 'pyqtgraph', >> "%SPEC_FILE%"
echo         'dash', 'plotly', 'flask', 'werkzeug', 'flask_compress', 'flask_compress.gzip', >> "%SPEC_FILE%"
echo         'dash_bootstrap_components', 'dash_daq' >> "%SPEC_FILE%"
echo     ], >> "%SPEC_FILE%"
echo ) >> "%SPEC_FILE%"
echo. >> "%SPEC_FILE%"
echo pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher) >> "%SPEC_FILE%"
echo. >> "%SPEC_FILE%"
echo exe = EXE( >> "%SPEC_FILE%"
echo     pyz, >> "%SPEC_FILE%"
echo     a.scripts, >> "%SPEC_FILE%"
echo     a.binaries, >> "%SPEC_FILE%"
echo     a.zipfiles, >> "%SPEC_FILE%"
echo     a.datas, >> "%SPEC_FILE%"
echo     [], >> "%SPEC_FILE%"
echo     name='%APP_NAME%', >> "%SPEC_FILE%"
echo     debug=False, >> "%SPEC_FILE%"
echo     bootloader_ignore_signals=False, >> "%SPEC_FILE%"
echo     strip=False, >> "%SPEC_FILE%"
echo     upx=True, >> "%SPEC_FILE%"
echo     console=False, >> "%SPEC_FILE%"
if exist "%ICON_FILE%" (
    echo     icon='%ICON_FILE%'^) >> "%SPEC_FILE%"
) else (
    echo     icon=None^) >> "%SPEC_FILE%"
)

:: Install PyInstaller if not found
echo [3/5] Checking dependencies...
pip install pyinstaller

:: Build the executable
echo [4/5] Building executable...
pyinstaller "%SPEC_FILE%" --clean --noconfirm --workpath "%WORK_DIR%" --distpath "%DIST_DIR%"

:: Verify build
echo [5/5] Verifying build...
if exist "%DIST_DIR%\%APP_NAME%\%APP_NAME%.exe" (
    echo.
    echo ===================================
    echo    BUILD SUCCESSFUL!
    echo ===================================
    echo.
    echo Executable created at: %~dp0%DIST_DIR%\%APP_NAME%\%APP_NAME%.exe
    echo.
    echo To run the application:
    echo   1. Navigate to %~dp0%DIST_DIR%\%APP_NAME%\
    echo   2. Double-click %APP_NAME%.exe
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
