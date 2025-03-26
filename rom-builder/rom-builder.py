#!/usr/bin/env python3

import os
import sys
import time
import argparse
import subprocess
import shutil
import re
import platform
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger("rom-builder")

# Default options
@dataclass
class BuildOptions:
    rom: str = "axion"
    device: str = "pipa"
    variant: str = "vanilla"
    date_string: str = datetime.now().strftime("%Y%m%d")
    skip_sync: bool = False
    clean_build: bool = True
    build_fastboot: bool = False

# ROM configurations
class RomInfo:
    def __init__(self, name: str, directory: str, manifest_url: str, branch: str):
        self.name = name
        self.directory = directory
        self.manifest_url = manifest_url
        self.branch = branch

# Global configurations
class Config:
    # ROM configurations
    ROM_INFO = {
        "axion": RomInfo("Axion AOSP", "ax", "https://github.com/AxionAOSP/android.git", "lineage-22.2"),
        "lmodroid": RomInfo("LMODroid", "lmo", "https://git.libremobileos.com/LMODroid/manifest.git", "fifteen")
    }

class Colors:
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    CYAN = Fore.CYAN
    NC = Style.RESET_ALL

class RomBuilder:
    def __init__(self, options: BuildOptions):
        self.options = options
        self.start_time = time.time()
        
        # Get script path
        self.script_path = os.path.realpath(__file__)
        self.script_dir = os.path.dirname(self.script_path)
        
        # Set up ROM information
        if self.options.rom in Config.ROM_INFO:
            self.rom_info = Config.ROM_INFO[self.options.rom]
        else:
            self.rom_info = None
            logger.error(f"{Colors.RED}Error: Invalid ROM '{self.options.rom}'{Colors.NC}")
            sys.exit(1)

        # Define paths
        self.home_dir = os.path.expanduser("~")
        self.rom_path = os.path.join(self.home_dir, self.rom_info.directory)
        self.release_dir = os.path.join(self.home_dir, f"{self.options.rom}-{self.options.device}-releases")
        
        # Ensure release directory exists
        os.makedirs(self.release_dir, exist_ok=True)

    def run_command(self, cmd: str, cwd: Optional[str] = None) -> Tuple[int, str, str]:
        """Run a shell command and return its exit code, stdout and stderr"""
        logger.info(f"{Colors.YELLOW}Running: {cmd}{Colors.NC}")
        
        process = subprocess.Popen(
            cmd, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            cwd=cwd,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.info(f"{Colors.RED}Command failed with exit code {process.returncode}{Colors.NC}")
            if stderr:
                logger.info(f"{Colors.RED}Error: {stderr}{Colors.NC}")
        
        return process.returncode, stdout, stderr

    def setup_environment(self) -> bool:
        """Setup ROM environment"""
        logger.info(f"{Colors.BLUE}=== Building {self.rom_info.name} for {self.options.device} ==={Colors.NC}")
        logger.info(f"{Colors.CYAN}ROM Directory:{Colors.NC} {self.rom_path}")
        logger.info(f"{Colors.CYAN}ROM Variant:{Colors.NC} {self.options.variant}")
        logger.info(f"{Colors.CYAN}Build Fastboot:{Colors.NC} {'Yes' if self.options.build_fastboot else 'No'}")
        logger.info(f"{Colors.CYAN}Source:{Colors.NC} {self.rom_info.manifest_url} (branch: {self.rom_info.branch})")
        logger.info(f"{Colors.CYAN}Release Directory:{Colors.NC} {self.release_dir}")
        
        # Set up the environment
        if not self.options.skip_sync:
            # Remove existing directory if it exists
            if os.path.isdir(self.rom_path):
                logger.info(f"{Colors.YELLOW}Removing existing directory: {self.rom_path}{Colors.NC}")
                shutil.rmtree(self.rom_path)
            
            # Create and set up new directory
            logger.info(f"{Colors.GREEN}Creating source directory: {self.rom_path}{Colors.NC}")
            os.makedirs(self.rom_path, exist_ok=True)
            os.chdir(self.rom_path)
            
            logger.info(f"{Colors.GREEN}Initializing repo from {self.rom_info.manifest_url} ({self.rom_info.branch})...{Colors.NC}")
            cmd = f"repo init -u {self.rom_info.manifest_url} -b {self.rom_info.branch} --git-lfs"
            exit_code, _, _ = self.run_command(cmd)
            if exit_code != 0:
                logger.error(f"{Colors.RED}Failed to initialize repo{Colors.NC}")
                return False
            
            # Create local_manifests directory and ensure it's clean
            logger.info(f"{Colors.GREEN}Setting up local manifests directory...{Colors.NC}")
            local_manifests_dir = os.path.join(self.rom_path, ".repo/local_manifests")
            if os.path.isdir(local_manifests_dir):
                for item in os.listdir(local_manifests_dir):
                    item_path = os.path.join(local_manifests_dir, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
            else:
                os.makedirs(local_manifests_dir, exist_ok=True)
            
            # Download the device manifest
            logger.info(f"{Colors.GREEN}Adding device manifest for {self.options.device}...{Colors.NC}")
            device_manifest_url = ""
            
            if self.options.rom == "axion" and self.options.device == "pipa":
                device_manifest_url = "https://raw.githubusercontent.com/ai94iq/local_manifests/main/axion-pipa-qpr2.xml"
            elif self.options.rom == "axion" and self.options.device == "raven":
                device_manifest_url = "https://raw.githubusercontent.com/ai94iq/local_manifests/main/axion-raven-qpr2.xml"
            elif self.options.rom == "lmodroid" and self.options.device == "pipa":
                device_manifest_url = "https://raw.githubusercontent.com/ai94iq/local_manifests/main/lmov-pipa.xml"
            else:
                logger.error(f"{Colors.RED}No device manifest available for {self.options.rom} + {self.options.device} combination{Colors.NC}")
                return False
            
            # Download the manifest file
            manifest_path = os.path.join(local_manifests_dir, "device.xml")
            cmd = f"wget -O {manifest_path} {device_manifest_url}"
            exit_code, _, _ = self.run_command(cmd)
            if exit_code != 0:
                logger.error(f"{Colors.RED}Failed to download device manifest{Colors.NC}")
                return False
            
            # Sync repositories
            logger.info(f"{Colors.GREEN}Syncing source code (may take a while)...{Colors.NC}")
            cores = os.cpu_count() or 4
            logger.info(f"{Colors.YELLOW}Using {cores} parallel jobs for sync{Colors.NC}")
            cmd = f"repo sync -c -j{cores} --force-sync --no-clone-bundle --no-tags"
            exit_code, _, _ = self.run_command(cmd)
            if exit_code != 0:
                logger.error(f"{Colors.RED}Failed to sync repositories{Colors.NC}")
                return False
        else:
            # Skip sync, but verify directory exists
            if not os.path.isdir(self.rom_path) or not os.path.isfile(os.path.join(self.rom_path, "build/envsetup.sh")):
                logger.error(f"{Colors.RED}Error: {self.rom_path} doesn't exist or is not a valid ROM source tree{Colors.NC}")
                logger.error(f"{Colors.RED}Try without the --skip-sync flag{Colors.NC}")
                return False
            
            os.chdir(self.rom_path)
            logger.info(f"{Colors.GREEN}Using existing source at: {self.rom_path}{Colors.NC}")
            
            # Update local manifest even when skipping sync
            logger.info(f"{Colors.GREEN}Updating device manifest...{Colors.NC}")
            local_manifests_dir = os.path.join(self.rom_path, ".repo/local_manifests")
            if os.path.isdir(local_manifests_dir):
                for item in os.listdir(local_manifests_dir):
                    item_path = os.path.join(local_manifests_dir, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
            else:
                os.makedirs(local_manifests_dir, exist_ok=True)
            
            # Download the device manifest
            device_manifest_url = ""
            
            if self.options.rom == "axion" and self.options.device == "pipa":
                device_manifest_url = "https://raw.githubusercontent.com/ai94iq/local_manifests/main/axion-pipa-qpr2.xml"
            elif self.options.rom == "axion" and self.options.device == "raven":
                device_manifest_url = "https://raw.githubusercontent.com/ai94iq/local_manifests/main/axion-raven-qpr2.xml"
            elif self.options.rom == "lmodroid" and self.options.device == "pipa":
                device_manifest_url = "https://raw.githubusercontent.com/ai94iq/local_manifests/main/lmov-pipa.xml"
            
            if device_manifest_url:
                manifest_path = os.path.join(local_manifests_dir, "device.xml")
                cmd = f"wget -O {manifest_path} {device_manifest_url}"
                self.run_command(cmd)
            
            # Limited sync for device files
            logger.info(f"{Colors.GREEN}Syncing device-specific repositories...{Colors.NC}")
            cores = os.cpu_count() or 4
            cmd = f"repo sync -c -j{cores} --force-sync --no-clone-bundle --no-tags -f device/ vendor/ kernel/ hardware/xiaomi/ hardware/google/"
            self.run_command(cmd)
        
        # Verify we're in a valid ROM directory
        if not os.path.isfile(os.path.join(self.rom_path, "build/envsetup.sh")):
            logger.error(f"{Colors.RED}Error: build/envsetup.sh not found in {os.getcwd()}{Colors.NC}")
            logger.error(f"{Colors.RED}This doesn't appear to be a valid ROM source directory{Colors.NC}")
            return False
            
        logger.info(f"{Colors.GREEN}Environment setup complete{Colors.NC}")
        return True
        
    def show_elapsed_time(self) -> None:
        """Display elapsed time of the build process"""
        elapsed = int(time.time() - self.start_time)
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        logger.info(f"{Colors.CYAN}Build time: {hours}h {minutes}m {seconds}s{Colors.NC}")

    def build_rom(self, variant: str, is_fastboot: bool) -> bool:
        """Simulate building the ROM"""
        output_dir = os.path.join(self.rom_path, "out/target/product", self.options.device)
        
        # Setup device-specific build environment
        logger.info(f"{Colors.GREEN}Setting up device: {self.options.device} with variant: {variant}{Colors.NC}")
        if self.options.rom == "axion":
            if self.options.device == "pipa" or self.options.device == "raven":
                # Set GMS build flag for Axion if needed
                if variant == "gms":
                    logger.info(f"{Colors.GREEN}Configuring build for GMS support{Colors.NC}")
                    cmd = f"axion {self.options.device} gms"
                    logger.info(f"{Colors.YELLOW}Would run: {cmd}{Colors.NC}")
                else:
                    logger.info(f"{Colors.GREEN}Configuring build for vanilla version (no GMS){Colors.NC}")
                    cmd = f"axion {self.options.device} va"
                    logger.info(f"{Colors.YELLOW}Would run: {cmd}{Colors.NC}")
        elif self.options.rom == "lmodroid":
            if self.options.device == "pipa":
                cmd = f"lunch lmodroid_pipa-userdebug || breakfast pipa"
                logger.info(f"{Colors.YELLOW}Would run: {cmd}{Colors.NC}")
            elif self.options.device == "raven":
                cmd = f"lunch lmodroid_raven-userdebug || breakfast raven"
                logger.info(f"{Colors.YELLOW}Would run: {cmd}{Colors.NC}")

        # Clean build if requested
        if self.options.clean_build:
            logger.info(f"{Colors.YELLOW}Running clean build...{Colors.NC}")
            cmd = "m clean"
            logger.info(f"{Colors.YELLOW}Would run: {cmd}{Colors.NC}")
        else:
            logger.info(f"{Colors.YELLOW}Running incremental build...{Colors.NC}")
            cmd = "m installclean"
            logger.info(f"{Colors.YELLOW}Would run: {cmd}{Colors.NC}")

        # Configure for fastboot build if requested
        if is_fastboot:
            logger.info(f"{Colors.YELLOW}Configuring for fastboot build...{Colors.NC}")
            cmd = "export BUILD_FASTBOOT=true"
            logger.info(f"{Colors.YELLOW}Would run: {cmd}{Colors.NC}")
        else:
            cmd = "export BUILD_FASTBOOT=false"
            logger.info(f"{Colors.YELLOW}Would run: {cmd}{Colors.NC}")

        # Start the build
        logger.info(f"{Colors.GREEN}Starting build process...{Colors.NC}")
        if self.options.rom == "axion":
            logger.info(f"{Colors.YELLOW}Building Axion for {self.options.device} with variant: {variant}{Colors.NC}")
            
            # Use brunch command for the actual build
            cmd = f"brunch {self.options.device}"
            logger.info(f"{Colors.YELLOW}Would run: {cmd}{Colors.NC}")
        else:
            logger.info(f"{Colors.YELLOW}Building LMODroid for {self.options.device}{Colors.NC}")
            cmd = "m lmodroid"
            logger.info(f"{Colors.YELLOW}Would run: {cmd}{Colors.NC}")

        # Simulate successful build
        logger.info(f"{Colors.GREEN}Build successful! (simulation){Colors.NC}")
        
        # Generate simulated output paths for files that would be copied
        logger.info(f"{Colors.GREEN}Copying build files to {self.release_dir}{Colors.NC}")
        
        # Simulate file operations for Axion ROM
        if self.options.rom == "axion":
            # Regular ROM ZIP
            zip_name = f"axion-1.2-BETA-{self.options.date_string}-OFFICIAL-{variant.upper()}-{self.options.device}.zip"
            logger.info(f"'out/target/product/{self.options.device}/{zip_name}' -> '{self.release_dir}/{zip_name}'")
            
            # Fastboot package if requested
            if is_fastboot:
                fastboot_name = f"axion-{self.options.date_string}-{variant.upper()}-{self.options.device}-FASTBOOT.zip"
                logger.info(f"'out/target/product/{self.options.device}/lineage_{self.options.device}-img.zip' -> '{self.release_dir}/{fastboot_name}'")
                logger.info(f"{Colors.GREEN}Copied fastboot image package{Colors.NC}")
            
            # JSON files for OTA
            if variant == "vanilla" and not is_fastboot:
                json_name = f"{self.options.device}-vanilla.json"
                logger.info(f"'out/target/product/{self.options.device}/VANILLA/{self.options.device}.json' -> '{self.release_dir}/{json_name}'")
                logger.info(f"{Colors.GREEN}Copied VANILLA OTA config json{Colors.NC}")
            elif variant == "gms" and not is_fastboot:
                json_name = f"{self.options.device}-gms.json"
                logger.info(f"'out/target/product/{self.options.device}/GMS/{self.options.device}.json' -> '{self.release_dir}/{json_name}'")
                logger.info(f"{Colors.GREEN}Copied GMS OTA config json{Colors.NC}")
        
        # Simulate file operations for LMODroid
        else:
            # Regular ROM ZIP
            zip_name = f"lmodroid-{self.options.date_string}-UNOFFICIAL-{self.options.device}.zip"
            logger.info(f"'out/target/product/{self.options.device}/{zip_name}' -> '{self.release_dir}/{zip_name}'")
            
            # Fastboot package if requested
            if is_fastboot:
                fastboot_name = f"lmodroid-{self.options.date_string}-{self.options.device}-FASTBOOT.zip"
                logger.info(f"'out/target/product/{self.options.device}/lmodroid_{self.options.device}-img.zip' -> '{self.release_dir}/{fastboot_name}'")
                logger.info(f"{Colors.GREEN}Copied fastboot image package{Colors.NC}")
        
        # Copy boot images only for non-fastboot builds
        if not is_fastboot:
            logger.info(f"'out/target/product/{self.options.device}/boot.img' -> '{self.release_dir}/boot.img'")
            logger.info(f"'out/target/product/{self.options.device}/dtbo.img' -> '{self.release_dir}/dtbo.img'")
            logger.info(f"'out/target/product/{self.options.device}/vendor_boot.img' -> '{self.release_dir}/vendor_boot.img'")
        
        logger.info(f"{Colors.GREEN}Build files copied to: {self.release_dir}{Colors.NC}")
        return True

    def run(self) -> int:
        """Main execution flow"""
        # Start tracking time
        self.start_time = time.time()
        
        # Setup environment
        if not self.setup_environment():
            return 1
        
        # Note about limitation
        logger.info(f"{Colors.YELLOW}Note: This Python script can only simulate the ROM build process{Colors.NC}")
        logger.info(f"{Colors.YELLOW}because it cannot source the Android build environment directly.{Colors.NC}")
        logger.info(f"{Colors.YELLOW}For actual builds, use rom-builder.sh{Colors.NC}")
        
        # Build ROM based on variant
        if self.options.rom == "axion" and self.options.variant == "both":
            # Build vanilla without fastboot
            logger.info(f"{Colors.BLUE}=== Building vanilla variant ==={Colors.NC}")
            self.build_rom("vanilla", False)
            
            # If fastboot is requested, also build vanilla fastboot
            if self.options.build_fastboot:
                logger.info(f"{Colors.BLUE}=== Building vanilla variant with fastboot ==={Colors.NC}")
                self.build_rom("vanilla", True)
            
            # Build GMS without fastboot
            logger.info(f"{Colors.BLUE}=== Building GMS variant ==={Colors.NC}")
            self.build_rom("gms", False)
            
            # If fastboot is requested, also build GMS fastboot
            if self.options.build_fastboot:
                logger.info(f"{Colors.BLUE}=== Building GMS variant with fastboot ==={Colors.NC}")
                self.build_rom("gms", True)
        else:
            # Build single variant without fastboot
            logger.info(f"{Colors.BLUE}=== Building {self.options.variant} variant ==={Colors.NC}")
            self.build_rom(self.options.variant, False)
            
            # If fastboot is requested, build it with fastboot
            if self.options.build_fastboot:
                logger.info(f"{Colors.BLUE}=== Building {self.options.variant} variant with fastboot ==={Colors.NC}")
                self.build_rom(self.options.variant, True)
        
        logger.info(f"{Colors.BLUE}=== All builds complete ==={Colors.NC}")
        logger.info(f"{Colors.GREEN}ROM files are available in: {self.release_dir}{Colors.NC}")
        
        # Show elapsed time
        self.show_elapsed_time()
        
        return 0


def main():
    """Main function to parse arguments and run the builder"""
    parser = argparse.ArgumentParser(description="ROM Builder")
    
    parser.add_argument("-r", "--rom", default="axion", help="Specify ROM: axion or lmodroid")
    parser.add_argument("-d", "--device", default="pipa", help="Specify target device: pipa or raven")
    parser.add_argument("-v", "--variant", default="vanilla", help="Variant for Axion: vanilla, gms, or both")
    parser.add_argument("-s", "--skip-sync", action="store_true", help="Skip repository sync step")
    parser.add_argument("-c", "--clean", dest="clean_build", action="store_true", default=True, help="Force clean build (default)")
    parser.add_argument("-f", "--fastboot", dest="build_fastboot", action="store_true", help="Build fastboot flashable package")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.rom not in ["axion", "lmodroid"]:
        logger.error(f"{Colors.RED}Error: Invalid ROM '{args.rom}'. Valid options are: axion, lmodroid{Colors.NC}")
        return 1
        
    if args.device not in ["pipa", "raven"]:
        logger.error(f"{Colors.RED}Error: Invalid device '{args.device}'. Valid options are: pipa, raven{Colors.NC}")
        return 1
        
    if args.variant not in ["vanilla", "gms", "both"]:
        logger.error(f"{Colors.RED}Error: Invalid variant '{args.variant}'. Valid options are: vanilla, gms, both{Colors.NC}")
        return 1
    
    # Create options object from arguments
    options = BuildOptions(
        rom=args.rom,
        device=args.device,
        variant=args.variant,
        skip_sync=args.skip_sync,
        clean_build=args.clean_build,
        build_fastboot=args.build_fastboot
    )
    
    # Create and run the builder
    builder = RomBuilder(options)
    return builder.run()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Build canceled by user{Colors.NC}")
        sys.exit(130)