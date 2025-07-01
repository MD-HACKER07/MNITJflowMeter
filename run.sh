#!/bin/bash
# MNITJFlowMeter - Run Script
# This script handles the execution of MNITJFlowMeter (use setup.sh for installation)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Version
VERSION="1.1.0"

# Dependencies
REQUIRED_PYTHON_PKGS=(
    "PyQt6"
    "pyqt6-qt6"
    "pyqt6-sip"
    "scapy"
    "pandas"
    "numpy"
    "pyqtgraph"
    "tqdm"
    "matplotlib"
)

# Default port
DEFAULT_PORT=8050

# Function to display header
show_header() {
    clear
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}    MNITJFlowMeter v${VERSION} - Setup & Run${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${YELLOW}This script will set up and run MNITJFlowMeter${NC}"
    echo -e "${YELLOW}with all required dependencies.${NC}\n"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a Python package is installed
is_package_installed() {
    python3 -c "import $1" 2>/dev/null
    return $?
}

# Function to check if virtual environment exists
check_venv() {
    if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
        echo -e "${RED}Virtual environment not found. Please run setup.sh first.${NC}"
        exit 1
    fi
}

# Function to activate virtual environment
activate_venv() {
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo -e "${GREEN}✓ Virtual environment activated${NC}"
        return 0
    else
        echo -e "${RED}Virtual environment not found. Please run setup.sh first.${NC}"
        return 1
    fi
}

# Function to check if required Python packages are installed
check_python_deps() {
    local required_packages=("numpy" "scipy" "scapy" "pandas" "matplotlib" "PyQt6" "dash")
    local missing_packages=()
    
    for pkg in "${required_packages[@]}"; do
        if ! python3 -c "import $pkg" &>/dev/null; then
            missing_packages+=("$pkg")
        fi
    done
    
    if [ ${#missing_packages[@]} -ne 0 ]; then
        echo -e "${RED}Missing required Python packages: ${missing_packages[*]}${NC}"
        echo -e "${YELLOW}Please run setup.sh to install all dependencies.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ All required Python packages are installed${NC}"
    return 0
}

# Function to check if a port is available
is_port_available() {
    local port=$1
    if command_exists lsof; then
        if lsof -i :$port -sTCP:LISTEN -t &>/dev/null; then
            return 1
        fi
    elif command_exists netstat; then
        if netstat -tuln | grep -q ":$port "; then
            return 1
        fi
    fi
    return 0
}

# Function to start the real-time analysis server
start_server() {
    local port=$1
    
    echo -e "\n${GREEN}Starting Real-time Analysis Server on port $port...${NC}"
    python3 -u realtime_analysis.py --port $port &> server.log &
    SERVER_PID=$!
    echo "Server started with PID: $SERVER_PID"
    echo "Server logs are being written to server.log"
    
    # Wait for server to start
    echo -e "${YELLOW}Waiting for server to start...${NC}"
    sleep 5
    
    # Check if server started successfully
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        echo -e "${RED}Error: Failed to start the real-time analysis server. Check server.log for details.${NC}"
        return 1
    fi
    
    return 0
}

# Function to start the GUI
start_gui() {
    echo -e "\n${GREEN}Starting MNITJFlowMeter GUI...${NC}"
    echo -e "If you run into any issues, please check the following:"
    echo "1. Make sure you have all required system dependencies installed"
    echo "2. Check that your Python version is 3.8 or higher"
    echo "3. Verify that all required Python packages are installed"
    echo "4. Check server.log for any server-related errors"
    echo -e "\n${GREEN}Application output:${NC}"
    
    python3 MNITJFlowMeter_gui.py "$@"
}

# Function to check if WebEngine is available
check_webengine() {
    echo -e "${BLUE}Checking for Qt WebEngine...${NC}"
    if ! python3 -c "from PyQt6.QtWebEngineWidgets import QWebEngineView" 2>/dev/null; then
        echo -e "${YELLOW}Warning: Qt WebEngine is not available. The real-time analysis tab will not work.${NC}"
        echo -e "${YELLOW}To enable full functionality, please install the required packages:${NC}"
        echo -e "${YELLOW}  - On Ubuntu/Debian: sudo apt-get install python3-pyqt6.qtwebengine${NC}"
        echo -e "${YELLOW}  - On Fedora: sudo dnf install python3-qt6-qtwebengine${NC}"
        return 1
    fi
    return 0
}

# Function to display help message
show_help() {
    echo -e "${GREEN}MNITJFlowMeter v${VERSION} - Usage${NC}"
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help      Show this help message and exit"
    echo "  -p, --port      Specify a custom port for the analysis server"
    echo "  --no-gui        Run in command-line mode (server only)"
    echo "  --no-server     Run the GUI without starting the analysis server"
    echo ""
    echo "Example: $0 --port 8060"
    exit 0
}

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down processes...${NC}"
    
    if [ -n "$SERVER_PID" ]; then
        echo "Stopping server process $SERVER_PID..."
        kill -TERM "$SERVER_PID" 2>/dev/null || true
    fi
    
    if [ -n "$GUI_PID" ]; then
        echo "Stopping GUI process $GUI_PID..."
        kill -TERM "$GUI_PID" 2>/dev/null || true
    fi
    
    # Deactivate virtual environment if active
    if [ -n "$VIRTUAL_ENV" ]; then
        echo "Deactivating virtual environment..."
        deactivate
    fi
    
    echo -e "${GREEN}Cleanup complete. Goodbye!${NC}"
    exit 0
}

# Function to start the application
start_application() {
    local port=$1
    
    # Check if Python 3.8+ is installed
    if ! command_exists python3; then
        echo -e "${RED}Python 3 is required but not installed. Please install Python 3.8 or higher.${NC}"
        exit 1
    fi
    
    # Verify Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [ "$(printf '%s\n' "3.8" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.8" ]; then
        echo -e "${YELLOW}Warning: Python 3.8 or higher is recommended. Found Python ${PYTHON_VERSION}${NC}"
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Activate virtual environment
    activate_venv
    
    # Check Python dependencies
    check_python_deps
    
    # Check if WebEngine is available
    check_webengine
    
    # Install additional dependencies if needed
    echo -e "${BLUE}Checking for additional dependencies...${NC}"
    for pkg in "${REQUIRED_PYTHON_PKGS[@]}"; do
        if ! is_package_installed "${pkg}"; then
            echo -e "${YELLOW}Installing missing package: ${pkg}${NC}"
            pip install "${pkg}" || {
                echo -e "${RED}Failed to install ${pkg}. Please install it manually.${NC}"
                exit 1
            }
        fi
    done
    
    # Start the real-time analysis server in background
    start_server
    
    # Start the GUI
    start_gui
}

# Main execution function
main() {
    # Show header
    show_header
    
    # Set default modes
    local gui_mode=true
    local server_mode=true
    local custom_port=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--version)
                echo "MNITJFlowMeter v${VERSION}"
                exit 0
                ;;
            -p|--port)
                if [ -n "$2" ] && [[ $2 =~ ^[0-9]+$ ]]; then
                    custom_port="$2"
                    shift
                else
                    echo -e "${RED}Error: Port number required after $1${NC}"
                    show_help
                    exit 1
                fi
                ;;
            --no-gui)
                gui_mode=false
                ;;
            --no-server)
                server_mode=false
                ;;
            --gui)
                gui_mode=true
                ;;
            --server)
                server_mode=true
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
        shift
    done
    
    # Check for required commands and dependencies
    if ! command_exists python3; then
        echo -e "${RED}Python 3 is required but not installed. Please run setup.sh first.${NC}"
        exit 1
    fi
    
    # Check virtual environment
    check_venv
    
    # Activate virtual environment
    activate_venv || exit 1
    
    # Check Python dependencies
    check_python_deps || exit 1
    
    # Handle server port
    PORT=""
    
    if [ -n "$custom_port" ]; then
        # Use custom port if specified
        if is_port_available "$custom_port"; then
            PORT="$custom_port"
        else
            echo -e "${YELLOW}Warning: Port $custom_port is not available. Finding an alternative...${NC}"
        fi
    fi
    
    # Find an available port if not already set
    if [ -z "$PORT" ]; then
        PORTS_TO_TRY=($DEFAULT_PORT 8051 8052 8053 8054 8055 8056 8057 8058 8059)
        
        for port in "${PORTS_TO_TRY[@]}"; do
            if is_port_available "$port"; then
                PORT="$port"
                break
            fi
            echo "Port $port is in use, trying next port..."
        done
        
        if [ -z "$PORT" ]; then
            echo -e "${RED}Error: Could not find an available port. Please close some applications and try again.${NC}"
            exit 1
        fi
    fi
    
    # Export the port for the GUI to use
    export DASH_SERVER_PORT=$PORT
    
    # Start the server if enabled
    if [ "$server_mode" = true ]; then
        echo -e "${GREEN}Starting server on port $PORT...${NC}"
        start_server "$PORT" || {
            echo -e "${RED}Failed to start the server. Check server.log for details.${NC}"
            exit 1
        }
    else
        echo -e "${YELLOW}Server mode disabled. Using existing server on port $PORT${NC}"
    fi
    
    # Start the GUI if enabled
    if [ "$gui_mode" = true ]; then
        echo -e "${GREEN}Starting GUI...${NC}"
        start_gui "$@" &
        GUI_PID=$!
        
        # Wait for GUI to exit
        wait $GUI_PID
    else
        echo -e "${YELLOW}GUI mode disabled. Running in server-only mode.${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop the server.${NC}"
        
        # Keep the script running until interrupted
        trap 'cleanup; exit 0' INT TERM
        while true; do
            sleep 3600
        done
    fi
    
    # Clean up when done
    cleanup
}

# Make sure we're in the script's directory
cd "$(dirname "$0")"

# Execute main function with all arguments
main "$@"
