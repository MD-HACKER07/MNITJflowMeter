#!/bin/bash

# MNITJFlowMeter - Setup Script
# This script handles the setup of MNITJFlowMeter

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Version
VERSION="1.0.0"

# Function to display header
show_header() {
    clear
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}    MNITJFlowMeter v${VERSION} - Setup${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${YELLOW}This script will set up MNITJFlowMeter${NC}"
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

# Function to install system dependencies
install_system_deps() {
    echo -e "\n${BLUE}Checking for system dependencies...${NC}"
    
    # Check for Python 3.8+
    if ! command_exists python3; then
        echo -e "${RED}Python 3 is required but not installed.${NC}"
        install_python
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c "import sys; print('{0[0]}.{0[1]}'.format(sys.version_info))")
    if [[ "$PYTHON_VERSION" < "3.8" ]]; then
        echo -e "${RED}Python 3.8 or higher is required. Found Python ${PYTHON_VERSION}${NC}"
        install_python
    fi
    
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION} is installed${NC}"
    
    # Check for pip
    if ! command_exists pip3; then
        echo -e "${YELLOW}pip3 not found. Installing pip...${NC}"
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt-get update
            sudo apt-get install -y python3-pip
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
            python3 get-pip.py
            rm get-pip.py
        fi
    fi
    
    echo -e "${GREEN}✓ pip is installed${NC}"
    
    # Install virtualenv if not present
    if ! command_exists virtualenv; then
        echo -e "${YELLOW}Installing virtualenv...${NC}"
        pip3 install --user virtualenv
    fi
    
    echo -e "${GREEN}✓ virtualenv is installed${NC}"
}

# Function to install Python if not found
install_python() {
    echo -e "\n${YELLOW}Installing Python 3.8+...${NC}"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Debian/Ubuntu
        if command_exists apt-get; then
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv
        # Fedora
        elif command_exists dnf; then
            sudo dnf install -y python3 python3-pip python3-venv
        # CentOS/RHEL
        elif command_exists yum; then
            sudo yum install -y python3 python3-pip python3-venv
        # Arch Linux
        elif command_exists pacman; then
            sudo pacman -S --noconfirm python python-pip python-virtualenv
        else
            echo -e "${RED}Could not determine package manager. Please install Python 3.8+ manually.${NC}"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            brew install python@3.9
        else
            echo -e "${YELLOW}Homebrew not found. Please install Python 3.8+ manually or install Homebrew.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Unsupported operating system. Please install Python 3.8+ manually.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Python installation complete${NC}"
}

# Function to create and activate virtual environment
setup_venv() {
    echo -e "\n${BLUE}Setting up Python virtual environment...${NC}"
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    else
        echo -e "${YELLOW}Virtual environment already exists${NC}"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
}

# Function to install Python dependencies
install_python_deps() {
    echo -e "\n${BLUE}Installing Python dependencies...${NC}"
    
    # Make sure we're in the virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        source venv/bin/activate
    fi
    
    # Upgrade pip and setuptools
    python -m pip install --upgrade pip setuptools
    
    # Install core dependencies from requirements.txt if it exists
    if [ -f "requirements.txt" ]; then
        echo -e "${BLUE}Installing dependencies from requirements.txt...${NC}"
        pip install -r requirements.txt
    else
        echo -e "${YELLOW}requirements.txt not found. Installing default dependencies...${NC}"
        pip install numpy scipy scapy requests pytest
    fi
    
    # Install additional required packages
    echo -e "${BLUE}Installing additional required packages...${NC}"
    pip install \
        pandas \
        matplotlib \
        PyQt6 \
        PyQt6-WebEngine \
        PyQt6-Qt6 \
        PyQt6-sip \
        pyqtgraph \
        dash \
        dash-bootstrap-components \
        dash-daq \
        plotly \
        scipy \
        numpy \
        scapy \
        requests \
        pytest \
        tqdm \
        python-dateutil \
        importlib-metadata \
        typing-extensions \
        nest-asyncio \
        retrying \
        Flask \
        Werkzeug \
        Jinja2 \
        itsdangerous \
        click \
        blinker \
        packaging \
        pyparsing \
        kiwisolver \
        pillow \
        contourpy \
        fonttools \
        cycler \
        pytz \
        tzdata \
        setuptools \
        altgraph \
        pyinstaller-hooks-contrib \
        pyinstaller
    
    # Install the package in development mode if setup.py exists
    if [ -f "setup.py" ]; then
        echo -e "${BLUE}Installing package in development mode...${NC}"
        pip install -e .
    fi
    
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
}

# Function to display help message
show_help() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -h, --help     Show this help message and exit"
    echo "  -v, --version  Show version information and exit"
    exit 0
}

# Main execution function
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                ;;
            -v|--version)
                echo "MNITJFlowMeter Setup v${VERSION}"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                ;;
        esac
    done
    
    show_header
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        echo -e "${YELLOW}Warning: It's not recommended to run this script as root.${NC}"
        read -p "Do you want to continue? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Start setup process
    install_system_deps
    setup_venv
    install_python_deps
    
    echo -e "\n${GREEN}✓ Setup completed successfully!${NC}"
    echo -e "To run MNITJFlowMeter, use: ${YELLOW}./run.sh${NC}"
    echo -e "To activate the virtual environment manually, run: ${YELLOW}source venv/bin/activate${NC}"
}

# Make sure we're in the script's directory
cd "$(dirname "$0")"

# Execute main function with all arguments
main "$@"