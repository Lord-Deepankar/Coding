#!/bin/bash

# Universal Python Service Setup Script
# This script creates a systemd service for any Python file
# Usage: ./setup_python_service.sh [python_file] [service_name] [description]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Function to detect Python executable
detect_python() {
    if command -v python3 &> /dev/null; then
        echo "python3"
    elif command -v python &> /dev/null; then
        echo "python"
    else
        print_error "Python is not installed or not in PATH"
        exit 1
    fi
}

# Function to get absolute path
get_absolute_path() {
    local file_path="$1"
    if [[ "$file_path" == /* ]]; then
        echo "$file_path"
    else
        echo "$(cd "$(dirname "$file_path")" && pwd)/$(basename "$file_path")"
    fi
}

# Function to create systemd service
create_service() {
    local python_file="$1"
    local service_name="$2"
    local description="$3"
    local python_exec="$4"
    local working_dir="$(dirname "$python_file")"
    local service_file="/etc/systemd/system/${service_name}.service"
    
    print_status "Creating systemd service file: $service_file"
    
    cat > "$service_file" << EOF
[Unit]
Description=$description
After=network.target
StartLimitIntervalSec=0

[Service]
Type=oneshot
RemainAfterExit=yes
User=root
WorkingDirectory=$working_dir
ExecStart=$python_exec $python_file
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$service_name

[Install]
WantedBy=multi-user.target
EOF

    print_success "Service file created successfully"
}

# Function to setup and start service
setup_service() {
    local service_name="$1"
    
    print_status "Reloading systemd daemon..."
    systemctl daemon-reload
    
    print_status "Enabling service to start on boot..."
    systemctl enable "$service_name"
    
    print_status "Starting service..."
    systemctl start "$service_name"
    
    # Check service status
    if systemctl is-active --quiet "$service_name"; then
        print_success "Service '$service_name' is running successfully!"
    else
        print_error "Service failed to start. Check logs with: journalctl -u $service_name"
        return 1
    fi
}

# Main function
main() {
    echo "============================================="
    echo "    Universal Python Service Setup Script"
    echo "============================================="
    echo
    
    # Check if running as root
    check_root
    
    # Parse arguments or get interactive input
    if [[ $# -eq 0 ]]; then
        # Interactive mode
        echo "No arguments provided. Running in interactive mode..."
        echo
        
        # Get Python file
        while true; do
            read -p "Enter the path to your Python file: " PYTHON_FILE
            if [[ -f "$PYTHON_FILE" ]]; then
                break
            else
                print_error "File not found: $PYTHON_FILE"
            fi
        done
        
        # Get service name
        read -p "Enter service name (default: $(basename "$PYTHON_FILE" .py)): " SERVICE_NAME
        if [[ -z "$SERVICE_NAME" ]]; then
            SERVICE_NAME=$(basename "$PYTHON_FILE" .py)
        fi
        
        # Get description
        read -p "Enter service description (default: Python Service - $SERVICE_NAME): " DESCRIPTION
        if [[ -z "$DESCRIPTION" ]]; then
            DESCRIPTION="Python Service - $SERVICE_NAME"
        fi
    else
        # Command line arguments mode
        PYTHON_FILE="$1"
        SERVICE_NAME="${2:-$(basename "$1" .py)}"
        DESCRIPTION="${3:-Python Service - $SERVICE_NAME}"
    fi
    
    # Validate Python file exists
    if [[ ! -f "$PYTHON_FILE" ]]; then
        print_error "Python file not found: $PYTHON_FILE"
        exit 1
    fi
    
    # Get absolute path
    PYTHON_FILE=$(get_absolute_path "$PYTHON_FILE")
    
    # Detect Python executable
    PYTHON_EXEC=$(detect_python)
    
    print_status "Configuration:"
    echo "  Python File: $PYTHON_FILE"
    echo "  Service Name: $SERVICE_NAME"
    echo "  Description: $DESCRIPTION"
    echo "  Python Executable: $PYTHON_EXEC"
    echo
    
    # Confirm before proceeding
    read -p "Do you want to proceed? (y/N): " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        print_warning "Operation cancelled by user"
        exit 0
    fi
    
    # Create and setup service
    create_service "$PYTHON_FILE" "$SERVICE_NAME" "$DESCRIPTION" "$PYTHON_EXEC"
    setup_service "$SERVICE_NAME"
    
    echo
    print_success "Setup completed successfully!"
    echo
    echo "Service Management Commands:"
    echo "  Start service:    sudo systemctl start $SERVICE_NAME"
    echo "  Stop service:     sudo systemctl stop $SERVICE_NAME"
    echo "  Restart service:  sudo systemctl restart $SERVICE_NAME"
    echo "  Check status:     sudo systemctl status $SERVICE_NAME"
    echo "  View logs:        sudo journalctl -u $SERVICE_NAME -f"
    echo "  Disable service:  sudo systemctl disable $SERVICE_NAME"
    echo
}

# Help function
show_help() {
    echo "Usage: $0 [python_file] [service_name] [description]"
    echo
    echo "Arguments:"
    echo "  python_file   Path to the Python file to run as service"
    echo "  service_name  Name of the systemd service (optional)"
    echo "  description   Description of the service (optional)"
    echo
    echo "Examples:"
    echo "  $0 cache_warmer.py"
    echo "  $0 /path/to/cache_warmer.py cache-warmer"
    echo "  $0 /path/to/script.py my-service \"My Python Service\""
    echo
    echo "If no arguments are provided, the script will run in interactive mode."
}

# Check for help flag
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
fi

# Run main function
main "$@"