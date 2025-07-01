import sys
import os
import subprocess
import threading
import time
from PyQt6.QtWidgets import QApplication
import MNITJFlowMeter_gui
import realtime_analysis

def start_server():
    """Start the real-time analysis server in a separate process"""
    try:
        # Get the base path for the executable
        if getattr(sys, 'frozen', False):
            # Running in a bundle
            base_path = sys._MEIPASS
        else:
            # Running in a normal Python environment
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Set the FLASK_APP environment variable
        os.environ['FLASK_APP'] = os.path.join(base_path, 'realtime_analysis.py')
        
        # Start the server
        realtime_analysis.app.run_server(debug=False, host='127.0.0.1', port=8050, use_reloader=False)
    except Exception as e:
        print(f"Failed to start server: {e}")

def main():
    # Start the server in a separate thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Give the server a moment to start
    time.sleep(2)
    
    # Start the GUI
    app = QApplication(sys.argv)
    gui = MNITJFlowMeter_gui.MNITJFlowMeterGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
