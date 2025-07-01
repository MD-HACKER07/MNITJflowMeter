# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['MNITJFlowMeter_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineQuick',
        'scapy',
        'scapy.packet',
        'scapy.fields',
        'scapy.layers.inet',
        'scapy.layers.l2',
        'scapy.layers.dns',
        'numpy',
        'pandas',
        'psutil',
        'pyqtgraph',
        'dash',
        'plotly',
        'flask',
        'werkzeug',
        'dash_bootstrap_components',
        'dash_daq',
        'flask_compress',
        'flask_compress.gzip'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['_tkinter', 'matplotlib'],
    noarchive=False,
)

# Add data files
a.datas += Tree('images', prefix='images')

# Add Python files as data files
for f in ['gui_flow_extractor_full.py', 'realtime_analysis.py', 'requirements.txt']:
    if os.path.exists(f):
        a.datas.append((f, '.', 'DATA'))

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MNITJFlowMeter',
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
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
