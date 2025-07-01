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
        'pyqtgraph.graphicsItems',
        'pyqtgraph.graphicsItems.PlotItem',
        'dash',
        'dash.dependencies',
        'dash.dcc',
        'dash.html',
        'dash.dash_table',
        'dash_bootstrap_components',
        'dash.dash_table.FormatTemplate',
        'dash.dash_table.Format',
        'dash_daq',
        'plotly',
        'flask',
        'flask_compress',
        'werkzeug.middleware.proxy_fix'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['_tkinter', 'matplotlib', 'scipy', 'pytest', 'unittest', 'email'],
    noarchive=False,
    optimize=1,
)

# Add data files
a.datas += [('gui_flow_extractor_full.py', '.', 'DATA')]
a.datas += [('realtime_analysis.py', '.', 'DATA')]
a.datas += [('requirements.txt', '.', 'DATA')]

# Add images directory if it exists
if os.path.isdir('images'):
    for root, dirs, files in os.walk('images'):
        for file in files:
            src = os.path.join(root, file)
            dst = os.path.join('images', os.path.relpath(root, 'images'))
            a.datas += [(src, dst, 'DATA')]

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
    console=True,  # Set to False for production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
