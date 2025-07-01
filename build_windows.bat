@echo off
setlocal enabledelayedexpansion

:: Create a virtual environment
python -m venv venv
call venv\Scripts\activate.bat

:: Install required packages
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller PyQt6-WebEngine

:: Create a spec file
(
echo # -*- mode: python ; coding: utf-8 -*-
echo.
echo block_cipher = None
echo.
echo a = Analysis(
echo     ['MNITJFlowMeter_gui.py'],
echo     pathex=[],
echo     binaries=[],
echo     datas=[('icon.ico', '.')],
echo     hiddenimports=[
echo         'PyQt6.QtWebEngineWidgets',
echo         'PyQt6.QtWebEngineCore',
echo         'PyQt6.QtWebEngineQuick',
echo         'attack_detection',
echo         'flow_session_integration',
echo         'gui_flow_extractor',
echo         'export_packets',
echo         'enhanced_flow_extractor',
echo         'process_pcap',
echo         'realtime_analysis',
echo         'simple_flow_analyzer',
echo         'simple_flow_extractor',
echo         'test_flow_extractor',
echo     ],
echo     hookspath=[],
echo     hooksconfig={"PyQt6.sip": {"sip_module": "PyQt6.sip"}},
echo     excludes=['_tkinter', 'matplotlib.tests', 'numpy.random._examples'],
echo     win_no_prefer_redirects=False,
echo     win_private_assemblies=False,
echo     cipher=block_cipher,
echo     noarchive=False,
echo )
echo.
echo for file in ['attack_detection.py', 'flow_session_integration.py', 'gui_flow_extractor.py', 'export_packets.py', 'enhanced_flow_extractor.py', 'process_pcap.py', 'realtime_analysis.py', 'simple_flow_analyzer.py', 'simple_flow_extractor.py', 'test_flow_extractor.py']:
echo     if os.path.exists(file):
echo         a.datas += [(file, '.', 'DATA')]
echo.
echo if os.path.exists('icon.ico'):
echo     a.datas += [('icon.ico', '.', 'DATA')]
echo.
echo pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
echo.
echo exe = EXE(
echo     pyz,
echo     a.scripts,
echo     a.binaries,
echo     a.zipfiles,
echo     a.datas,
echo     [],
echo     name='MNITJFlowMeter_gui',
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=True,
echo     runtime_tmpdir=None,
echo     console=False,
echo     icon='icon.ico',
echo )
) > mnitjflowmeter.spec

:: Build the executable
pyinstaller --clean --noconfirm mnitjflowmeter.spec

echo.
echo Build complete! The executable is in the 'dist' folder.
pause
