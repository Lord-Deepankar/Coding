#!/bin/bash

# Btrfs Lightning-Fast File Search - Installation Script
# Usage: sudo ./install.sh [--prefix=/usr/local]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default installation prefix
PREFIX="/usr/local"
INSTALL_SERVICE=true
CREATE_DATABASE=true
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --prefix=*)
            PREFIX="${1#*=}"
            shift
            ;;
        --no-service)
            INSTALL_SERVICE=false
            shift
            ;;
        --no-database)
            CREATE_DATABASE=false
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --prefix=PATH     Installation prefix (default: /usr/local)"
            echo "  --no-service      Don't install systemd service"
            echo "  --no-database     Don't create initial database"
            echo "  -h, --help        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    echo "Usage: sudo ./install.sh"
    exit 1
fi

# Get the actual user (not root when using sudo)
if [[ -n "$SUDO_USER" ]]; then
    REAL_USER="$SUDO_USER"
    REAL_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
    REAL_USER="root"
    REAL_HOME="/root"
fi

echo -e "${BLUE}Btrfs Lightning-Fast File Search - Installer${NC}"
echo -e "${BLUE}============================================${NC}"
echo "Installation prefix: $PREFIX"
echo "Real user: $REAL_USER"
echo "Home directory: $REAL_HOME"
echo ""

# Function to print status messages
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check system requirements
check_requirements() {
    echo -e "${BLUE}Checking system requirements...${NC}"
    
    # Check for required commands
    local missing_deps=()
    
    if ! command -v gcc &> /dev/null; then
        missing_deps+=("gcc")
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if ! python3 -c "import pyinotify" &> /dev/null; then
        missing_deps+=("python3-pyinotify")
    fi
    
    if ! command -v sqlite3 &> /dev/null; then
        missing_deps+=("sqlite3")
    fi
    
    if [[ ${#missing_deps[@]} -ne 0 ]]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        echo ""
        echo "Please install missing dependencies:"
        echo ""
        echo "# For CachyOS/Arch:"
        echo "sudo pacman -S gcc python python-pyinotify sqlite"
        echo ""
        echo "# For Ubuntu/Debian:"
        echo "sudo apt install build-essential python3 python3-pyinotify sqlite3"
        echo ""
        echo "# For Fedora/RHEL:"
        echo "sudo dnf install gcc python3 python3-pyinotify sqlite"
        exit 1
    fi
    
    print_status "All dependencies found"
}

# Compile btrfs-indexer
compile_indexer() {
    echo -e "${BLUE}Compiling btrfs-indexer...${NC}"
    
    if [[ ! -f "$CURRENT_DIR/btrfs-indexer.c" ]]; then
        print_error "btrfs-indexer.c not found in $CURRENT_DIR"
        exit 1
    fi
    
    cd "$CURRENT_DIR"
    if gcc -o btrfs-indexer btrfs-indexer.c; then
        print_status "btrfs-indexer compiled successfully"
    else
        print_error "Failed to compile btrfs-indexer"
        exit 1
    fi
}

# Install files
install_files() {
    echo -e "${BLUE}Installing files...${NC}"
    
    # Create directories
    mkdir -p "$PREFIX/bin"
    mkdir -p "$PREFIX/lib/btrfs-search"
    mkdir -p "$PREFIX/share/doc/btrfs-search"
    mkdir -p "/etc/btrfs-search"
    
    # Install binaries
    cp "$CURRENT_DIR/btrfs-indexer" "$PREFIX/bin/"
    chmod 755 "$PREFIX/bin/btrfs-indexer"
    print_status "Installed btrfs-indexer binary"
    
    # Install Python scripts
    cp "$CURRENT_DIR/indexer.py" "$PREFIX/lib/btrfs-search/"
    cp "$CURRENT_DIR/search.py" "$PREFIX/lib/btrfs-search/"
    cp "$CURRENT_DIR/inotify_daemon.py" "$PREFIX/lib/btrfs-search/"
    cp "$CURRENT_DIR/setup.sh" "$PREFIX/lib/btrfs-search/"
    chmod 755 "$PREFIX/lib/btrfs-search/"*.py
    chmod 755 "$PREFIX/lib/btrfs-search/setup.sh"
    print_status "Installed Python scripts"
    
    # Create wrapper scripts in /usr/local/bin
    cat > "$PREFIX/bin/btrfs-search" << 'EOF'
#!/bin/bash
exec python3 /usr/local/lib/btrfs-search/search.py "$@"
EOF
    chmod 755 "$PREFIX/bin/btrfs-search"
    print_status "Created btrfs-search command"
    
    cat > "$PREFIX/bin/btrfs-setup" << 'EOF'
#!/bin/bash
exec /usr/local/lib/btrfs-search/setup.sh "$@"
EOF
    chmod 755 "$PREFIX/bin/btrfs-setup"
    print_status "Created btrfs-setup command"
    
    # Install documentation
    cp "$CURRENT_DIR/README.md" "$PREFIX/share/doc/btrfs-search/"
    print_status "Installed documentation"
    
    # Install configuration
    if [[ ! -f "/etc/btrfs-search/inotify_config.json" ]]; then
        cp "$CURRENT_DIR/inotify_config.json" "/etc/btrfs-search/"
        print_status "Installed default configuration"
    else
        print_warning "Configuration already exists, not overwriting"
    fi
}

# Install systemd service
install_service() {
    if [[ "$INSTALL_SERVICE" == "true" ]]; then
        echo -e "${BLUE}Installing systemd service...${NC}"
        
        # Update service file with correct paths
        sed "s|WorkingDirectory=.*|WorkingDirectory=$PREFIX/lib/btrfs-search|g; \
             s|ExecStart=.*|ExecStart=/usr/bin/python3 $PREFIX/lib/btrfs-search/inotify_daemon.py /etc/btrfs-search/inotify_config.json|g" \
             "$CURRENT_DIR/btrfs-indexer.service" > "/etc/systemd/system/btrfs-indexer.service"
        
        systemctl daemon-reload
        print_status "Installed systemd service"
        
        echo ""
        echo -e "${YELLOW}To enable the service:${NC}"
        echo "  sudo systemctl enable btrfs-indexer"
        echo "  sudo systemctl start btrfs-indexer"
    fi
}

# Create initial database
create_database() {
    if [[ "$CREATE_DATABASE" == "true" ]]; then
        echo -e "${BLUE}Creating initial database...${NC}"
        echo "This may take a while for large filesystems..."
        
        # Create database in user's home directory
        DATABASE_PATH="$REAL_HOME/.local/share/btrfs-search"
        mkdir -p "$DATABASE_PATH"
        chown "$REAL_USER:$(id -gn "$REAL_USER")" "$DATABASE_PATH"
        
        # Update config to use user's database path
        sed -i "s|\"database_path\": \"file_index.db\"|\"database_path\": \"$DATABASE_PATH/file_index.db\"|g" \
               "/etc/btrfs-search/inotify_config.json"
        
        # Run setup script
        cd "$PREFIX/lib/btrfs-search"
        if ./setup.sh "$REAL_HOME" "$DATABASE_PATH/file_index.db"; then
            chown "$REAL_USER:$(id -gn "$REAL_USER")" "$DATABASE_PATH/file_index.db"
            print_status "Database created successfully"
            
            # Show database stats
            FILE_COUNT=$(sqlite3 "$DATABASE_PATH/file_index.db" "SELECT COUNT(*) FROM files;")
            DB_SIZE=$(du -h "$DATABASE_PATH/file_index.db" | cut -f1)
            echo "  Files indexed: $FILE_COUNT"
            echo "  Database size: $DB_SIZE"
        else
            print_warning "Database creation failed, you can create it later with: sudo btrfs-setup"
        fi
    fi
}

# Show completion message
show_completion() {
    echo ""
    echo -e "${GREEN}🎉 Installation completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}Usage:${NC}"
    echo "  btrfs-search myfile.txt          # Search for files"
    echo "  btrfs-search -i                  # Interactive mode"
    echo "  btrfs-search --stats             # Show statistics"
    echo ""
    echo -e "${BLUE}Service management:${NC}"
    echo "  sudo systemctl enable btrfs-indexer    # Enable auto-start"
    echo "  sudo systemctl start btrfs-indexer     # Start now"
    echo "  sudo systemctl status btrfs-indexer    # Check status"
    echo ""
    echo -e "${BLUE}Configuration:${NC}"
    echo "  /etc/btrfs-search/inotify_config.json  # Daemon config"
    echo "  $REAL_HOME/.local/share/btrfs-search/   # Database location"
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo "  $PREFIX/share/doc/btrfs-search/README.md"
    echo ""
    
    if [[ "$INSTALL_SERVICE" == "true" ]]; then
        echo -e "${YELLOW}Don't forget to start the service for real-time updates!${NC}"
        echo "  sudo systemctl enable --now btrfs-indexer"
    fi
}

# Main installation flow
main() {
    check_requirements
    compile_indexer
    install_files
    install_service
    create_database
    show_completion
}

# Run main function
main
