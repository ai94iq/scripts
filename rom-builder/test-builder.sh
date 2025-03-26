#!/bin/bash

# Create a temporary directory for testing in ~/tmp/ instead of /tmp
mkdir -p ~/tmp
TEST_DIR=$(mktemp -d -p ~/tmp)
echo "Created test directory: $TEST_DIR"

# Set up cleanup trap to remove test directory on exit
trap 'echo "Cleaning up test environment..."; rm -rf "$TEST_DIR"; echo "Done."; exit' EXIT INT TERM

# Mock the Android build environment
mkdir -p "$TEST_DIR/build"
touch "$TEST_DIR/build/envsetup.sh"

# Create dummy repo command
cat > "$TEST_DIR/repo" << 'EOF'
#!/bin/bash
echo "[MOCK] repo $@"
exit 0
EOF
chmod +x "$TEST_DIR/repo"

# Create dummy wget command
cat > "$TEST_DIR/wget" << 'EOF'
#!/bin/bash
echo "[MOCK] wget $@"
touch "$3" 2>/dev/null || echo "Creating mock file"
exit 0
EOF
chmod +x "$TEST_DIR/wget"

# Create dummy axion command
cat > "$TEST_DIR/axion" << 'EOF'
#!/bin/bash
echo "[MOCK] axion $@"
exit 0
EOF
chmod +x "$TEST_DIR/axion"

# Create dummy brunch command
cat > "$TEST_DIR/brunch" << 'EOF'
#!/bin/bash
echo "[MOCK] Building ROM for device: $1"
mkdir -p out/target/product/$1
touch out/target/product/$1/boot.img
touch out/target/product/$1/vendor_boot.img
touch out/target/product/$1/dtbo.img
touch out/target/product/$1/axion-test-$1.zip
exit 0
EOF
chmod +x "$TEST_DIR/brunch"

# Create dummy m command
cat > "$TEST_DIR/m" << 'EOF'
#!/bin/bash
echo "[MOCK] m $@"
if [[ "$1" == "lmodroid" ]]; then
    device=$(echo $DEVICE)
    mkdir -p out/target/product/$device
    touch out/target/product/$device/boot.img
    touch out/target/product/$device/vendor_boot.img
    touch out/target/product/$device/dtbo.img
    touch out/target/product/$device/lmodroid-test-$device.zip
fi
exit 0
EOF
chmod +x "$TEST_DIR/m"

# Create dummy lunch command
cat > "$TEST_DIR/lunch" << 'EOF'
#!/bin/bash
echo "[MOCK] lunch $@"
export DEVICE=$(echo $1 | cut -d'_' -f2 | cut -d'-' -f1)
echo "Set device to $DEVICE"
exit 0
EOF
chmod +x "$TEST_DIR/lunch"

# Create dummy breakfast command
cat > "$TEST_DIR/breakfast" << 'EOF'
#!/bin/bash
echo "[MOCK] breakfast $@"
export DEVICE=$1
echo "Set device to $DEVICE"
exit 0
EOF
chmod +x "$TEST_DIR/breakfast"

# Create mock .repo directory
mkdir -p "$TEST_DIR/.repo/local_manifests"

# Create fake HOME directory to avoid messing with real home
export REAL_HOME=$HOME
export HOME=$TEST_DIR

# Add mock tools to PATH
export PATH="$TEST_DIR:$PATH"
export MOCK_TEST=true

# Create a wrapper script that will explicitly execute rom-builder.sh with bash
cat > "$TEST_DIR/wrapper.sh" << 'EOF'
#!/bin/bash
# This wrapper ensures the script is executed with bash
# regardless of what interpreter the caller is using

SCRIPT_PATH="$(dirname "$(readlink -f "$0")")/../rom-builder.sh"
echo "Executing: bash $SCRIPT_PATH $@"
# Explicitly call with bash to ensure bash-specific features work
bash "$SCRIPT_PATH" "$@"
EOF
chmod +x "$TEST_DIR/wrapper.sh"

echo "==== Test Environment Ready ===="
echo "To test your script from any directory, run:"
echo "bash $TEST_DIR/wrapper.sh [options]"
echo ""
echo "Example tests:"
echo "bash $TEST_DIR/wrapper.sh -r axion -d pipa -v vanilla"
echo "bash $TEST_DIR/wrapper.sh -r axion -d pipa -v gms -f"
echo "bash $TEST_DIR/wrapper.sh -r lmodroid -d raven -s"
echo ""
echo "The wrapper script explicitly calls bash for executing rom-builder.sh"
echo "This prevents the shell compatibility issues with /bin/sh"
echo "==== Test Environment Ready ===="

# Try a simple test run
echo "Running a sample test..."
bash "$TEST_DIR/wrapper.sh" -r axion -d pipa -v vanilla -s