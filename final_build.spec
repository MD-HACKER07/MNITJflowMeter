# -*- mode: python ; coding: utf-8 -*- 
 
block_cipher = None 
 
a = Analysis( 
    ['MNITJFlowMeter_gui.py'], 
    pathex=[], 
    binaries=[], 
    datas=[ 
        ('gui_flow_extractor_full.py', '.'), 
        ('realtime_analysis.py', '.'), 
        ('requirements.txt', '.'), 
        ('images', 'images') 
    ], 
    hiddenimports=[ 
        'PyQt6.QtWebEngineWidgets', 
        'PyQt6.QtWebEngineCore', 
        'PyQt6.QtWebEngineQuick', 
        'scapy', 'scapy.packet', 'scapy.fields', 'scapy.layers.inet', 'scapy.layers.l2', 'scapy.layers.dns', 
        'numpy', 'pandas', 'psutil', 'pyqtgraph', 
        'dash', 'plotly', 'flask', 'werkzeug', 'flask_compress', 'flask_compress.gzip', 
        'dash_bootstrap_components', 'dash_daq' 
    ], 
    hookspath=[], 
    hooksconfig={}, 
    runtime_hooks=[], 
    excludes=['_tkinter', 'matplotlib'], 
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
    icon='icon.ico') 
