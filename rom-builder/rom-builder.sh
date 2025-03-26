#!/bin/bash

# Get the directory of the script
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

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
            echo -e "  -v, --variant VAR    Specify build variant for Axion (vanilla, gms, both)"
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

# Define release directory
RELEASE_DIR="$HOME/${ROM}-${DEVICE}-releases"
mkdir -p "$RELEASE_DIR"

echo -e "${BLUE}=== Building $ROM_NAME for $DEVICE ===${NC}"
echo -e "${CYAN}ROM Directory:${NC} $ROM_PATH"
echo -e "${CYAN}ROM Variant:${NC} $VARIANT"
echo -e "${CYAN}Build Fastboot:${NC} $(if [[ "$BUILD_FASTBOOT" == true ]]; then echo "Yes"; else echo "No"; fi)"
echo -e "${CYAN}Source:${NC} $MANIFEST_URL (branch: $BRANCH)"
echo -e "${CYAN}Release Directory:${NC} $RELEASE_DIR"

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

# Function to build ROM
build_rom() {
    local variant=$1
    local is_fastboot=$2
    local output_dir="out/target/product/$DEVICE"
    
    # Setup device-specific build environment
    echo -e "${GREEN}Setting up device: $DEVICE with variant: $variant${NC}"
    if [[ "$ROM" == "axion" ]]; then
        if [[ "$DEVICE" == "pipa" || "$DEVICE" == "raven" ]]; then
            # Set GMS build flag for Axion if needed
            if [[ "$variant" == "gms" ]]; then
                echo -e "${GREEN}Configuring build for GMS support${NC}"
                axion "$DEVICE" gms || {
                    echo -e "${RED}Failed to configure Axion with GMS${NC}"
                    return 1
                }
            else
                echo -e "${GREEN}Configuring build for vanilla version (no GMS)${NC}"
                axion "$DEVICE" va || {
                    echo -e "${RED}Failed to configure vanilla Axion${NC}"
                    return 1
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
    if [[ "$is_fastboot" == true ]]; then
        echo -e "${YELLOW}Building with fastboot package...${NC}"
        
        # For Axion ROM
        if [[ "$ROM" == "axion" ]]; then
            # First configure the correct device and variant
            if [[ "$variant" == "gms" ]]; then
                echo -e "${GREEN}Configuring build for GMS support${NC}"
                axion "$DEVICE" gms
            else
                echo -e "${GREEN}Configuring build for vanilla version (no GMS)${NC}"
                axion "$DEVICE" va
            fi
            
            # Now build the updatepackage (fastboot package)
            echo -e "${YELLOW}Building updatepackage (fastboot flashable package)...${NC}"
            m updatepackage -j$(nproc --all)
        else
            # For LMODroid
            lunch lmodroid_${DEVICE}-userdebug || breakfast ${DEVICE}
            m updatepackage -j$(nproc --all)
        fi
    else
        # Regular ROM build
        if [[ "$ROM" == "axion" ]]; then
            echo -e "${YELLOW}Building Axion for $DEVICE with variant: $variant${NC}"
            brunch "$DEVICE"
        else
            echo -e "${YELLOW}Building LMODroid for $DEVICE${NC}"
            m lmodroid
        fi
    fi

    # Check if build was successful
    if [[ -f "$output_dir/boot.img" ]]; then
        echo -e "${GREEN}Build successful!${NC}"
        
        # Debug: List zip files in output dir after build
        if [[ "$is_fastboot" == true ]]; then
            echo -e "${YELLOW}Checking for fastboot image files:${NC}"
            find "$output_dir" -name "*update*.zip" -type f | sort
            echo -e "${YELLOW}All zip files in output dir:${NC}"
            find "$output_dir" -name "*.zip" -type f | sort
        fi
        
        # Copy ROM zip files
        echo -e "${GREEN}Copying build files to $RELEASE_DIR${NC}"
        
        # Find and copy regular ROM zip files (for non-fastboot builds)
        if [[ ! "$is_fastboot" == true ]]; then
            if [[ "$ROM" == "axion" ]]; then
                for zip_file in $(find "$output_dir" -maxdepth 1 -name "axion-*.zip" -type f); do
                    local base_name=$(basename "$zip_file")
                    cp -v "$zip_file" "$RELEASE_DIR/$base_name"
                done
                
                # Copy JSON files used for OTA - add suffix for JSON files only
                if [[ "$variant" == "vanilla" ]]; then
                    if [[ -f "$output_dir/VANILLA/$DEVICE.json" ]]; then
                        cp -v "$output_dir/VANILLA/$DEVICE.json" "$RELEASE_DIR/${DEVICE}-vanilla.json"
                        echo -e "${GREEN}Copied VANILLA OTA config json${NC}"
                    fi
                elif [[ "$variant" == "gms" ]]; then
                    if [[ -f "$output_dir/GMS/$DEVICE.json" ]]; then
                        cp -v "$output_dir/GMS/$DEVICE.json" "$RELEASE_DIR/${DEVICE}-gms.json"
                        echo -e "${GREEN}Copied GMS OTA config json${NC}"
                    fi
                fi
                
                # Copy boot images
                cp -v "$output_dir/boot.img" "$RELEASE_DIR/"
                [[ -f "$output_dir/dtbo.img" ]] && cp -v "$output_dir/dtbo.img" "$RELEASE_DIR/"
                [[ -f "$output_dir/vendor_boot.img" ]] && cp -v "$output_dir/vendor_boot.img" "$RELEASE_DIR/"
            else
                # For LMODroid
                for zip_file in $(find "$output_dir" -maxdepth 1 -name "lmodroid-*.zip" -type f); do
                    local base_name=$(basename "$zip_file")
                    cp -v "$zip_file" "$RELEASE_DIR/$base_name"
                done
                
                # Copy boot images
                cp -v "$output_dir/boot.img" "$RELEASE_DIR/"
                [[ -f "$output_dir/dtbo.img" ]] && cp -v "$output_dir/dtbo.img" "$RELEASE_DIR/"
                [[ -f "$output_dir/vendor_boot.img" ]] && cp -v "$output_dir/vendor_boot.img" "$RELEASE_DIR/"
            fi
        # Handle fastboot packages specifically
        else
            # For fastboot builds
            if [[ "$ROM" == "axion" ]]; then
                # Look for updatepackage output
                local update_files=(
                    "$output_dir/update.zip"
                    "$output_dir/updatepackage.zip"
                    "$output_dir/${DEVICE}_update.zip"
                    "$output_dir/lineage_${DEVICE}-img.zip"
                    "$output_dir/axion_${DEVICE}-img.zip"
                )
                
                local found_update=false
                for update_file in "${update_files[@]}"; do
                    if [[ -f "$update_file" ]]; then
                        local fastboot_target="$RELEASE_DIR/axion-$(date +%Y%m%d)-${variant^^}-$DEVICE-FASTBOOT.zip"
                        cp -v "$update_file" "$fastboot_target"
                        echo -e "${GREEN}Copied fastboot package from $update_file${NC}"
                        found_update=true
                        break
                    fi
                done
                
                if [[ "$found_update" == false ]]; then
                    # Try more aggressive search for update packages
                    echo -e "${YELLOW}Searching for update packages...${NC}"
                    local search_result=$(find "$output_dir" -name "*update*.zip" -type f | head -1)
                    if [[ -n "$search_result" ]]; then
                        local fastboot_target="$RELEASE_DIR/axion-$(date +%Y%m%d)-${variant^^}-$DEVICE-FASTBOOT.zip"
                        cp -v "$search_result" "$fastboot_target"
                        echo -e "${GREEN}Copied fastboot package from $search_result${NC}"
                        found_update=true
                    fi
                    
                    # Try searching for any img.zip as fallback
                    if [[ "$found_update" == false ]]; then
                        search_result=$(find "$output_dir" -name "*img*.zip" -type f | head -1)
                        if [[ -n "$search_result" ]]; then
                            local fastboot_target="$RELEASE_DIR/axion-$(date +%Y%m%d)-${variant^^}-$DEVICE-FASTBOOT.zip"
                            cp -v "$search_result" "$fastboot_target"
                            echo -e "${GREEN}Copied fastboot package from $search_result${NC}"
                            found_update=true
                        fi
                    fi
                fi
                
                # Create manual package as a last resort
                if [[ "$found_update" == false ]]; then
                    echo -e "${YELLOW}Creating manual fastboot package...${NC}"
                    local target_out="$output_dir/target_files"
                    local fastboot_target="$RELEASE_DIR/axion-$(date +%Y%m%d)-${variant^^}-$DEVICE-FASTBOOT.zip"
                    
                    mkdir -p "$target_out/IMAGES"
                    cp -v "$output_dir/boot.img" "$target_out/IMAGES/"
                    [[ -f "$output_dir/dtbo.img" ]] && cp -v "$output_dir/dtbo.img" "$target_out/IMAGES/"
                    [[ -f "$output_dir/vendor_boot.img" ]] && cp -v "$output_dir/vendor_boot.img" "$target_out/IMAGES/"
                    [[ -f "$output_dir/system.img" ]] && cp -v "$output_dir/system.img" "$target_out/IMAGES/"
                    [[ -f "$output_dir/vendor.img" ]] && cp -v "$output_dir/vendor.img" "$target_out/IMAGES/"
                    [[ -f "$output_dir/product.img" ]] && cp -v "$output_dir/product.img" "$target_out/IMAGES/"
                    [[ -f "$output_dir/system_ext.img" ]] && cp -v "$output_dir/system_ext.img" "$target_out/IMAGES/"
                    
                    (cd "$target_out" && zip -r "$fastboot_target" IMAGES/)
                    echo -e "${GREEN}Manually created fastboot package: $fastboot_target${NC}"
                    found_update=true
                fi
            else
                # For LMODroid
                local update_files=(
                    "$output_dir/update.zip"
                    "$output_dir/updatepackage.zip"
                    "$output_dir/${DEVICE}_update.zip"
                    "$output_dir/lmodroid_${DEVICE}-img.zip"
                )
                
                local found_update=false
                for update_file in "${update_files[@]}"; do
                    if [[ -f "$update_file" ]]; then
                        cp -v "$update_file" "$RELEASE_DIR/lmodroid-$(date +%Y%m%d)-$DEVICE-FASTBOOT.zip"
                        echo -e "${GREEN}Copied fastboot package from $update_file${NC}"
                        found_update=true
                        break
                    fi
                done
                
                if [[ "$found_update" == false ]]; then
                    # Try more aggressive search
                    echo -e "${YELLOW}Searching for update packages...${NC}"
                    local search_result=$(find "$output_dir" -name "*update*.zip" -type f | head -1)
                    if [[ -n "$search_result" ]]; then
                        cp -v "$search_result" "$RELEASE_DIR/lmodroid-$(date +%Y%m%d)-$DEVICE-FASTBOOT.zip"
                        echo -e "${GREEN}Copied fastboot package from $search_result${NC}"
                        found_update=true
                    fi
                    
                    # Try searching for any img.zip as fallback
                    if [[ "$found_update" == false ]]; then
                        search_result=$(find "$output_dir" -name "*img*.zip" -type f | head -1)
                        if [[ -n "$search_result" ]]; then
                            cp -v "$search_result" "$RELEASE_DIR/lmodroid-$(date +%Y%m%d)-$DEVICE-FASTBOOT.zip"
                            echo -e "${GREEN}Copied fastboot package from $search_result${NC}"
                            found_update=true
                        fi
                    fi
                fi
                
                # Create manual package as a last resort
                if [[ "$found_update" == false ]]; then
                    echo -e "${YELLOW}Creating manual fastboot package...${NC}"
                    local target_out="$output_dir/target_files"
                    local fastboot_target="$RELEASE_DIR/lmodroid-$(date +%Y%m%d)-$DEVICE-FASTBOOT.zip"
                    
                    mkdir -p "$target_out/IMAGES"
                    cp -v "$output_dir/boot.img" "$target_out/IMAGES/"
                    [[ -f "$output_dir/dtbo.img" ]] && cp -v "$output_dir/dtbo.img" "$target_out/IMAGES/"
                    [[ -f "$output_dir/vendor_boot.img" ]] && cp -v "$output_dir/vendor_boot.img" "$target_out/IMAGES/"
                    [[ -f "$output_dir/system.img" ]] && cp -v "$output_dir/system.img" "$target_out/IMAGES/"
                    [[ -f "$output_dir/vendor.img" ]] && cp -v "$output_dir/vendor.img" "$target_out/IMAGES/"
                    [[ -f "$output_dir/product.img" ]] && cp -v "$output_dir/product.img" "$target_out/IMAGES/"
                    [[ -f "$output_dir/system_ext.img" ]] && cp -v "$output_dir/system_ext.img" "$target_out/IMAGES/"
                    
                    (cd "$target_out" && zip -r "$fastboot_target" IMAGES/)
                    echo -e "${GREEN}Manually created fastboot package: $fastboot_target${NC}"
                fi
            fi
        fi
        
        echo -e "${GREEN}Build files copied to: $RELEASE_DIR${NC}"
        return 0
    else
        echo -e "${RED}Build failed - check the build logs${NC}"
        return 1
    fi
}

# Process variants based on selection
if [[ "$VARIANT" == "both" || "$VARIANT" == "all" ]]; then
    echo -e "${BLUE}=== Building both variants sequentially ===${NC}"
    
    # Build vanilla without fastboot
    echo -e "${BLUE}=== Building vanilla variant ===${NC}"
    build_rom "vanilla" false
    
    # If fastboot is requested, also build vanilla fastboot
    if [[ "$BUILD_FASTBOOT" == true ]]; then
        echo -e "${BLUE}=== Building vanilla variant with fastboot ===${NC}"
        build_rom "vanilla" true
    fi
    
    # Build GMS without fastboot
    echo -e "${BLUE}=== Building GMS variant ===${NC}"
    build_rom "gms" false
    
    # If fastboot is requested, also build GMS fastboot
    if [[ "$BUILD_FASTBOOT" == true ]]; then
        echo -e "${BLUE}=== Building GMS variant with fastboot ===${NC}"
        build_rom "gms" true
    fi
else
    # Build single variant without fastboot
    echo -e "${BLUE}=== Building $VARIANT variant ===${NC}"
    build_rom "$VARIANT" false
    
    # If fastboot is requested, build it with fastboot
    if [[ "$BUILD_FASTBOOT" == true ]]; then
        echo -e "${BLUE}=== Building $VARIANT variant with fastboot ===${NC}"
        build_rom "$VARIANT" true
    fi
fi

echo -e "${BLUE}=== All builds complete ===${NC}"
echo -e "${GREEN}ROM files are available in: $RELEASE_DIR${NC}"