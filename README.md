# MNITJFlowMeter GUI

A modern graphical user interface for MNITJFlowMeter, built with PyQt6 and pyqtgraph.

Developed by MD ABU SHALEM ALAM

## Features

- Modern, dark-themed interface
- Load and analyze PCAP files
- View flow statistics in a sortable table
- Filter flows by protocol, IP address, or port
- Visualize flow data with interactive plots
- Export results to CSV
- Real-time progress updates

## Installation

1. Make sure you have Python 3.8 or later installed.

2. Install the required dependencies:
   ```
   pip install -r requirements-gui.txt
   ```

## Usage

Run the GUI application:
```
python MNITJFlowMeter_gui.py
```

### How to Use

1. Click "Browse PCAP" to select a PCAP file for analysis
2. Click "Start Analysis" to begin processing the PCAP file
3. View the results in the table or visualization tabs
4. Use the filter controls to narrow down the results
5. Export the results to CSV using the "Export to CSV" button

## Keyboard Shortcuts

- `Ctrl+O`: Open a PCAP file
- `Ctrl+E`: Export results to CSV
- `Ctrl+Q`: Quit the application

## Requirements

- Python 3.8+
- PyQt6
- pyqtgraph
- pandas
- numpy
- scapy

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
