#!/bin/bash

# Create a temporary directory for testing
TEST_DIR=$(mktemp -d)
echo "Created test directory: $TEST_DIR"

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

# Create a modified version of the script with safety guards
cat > "$TEST_DIR/rom-builder-test.sh" << 'EOF'
#!/bin/bash
# This is a safe testing wrapper for rom-builder.sh

if [[ "$MOCK_TEST" != "true" ]]; then
    echo "ERROR: This test script should only be run in the mock environment!"
    exit 1
fi

# Source the actual script but overwrite dangerous commands
source rom-builder.sh

# Override dangerous commands
function rm() {
    echo "[MOCK] Would remove: $@"
}

function repo() {
    echo "[MOCK] repo $@"
    return 0
}

function wget() {
    echo "[MOCK] wget $@"
    return 0
}

# Run the script with the provided arguments
main "$@"
EOF
chmod +x "$TEST_DIR/rom-builder-test.sh"

echo "==== Test Environment Ready ===="
echo "To test your script with different parameters, run:"
echo "MOCK_TEST=true $TEST_DIR/rom-builder-test.sh [options]"
echo ""
echo "Example tests:"
echo "MOCK_TEST=true $TEST_DIR/rom-builder-test.sh -r axion -d pipa -v vanilla"
echo "MOCK_TEST=true $TEST_DIR/rom-builder-test.sh -r axion -d pipa -v gms -f"
echo "MOCK_TEST=true $TEST_DIR/rom-builder-test.sh -r lmodroid -d raven"
echo ""
echo "When done testing, remove the test directory with:"
echo "rm -rf $TEST_DIR"
echo "==== Test Environment Ready ===="

# Try a simple test run
echo "Running a sample test..."
pushd $(dirname $(readlink -f "$0")) > /dev/null
MOCK_TEST=true bash -c "bash $TEST_DIR/rom-builder-test.sh -r axion -d pipa -v vanilla -s"
popd > /dev/null