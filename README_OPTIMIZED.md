# MNITJFlowMeter - Optimized Version

An optimized version of MNITJFlowMeter for efficient processing of large PCAP files (1-2GB) with improved memory management and performance.

## Key Optimizations

- **Memory-Efficient Processing**: Processes PCAP files in chunks to minimize memory usage
- **Optimized Flow Extraction**: Faster flow extraction with reduced CPU overhead
- **Responsive UI**: Non-blocking GUI with progress updates
- **Reduced Memory Footprint**: Better memory management for large datasets
- **Faster Analysis**: Optimized algorithms for quicker processing

## Features

- Load and analyze PCAP files
- Extract flow features with detailed statistics
- View flow data in a sortable table
- Export results to CSV
- Memory usage monitoring
- Progress tracking for long-running analyses

## Requirements

- Python 3.8+
- Windows/Linux/macOS
- 4GB+ RAM recommended for large PCAP files

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/MNITJFlowMeter.git
   cd MNITJFlowMeter
   ```

2. Install the required packages:
   ```
   pip install -r requirements_optimized.txt
   ```

## Usage

### Running the Application

1. **Using Python**:
   ```
   python optimized_gui.py
   ```

2. **Using the Batch File (Windows)**:
   ```
   run_optimized.bat
   ```

### Building a Standalone Executable

To create a standalone executable:

1. Run the build script:
   ```
   build_optimized.bat
   ```
   This will create an executable in the `dist` directory.

## How It Works

The optimized version includes several key improvements:

1. **Chunked Processing**: Large PCAP files are processed in smaller chunks to avoid memory issues
2. **Efficient Data Structures**: Uses optimized data structures for flow tracking
3. **Background Processing**: Long-running tasks run in separate threads to keep the UI responsive
4. **Memory Monitoring**: Tracks and displays memory usage during analysis

## Performance Tips

- Close other memory-intensive applications when analyzing large PCAP files
- For extremely large files (>2GB), consider splitting them into smaller chunks
- Monitor memory usage in the status bar during analysis

## Troubleshooting

### Common Issues

1. **Memory Errors**:
   - Close other applications to free up memory
   - Reduce the chunk size in `optimized_flow_extractor.py`

2. **Missing Dependencies**:
   - Run `pip install -r requirements_optimized.txt`
   - Ensure you're using Python 3.8 or later

3. **Application Crashes**:
   - Check the console for error messages
   - Ensure the PCAP file is not corrupted

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Based on the original MNITJFlowMeter
- Uses Scapy for packet processing
- Built with PyQt6 for the GUI
