#!/bin/bash

# File Search System Setup Script
# Usage: ./setup.sh [btrfs_mount_point] [database_name]

set -e

# Configuration
BTRFS_MOUNT=${1:-"/home"}
DB_NAME=${2:-"file_index.db"}
JSON_FILE="files_temp.json"

echo "Fast File Search System"
echo "====================="
echo "Mount point: $BTRFS_MOUNT"
echo "Database: $DB_NAME"
echo ""

# Check if running as root (needed for btrfs metadata access)
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root to access Btrfs metadata"
    echo "Usage: sudo ./setup.sh [mount_point] [db_name]"
    exit 1
fi

# Check if btrfs-indexer exists
if [ ! -f "./btrfs-indexer" ]; then
    echo "Error: btrfs-indexer binary not found in current directory"
    echo "Please compile it first: gcc -o btrfs-indexer btrfs-indexer.c"
    exit 1
fi

# Check if mount point exists and is accessible
if [ ! -d "$BTRFS_MOUNT" ]; then
    echo "Error: Mount point '$BTRFS_MOUNT' does not exist"
    exit 1
fi

# Step 1: Extract metadata using C binary
echo "Step 1: Extracting Btrfs metadata..."
echo "This may take a while for large filesystems..."
start_time=$(date +%s)

if ! ./btrfs-indexer "$BTRFS_MOUNT" > "$JSON_FILE"; then
    echo "Error: Failed to extract Btrfs metadata"
    exit 1
fi

extract_time=$(date +%s)
echo "Metadata extraction completed in $((extract_time - start_time)) seconds"
echo "JSON file size: $(du -h $JSON_FILE | cut -f1)"

# Step 2: Build database using Python indexer
echo ""
echo "Step 2: Building search database..."

if ! python3 indexer.py "$JSON_FILE" "$DB_NAME"; then
    echo "Error: Failed to build database"
    exit 1
fi

build_time=$(date +%s)
echo "Database build completed in $((build_time - extract_time)) seconds"
echo "Database size: $(du -h $DB_NAME | cut -f1)"

# Cleanup temporary JSON file
rm -f "$JSON_FILE"

total_time=$((build_time - start_time))
echo ""
echo "Setup completed successfully in $total_time seconds!"
echo ""
echo "Usage examples:"
echo "  ./search.py document.txt          # Quick search"
echo "  ./search.py -i                    # Interactive mode"
echo "  ./search.py --stats               # Show statistics"
echo "  ./search.py --recent 7            # Files from last 7 days"
echo "  ./search.py --size-min 100MB      # Large files"
echo ""
echo "For continuous updates, set up the inotify daemon (optional)."