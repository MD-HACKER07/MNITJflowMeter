import os
import sys
import PyInstaller.__main__

def build():
    # Get the current directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create a temporary build directory
    build_dir = os.path.join(base_dir, 'build_minimal')
    dist_dir = os.path.join(base_dir, 'dist_minimal')
    
    # Clean up previous builds
    for d in [build_dir, dist_dir]:
        if os.path.exists(d):
            import shutil
            shutil.rmtree(d)
    
    # Define the main script and icon paths
    main_script = os.path.join(base_dir, 'cicflowmeter_gui_new.py')
    icon_file = os.path.join(base_dir, 'icon.ico')
    
    # Build the command
    cmd = [
        '--name=CICFlowMeter',
        f'--workpath={build_dir}',
        f'--distpath={dist_dir}',
        '--windowed',
        '--onefile',
        f'--icon={icon_file}',
        '--clean',
        '--noconfirm',
        '--exclude-module=_tkinter',
        '--exclude-module=matplotlib.tests',
        '--exclude-module=numpy.random._examples',
        f'--add-data={icon_file}:.',
        main_script
    ]
    
    # Run PyInstaller
    PyInstaller.__main__.run(cmd)

if __name__ == '__main__':
    build()
