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

## ROM Builder Overview

The `rom-builder.sh` script automates the process of building custom Android ROMs from source code. It handles the complex steps involved in Android ROM compilation, including repository synchronization, environment setup, build configuration, and output management.

### Key Features

- **Multi-ROM Support**: Build different custom Android distributions (Axion, LMODroid)
- **Device-Specific Configurations**: Pre-configured settings for supported devices
- **Build Variants**: Support for vanilla and GMS (Google Mobile Services) builds
- **Automated Dependency Resolution**: Installs required build dependencies
- **Configurable Output**: Store builds locally or on a remote server
- **Flexible Build Options**: Clean builds, skipping sync, non-interactive mode
- **Fastboot Package Generation**: Create flashable packages for direct fastboot updates

### Configuration System

Each device and ROM combination uses a dedicated configuration file (e.g., `pipa-axion.conf`) that defines:

- Repository sources and branches
- Device-specific build flags
- Custom patches to apply
- Output paths and naming conventions

## Architecture

1. **Parameter Parsing**: Process command-line arguments and set build parameters
2. **Configuration Loading**: Source the appropriate config file based on device/ROM selection
3. **Environment Setup**: Install dependencies and configure build environment
4. **Repository Management**: Initialize and synchronize source repositories
5. **Build Process**: Execute the ROM-specific build commands
6. **Output Handling**: Package and store the built ROM files
7. **Fastboot Package**: Generate flashable packages for direct fastboot updates (optional)

## Usage

```bash
./rom-builder.sh [options]
```

### Options:

-r, --rom ROM: Specify ROM to build (axion, lmodroid)
-d, --device DEVICE: Specify target device (pipa, raven)
-v, --variant VAR: Specify build variant for Axion (vanilla, gms, both)
-n, --non-interactive: Skip interactive prompts
-l, --local-path: Store output in local path instead of server path
-s, --skip-sync: Skip repository sync step
-c, --clean: Force a clean build
-f, --fastboot: Build fastboot flashable package
-h, --help: Show help information

### Examples

Building LMODroid for Xiaomi Pad 5 Pro:
```bash
./rom-builder.sh -r lmodroid -d pipa
```

Building Axion ROM with GMS for Google Pixel 6 Pro:
```bash
./rom-builder.sh -r axion -d raven -v gms
```

Building both vanilla and GMS variants of Axion for Xiaomi Pad 5 Pro:
```bash
./rom-builder.sh -r axion -d pipa -v both
```

Building Axion ROM with a fastboot package:
```bash
./rom-builder.sh -r axion -d pipa -v vanilla -f
```

### Requirements
- Linux-based operating system
- Sufficient storage space (300GB+ recommended)
- At least 32GB RAM (64GB+ recommended)
- Fast internet connection
- Android build dependencies installed
- Write permissions to output directories