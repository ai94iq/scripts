#!/bin/bash

# ANSI color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default options
ROM="axion"
DEVICE="pipa"
VARIANT="vanilla"
DATE_STRING=$(date +"%Y%m%d")
SKIP_SYNC=false
CLEAN_BUILD=true
BUILD_FASTBOOT=false  # Added option for fastboot package

# ROM configurations
declare -A ROM_INFO
# Format: [rom_id]="ROM name|Directory|Manifest URL|Branch"
ROM_INFO["axion"]="Axion AOSP|ax|https://github.com/AxionAOSP/android.git|lineage-22.2"
ROM_INFO["lmodroid"]="LMODroid|lmo|https://git.libremobileos.com/LMODroid/manifest.git|fifteen"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -r|--rom) ROM="$2"; shift 2 ;;
        -d|--device) DEVICE="$2"; shift 2 ;;
        -v|--variant) VARIANT="$2"; shift 2 ;;
        -s|--skip-sync) SKIP_SYNC=true; shift ;;
        -c|--clean) CLEAN_BUILD=true; shift ;;
        -f|--fastboot) BUILD_FASTBOOT=true; shift ;;  # New fastboot option
        -h|--help) 
            echo -e "${BLUE}=== ROM Builder Script ====${NC}"
            echo -e "Usage: ./rom-builder.sh [options]"
            echo -e "${CYAN}Options:${NC}"
            echo -e "  -r, --rom ROM        Specify ROM to build (axion, lmodroid)"
            echo -e "  -d, --device DEVICE  Specify target device (pipa, raven)"
            echo -e "  -v, --variant VAR    Specify build variant for Axion (vanilla, gms)"
            echo -e "  -s, --skip-sync      Skip repository sync step"
            echo -e "  -c, --clean          Force a clean build (default)"
            echo -e "  -f, --fastboot       Build fastboot flashable package"
            echo -e "  -h, --help           Show this help message"
            exit 0 ;;
        *) echo -e "${RED}Unknown option: $1${NC}"; 
           echo -e "Use -h or --help to see available options"; 
           exit 1 ;;
    esac
done

# Get ROM information
if [[ -z "${ROM_INFO[$ROM]}" ]]; then
    echo -e "${RED}Error: Invalid ROM '$ROM'${NC}"
    exit 1
fi

IFS='|' read -r ROM_NAME ROM_DIR MANIFEST_URL BRANCH <<< "${ROM_INFO[$ROM]}"

# Full path to the ROM directory
ROM_PATH="$HOME/$ROM_DIR"

echo -e "${BLUE}=== Building $ROM_NAME for $DEVICE ===${NC}"
echo -e "${CYAN}ROM Directory:${NC} $ROM_PATH"
echo -e "${CYAN}ROM Variant:${NC} $VARIANT"
echo -e "${CYAN}Build Fastboot:${NC} $(if [[ "$BUILD_FASTBOOT" == true ]]; then echo "Yes"; else echo "No"; fi)"
echo -e "${CYAN}Source:${NC} $MANIFEST_URL (branch: $BRANCH)"

# Set up the environment
if [[ "$SKIP_SYNC" == false ]]; then
    # Remove existing directory if it exists
    if [[ -d "$ROM_PATH" ]]; then
        echo -e "${YELLOW}Removing existing directory: $ROM_PATH${NC}"
        rm -rf "$ROM_PATH"
    fi
    
    # Create and set up new directory
    echo -e "${GREEN}Creating source directory: $ROM_PATH${NC}"
    mkdir -p "$ROM_PATH"
    cd "$ROM_PATH" || { echo -e "${RED}Failed to change to $ROM_PATH${NC}"; exit 1; }
    
    echo -e "${GREEN}Initializing repo from $MANIFEST_URL ($BRANCH)...${NC}"
    repo init -u "$MANIFEST_URL" -b "$BRANCH" --git-lfs
    
    # Create local_manifests directory and ensure it's clean
    echo -e "${GREEN}Setting up local manifests directory...${NC}"
    if [[ -d ".repo/local_manifests" ]]; then
        echo -e "${YELLOW}Removing existing local manifests...${NC}"
        rm -rf .repo/local_manifests/*
    else
        mkdir -p .repo/local_manifests
    fi
    
    # Download the device manifest
    echo -e "${GREEN}Adding device manifest for $DEVICE...${NC}"
    if [[ "$ROM" == "axion" && "$DEVICE" == "pipa" ]]; then
        wget -O .repo/local_manifests/device.xml https://raw.githubusercontent.com/ai94iq/local_manifests/main/axion-pipa-qpr2.xml
    elif [[ "$ROM" == "axion" && "$DEVICE" == "raven" ]]; then
        wget -O .repo/local_manifests/device.xml https://raw.githubusercontent.com/ai94iq/local_manifests/main/axion-raven-qpr2.xml
    elif [[ "$ROM" == "lmodroid" && "$DEVICE" == "pipa" ]]; then
        wget -O .repo/local_manifests/device.xml https://raw.githubusercontent.com/ai94iq/local_manifests/main/lmov-pipa.xml
    else
        echo -e "${RED}No device manifest available for $ROM + $DEVICE combination${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Syncing source code (may take a while)...${NC}"
    echo -e "${YELLOW}Using $(nproc --all) parallel jobs for sync${NC}"
    repo sync -c -j$(nproc --all) --force-sync --no-clone-bundle --no-tags || {
        echo -e "${RED}Failed to sync repositories${NC}"
        exit 1
    }
else
    # Skip sync, but verify directory exists and has build/envsetup.sh
    if [[ ! -d "$ROM_PATH" || ! -f "$ROM_PATH/build/envsetup.sh" ]]; then
        echo -e "${RED}Error: $ROM_PATH doesn't exist or is not a valid ROM source tree${NC}"
        echo -e "${RED}Try without the --skip-sync flag${NC}"
        exit 1
    fi
    
    cd "$ROM_PATH" || { echo -e "${RED}Failed to change to $ROM_PATH${NC}"; exit 1; }
    echo -e "${GREEN}Using existing source at: $ROM_PATH${NC}"
    
    # Update local manifest even when skipping sync
    echo -e "${GREEN}Updating device manifest...${NC}"
    if [[ -d ".repo/local_manifests" ]]; then
        echo -e "${YELLOW}Removing existing local manifests...${NC}"
        rm -rf .repo/local_manifests/*
    else
        mkdir -p .repo/local_manifests
    fi
    
    # Download the device manifest
    if [[ "$ROM" == "axion" && "$DEVICE" == "pipa" ]]; then
        wget -O .repo/local_manifests/device.xml https://raw.githubusercontent.com/ai94iq/local_manifests/main/axion-pipa-qpr2.xml
    elif [[ "$ROM" == "axion" && "$DEVICE" == "raven" ]]; then
        wget -O .repo/local_manifests/device.xml https://raw.githubusercontent.com/ai94iq/local_manifests/main/axion-raven-qpr2.xml
    elif [[ "$ROM" == "lmodroid" && "$DEVICE" == "pipa" ]]; then
        wget -O .repo/local_manifests/device.xml https://raw.githubusercontent.com/ai94iq/local_manifests/main/lmov-pipa.xml
    fi

    # Do a limited sync to get the new manifest changes
    echo -e "${GREEN}Syncing device-specific repositories...${NC}"
    repo sync -c -j$(nproc --all) --force-sync --no-clone-bundle --no-tags -f device/ vendor/ kernel/ hardware/xiaomi/ hardware/google/
fi

# We should now be in the ROM directory
echo -e "${CYAN}Current directory: $(pwd)${NC}"

# Verify we're in a valid ROM directory
if [[ ! -f "build/envsetup.sh" ]]; then
    echo -e "${RED}Error: build/envsetup.sh not found in $(pwd)${NC}"
    echo -e "${RED}This doesn't appear to be a valid ROM source directory${NC}"
    exit 1
fi

# Source build environment
echo -e "${GREEN}Setting up build environment...${NC}"
source build/envsetup.sh || {
    echo -e "${RED}Failed to source build environment${NC}"
    exit 1
}

# Setup device-specific build environment
echo -e "${GREEN}Setting up device: $DEVICE${NC}"
if [[ "$ROM" == "axion" ]]; then
    if [[ "$DEVICE" == "pipa" ]]; then
        # Set GMS build flag for Axion if needed
        if [[ "$VARIANT" == "gms" ]]; then
            echo -e "${GREEN}Configuring build for GMS support${NC}"
            axion "$DEVICE" gms || {
                echo -e "${RED}Failed to configure Axion with GMS${NC}"
                exit 1
            }
        else
            echo -e "${GREEN}Configuring build for vanilla version (no GMS)${NC}"
            axion "$DEVICE" va || {
                echo -e "${RED}Failed to configure vanilla Axion${NC}"
                exit 1
            }
        fi
    elif [[ "$DEVICE" == "raven" ]]; then
        # Set GMS build flag for Axion if needed
        if [[ "$VARIANT" == "gms" ]]; then
            echo -e "${GREEN}Configuring build for GMS support${NC}"
            axion "$DEVICE" gms || {
                echo -e "${RED}Failed to configure Axion with GMS${NC}"
                exit 1
            }
        else
            echo -e "${GREEN}Configuring build for vanilla version (no GMS)${NC}"
            axion "$DEVICE" va || {
                echo -e "${RED}Failed to configure vanilla Axion${NC}"
                exit 1
            }
        fi
    fi
elif [[ "$ROM" == "lmodroid" ]]; then
    if [[ "$DEVICE" == "pipa" ]]; then
        lunch lmodroid_pipa-userdebug || breakfast pipa
    elif [[ "$DEVICE" == "raven" ]]; then
        lunch lmodroid_raven-userdebug || breakfast raven
    fi
fi

# Clean build if requested
if [[ "$CLEAN_BUILD" == true ]]; then
    echo -e "${YELLOW}Running clean build...${NC}"
    m clean
else
    echo -e "${YELLOW}Running incremental build...${NC}"
    m installclean
fi

# Start the build
echo -e "${GREEN}Starting build process...${NC}"
if [[ "$ROM" == "axion" ]]; then
    echo -e "${YELLOW}Building Axion for $DEVICE with variant: $VARIANT${NC}"
    if [[ "$BUILD_FASTBOOT" == true ]]; then
        echo -e "${YELLOW}Including fastboot package${NC}"
        export BUILD_FASTBOOT=true  # Set environment variable for fastboot
    fi
    
    # Use brunch command for the actual build
    brunch "$DEVICE"
else
    echo -e "${YELLOW}Building LMODroid for $DEVICE${NC}"
    m lmodroid
fi

# Check if build was successful
OUTPUT_DIR="out/target/product/$DEVICE"
if [[ -f "$OUTPUT_DIR/boot.img" ]]; then
    echo -e "${GREEN}Build successful!${NC}"
    
    # Show output files
    echo -e "${CYAN}Build outputs:${NC}"
    if [[ "$ROM" == "axion" ]]; then
        find "$OUTPUT_DIR" -maxdepth 1 -name "axion-*.zip" -type f | while read -r file; do
            echo -e "${YELLOW}ROM zip: ${NC}$(basename "$file")"
        done
    else
        find "$OUTPUT_DIR" -maxdepth 1 -name "lmodroid-*.zip" -type f | while read -r file; do
            echo -e "${YELLOW}ROM zip: ${NC}$(basename "$file")"
        done
    fi
    
    echo -e "${YELLOW}Boot image:${NC} $OUTPUT_DIR/boot.img"
    [[ -f "$OUTPUT_DIR/dtbo.img" ]] && echo -e "${YELLOW}DTBO image:${NC} $OUTPUT_DIR/dtbo.img"
    [[ -f "$OUTPUT_DIR/vendor_boot.img" ]] && echo -e "${YELLOW}Vendor boot:${NC} $OUTPUT_DIR/vendor_boot.img"
else
    echo -e "${RED}Build failed - check the build logs${NC}"
    exit 1
fi

echo -e "${BLUE}=== Build complete ===${NC}"