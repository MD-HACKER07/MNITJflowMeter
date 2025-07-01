import sys
import os
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog,
    QLabel, QProgressBar, QTableWidget, QTableWidgetItem, QTabWidget, QHBoxLayout,
    QHeaderView, QMessageBox, QStatusBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import pyqtgraph as pg
from optimized_flow_extractor import OptimizedFlowExtractor

# Configure pyqtgraph
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

class FlowExtractorThread(QThread):
    progress_updated = pyqtSignal(int, int)  # current, total
    status_updated = pyqtSignal(str)
    finished = pyqtSignal(pd.DataFrame)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, pcap_file):
        super().__init__()
        self.pcap_file = pcap_file
        self._is_running = True
    
    def run(self):
        try:
            self.status_updated.emit("Initializing...")
            extractor = OptimizedFlowExtractor()
            
            def progress_callback(current, total):
                if not self._is_running:
                    return False
                self.progress_updated.emit(current, total)
                return True
            
            self.status_updated.emit("Processing PCAP file...")
            extractor.process_pcap(self.pcap_file, progress_callback)
            
            if self._is_running:
                self.status_updated.emit("Finalizing...")
                df = extractor.get_flow_dataframe()
                self.finished.emit(df)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def stop(self):
        self._is_running = False

class OptimizedMNITJFlowMeter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pcap_file = None
        self.flow_data = None
        self.worker_thread = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("MNITJFlowMeter - Optimized")
        self.setGeometry(100, 100, 1200, 800)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Top panel
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        
        # File selection
        self.pcap_label = QLabel("PCAP File: Not selected")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_pcap)
        
        # Control buttons
        self.start_btn = QPushButton("Start Analysis")
        self.start_btn.clicked.connect(self.start_analysis)
        self.start_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_analysis)
        self.stop_btn.setEnabled(False)
        
        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.clicked.connect(self.export_to_csv)
        self.export_btn.setEnabled(False)
        
        # Add widgets to top layout
        top_layout.addWidget(self.pcap_label, 1)
        top_layout.addWidget(browse_btn)
        top_layout.addWidget(self.start_btn)
        top_layout.addWidget(self.stop_btn)
        top_layout.addWidget(self.export_btn)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        
        # Flow table
        self.flow_table = QTableWidget()
        self.flow_table.setColumnCount(0)
        self.flow_table.horizontalHeader().setStretchLastSection(True)
        self.flow_table.setSortingEnabled(True)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add widgets to main layout
        layout.addWidget(top_panel)
        layout.addWidget(self.progress)
        layout.addWidget(self.flow_table, 1)  # Take remaining space
    
    def browse_pcap(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open PCAP File", "", "PCAP Files (*.pcap *.pcapng)")
        
        if file_name:
            self.pcap_file = file_name
            self.pcap_label.setText(f"PCAP File: {os.path.basename(file_name)}")
            self.start_btn.setEnabled(True)
    
    def start_analysis(self):
        if not self.pcap_file or not os.path.exists(self.pcap_file):
            QMessageBox.warning(self, "Error", "Please select a valid PCAP file")
            return
        
        # Reset UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.export_btn.setEnabled(False)
        self.progress.setValue(0)
        
        # Clear previous data
        self.flow_data = None
        self.flow_table.setRowCount(0)
        self.flow_table.setColumnCount(0)
        
        # Start worker thread
        self.worker_thread = FlowExtractorThread(self.pcap_file)
        self.worker_thread.progress_updated.connect(self.update_progress)
        self.worker_thread.status_updated.connect(self.update_status)
        self.worker_thread.finished.connect(self.analysis_complete)
        self.worker_thread.error_occurred.connect(self.analysis_error)
        self.worker_thread.start()
    
    def stop_analysis(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.wait()
            self.status_bar.showMessage("Analysis stopped")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
    
    def update_progress(self, current, total):
        if total > 0:
            progress = int((current / total) * 100)
            self.progress.setValue(progress)
    
    def update_status(self, message):
        self.status_bar.showMessage(message)
    
    def analysis_complete(self, df):
        try:
            self.flow_data = df
            
            # Update table
            if not df.empty:
                self.flow_table.setRowCount(len(df))
                self.flow_table.setColumnCount(len(df.columns))
                self.flow_table.setHorizontalHeaderLabels(df.columns)
                
                for row_idx, row in df.iterrows():
                    for col_idx, value in enumerate(row):
                        self.flow_table.setItem(
                            row_idx, col_idx, 
                            QTableWidgetItem(str(value))
                        )
                
                # Resize columns to contents
                self.flow_table.resizeColumnsToContents()
            
            # Update UI
            self.export_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_bar.showMessage("Analysis complete")
            
        except Exception as e:
            self.analysis_error(str(e))
    
    def analysis_error(self, error_msg):
        QMessageBox.critical(self, "Analysis Error", error_msg)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_bar.showMessage("Analysis failed")
    
    def export_to_csv(self):
        if self.flow_data is None or self.flow_data.empty:
            QMessageBox.warning(self, "Error", "No data to export")
            return
        
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "", "CSV Files (*.csv)")
        
        if file_name:
            try:
                if not file_name.endswith('.csv'):
                    file_name += '.csv'
                self.flow_data.to_csv(file_name, index=False)
                QMessageBox.information(self, "Success", f"Data exported to {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = OptimizedMNITJFlowMeter()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
