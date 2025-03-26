# Android ROM Builder Script

A simplified script to build custom Android ROMs for specific devices.

## Overview

The `rom-builder.sh` script automates the process of building custom Android ROMs from source code. It handles repository synchronization, environment setup, build configuration, and displays output paths.

### Supported ROMs

- **Axion AOSP** (`axion`): A custom AOSP-based ROM with additional features
- **LMODroid** (`lmodroid`): LibreOS-based Android distribution

### Supported Devices

- **Xiaomi Pad 6** (`pipa`): Support for both ROMs
- **Google Pixel 6 Pro** (`raven`): Support for both ROMs

## Prerequisites

1. **Linux Environment**: Ubuntu 20.04 or newer is recommended for Android builds
2. **Repo Tool**: Make sure you have the Android `repo` tool installed
   ```bash
   sudo apt-get install repo
   ```
3. **Git LFS**: Required for some repositories
   ```bash
   sudo apt-get install git-lfs
   ```

## ROM Builder Overview

The `rom-builder.sh` script automates the process of building custom Android ROMs from source code. It handles the complex steps involved in Android ROM compilation, including repository synchronization, environment setup, build configuration, and output management.

### Key Features

- **Multi-ROM Support**: Build different custom Android distributions (Axion, LMODroid)
- **Device-Specific Configurations**: Pre-configured settings for supported devices
- **Build Variants**: Support for vanilla and GMS (Google Mobile Services) builds
- **Automated Repository Management**: Handles device-specific repositories
- **Flexible Build Options**: Clean builds, skipping sync, fastboot package generation
- **OTA Configuration**: Properly handles OTA config JSON files for updates
- **Fastboot Package Generation**: Create flashable packages for direct fastboot updates

## Architecture

1. **Parameter Parsing**: Process command-line arguments and set build parameters
2. **Environment Setup**: Configures build environment and source directories
3. **Repository Management**: Initialize and synchronize source repositories
4. **Variant Configuration**: Configure for vanilla or GMS build
5. **Build Process**: Execute the ROM-specific build commands
6. **Output Handling**: Package and store the built ROM files with proper naming
7. **Fastboot Package**: Generate flashable packages for direct fastboot updates (when requested)

## Usage

```bash
./rom-builder.sh [options]
```

### Options:

- `-r, --rom ROM`: Specify ROM to build (axion, lmodroid)
- `-d, --device DEVICE`: Specify target device (pipa, raven)
- `-v, --variant VAR`: Specify build variant for Axion (vanilla, gms, both)
- `-s, --skip-sync`: Skip repository sync step
- `-c, --clean`: Force a clean build (default)
- `-f, --fastboot`: Build fastboot flashable package
- `-h, --help`: Show help information

### Examples

Building LMODroid for Xiaomi Pad 6:
```bash
./rom-builder.sh -r lmodroid -d pipa
```

Building Axion ROM with GMS for Google Pixel 6 Pro:
```bash
./rom-builder.sh -r axion -d raven -v gms
```

Building both vanilla and GMS variants of Axion for Xiaomi Pad 6:
```bash
./rom-builder.sh -r axion -d pipa -v both
```

Building Axion ROM with a fastboot package:
```bash
./rom-builder.sh -r axion -d pipa -v vanilla -f
```

Building both variants of Axion with fastboot packages:
```bash
./rom-builder.sh -r axion -d pipa -v both -f
```

## Output Files

The script generates the following files in the release directory (`~/[rom]-[device]-releases/`):

1. **ROM ZIP files**:
   - Normal builds: Original ROM ZIP names are preserved
   - Fastboot builds: `-FASTBOOT` suffix is added to the filename

2. **Boot images**:
   - `boot.img`: Boot image for the device
   - `dtbo.img`: DTBO image (if available)
   - `vendor_boot.img`: Vendor boot image (if available)

3. **OTA Configuration**:
   - `[device]-vanilla.json`: OTA configuration for vanilla builds
   - `[device]-gms.json`: OTA configuration for GMS builds

### Requirements
- Linux-based operating system
- Sufficient storage space (300GB+ recommended)
- At least 32GB RAM (64GB+ recommended)
- Fast internet connection
- Android build dependencies installed
- Write permissions to output directories

## Technical Notes

- The script automatically detects its own path using `readlink` and `BASH_SOURCE`
- Builds are stored in `~/[rom]-[device]-releases/` by default
- The source code is stored in `~/ax/` for Axion and `~/lmo/` for LMODroid
- When building both variants, each variant is built sequentially
- Fastboot packages are built separately from regular packages