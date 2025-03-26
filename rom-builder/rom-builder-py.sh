#!/bin/bash
# filepath: c:\Users\abdoi\Desktop\scripts\rom-builder\run-rom-builder.sh

echo -e "\033[1;36m=== ROM Builder Launcher ===\033[0m"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "\033[1;31mERROR: Python 3 is not installed\033[0m"
    echo -e "\033[1;33mPlease install Python 3 to continue\033[0m"
    exit 1
fi

# Check Python version is at least 3.7 (for dataclasses) - without bc
py_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
major=$(echo "$py_version" | cut -d. -f1)
minor=$(echo "$py_version" | cut -d. -f2)
if [[ "$major" -lt 3 || ("$major" -eq 3 && "$minor" -lt 7) ]]; then
    echo -e "\033[1;31mERROR: Python $py_version detected, but version 3.7+ is required\033[0m"
    echo -e "\033[1;33mPlease upgrade your Python installation\033[0m"
    exit 1
fi

# Check for required Python packages
echo -e "\033[1;34mChecking Python dependencies...\033[0m"
missing_packages=()

check_package() {
    python3 -c "import $1" 2>/dev/null || missing_packages+=("$1")
}

check_package "colorama"

# Install missing packages if any
if [ ${#missing_packages[@]} -gt 0 ]; then
    echo -e "\033[1;33mMissing Python packages: ${missing_packages[*]}\033[0m"
    read -p "Install them now? (y/n): " install_choice
    
    if [[ "$install_choice" == "y" || "$install_choice" == "Y" ]]; then
        echo -e "\033[1;34mInstalling required packages...\033[0m"
        pip install ${missing_packages[@]}
        
        # Verify installation
        for pkg in "${missing_packages[@]}"; do
            if ! python3 -c "import $pkg" 2>/dev/null; then
                echo -e "\033[1;31mFailed to install $pkg. Please install it manually:\033[0m"
                echo -e "\033[1;33mpip install $pkg\033[0m"
                exit 1
            fi
        done
    else
        echo -e "\033[1;31mRequired packages are missing. Cannot continue.\033[0m"
        exit 1
    fi
fi

# Check Android build environment dependencies
echo -e "\033[1;34mChecking ROM build environment dependencies...\033[0m"

# Common required tools for ROM building
required_tools=("git" "repo" "curl" "adb" "fastboot" "gcc" "g++")
missing_tools=()

for tool in "${required_tools[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        missing_tools+=("$tool")
    fi
done

if [ ${#missing_tools[@]} -gt 0 ]; then
    echo -e "\033[1;31mWARNING: The following tools required for ROM building are missing:\033[0m"
    
    for tool in "${missing_tools[@]}"; do
        echo -e "\033[1;33m - $tool\033[0m"
    done
    
    echo -e "\033[1;33mYou may need to install these tools before building a ROM.\033[0m"
    echo -e "\033[1;33mOn Ubuntu/Debian, you can install most of these with:\033[0m"
    echo -e "\033[1;34msudo apt update && sudo apt install git curl repo build-essential adb fastboot\033[0m"
    
    read -p "Continue anyway? (y/n): " continue_choice
    if [[ "$continue_choice" != "y" && "$continue_choice" != "Y" ]]; then
        echo -e "\033[1;31mExiting.\033[0m"
        exit 1
    fi
fi

# Check for enough disk space (at least 100GB free)
free_space=$(df -h ~ | awk 'NR==2 {print $4}')
free_space_gb=$(df -BG ~ | awk 'NR==2 {print $4}' | sed 's/G//')

if (( free_space_gb < 100 )); then
    echo -e "\033[1;31mWARNING: You have only $free_space of free space\033[0m"
    echo -e "\033[1;33mBuilding Android ROMs typically requires at least 100GB free disk space\033[0m"
    read -p "Continue anyway? (y/n): " space_choice
    
    if [[ "$space_choice" != "y" && "$space_choice" != "Y" ]]; then
        echo -e "\033[1;31mExiting due to insufficient disk space.\033[0m"
        exit 1
    fi
fi

# Check temporary directory space
temp_space_gb=$(df -BG /tmp | awk 'NR==2 {print $4}' | sed 's/G//')
if (( temp_space_gb < 10 )); then
    echo -e "\033[1;31mWARNING: Low space in /tmp directory ($temp_space_gb GB)\033[0m"
    echo -e "\033[1;33mThis might cause issues during compilation\033[0m"
    read -p "Continue anyway? (y/n): " temp_choice
    if [[ "$temp_choice" != "y" && "$temp_choice" != "Y" ]]; then
        echo -e "\033[1;31mExiting.\033[0m"
        exit 1
    fi
fi

# Check RAM amount with more precision
total_ram_mb=$(free -m | awk '/^Mem:/{print $2}')
if (( total_ram_mb < 16000 )); then
    ram_gb=$(echo "scale=1; $total_ram_mb/1024" | bc)
    echo -e "\033[1;31mWARNING: You have only ${ram_gb}GB of RAM\033[0m"
    echo -e "\033[1;33mBuilding Android ROMs typically requires at least 16GB RAM\033[0m"
    echo -e "\033[1;33mThe build process might fail or be very slow\033[0m"
    read -p "Continue anyway? (y/n): " ram_choice
    
    if [[ "$ram_choice" != "y" && "$ram_choice" != "Y" ]]; then
        echo -e "\033[1;31mExiting due to insufficient RAM.\033[0m"
        exit 1
    fi
fi

# Check CPU cores
cores=$(nproc)
if (( cores < 4 )); then
    echo -e "\033[1;31mWARNING: Only $cores CPU cores available\033[0m"
    echo -e "\033[1;33mBuilding with fewer than 4 cores may be very slow\033[0m"
    read -p "Continue anyway? (y/n): " cores_choice
    if [[ "$cores_choice" != "y" && "$cores_choice" != "Y" ]]; then
        echo -e "\033[1;31mExiting.\033[0m"
        exit 1
    fi
fi

# Check JDK version
if command -v java &> /dev/null; then
    java_version=$(java -version 2>&1 | head -1 | cut -d'"' -f2 | sed 's/^1\.//' | cut -d'.' -f1)
    if [[ "$java_version" != "11" && "$java_version" != "8" ]]; then
        echo -e "\033[1;31mWARNING: Java version $java_version detected\033[0m"
        echo -e "\033[1;33mAndroid ROM building typically requires JDK 8 or 11\033[0m"
        read -p "Continue anyway? (y/n): " java_choice
        if [[ "$java_choice" != "y" && "$java_choice" != "Y" ]]; then
            echo -e "\033[1;31mExiting.\033[0m"
            exit 1
        fi
    else
        echo -e "\033[1;32mJDK $java_version detected - compatible with Android building\033[0m"
    fi
else
    echo -e "\033[1;31mWARNING: Java not found in PATH\033[0m"
    echo -e "\033[1;33mJava JDK 8 or 11 is required for ROM building\033[0m"
    read -p "Continue anyway? (y/n): " java_missing_choice
    if [[ "$java_missing_choice" != "y" && "$java_missing_choice" != "Y" ]]; then
        echo -e "\033[1;31mExiting.\033[0m"
        exit 1
    fi
fi

echo -e "\033[1;32mAll dependency checks completed.\033[0m"
echo -e "\033[1;36mLaunching ROM Builder...\033[0m"

# Run the Python script
if [ $# -eq 0 ]; then
    # No arguments, run in interactive mode
    python3 rom-builder.py
else
    # Pass all arguments to the Python script
    python3 rom-builder.py "$@"
fi

# Check if the script exited with an error
if [ $? -ne 0 ]; then
    echo -e "\033[1;31mROM Builder exited with an error.\033[0m"
    
    # Find the most recent log file without using -mtime
    log_files=$(find ~/rom_build_logs -name "build_*.log" -type f -exec stat -c "%Y %n" {} \; | sort -nr | head -1 | cut -d' ' -f2-)
    if [ -n "$log_files" ]; then
        echo -e "\033[1;33mCheck the latest log file for details:\033[0m"
        echo -e "\033[1;33m$log_files\033[0m"
    fi
else
    echo -e "\033[1;32mROM Builder completed successfully!\033[0m"
fi

# If this script was run directly (not sourced), wait for user input before exiting
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo -e "\033[1;36mPress Enter to exit...\033[0m"
    read
fi