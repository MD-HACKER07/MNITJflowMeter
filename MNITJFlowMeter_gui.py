import sys
import os
import csv
import time
import numpy as np
import psutil
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog,
    QLabel, QProgressBar, QTableWidget, QTableWidgetItem, QTabWidget, QHBoxLayout,
    QHeaderView, QMessageBox, QLineEdit, QComboBox, QStatusBar, QStyleFactory,
    QTextEdit, QSplitter
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPalette, QColor, QAction, QFont, QIcon, QPixmap

import pyqtgraph as pg
from pyqtgraph import PlotWidget, mkPen, mkBrush

# Configure pyqtgraph to use white background and black foreground
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
from scapy.all import rdpcap

# Import our full-featured flow extractor
from gui_flow_extractor_full import FullFlowExtractor

class FlowExtractorThread(QThread):
    """Worker thread for flow extraction to keep the UI responsive"""
    progress_updated = pyqtSignal(int, int, float, float)  # current, total, elapsed_time, memory_usage
    finished = pyqtSignal(pd.DataFrame)  # DataFrame with results
    error_occurred = pyqtSignal(str)  # error message
    status_update = pyqtSignal(str)  # Status update message
    
    def __init__(self, pcap_file):
        super().__init__()
        self.pcap_file = pcap_file
        self.extractor = FullFlowExtractor()
        self._is_running = True
        
    def stop(self):
        """Stop the thread gracefully"""
        self._is_running = False
        self.status_update.emit("Stopping analysis...")
        
    def run(self):
        try:
            self._is_running = True
            
            # Create a wrapper function that properly emits progress
            def progress_callback(current, total, elapsed_time, memory_usage):
                if not self._is_running:
                    return False  # Signal to stop processing
                    
                # Calculate estimated time remaining
                if current > 0 and elapsed_time > 0:
                    remaining_time = (total - current) * (elapsed_time / current)
                    eta = f"ETA: {remaining_time/60:.1f} min"
                else:
                    eta = "Calculating..."
                
                # Update status
                status = f"Processing: {current:,} / {total:,} packets | " \
                        f"Memory: {memory_usage:.1f} MB | {eta}"
                self.status_update.emit(status)
                
                # Emit progress
                self.progress_updated.emit(current, total, elapsed_time, memory_usage)
                return self._is_running
                
            # Process the pcap file with full feature extraction
            self.status_update.emit(f"Starting analysis of {os.path.basename(self.pcap_file)}...")
            self.extractor.process_pcap(self.pcap_file, progress_callback)
            
            if not self._is_running:
                self.status_update.emit("Analysis stopped by user")
                return
                
            self.status_update.emit("Extracting flow features...")
            df = self.extractor.get_flow_dataframe()
            
            if not self._is_running:
                self.status_update.emit("Analysis stopped by user")
                return
                
            self.status_update.emit(f"Extracted {len(df):,} flow records")
            self.finished.emit(df)
            
        except Exception as e:
            import traceback
            error_msg = f"Error during analysis: {str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            self.error_occurred.emit(str(e))
        finally:
            self._is_running = False

class MNITJFlowMeterGUI(QMainWindow):
    def __init__(self):
        # Set up the main window
        super().__init__()
        self.setWindowTitle("MNITJFlowMeter - Network Flow Analysis Tool")
        self.setWindowIconText("MNITJFlowMeter")
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), 'images', 'Logo.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin: 10px;
            }
            QLabel#author {
                font-size: 12px;
                color: #7f8c8d;
                margin-bottom: 15px;
            }
        """)
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize UI elements
        self.main_layout = None
        self.tabs = None
        self.flow_tab = None
        self.stats_tab = None
        self.plot_tab = None
        self.realtime_tab = None
        self.flow_table = None
        self.status_bar = None
        self.progress_bar = None
        self.export_button = None
        self.filter_input = None
        self.apply_filter_button = None
        self.clear_filter_button = None
        self.start_button = None
        self.stop_button = None
        self.pcap_file_label = None
        self.output_dir_label = None
        self.flow_data = None
        self.src_ip_filter = None
        self.dst_ip_filter = None
        self.web_view = None
        
        # Create main layout
        self.main_layout = QVBoxLayout()
        
        # Add title and author
        title_label = QLabel("MNITJFlowMeter - Network Flow Analysis Tool")
        title_label.setObjectName("title")
        author_label = QLabel("Developed by MNIT SIP")
        author_label.setObjectName("author")
        
        # Add title and author to main layout
        self.main_layout.addWidget(title_label)
        self.main_layout.addWidget(author_label)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.flow_tab = QWidget()
        self.stats_tab = QWidget()
        self.plot_tab = QWidget()
        
        # Initialize real-time tab as None, will be created on demand
        self.realtime_tab = None
        self.realtime_initialized = False
        
        # Add tabs
        self.tabs.addTab(self.flow_tab, "Flow Data")
        self.tabs.addTab(self.stats_tab, "Statistics")
        self.tabs.addTab(self.plot_tab, "Plots")
        
        # Add real-time tab placeholder
        self.tabs.addTab(QWidget(), "Real-time Analysis")
        
        # Connect tab change signal
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Set up the UI
        self.init_ui()
        
    def start_realtime_server(self, port=8050):
        """Start the real-time analysis server"""
        try:
            from realtime_analysis import start_server
            # Start the server in a separate thread
            self.server_thread = start_server(port)
            self.realtime_initialized = True
            self.status_bar.showMessage(f"Real-time analysis server started on http://localhost:{port}")
        except Exception as e:
            error_msg = f"Failed to start real-time analysis: {str(e)}"
            print(error_msg)
            self.status_bar.showMessage(error_msg)
    
    def on_tab_changed(self, index):
        """Handle tab change events to initialize real-time tab when selected"""
        if index == 3:  # Real-time Analysis tab
            if not hasattr(self, 'realtime_initialized') or not self.realtime_initialized:
                try:
                    # Set up the real-time tab
                    self.setup_realtime_tab()
                    self.realtime_initialized = True
                except Exception as e:
                    error_msg = f"Failed to initialize real-time analysis: {str(e)}"
                    print(error_msg)
                    self.status_bar.showMessage(error_msg)
        
    def init_ui(self):
        """Initialize the user interface"""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Top panel - File selection and controls
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        
        # File selection
        self.pcap_file_label = QLabel("No file selected")
        self.pcap_file_label.setStyleSheet("color: #ffffff;")
        self.browse_btn = QPushButton("Browse PCAP")
        self.browse_btn.clicked.connect(self.browse_pcap)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        
        # Start analysis button
        self.start_button = QPushButton("Start Analysis")
        self.start_button.clicked.connect(self.start_analysis)
        self.start_button.setEnabled(False)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        
        # Browse Another PCAP button
        self.browse_another_btn = QPushButton("Browse Another PCAP")
        self.browse_another_btn.clicked.connect(self.reset_for_new_pcap)
        self.browse_another_btn.setEnabled(False)
        self.browse_another_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        
        # Export button
        self.export_button = QPushButton("Export to CSV")
        self.export_button.clicked.connect(self.export_to_csv)
        self.export_button.setEnabled(False)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        
        # Stop analysis button
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_analysis)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        
        # Add widgets to top layout
        top_layout.addWidget(QLabel("PCAP File:"))
        top_layout.addWidget(self.pcap_file_label, 1)
        top_layout.addWidget(self.browse_btn)
        top_layout.addWidget(self.start_button)
        top_layout.addWidget(self.stop_button)
        top_layout.addWidget(self.export_button)
        top_layout.addWidget(self.browse_another_btn)
        
        # Progress bar with details
        self.progress_container = QWidget()
        self.progress_layout = QVBoxLayout(self.progress_container)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(5)
        
        # Progress bar with text
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m packets")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #34495e;
                border-radius: 5px;
                text-align: center;
                background-color: #2c3e50;
                color: white;
                height: 25px;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #3498db, stop: 0.5 #9b59b6, stop: 1 #e74c3c
                );
                border-radius: 4px;
                width: 10px;
                margin: 0.5px;
            }
        """)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #95a5a6; font-size: 11px;")
        
        # Stats label
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #bdc3c7; font-size: 10px;")
        
        # Memory usage bar
        self.memory_bar = QProgressBar()
        self.memory_bar.setRange(0, 100)
        self.memory_bar.setValue(0)
        self.memory_bar.setTextVisible(True)
        self.memory_bar.setFormat("Memory: %p%")
        self.memory_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #34495e;
                border-radius: 5px;
                text-align: center;
                background-color: #2c3e50;
                color: white;
                height: 20px;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #2ecc71, stop: 1 #f1c40f
                );
                border-radius: 4px;
                width: 5px;
                margin: 0.5px;
            }
        """)
        
        # Add widgets to progress container
        self.progress_layout.addWidget(self.progress_bar)
        self.progress_layout.addWidget(self.status_label)
        self.progress_layout.addWidget(self.stats_label)
        self.progress_layout.addWidget(self.memory_bar)
        
        # Create tabs
        self.tabs = QTabWidget()
        
        # Flow table tab
        self.flow_table = QTableWidget()
        self.flow_table.setColumnCount(0)
        self.flow_table.setHorizontalHeaderLabels([])
        self.flow_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.flow_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.flow_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.flow_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.flow_table.horizontalHeader().setStretchLastSection(True)
        self.flow_table.verticalHeader().setVisible(False)
        self.flow_table.setSortingEnabled(True)
        self.flow_table.itemSelectionChanged.connect(self.on_flow_selection_changed)
        
        # Add table to scroll area
        table_scroll = QWidget()
        table_layout = QVBoxLayout(table_scroll)
        table_layout.addWidget(self.flow_table)
        
        # Add tabs
        self.tabs.addTab(table_scroll, "Flow Table")
        
        # Add plots tab
        plots_tab = QWidget()
        plots_layout = QVBoxLayout(plots_tab)
        
        # Protocol distribution plot
        protocol_widget = pg.PlotWidget(title="Protocol Distribution")
        protocol_widget.setBackground('w')
        protocol_widget.setLabel('left', 'Count')
        protocol_widget.setLabel('bottom', 'Protocol')
        protocol_widget.showGrid(x=True, y=True)
        self.protocol_plot = protocol_widget
        plots_layout.addWidget(protocol_widget)
        
        # Flow size plot
        flow_size_widget = pg.PlotWidget(title="Flow Size Distribution")
        flow_size_widget.setBackground('w')
        flow_size_widget.setLabel('left', 'Count')
        flow_size_widget.setLabel('bottom', 'Flow Size (bytes)')
        flow_size_widget.showGrid(x=True, y=True)
        self.flow_size_plot = flow_size_widget
        plots_layout.addWidget(flow_size_widget)
        
        # Add plots tab
        self.tabs.addTab(plots_tab, "Plots")
        
        # Set up real-time analysis tab
        self.setup_realtime_tab()
        
        # Add widgets to main layout with stretch
        layout.addWidget(top_panel)
        layout.addWidget(self.progress_container)
        layout.addWidget(self.tabs, 1)  # Add stretch to make tabs expandable
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Set style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            QLabel {
                color: #ecf0f1;
            }
            QTableWidget {
                background-color: #34495e;
                color: #ecf0f1;
                gridline-color: #7f8c8d;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: #ecf0f1;
                padding: 5px;
                border: 1px solid #7f8c8d;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTabWidget::pane {
                border: 1px solid #7f8c8d;
                background: #34495e;
            }
            QTabBar::tab {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 8px 16px;
                border: 1px solid #7f8c8d;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #3498db;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
        """)
    
    def browse_pcap(self):
        """Open a file dialog to select a PCAP file"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open PCAP File", "", "PCAP Files (*.pcap *.pcapng);;All Files (*)")
            
        if file_name:
            self.pcap_file = file_name
            self.pcap_file_label.setText(os.path.basename(file_name))
            if hasattr(self, 'start_button') and self.start_button is not None:
                self.start_button.setEnabled(True)
            if hasattr(self, 'browse_another_btn') and self.browse_another_btn is not None:
                self.browse_another_btn.setEnabled(False)
            if hasattr(self, 'status_bar') and self.status_bar is not None:
                self.status_bar.showMessage(f"Selected: {file_name}")
                
    def on_flow_selection_changed(self):
        """Handle flow selection change"""
        if not hasattr(self, 'flow_table') or self.flow_table is None:
            return
            
        selected_items = self.flow_table.selectedItems()
        if not selected_items:
            return
            
        # Get the selected row data
        row = selected_items[0].row()
        flow_data = {}
        for col in range(self.flow_table.columnCount()):
            header_item = self.flow_table.horizontalHeaderItem(col)
            if header_item is not None:
                header = header_item.text()
                item = self.flow_table.item(row, col)
                if item is not None:
                    flow_data[header] = item.text()
        
        # Update the status bar
        if hasattr(self, 'status_bar') and self.status_bar is not None:
            self.status_bar.showMessage(f"Selected flow: {flow_data.get('Source IP', '')} → {flow_data.get('Dest IP', '')}")
    
    def set_dark_theme(self):
        # Set the dark theme for the application
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
        # Apply the dark palette
        app = QApplication.instance()
        if app is not None:
            app.setPalette(dark_palette)
            
            # Set the style sheet for better dark theme support
            app.setStyle("Fusion")
    
    def start_analysis(self):
        """Start the flow extraction process"""
        if not hasattr(self, 'pcap_file') or not self.pcap_file:
            QMessageBox.warning(self, "Error", "No PCAP file selected")
            return
            
        if not os.path.exists(self.pcap_file):
            QMessageBox.critical(self, "Error", f"File not found: {self.pcap_file}")
            return
            
        try:
            # Get file size for stats
            file_size = os.path.getsize(self.pcap_file) / (1024 * 1024)  # in MB
            
            # Disable UI elements during analysis
            self.start_button.setEnabled(False)
            self.browse_btn.setEnabled(False)
            self.browse_another_btn.setEnabled(False)
            self.export_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # Reset progress and stats
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)  # Will be updated with actual packet count
            self.status_label.setText("Initializing analysis...")
            self.stats_label.setText(f"File: {os.path.basename(self.pcap_file)} | Size: {file_size:.1f} MB")
            self.memory_bar.setValue(0)
            
            # Update memory stats
            self.update_memory_usage()
            
            # Create and start worker thread
            self.worker_thread = FlowExtractorThread(self.pcap_file)
            self.worker_thread.progress_updated.connect(self.update_progress)
            self.worker_thread.finished.connect(self.analysis_finished)
            self.worker_thread.error_occurred.connect(self.analysis_error)
            self.worker_thread.status_update.connect(self.update_status)
            self.worker_thread.start()
            
            # Start memory monitoring timer
            self.memory_timer = QTimer(self)
            self.memory_timer.timeout.connect(self.update_memory_usage)
            self.memory_timer.start(1000)  # Update every second
            
            # Update status
            self.status_bar.showMessage("Analysis in progress...")
            
        except Exception as e:
            self.analysis_error(f"Failed to start analysis: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def analysis_finished(self, df):
        """Handle analysis completion"""
        try:
            # Store the results
            self.flow_data = df
            
            # Update UI
            self.update_flow_table(df)
            self.update_statistics(df)
            self.update_plots(df)
            
            # Update status with analysis summary
            if df is not None and not df.empty:
                total_bytes = df['totlen_fwd_pkts'].sum() + df['totlen_bwd_pkts'].sum()
                total_packets = df['tot_fwd_pkts'].sum() + df['tot_bwd_pkts'].sum()
                duration = df['flow_duration'].max() - df['flow_duration'].min()
                
                summary = (
                    f"Analysis completed: {len(df):,} flows | "
                    f"{total_packets:,} packets | "
                    f"{total_bytes/1024/1024:,.1f} MB | "
                    f"Duration: {duration:.1f}s"
                )
                self.status_bar.showMessage(summary)
                self.status_label.setText("Analysis completed successfully")
                
                # Update stats label with summary
                self.stats_label.setText(
                    f"Flows: {len(df):,} | Packets: {total_packets:,} | "
                    f"Data: {total_bytes/1024/1024:,.1f} MB | "
                    f"Duration: {duration:.1f}s"
                )
            else:
                self.status_bar.showMessage("Analysis completed - No flows found")
                self.status_label.setText("No network flows detected in the capture")
            
            # Enable export button
            self.export_button.setEnabled(True)
            self.browse_another_btn.setEnabled(True)
            
            # Clean up
            self.cleanup_after_analysis()
            
        except Exception as e:
            self.analysis_error(f"Error in analysis results: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Clean up even if there was an error
            self.cleanup_after_analysis()
    
    def analysis_error(self, error_message):
        """Handle errors during analysis"""
        QMessageBox.critical(self, "Analysis Error", error_message)
        self.status_bar.showMessage("Analysis failed")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.export_button.setEnabled(hasattr(self, 'flow_data') and self.flow_data is not None)
        self.browse_btn.setEnabled(True)
        self.browse_another_btn.setEnabled(False)
        self.progress_bar.setValue(0)

    def update_progress(self, current, total, elapsed_time, memory_usage):
        """Update the progress bar with detailed information"""
        try:
            # Update progress bar
            if total > 0:
                progress = int((current / total) * 100)
                self.progress_bar.setValue(progress)
                
                # Calculate packet rate
                if elapsed_time > 0:
                    pps = current / elapsed_time if elapsed_time > 0 else 0
                    rate_text = f"{pps:,.1f} pkt/s"
                else:
                    rate_text = "Calculating..."
                
                # Update progress text
                self.progress_bar.setFormat(f"%p% - {current:,} / {total:,} packets | {rate_text}")
                
                # Update memory usage
                self.update_memory_usage()
                
                # Update status with more detailed information
                if elapsed_time > 0:
                    # Calculate ETA
                    remaining = (total - current) * (elapsed_time / current) if current > 0 else 0
                    eta = time.strftime("%H:%M:%S", time.gmtime(remaining))
                    
                    # Update stats
                    self.stats_label.setText(
                        f"Processed: {current:,} / {total:,} packets | "
                        f"Speed: {rate_text} | "
                        f"Elapsed: {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))} | "
                        f"ETA: {eta}"
                    )
                    
        except Exception as e:
            print(f"Error updating progress: {e}")
            import traceback
            traceback.print_exc()
            
    def update_memory_usage(self):
        """Update the memory usage display"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
            
            # Update memory progress bar (0-4GB range)
            memory_percent = min(int((memory_mb / 4096) * 100), 100)
            self.memory_bar.setValue(memory_percent)
            self.memory_bar.setFormat(f"Memory: {memory_mb:.1f} MB")
            
            # Update status label with memory info
            if hasattr(self, 'stats_label'):
                self.stats_label.setText(
                    f"Memory: {memory_mb:.1f} MB | "
                    f"Flows: {len(self.flow_data) if hasattr(self, 'flow_data') and self.flow_data is not None else 0}"
                )
            
            return memory_mb
            
        except Exception as e:
            print(f"Error updating memory usage: {e}")
            return 0
            
    def update_statistics(self, df):
        """Update the statistics display with flow analysis results"""
        try:
            if df is None or df.empty:
                return
                
            # Calculate basic statistics
            total_flows = len(df)
            total_packets = int(df['tot_fwd_pkts'].sum() + df['tot_bwd_pkts'].sum())
            total_bytes = int(df['totlen_fwd_pkts'].sum() + df['totlen_bwd_pkts'].sum())
            avg_flow_duration = df['flow_duration'].mean()
            
            # Get top protocols if available
            protocol_col = next((col for col in ['protocol', 'proto', 'Protocol'] if col in df.columns), None)
            if protocol_col:
                protocol_counts = df[protocol_col].value_counts().head(3)
                top_protocols = ", ".join([f"{proto} ({count})" for proto, count in protocol_counts.items()])
            else:
                top_protocols = "N/A"
                
            # Update status bar with statistics
            stats_text = (
                f"Flows: {total_flows:,} | "
                f"Packets: {total_packets:,} | "
                f"Data: {total_bytes/(1024*1024):.2f} MB | "
                f"Avg Duration: {avg_flow_duration:.2f}s"
            )
            
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(stats_text)
                
            # Update stats label if available
            if hasattr(self, 'stats_label'):
                self.stats_label.setText(
                    f"{stats_text} | Top Protocols: {top_protocols}"
                )
                
        except Exception as e:
            print(f"Error updating statistics: {e}")
            import traceback
            traceback.print_exc()
            
    def update_status(self, message):
        """Update the status label with a message"""
        self.status_label.setText(message)
        self.status_bar.showMessage(message)
    
    def stop_analysis(self):
        """Stop the analysis gracefully"""
        try:
            if hasattr(self, 'worker_thread') and self.worker_thread.isRunning():
                # Stop the worker thread
                self.worker_thread.stop()
                self.status_label.setText("Stopping analysis...")
                self.status_bar.showMessage("Stopping analysis, please wait...")
                
                # Disable stop button to prevent multiple clicks
                self.stop_button.setEnabled(False)
                
                # Set a timer to force quit if not stopped gracefully
                QTimer.singleShot(5000, self.force_stop_analysis)
                
        except Exception as e:
            self.status_bar.showMessage(f"Error stopping analysis: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def force_stop_analysis(self):
        """Force stop the analysis if it's not responding"""
        if hasattr(self, 'worker_thread') and self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()
            self.cleanup_after_analysis()
            self.status_bar.showMessage("Analysis stopped forcefully")
    
    def cleanup_after_analysis(self):
        """Clean up resources after analysis is done or stopped"""
        try:
            # Stop memory timer if it exists
            if hasattr(self, 'memory_timer'):
                self.memory_timer.stop()
                self.memory_timer.deleteLater()
                del self.memory_timer
                
            # Enable/disable UI elements
            self.start_button.setEnabled(True)
            self.browse_btn.setEnabled(True)
            self.browse_another_btn.setEnabled(True)
            self.stop_button.setEnabled(False)
            
            # Update status
            self.status_label.setText("Ready")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
            import traceback
            traceback.print_exc()
            
    def reset_for_new_pcap(self):
        """Reset the UI for a new PCAP file"""
        try:
            # Stop any running analysis
            if hasattr(self, 'worker_thread') and self.worker_thread.isRunning():
                self.stop_analysis()
            
            # Reset UI elements
            self.flow_table.setRowCount(0)
            self.flow_table.setColumnCount(0)
            self.protocol_plot.clear()
            self.flow_size_plot.clear()
            
        except Exception as e:
            print(f"Error resetting for new PCAP: {e}")
            import traceback
            traceback.print_exc()
            
        QApplication.processEvents()

    def update_flow_table(self, flows_df=None):
        """Update the flow table with the given DataFrame"""
        try:
            if flows_df is None:
                if hasattr(self, 'filtered_flows') and self.filtered_flows is not None:
                    flows_df = self.filtered_flows
                elif hasattr(self, 'flow_data') and self.flow_data is not None:
                    flows_df = self.flow_data
                else:
                    return

            if not hasattr(self, 'flow_table') or self.flow_table is None:
                return

            self.flow_table.setSortingEnabled(False)
            self.flow_table.setRowCount(0)

            if flows_df.empty:
                return

            # Make a copy of the dataframe to avoid modifying the original
            display_df = flows_df.copy()
            
            # Replace NaN values with 0 for numeric columns
            for col in display_df.select_dtypes(include=['float64', 'int64']).columns:
                display_df[col] = display_df[col].fillna(0)
            
            # Add SR.NO column as the first column
            display_df.insert(0, 'SR.NO', range(1, len(display_df) + 1))

            # Set column headers
            self.flow_table.setColumnCount(len(display_df.columns))
            self.flow_table.setHorizontalHeaderLabels(display_df.columns)

            # Add data rows
            self.flow_table.setRowCount(len(display_df))
            for row_idx, (_, row) in enumerate(display_df.iterrows()):
                for col_idx, value in enumerate(row):
                    # Format the value, handling different data types
                    display_value = ''
                    if pd.isna(value):
                        display_value = '0'
                    elif isinstance(value, (float, np.floating)):
                        display_value = f"{value:.4f}" if value != 0 else '0'
                    else:
                        display_value = str(value)
                        
                    item = QTableWidgetItem(display_value)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.flow_table.setItem(row_idx, col_idx, item)

            # Resize columns to fit content
            self.flow_table.resizeColumnsToContents()
            self.flow_table.setSortingEnabled(True)

            # Enable export button
            if hasattr(self, 'export_button') and self.export_button is not None:
                self.export_button.setEnabled(True)

            # Update plots with the original data (without SR.NO)
            self.update_plots(flows_df)

        except Exception as e:
            print(f"Error updating flow table: {e}")
            if hasattr(self, 'status_bar') and self.status_bar is not None:
                self.status_bar.showMessage(f"Error updating flow table: {str(e)}")
    
    def update_plots(self, flows_df=None):
        """Update the plots with flow data

        Args:
            flows_df: Optional DataFrame to plot. If None, uses self.filtered_flows
        """
        try:
            # Use provided DataFrame or fall back to filtered_flows
            if flows_df is None:
                if not hasattr(self, 'filtered_flows') or self.filtered_flows is None or self.filtered_flows.empty:
                    if hasattr(self, 'flow_data') and self.flow_data is not None and not self.flow_data.empty:
                        flows_df = self.flow_data
                    else:
                        return
                else:
                    flows_df = self.filtered_flows
                    
            if flows_df is None or flows_df.empty:
                return
            
            # Clear previous plots
            for plot_name in ['protocol_plot', 'flow_size_plot']:
                if hasattr(self, plot_name) and getattr(self, plot_name) is not None:
                    getattr(self, plot_name).clear()
            
            # Protocol distribution plot
            if 'protocol' in flows_df.columns and hasattr(self, 'protocol_plot') and self.protocol_plot is not None:
                protocol_counts = flows_df['protocol'].value_counts()
                if not protocol_counts.empty:
                    try:
                        x = np.arange(len(protocol_counts))
                        y = protocol_counts.values
                        
                        # For single protocol, use bar plot instead of step plot
                        if len(protocol_counts) == 1:
                            bg = pg.BarGraphItem(x=x, height=y, width=0.6, brush=(52, 152, 219, 150))
                            self.protocol_plot.addItem(bg)
                            self.protocol_plot.getAxis('bottom').setTicks([[(0, str(protocol_counts.index[0]))]])
                        else:
                            # For multiple protocols, use step plot
                            self.protocol_plot.plot(x, y, stepMode=True, fillLevel=0, 
                                                 brush=(52, 152, 219, 150))
                            self.protocol_plot.getAxis('bottom').setTicks([[(i, str(p)) for i, p in enumerate(protocol_counts.index)]])
                        
                        # Set better y-axis range
                        y_max = max(y) * 1.1  # Add 10% padding
                        self.protocol_plot.setYRange(0, y_max if y_max > 0 else 1)
                        
                    except Exception as e:
                        print(f"Error creating protocol chart: {e}")
            
            # Flow size plot
            if 'total_bytes' in flows_df.columns and hasattr(self, 'flow_size_plot') and self.flow_size_plot is not None:
                sizes = flows_df['total_bytes'].values
                if len(sizes) > 0:
                    try:
                        y, x = np.histogram(sizes, bins=min(20, len(sizes)))
                        self.flow_size_plot.plot(x, y, stepMode=True, fillLevel=0, brush=(52, 152, 219, 150))
                    except Exception as e:
                        print(f"Error plotting flow size: {e}")
        except Exception as e:
            print(f"Error updating plots: {e}")
    
    def export_to_csv(self):
        """Export the flow data to a CSV file"""
        if self.flow_data is None or self.flow_data.empty:
            QMessageBox.warning(self, "No Data", "No flow data available to export.")
            return
                
        try:
            # Get save file path
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Flow Data", "", "CSV Files (*.csv)")
                
            if not file_path:
                return  # User cancelled
                    
            # Add .csv extension if not present
            if not file_path.lower().endswith('.csv'):
                file_path += '.csv'
                
            # Create a copy of the data to avoid modifying the original
            export_data = self.flow_data.copy()
            
            # Replace NaN values with empty strings for string columns and 0 for numeric columns
            for col in export_data.columns:
                if export_data[col].dtype == 'object':
                    export_data[col] = export_data[col].fillna('')
                else:
                    export_data[col] = export_data[col].fillna(0)
            
            # Export to CSV without index and with proper handling of NaN values
            export_data.to_csv(file_path, index=False, na_rep='')
                
            # Show success message
            if hasattr(self, 'status_bar') and self.status_bar is not None:
                self.status_bar.showMessage(f"Exported {len(export_data)} flows to {file_path}")
            QMessageBox.information(self, "Export Successful", 
                                 f"Successfully exported {len(export_data)} flows to {file_path}")
                
        except Exception as e:
            error_msg = f"Error exporting to CSV: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Export Error", error_msg)
            if hasattr(self, 'status_bar') and self.status_bar is not None:
                self.status_bar.showMessage(f"Export failed: {str(e)}")

    def setup_realtime_tab(self):
        """Set up the real-time analysis tab with web view."""
        try:
            # Get the server port from environment variable or use default
            server_port = os.environ.get('DASH_SERVER_PORT', '8050')
            dashboard_url = f"http://localhost:{server_port}"
            
            # Create the real-time tab if it doesn't exist
            if not hasattr(self, 'realtime_tab') or self.realtime_tab is None:
                self.realtime_tab = QWidget()
            
            # Clear existing layout
            if self.realtime_tab.layout():
                QWidget().setLayout(self.realtime_tab.layout())
            
            # Create main layout
            layout = QVBoxLayout(self.realtime_tab)
            
            # Create web view for the dashboard
            self.web_view = QWebEngineView()
            
            # Set a default page in case the server isn't running yet
            self.web_view.setHtml("""
                <html><body style='background-color:#2d2d2d; color:#e0e0e0; text-align:center; padding:50px;'>
                    <h2>MNITJFlowMeter Real-time Analysis</h2>
                    <p>Starting dashboard server...</p>
                    <p>If this message persists, please check the application logs.</p>
                    <p>Dashboard URL: <a href='{0}' style='color:#3498db;'>{0}</a></p>
                </body></html>
            """.format(dashboard_url))
            
            # Start the server and load the dashboard
            self.start_realtime_server(server_port)
            
            # Try to load the actual dashboard
            self.web_view.setUrl(QUrl(dashboard_url))
            
            # Add refresh button and status label
            btn_refresh = QPushButton("↻ Refresh Dashboard")
            btn_refresh.clicked.connect(self.refresh_dashboard)
            
            # Style the refresh button
            btn_refresh.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    font-size: 14px;
                    border-radius: 4px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #2472a4;
                }
            """)
            
            # Add status label
            self.status_label = QLabel(f"Dashboard URL: {dashboard_url}")
            self.status_label.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 5px;")
            
            # Create top bar layout
            top_bar = QHBoxLayout()
            top_bar.addWidget(btn_refresh)
            top_bar.addStretch()
            top_bar.addWidget(self.status_label)
            
            # Add widgets to main layout
            layout.addLayout(top_bar)
            layout.addWidget(self.web_view)
            
            # Add instructions
            instructions = QLabel(
                "Note: The dashboard shows real-time network flow analysis. "
                "Make sure the real-time analysis server is running."
            )
            instructions.setStyleSheet("color: #e74c3c; font-size: 12px; padding: 10px; background-color: #2c3e50; border-radius: 4px;")
            instructions.setWordWrap(True)
            layout.addWidget(instructions)
            
            # Add or update the tab
            if hasattr(self, 'tabs') and self.tabs is not None:
                tab_index = -1
                for i in range(self.tabs.count()):
                    try:
                        if self.tabs.tabText(i) == "Real-time Analysis":
                            tab_index = i
                            break
                    except Exception:
                        continue
                
                try:
                    if tab_index == -1:
                        # Add new tab
                        self.tabs.addTab(self.realtime_tab, "Real-time Analysis")
                        self.tabs.setCurrentWidget(self.realtime_tab)
                    else:
                        # Update existing tab
                        self.tabs.removeTab(tab_index)
                        self.tabs.insertTab(tab_index, self.realtime_tab, "Real-time Analysis")
                        self.tabs.setCurrentIndex(tab_index)
                except Exception as e:
                    print(f"Error updating tabs: {str(e)}")
                    # Fallback: Just add the tab
                    self.tabs.addTab(self.realtime_tab, "Real-time Analysis")
            
        except Exception as e:
            error_msg = f"Error setting up real-time tab: {str(e)}"
            print(error_msg)
            
            # Fallback to error message
            error_widget = QWidget()
            layout = QVBoxLayout(error_widget)
            
            error_label = QLabel(
                f"<h3>Error Initializing Real-time Analysis</h3>"
                f"<p>{error_msg}</p>"
                "<p>Please ensure all dependencies are installed:</p>"
                "<pre>pip install PyQt6-WebEngine dash plotly</pre>"
            )
            error_label.setWordWrap(True)
            error_label.setOpenExternalLinks(True)
            error_label.setTextFormat(Qt.TextFormat.RichText)
            
            layout.addWidget(error_label)
            
            # Add the error widget to the tab
            if hasattr(self, 'tabs') and self.tabs is not None:
                self.tabs.addTab(error_widget, "Real-time Analysis (Error)")

    def refresh_dashboard(self):
        """Refresh the dashboard web view."""
        try:
            if not hasattr(self, 'web_view') or not self.web_view:
                print("Web view not initialized, setting up real-time tab...")
                self.setup_realtime_tab()
                return
                
            # Get the current server port from environment or use default
            server_port = os.environ.get('DASH_SERVER_PORT', '8050')
            dashboard_url = f"http://localhost:{server_port}"
            
            # Update the status label
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText(f"Dashboard URL: {dashboard_url} (Refreshing...)")
            
            # Force a hard refresh
            self.web_view.setUrl(QUrl(dashboard_url))
            
            # Update the status label after a short delay
            if hasattr(self, 'status_label') and self.status_label:
                QTimer.singleShot(2000, lambda: self.status_label.setText(f"Dashboard URL: {dashboard_url}"))
                
        except Exception as e:
            error_msg = f"Error refreshing dashboard: {str(e)}"
            print(error_msg)
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText(f"Error: {str(e)}")
            
            # Show error message if web view fails to load
            QMessageBox.critical(
                self,
                "Dashboard Error",
                f"Failed to load the dashboard. Please ensure the real-time analysis server is running.\n\nError: {error_msg}"
            )

def main():
    """Main function to start the application"""
    app = QApplication(sys.argv)
    
    # Set application style and palette
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setApplicationName("MNITJFlowMeter")
    app.setApplicationDisplayName("MNITJFlowMeter - Network Flow Analysis Tool")
    
    # Create and show the main window
    window = MNITJFlowMeterGUI()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
