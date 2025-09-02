#!/bin/bash

# Create release package for Btrfs Lightning-Fast File Search
# Usage: ./create_release.sh [version]

set -e

VERSION=${1:-"1.0.0"}
PROJECT_NAME="btrfs-lightning-search"
RELEASE_NAME="${PROJECT_NAME}-${VERSION}"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Creating release package: ${RELEASE_NAME}"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
RELEASE_DIR="${TEMP_DIR}/${RELEASE_NAME}"

# Create release directory structure
mkdir -p "${RELEASE_DIR}"
mkdir -p "${RELEASE_DIR}/config-examples"
mkdir -p "${RELEASE_DIR}/docs"

# Copy core files
echo "Copying core files..."
cp "${CURRENT_DIR}/btrfs-indexer.c" "${RELEASE_DIR}/"
cp "${CURRENT_DIR}/btrfs-indexer2.c" "${RELEASE_DIR}/"
cp "${CURRENT_DIR}/indexer.py" "${RELEASE_DIR}/"
cp "${CURRENT_DIR}/search.py" "${RELEASE_DIR}/"
cp "${CURRENT_DIR}/inotify_daemon.py" "${RELEASE_DIR}/"
cp "${CURRENT_DIR}/setup.sh" "${RELEASE_DIR}/"
cp "${CURRENT_DIR}/install.sh" "${RELEASE_DIR}/"

# Copy configuration files
echo "Copying configuration files..."
cp "${CURRENT_DIR}/inotify_config.json" "${RELEASE_DIR}/"
cp "${CURRENT_DIR}/btrfs-indexer.service" "${RELEASE_DIR}/"
cp -r "${CURRENT_DIR}/config-examples/"* "${RELEASE_DIR}/config-examples/"

# Copy documentation
echo "Copying documentation..."
cp "${CURRENT_DIR}/README.md" "${RELEASE_DIR}/"
cp "${CURRENT_DIR}/LICENSE" "${RELEASE_DIR}/"

# Create version file
echo "${VERSION}" > "${RELEASE_DIR}/VERSION"

# Create installation verification script
cat > "${RELEASE_DIR}/verify_installation.sh" << 'EOF'
#!/bin/bash

# Verify installation requirements
echo "Btrfs Lightning-Fast File Search - Installation Verification"
echo "============================================================"

# Check system requirements
check_requirement() {
    local cmd="$1"
    local desc="$2"
    
    if command -v "$cmd" &> /dev/null; then
        echo "✓ $desc: $(command -v "$cmd")"
        return 0
    else
        echo "✗ $desc: Not found"
        return 1
    fi
}

check_python_module() {
    local module="$1"
    local desc="$2"
    
    if python3 -c "import $module" &> /dev/null 2>&1; then
        echo "✓ $desc: Available"
        return 0
    else
        echo "✗ $desc: Not found"
        return 1
    fi
}

# Check filesystem
check_btrfs() {
    if findmnt -t btrfs &> /dev/null; then
        echo "✓ Btrfs filesystem: Detected"
        findmnt -t btrfs | head -5
        return 0
    else
        echo "⚠ Btrfs filesystem: Not detected (will work on other filesystems but slower)"
        return 1
    fi
}

echo ""
echo "Checking system requirements:"
failures=0

check_requirement "gcc" "GCC Compiler" || ((failures++))
check_requirement "python3" "Python 3" || ((failures++))
check_requirement "sqlite3" "SQLite 3" || ((failures++))
check_python_module "pyinotify" "Python inotify module" || ((failures++))

echo ""
echo "Checking filesystem:"
check_btrfs

echo ""
if [[ $failures -eq 0 ]]; then
    echo "🎉 All requirements met! Ready to install."
    echo ""
    echo "Next steps:"
    echo "  sudo ./install.sh"
else
    echo "❌ Missing $failures requirement(s). Please install missing dependencies first."
    echo ""
    echo "Installation commands by distribution:"
    echo ""
    echo "CachyOS/Arch Linux:"
    echo "  sudo pacman -S gcc python python-pyinotify sqlite"
    echo ""
    echo "Ubuntu/Debian:"
    echo "  sudo apt update"
    echo "  sudo apt install build-essential python3 python3-pyinotify sqlite3"
    echo ""
    echo "Fedora/RHEL:"
    echo "  sudo dnf install gcc python3 python3-pyinotify sqlite"
fi
EOF

chmod +x "${RELEASE_DIR}/verify_installation.sh"

# Create quick start guide
cat > "${RELEASE_DIR}/QUICKSTART.md" << EOF
# Quick Start Guide

## 1. Verify System Requirements
\`\`\`bash
./verify_installation.sh
\`\`\`

## 2. Install
\`\`\`bash
sudo ./install.sh
\`\`\`

## 3. Start Searching
\`\`\`bash
# Basic search
btrfs-search myfile.txt

# Interactive mode
btrfs-search -i

# Enable real-time updates
sudo systemctl enable --now btrfs-indexer
\`\`\`

For detailed documentation, see README.md
EOF

# Make scripts executable
chmod +x "${RELEASE_DIR}/"*.sh
chmod +x "${RELEASE_DIR}/"*.py

# Create tarball
echo "Creating release archive..."
cd "${TEMP_DIR}"
tar -czf "${CURRENT_DIR}/${RELEASE_NAME}.tar.gz" "${RELEASE_NAME}/"

# Create zip file for Windows users (who might want to examine the code)
zip -r "${CURRENT_DIR}/${RELEASE_NAME}.zip" "${RELEASE_NAME}/" > /dev/null

# Cleanup
rm -rf "${TEMP_DIR}"

# Show results
echo ""
echo "✅ Release packages created:"
echo "  📦 ${RELEASE_NAME}.tar.gz ($(du -h "${CURRENT_DIR}/${RELEASE_NAME}.tar.gz" | cut -f1))"
echo "  📦 ${RELEASE_NAME}.zip ($(du -h "${CURRENT_DIR}/${RELEASE_NAME}.zip" | cut -f1))"
echo ""

# Create checksums
echo "Creating checksums..."
cd "${CURRENT_DIR}"
sha256sum "${RELEASE_NAME}.tar.gz" > "${RELEASE_NAME}.tar.gz.sha256"
sha256sum "${RELEASE_NAME}.zip" > "${RELEASE_NAME}.zip.sha256"

echo "  🔐 ${RELEASE_NAME}.tar.gz.sha256"
echo "  🔐 ${RELEASE_NAME}.zip.sha256"
echo ""

# Show upload/distribution suggestions
echo "📋 Distribution checklist:"
echo "  [ ] Test installation on clean system"
echo "  [ ] Upload to GitHub Releases"
echo "  [ ] Update project README with download links"
echo "  [ ] Announce on relevant forums/communities"
echo "  [ ] Consider creating AUR package for Arch users"
echo "  [ ] Consider creating .deb/.rpm packages"
echo ""

echo "🎉 Release ${VERSION} is ready for distribution!"
