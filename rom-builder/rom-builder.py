#!/usr/bin/env python3
# filepath: c:\Users\abdoi\Desktop\scripts\rom-builder\rom-builder.py

import os
import sys
import time
import argparse
import subprocess
import shutil
import re
import json
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
    rom: str = ""
    device: str = ""
    variant: str = ""
    use_server_path: bool = True
    date_string: str = datetime.now().strftime("%Y%m%d")
    skip_sync: bool = False
    clean_build: bool = True
    build_fastboot: bool = True
    interactive: bool = True

# Device configurations
class DeviceInfo:
    def __init__(self, name: str, soc: str, manufacturer: str):
        self.name = name
        self.soc = soc
        self.manufacturer = manufacturer

# ROM configurations
class RomInfo:
    def __init__(self, name: str, directory: str, manifest_url: str, branch: str):
        self.name = name
        self.directory = directory
        self.manifest_url = manifest_url
        self.branch = branch

# Global configurations
class Config:
    # Device configurations
    DEVICE_INFO = {
        "pipa": DeviceInfo("Xiaomi Pad 6", "sm8250", "xiaomi"),
        "raven": DeviceInfo("Google Pixel 6 Pro", "gs101", "google")
    }
    
    # ROM configurations
    ROM_INFO = {
        "axion": RomInfo("Axion AOSP", "ax", "https://github.com/AxionAOSP/android.git", "lineage-22.2"),
        "lmodroid": RomInfo("LMODroid", "lmo", "https://git.libremobileos.com/LMODroid/manifest.git", "fifteen")
    }

    # Device repositories
    DEVICE_REPOS = {
        "axion": {
            "pipa": ("https://github.com/ai94iq/android_device_xiaomi_pipa", "axv-qpr2"),
            "raven": {
                "device": None,  # Using breakfast instead
                "vendor": ("https://github.com/TheMuppets/proprietary_vendor_google_raven", "lineage-22.2", "vendor/google/raven")
            }
        },
        "lmodroid": {
            "pipa": ("https://github.com/ai94iq/android_device_xiaomi_pipa", "lmov"),
            "raven": None  # Using breakfast instead
        }
    }
    
    # LineageOS repositories needed for Axion
    LINEAGE_REPOS = {
        "hardware/xiaomi": ("https://github.com/LineageOS/android_hardware_xiaomi", "lineage-22.2"),
        "hardware/lineage/compat": ("https://github.com/LineageOS/android_hardware_lineage_compat", "lineage-22.2"),
        "hardware/lineage/interfaces": ("https://github.com/LineageOS/android_hardware_lineage_interfaces", "lineage-22.2"),
        "hardware/lineage/livedisplay": ("https://github.com/LineageOS/android_hardware_lineage_livedisplay", "lineage-22.2")
    }
    
    # Required repositories for device validation
    DEVICE_REQUIRED_REPOS = {
        "pipa": [
            "device/xiaomi/pipa",
            "device/xiaomi/sm8250-common",
            "kernel/xiaomi/sm8250",
            "vendor/xiaomi/sm8250-common",
            "vendor/xiaomi/pipa"
        ],
        "raven": [
            "device/google/raviole"
        ]
    }

class Colors:
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN
    NC = Style.RESET_ALL

class RomBuilder:
    def __init__(self, options: BuildOptions):
        self.options = options
        self.config = Config()
        self.start_time = time.time()
        
        # Set up paths and variables
        if self.options.rom:
            self.rom_info = Config.ROM_INFO[self.options.rom]
        else:
            self.rom_info = None
            
        if self.options.device:
            self.device_info = Config.DEVICE_INFO[self.options.device]
        else:
            self.device_info = None
            
        self.log_file = None
        self.log_dir = os.path.expanduser("~/rom_build_logs")
        os.makedirs(self.log_dir, exist_ok=True)

    def setup_logging(self):
        """Set up logging for the build process"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"build_{timestamp}.log")
        
        with open(self.log_file, "w") as f:
            f.write(f"ROM Builder Log - {datetime.now()}\n")
            f.write(f"ROM: {self.options.rom} | Device: {self.options.device} | Variant: {self.options.variant}\n")
            f.write(f"Skip sync: {self.options.skip_sync} | Clean build: {self.options.clean_build}\n")
        
        logger.info(f"{Colors.CYAN}Log:{Colors.NC} {self.log_file}")
        return self.log_file

    def show_usage(self):
        """Display usage information with detailed explanations"""
        print(f"{Colors.BLUE}=== ROM Builder Help ==={Colors.NC}")
        print(f"{Colors.CYAN}Usage:{Colors.NC} rom-builder.py [options]")
        print(f"{Colors.CYAN}Options:{Colors.NC}")
        print(f"  {Colors.GREEN}-r, --rom{Colors.NC} ROM       Specify ROM: {Colors.YELLOW}axion{Colors.NC} or {Colors.YELLOW}lmodroid{Colors.NC}")
        print(f"  {Colors.GREEN}-d, --device{Colors.NC} DEVICE Specify device: {Colors.YELLOW}pipa{Colors.NC} (Xiaomi Pad 6) or {Colors.YELLOW}raven{Colors.NC} (Pixel 6 Pro)")
        print(f"  {Colors.GREEN}-v, --variant{Colors.NC} VAR   Variant for Axion: {Colors.YELLOW}vanilla{Colors.NC}, {Colors.YELLOW}gms{Colors.NC}, or {Colors.YELLOW}both{Colors.NC}")
        print(f"  {Colors.GREEN}-n, --non-interactive{Colors.NC} Skip interactive prompts")
        print(f"  {Colors.GREEN}-l, --local-path{Colors.NC}    Use local path (~/) instead of server path")
        print(f"  {Colors.GREEN}-s, --skip-sync{Colors.NC}     Skip repo sync step")
        print(f"  {Colors.GREEN}-c, --clean{Colors.NC}         Force clean build")
        print(f"  {Colors.GREEN}-f, --fastboot{Colors.NC}      Build fastboot package")
        print(f"  {Colors.GREEN}-h, --help{Colors.NC}          Show help info")
        print(f"{Colors.BLUE}Examples:{Colors.NC}")
        print(f"  rom-builder.py -r axion -d pipa -v gms -n    # Build Axion for Pad 6 with GMS")
        print(f"  rom-builder.py -r lmodroid -d raven          # Build LMODroid for Pixel 6 Pro (interactive)")

    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        missing_deps = 0
        deps = ["repo", "git", "curl"]
        
        logger.info(f"{Colors.CYAN}Checking dependencies...{Colors.NC}")
        for dep in deps:
            if shutil.which(dep) is None:
                logger.info(f"{Colors.RED}Missing: {dep}{Colors.NC}")
                missing_deps += 1
        
        if missing_deps > 0:
            logger.info(f"{Colors.YELLOW}Please install missing dependencies{Colors.NC}")
            return False
        else:
            logger.info(f"{Colors.GREEN}All dependencies satisfied{Colors.NC}")
            return True

    def run_command(self, cmd: str, cwd: Optional[str] = None, silent: bool = False) -> Tuple[int, str, str]:
        """Run a shell command and return its exit code, stdout and stderr"""
        if not silent:
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
        
        if process.returncode != 0 and not silent:
            logger.info(f"{Colors.RED}Command failed with exit code {process.returncode}{Colors.NC}")
            if stderr:
                logger.info(f"{Colors.RED}Error: {stderr}{Colors.NC}")
        
        return process.returncode, stdout, stderr

    def analyze_build_error(self, log_file: str) -> bool:
        """Analyze build errors from the log file"""
        if not os.path.isfile(log_file):
            logger.info(f"{Colors.RED}Log file not found{Colors.NC}")
            return False
        
        logger.info(f"{Colors.YELLOW}Analyzing build errors...{Colors.NC}")
        
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            log_content = f.read()
            
        if re.search(r"error: package .* does not exist", log_content):
            logger.info(f"{Colors.RED}Error: Missing package dependency{Colors.NC}")
            logger.info(f"{Colors.YELLOW}Try running 'repo sync' again{Colors.NC}")
        elif re.search(r"error: '.*' has no member named", log_content):
            logger.info(f"{Colors.RED}Error: C++ compilation error{Colors.NC}")
        elif "Out of memory" in log_content:
            logger.info(f"{Colors.RED}Error: System ran out of memory{Colors.NC}")
        elif "No space left on device" in log_content:
            logger.info(f"{Colors.RED}Error: Disk space full{Colors.NC}")
        else:
            logger.info(f"{Colors.YELLOW}Check log for details{Colors.NC}")
        
        return False

    def upload_build(self, release_dir: str) -> bool:
        """Upload build files to various destinations"""
        if not self.options.interactive:
            return True
            
        upload_choice = input(f"{Colors.CYAN}Upload build? (y/n):{Colors.NC} ")
        
        if upload_choice.lower() != 'y':
            return True
        
        print(f"{Colors.CYAN}Destination: {Colors.GREEN}1){Colors.NC} Google Drive {Colors.GREEN}2){Colors.NC} PixelDrain {Colors.GREEN}3){Colors.NC} SFTP")
        dest_choice = input("Choice (1-3): ")
        
        if dest_choice == '1':
            # Google Drive upload
            if not shutil.which("gdrive"):
                logger.info(f"{Colors.RED}gdrive not installed{Colors.NC}")
                return False
            
            logger.info(f"{Colors.CYAN}Uploading to Google Drive...{Colors.NC}")
            folder_name = f"ROM-{self.options.rom}-{self.options.device}-{self.options.date_string}"
            
            # Create folder
            exit_code, stdout, _ = self.run_command(f"gdrive mkdir \"{folder_name}\"")
            if exit_code != 0:
                logger.info(f"{Colors.RED}Failed to create folder{Colors.NC}")
                return False
            
            # Extract folder ID
            folder_id = None
            for line in stdout.splitlines():
                if "Directory ID:" in line:
                    folder_id = line.split()[-1]
                    break
            
            if not folder_id:
                logger.info(f"{Colors.RED}Failed to get folder ID{Colors.NC}")
                return False
            
            # Upload files
            for ext in ["zip", "img"]:
                for file in Path(release_dir).glob(f"*.{ext}"):
                    logger.info(f"{Colors.CYAN}Uploading: {file.name}{Colors.NC}")
                    self.run_command(f"gdrive upload --parent \"{folder_id}\" \"{file}\"")
            
            logger.info(f"{Colors.GREEN}Uploaded to: {folder_name}{Colors.NC}")
            
        elif dest_choice == '2':
            # PixelDrain upload
            logger.info(f"{Colors.CYAN}Uploading to PixelDrain...{Colors.NC}")
            
            for file in Path(release_dir).glob("*.zip"):
                logger.info(f"{Colors.CYAN}Uploading: {file.name}{Colors.NC}")
                exit_code, stdout, _ = self.run_command(f"curl -# -F \"file=@{file}\" https://pixeldrain.com/api/file/")
                
                if exit_code == 0:
                    try:
                        data = json.loads(stdout)
                        file_id = data.get('id')
                        if file_id:
                            logger.info(f"{Colors.GREEN}URL: https://pixeldrain.com/u/{file_id}{Colors.NC}")
                        else:
                            logger.info(f"{Colors.RED}Upload failed, couldn't get file ID{Colors.NC}")
                    except json.JSONDecodeError:
                        logger.info(f"{Colors.RED}Upload failed, couldn't parse response{Colors.NC}")
                else:
                    logger.info(f"{Colors.RED}Upload failed{Colors.NC}")
            
        elif dest_choice == '3':
            # SFTP upload
            sftp_server = input("SFTP server: ")
            sftp_user = input("Username: ")
            remote_dir = input("Remote dir: ")
            
            if not sftp_server or not sftp_user or not remote_dir:
                logger.info(f"{Colors.RED}Missing SFTP info{Colors.NC}")
                return False
            
            logger.info(f"{Colors.CYAN}Uploading to SFTP...{Colors.NC}")
            self.run_command(f"ssh \"{sftp_user}@{sftp_server}\" \"mkdir -p {remote_dir}\"")
            
            for ext in ["zip", "img"]:
                for file in Path(release_dir).glob(f"*.{ext}"):
                    logger.info(f"{Colors.CYAN}Uploading: {file.name}{Colors.NC}")
                    self.run_command(f"scp \"{file}\" \"{sftp_user}@{sftp_server}:{remote_dir}/\"")
            
            logger.info(f"{Colors.GREEN}Files uploaded to SFTP{Colors.NC}")
            
        return True

    def generate_docs(self, rom_dir: str, variant: str = None) -> str:
        """Generate documentation about the build"""
        logger.info(f"{Colors.CYAN}Generating docs...{Colors.NC}")
        
        if self.options.use_server_path:
            if self.options.rom == "axion" and variant and variant != "both":
                doc_file = f"/var/www/html/{self.options.rom}-{self.options.device}-releases-{self.options.date_string}/{variant}/README.md"
            else:
                doc_file = f"/var/www/html/{self.options.rom}-{self.options.device}-releases-{self.options.date_string}/README.md"
        else:
            if self.options.rom == "axion" and variant and variant != "both":
                doc_file = os.path.expanduser(f"~/{self.options.rom}-{self.options.device}-releases/{variant}/README.md")
            else:
                doc_file = os.path.expanduser(f"~/{self.options.rom}-{self.options.device}-releases/README.md")
        
        # Create parent directory
        os.makedirs(os.path.dirname(doc_file), exist_ok=True)
        
        # Get device name
        device_name = self.options.device
        if self.options.device in self.config.DEVICE_INFO:
            device_name = self.config.DEVICE_INFO[self.options.device].name

        # Get repo URLs from config
        manifest_url = self.rom_info.manifest_url
        branch = self.rom_info.branch
        
        device_repo = ""
        device_branch = ""
        if self.options.rom == "axion":
            if self.options.device == "pipa":
                device_repo, device_branch = self.config.DEVICE_REPOS["axion"]["pipa"]
            elif self.options.device == "raven":
                device_repo = "https://github.com/LineageOS/android_device_google_raviole"
                device_branch = "lineage-22.2"
        else:  # lmodroid
            if self.options.device == "pipa":
                device_repo, device_branch = self.config.DEVICE_REPOS["lmodroid"]["pipa"]
            elif self.options.device == "raven":
                device_repo = "https://github.com/LineageOS/android_device_google_raviole"
                device_branch = "lineage-22.2"
        
        with open(doc_file, "w") as f:
            f.write(f"# {self.options.rom} ROM Build for {device_name} ({self.options.device})\n\n")
            
            f.write("## Build Information\n")
            f.write(f"- Date: {datetime.now()}\n")
            f.write(f"- ROM: {self.options.rom}\n")
            f.write(f"- Device: {device_name} ({self.options.device})\n")
            if self.options.rom == "axion":
                f.write(f"- Variant: {variant if variant else self.options.variant}\n")
            f.write(f"- Build host: {platform.node()}\n\n")
            
            f.write("## Installation Instructions\n")
            f.write("1. Download the ROM zip file\n")
            f.write("2. Boot to recovery mode (TWRP recommended)\n")
            f.write("3. Wipe data, cache, and dalvik cache\n")
            f.write("4. Flash the ROM zip file\n")
            if self.options.rom == "axion" and (not variant or variant == "vanilla"):
                f.write("5. Flash GApps if desired\n")
            f.write("5. Reboot system\n\n")
            
            f.write("## Source Code\n")
            f.write(f"- ROM: {manifest_url} (branch: {branch})\n")
            f.write(f"- Device: {device_repo} (branch: {device_branch})\n\n")
            
            f.write(f"## Build Completed: {datetime.now()}\n")
        
        logger.info(f"{Colors.GREEN}Docs: {doc_file}{Colors.NC}")
        return doc_file

    def update_device_trees(self, rom_dir: str) -> bool:
        """Update device trees with git pull"""
        # Skip this prompt if non-interactive mode OR we just synced the source
        if not self.options.interactive or not self.options.skip_sync:
            # We're either non-interactive or we just performed a full sync
            return True
            
        update_choice = input(f"{Colors.CYAN}Update device trees? (y/n): {Colors.NC}")
        
        if update_choice.lower() != 'y':
            return True
        
        home_dir = os.path.expanduser("~")
        rom_dir_path = os.path.join(home_dir, rom_dir)
        
        if self.options.device == "pipa":
            logger.info(f"{Colors.GREEN}Updating Pad 6 trees...{Colors.NC}")
            
            # Use correct branch based on ROM
            if self.options.rom == "axion":
                # For Axion ROM - branch axv-qpr2
                repo_path = os.path.join(rom_dir_path, "device/xiaomi/pipa")
                if os.path.isdir(repo_path):
                    logger.info(f"Updating device/xiaomi/pipa to axv-qpr2...")
                    self.run_command("git checkout axv-qpr2 && git pull", cwd=repo_path)
                else:
                    logger.info(f"{Colors.YELLOW}Directory not found: device/xiaomi/pipa{Colors.NC}")
                    
                dirs_to_update = [
                    "device/xiaomi/sm8250-common",
                    "kernel/xiaomi/sm8250",
                    "vendor/xiaomi/sm8250-common",
                    "vendor/xiaomi/pipa"
                ]
                
                for dir_path in dirs_to_update:
                    full_path = os.path.join(rom_dir_path, dir_path)
                    if os.path.isdir(full_path):
                        logger.info(f"Updating {dir_path}...")
                        self.run_command("git pull", cwd=full_path)
                    else:
                        logger.info(f"{Colors.YELLOW}Directory not found: {dir_path}{Colors.NC}")
            else:
                # For LMODroid ROM - branch lmov
                repo_path = os.path.join(rom_dir_path, "device/xiaomi/pipa")
                if os.path.isdir(repo_path):
                    logger.info(f"Updating device/xiaomi/pipa to lmov...")
                    self.run_command("git checkout lmov && git pull", cwd=repo_path)
                else:
                    logger.info(f"{Colors.YELLOW}Directory not found: device/xiaomi/pipa{Colors.NC}")
                    
                dirs_to_update = [
                    "device/xiaomi/sm8250-common",
                    "kernel/xiaomi/sm8250",
                    "vendor/xiaomi/sm8250-common",
                    "vendor/xiaomi/pipa"
                ]
                
                for dir_path in dirs_to_update:
                    full_path = os.path.join(rom_dir_path, dir_path)
                    if os.path.isdir(full_path):
                        logger.info(f"Updating {dir_path}...")
                        self.run_command("git pull", cwd=full_path)
                    else:
                        logger.info(f"{Colors.YELLOW}Directory not found: {dir_path}{Colors.NC}")
        
        elif self.options.device == "raven":
            logger.info(f"{Colors.GREEN}Updating Pixel 6 Pro trees...{Colors.NC}")
            
            if self.options.rom == "axion":
                # For Axion ROM, handle vendor directory with lineage-22.2 branch
                vendor_dir = "vendor/google/raven"
                full_path = os.path.join(rom_dir_path, vendor_dir)
                if os.path.isdir(full_path):
                    logger.info(f"Updating {vendor_dir} to lineage-22.2...")
                    self.run_command("git checkout lineage-22.2 && git pull", cwd=full_path)
                else:
                    logger.info(f"{Colors.YELLOW}Directory not found: {vendor_dir}{Colors.NC}")
        
        return True

    def setup_environment(self) -> bool:
        """Setup ROM environment"""
        rom = self.options.rom
        device = self.options.device
        
        rom_info = self.config.ROM_INFO[rom]
        rom_name = rom_info.name
        rom_dir = rom_info.directory
        manifest_url = rom_info.manifest_url
        branch = rom_info.branch
        
        device_info = self.config.DEVICE_INFO[device]
        device_name = device_info.name
        soc = device_info.soc
        manufacturer = device_info.manufacturer
        
        # Define device-specific repository info
        if rom == "axion":
            if device == "pipa":
                device_repo, device_branch = self.config.DEVICE_REPOS["axion"]["pipa"]
            else:  # raven
                device_repo = "Managed by breakfast"
                device_branch = "lineage-22.2"
                vendor_repo, vendor_branch, vendor_dir = self.config.DEVICE_REPOS["axion"]["raven"]["vendor"]
        else:  # lmodroid
            if device == "pipa":
                device_repo, device_branch = self.config.DEVICE_REPOS["lmodroid"]["pipa"]
            else:  # raven
                device_repo = "Managed by breakfast"
                device_branch = "fifteen"
        
        # Print detailed environment setup info
        logger.info(f"{Colors.BLUE}=== Setting up {rom_name} ({rom}) environment ==={Colors.NC}")
        logger.info(f"{Colors.CYAN}Device:{Colors.NC} {device_name} ({device}) | {Colors.CYAN}SOC:{Colors.NC} {soc} | {Colors.CYAN}Manufacturer:{Colors.NC} {manufacturer}")
        logger.info(f"{Colors.CYAN}Source:{Colors.NC} {manifest_url}")
        logger.info(f"{Colors.CYAN}Branch:{Colors.NC} {branch}")
        
        home_dir = os.path.expanduser("~")
        rom_path = os.path.join(home_dir, rom_dir)
        logger.info(f"{Colors.CYAN}Path:{Colors.NC} {rom_path}")
        
        # Handle skip sync option
        if self.options.skip_sync:
            if not os.path.isdir(rom_path):
                logger.info(f"{Colors.RED}ROM directory {rom_path} not found - can't skip sync{Colors.NC}")
                logger.info(f"{Colors.YELLOW}Falling back to full source sync{Colors.NC}")
                self.options.skip_sync = False
            else:
                logger.info(f"{Colors.GREEN}Using existing source at: {rom_path}{Colors.NC}")
                os.chdir(rom_path)
        
        if not self.options.skip_sync:
            # Remove existing directory if needed
            if os.path.isdir(rom_path):
                logger.info(f"{Colors.YELLOW}Removing existing directory: {rom_path}{Colors.NC}")
                shutil.rmtree(rom_path)
            
            # Create and setup repo
            logger.info(f"{Colors.GREEN}Creating source directory: {rom_path}{Colors.NC}")
            os.makedirs(rom_path, exist_ok=True)
            os.chdir(rom_path)
            
            logger.info(f"{Colors.GREEN}Initializing repo from {manifest_url} ({branch})...{Colors.NC}")
            cmd = f"repo init -u {manifest_url} -b {branch} --git-lfs"
            exit_code, _, _ = self.run_command(cmd)
            if exit_code != 0:
                logger.info(f"{Colors.RED}Failed to initialize repo{Colors.NC}")
                return False
            
            cores = os.cpu_count() or 4
            logger.info(f"{Colors.GREEN}Syncing source code (may take a while)...{Colors.NC}")
            logger.info(f"{Colors.YELLOW}Using {cores} parallel jobs for sync{Colors.NC}")
            cmd = f"repo sync -c -j{cores} --force-sync --no-clone-bundle --no-tags"
            exit_code, _, _ = self.run_command(cmd)
            if exit_code != 0:
                logger.info(f"{Colors.RED}Repo sync failed{Colors.NC}")
                return False
            
            # Copy vendor files if they exist
            vendor_path = os.path.join(home_dir, "vendor")
            if os.path.isdir(vendor_path):
                logger.info(f"{Colors.GREEN}Copying vendor files from ~/vendor...{Colors.NC}")
                vendor_dest = os.path.join(rom_path, "vendor")
                shutil.copytree(vendor_path, vendor_dest, dirs_exist_ok=True)
        else:
            logger.info(f"{Colors.GREEN}Skipping repo sync - using existing source code{Colors.NC}")
        
        # Option to update device trees - only if interactive and skipping sync
        if self.options.interactive and self.options.skip_sync:
            logger.info(f"{Colors.CYAN}Device trees:{Colors.NC} {device_repo} (branch: {device_branch})")
            self.update_device_trees(rom_dir)
        
        # Source build environment
        logger.info(f"{Colors.GREEN}Setting up build environment...{Colors.NC}")
        logger.info(f"{Colors.YELLOW}Loading Android build tools and environment variables{Colors.NC}")
        
        os.environ["ROM_DIR"] = rom_dir
        os.environ["DEVICE"] = device
        
        # FIXME: We can't actually source build/envsetup.sh directly in Python
        # This would require running the script in a subprocess shell and passing environment
        # back, or having a wrapper bash script that sources it then calls our Python
        logger.error(f"{Colors.RED}NOTE: In Python, we can't directly source build/envsetup.sh.{Colors.NC}")
        logger.error(f"{Colors.RED}You would need to exit this script, manually run:{Colors.NC}")
        logger.error(f"{Colors.GREEN}cd ~/{rom_dir} && source build/envsetup.sh{Colors.NC}")
        logger.error(f"{Colors.RED}Then continue with the device-specific steps below.{Colors.NC}")
        
        # Device-specific setup flows - properly handling both interactive and non-interactive modes
        if device == "pipa":
            # PIPA flow
            logger.info(f"{Colors.BLUE}=== Xiaomi Pad 6 (pipa) setup steps ==={Colors.NC}")
            
            # Set up initial environment based on ROM
            if rom == "axion":
                logger.info(f"{Colors.GREEN}After sourcing build environment, run: axion pipa{Colors.NC}")
            else:
                logger.info(f"{Colors.GREEN}After sourcing build environment, run: lunch lmodroid_pipa-userdebug{Colors.NC}")
            
            # Always validate required repositories, regardless of interactive mode
            logger.info(f"{Colors.GREEN}Validate required repositories for Xiaomi Pad 6:{Colors.NC}")
            
            required_repos = self.config.DEVICE_REQUIRED_REPOS["pipa"]
            for repo in required_repos:
                repo_path = os.path.join(rom_path, repo)
                if os.path.isdir(repo_path):
                    logger.info(f"{Colors.CYAN}✓ Would find{Colors.NC} {repo}")
                else:
                    logger.info(f"{Colors.RED}✗ Would be missing{Colors.NC} {repo}")
            
            # Handle missing repositories differently based on interactive mode
            logger.info(f"{Colors.YELLOW}In non-interactive mode, would continue despite missing repositories.{Colors.NC}" if not self.options.interactive else 
                       f"{Colors.YELLOW}In interactive mode, would prompt to continue if repositories are missing.{Colors.NC}")
            
        elif device == "raven":
            # RAVEN flow
            logger.info(f"{Colors.BLUE}=== Pixel 6 Pro (raven) setup steps ==={Colors.NC}")
            
            # Run breakfast to set up device environment
            logger.info(f"{Colors.GREEN}After sourcing build environment, run: breakfast raven{Colors.NC}")
            
            # Always check vendor after breakfast for Axion
            if rom == "axion":
                vendor_dir = "vendor/google/raven"
                logger.info(f"{Colors.GREEN}Check if vendor files exist in {vendor_dir}{Colors.NC}")
                logger.info(f"{Colors.YELLOW}If missing, would clone from: {vendor_repo} (branch: {vendor_branch}){Colors.NC}")
            
            # Always validate device setup
            required_repos = self.config.DEVICE_REQUIRED_REPOS["raven"]
            for repo in required_repos:
                repo_path = os.path.join(rom_path, repo)
                if os.path.isdir(repo_path):
                    logger.info(f"{Colors.CYAN}✓ Would find{Colors.NC} {repo}")
                else:
                    logger.info(f"{Colors.RED}✗ Would be missing{Colors.NC} {repo}")
            
            # Handle missing components differently based on interactive mode
            logger.info(f"{Colors.YELLOW}In non-interactive mode, would continue despite missing components.{Colors.NC}" if not self.options.interactive else 
                       f"{Colors.YELLOW}In interactive mode, would prompt to continue if components are missing.{Colors.NC}")
        
        # Check LineageOS repos for Axion
        if rom == "axion":
            logger.info(f"{Colors.GREEN}Checking LineageOS repositories for Axion...{Colors.NC}")
            
            # Define required LineageOS repos
            for repo_path, (repo_url, repo_branch) in self.config.LINEAGE_REPOS.items():
                repo_full_path = os.path.join(rom_path, repo_path)
                if os.path.isdir(repo_full_path):
                    logger.info(f"{Colors.CYAN}✓ Would find{Colors.NC} {repo_path}")
                else:
                    logger.info(f"{Colors.YELLOW}• Would be missing{Colors.NC} {repo_path}")
                    logger.info(f"  {Colors.GREEN}Would clone:{Colors.NC} {repo_path} from {repo_url} (branch: {repo_branch})")
        
        logger.info(f"{Colors.BLUE}=== Environment setup description complete ==={Colors.NC}")
        logger.info(f"{Colors.YELLOW}Note: This Python script can only simulate the ROM build process{Colors.NC}")
        logger.info(f"{Colors.YELLOW}      because it cannot source the Android build environment directly.{Colors.NC}")
        
        return True

    def build_axion(self, variant: str, device: str) -> bool:
        """Simulation of building Axion ROM"""
        # This is a simulation as we can't actually run the build in Python
        # since we can't source build/envsetup.sh properly
        
        rom_dir = self.config.ROM_INFO["axion"].directory
        
        logger.info(f"{Colors.BLUE}=== Building Axion ROM for {device} ==={Colors.NC}")
        var_display = "VANILLA (without Google apps)" if variant == "vanilla" else "GMS (with Google Mobile Services)"
        logger.info(f"{Colors.CYAN}ROM Variant:{Colors.NC} {var_display}")
        pkg_types = "OTA installation zip"
        if self.options.build_fastboot:
            pkg_types += " + Fastboot flashable package"
        logger.info(f"{Colors.CYAN}Package Types:{Colors.NC} {pkg_types}")
        
        logger.info(f"{Colors.GREEN}In the actual build process, you would:{Colors.NC}")
        logger.info(f"1. Set WITH_GMS={'true' if variant == 'gms' else 'false'}")
        logger.info(f"2. Run {'m clean' if self.options.clean_build else 'm installclean'}")
        logger.info(f"3. Configure with 'axion {device} {variant}'")
        logger.info(f"4. Start build with 'brunch {device}'")
        
        # Simulate successful build - determine paths where files would be created
        home_dir = os.path.expanduser("~")
        output_dir = os.path.join(home_dir, rom_dir, "out", "target", "product", device)
        variant_dir = os.path.join(output_dir, variant.upper())
        
        # Create release directory
        if self.options.use_server_path:
            release_base = f"/var/www/html/axion-{device}-releases-{self.options.date_string}"
            release_dir = os.path.join(release_base, variant)
        else:
            release_base = os.path.join(home_dir, f"axion-{device}-releases")
            release_dir = os.path.join(release_base, variant)
        
        logger.info(f"{Colors.GREEN}Files would be copied to: {release_dir}{Colors.NC}")
        
        # Generate documentation
        self.generate_docs(rom_dir, variant)
        
        logger.info(f"{Colors.GREEN}Build simulation complete!{Colors.NC}")
        return True

    def build_lmodroid(self, device: str) -> bool:
        """Simulation of building LMODroid ROM"""
        # This is a simulation as we can't actually run the build in Python
        # since we can't source build/envsetup.sh properly
        
        rom_dir = self.config.ROM_INFO["lmodroid"].directory
        
        logger.info(f"{Colors.BLUE}=== Building LMODroid ROM for {device} ==={Colors.NC}")
        pkg_types = "OTA installation zip"
        if self.options.build_fastboot:
            pkg_types += " + Fastboot flashable package"
        logger.info(f"{Colors.CYAN}Package Types:{Colors.NC} {pkg_types}")
        
        logger.info(f"{Colors.GREEN}In the actual build process, you would:{Colors.NC}")
        logger.info(f"1. Run {'m clean' if self.options.clean_build else 'm installclean'}")
        logger.info(f"2. Configure with 'lunch lmodroid_{device}-userdebug'")
        logger.info(f"3. Start build with 'm lmodroid'")
        
        # Simulate successful build - determine paths where files would be created
        home_dir = os.path.expanduser("~")
        output_dir = os.path.join(home_dir, rom_dir, "out", "target", "product", device)
        
        # Create release directory
        if self.options.use_server_path:
            release_dir = f"/var/www/html/lmodroid-{device}-releases-{self.options.date_string}"
        else:
            release_dir = os.path.join(home_dir, f"lmodroid-{device}-releases")
        
        logger.info(f"{Colors.GREEN}Files would be copied to: {release_dir}{Colors.NC}")
        
        # Generate documentation
        self.generate_docs(rom_dir)
        
        logger.info(f"{Colors.GREEN}Build simulation complete!{Colors.NC}")
        return True

    def show_elapsed_time(self) -> None:
        """Display elapsed time of the build process"""
        elapsed = int(time.time() - self.start_time)
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        logger.info(f"{Colors.CYAN}Build time: {hours}h {minutes}m {seconds}s{Colors.NC}")

    def show_device_list(self) -> int:
        """Display available devices and return count"""
        logger.info(f"{Colors.CYAN}Available devices:{Colors.NC}")
        devices = list(self.config.DEVICE_INFO.keys())
        for i, device in enumerate(devices, 1):
            info = self.config.DEVICE_INFO[device]
            logger.info(f"  {Colors.GREEN}{i}){Colors.NC} {info.name} ({device})")
        return len(devices)

    def show_rom_list(self) -> int:
        """Display available ROMs and return count"""
        logger.info(f"{Colors.CYAN}Available ROMs:{Colors.NC}")
        roms = list(self.config.ROM_INFO.keys())
        for i, rom in enumerate(roms, 1):
            info = self.config.ROM_INFO[rom]
            logger.info(f"  {Colors.GREEN}{i}){Colors.NC} {info.name}")
        return len(roms)

    def run(self) -> int:
        """Main execution flow"""
        # Start tracking time
        self.start_time = time.time()
        
        # Check dependencies
        if not self.check_dependencies():
            return 1
            
        # Setup logging
        self.setup_logging()
        
        # Interactive mode handling if no options were provided
        if self.options.interactive and (not self.options.rom or not self.options.device or 
                                       (self.options.rom == "axion" and not self.options.variant)):
            logger.info(f"{Colors.BLUE}=== ROM Builder - Interactive ==={Colors.NC}")
            
            # ROM selection
            if not self.options.rom:
                rom_count = self.show_rom_list()
                roms = list(self.config.ROM_INFO.keys())
                
                while True:
                    try:
                        choice = int(input(f"Select ROM (1-{rom_count}): "))
                        if 1 <= choice <= rom_count:
                            self.options.rom = roms[choice-1]
                            self.rom_info = self.config.ROM_INFO[self.options.rom]
                            break
                        else:
                            logger.info(f"{Colors.RED}Invalid choice{Colors.NC}")
                    except ValueError:
                        logger.info(f"{Colors.RED}Please enter a number{Colors.NC}")
            
            # Device selection
            if not self.options.device:
                device_count = self.show_device_list()
                devices = list(self.config.DEVICE_INFO.keys())
                
                while True:
                    try:
                        choice = int(input(f"Select device (1-{device_count}): "))
                        if 1 <= choice <= device_count:
                            self.options.device = devices[choice-1]
                            self.device_info = self.config.DEVICE_INFO[self.options.device]
                            break
                        else:
                            logger.info(f"{Colors.RED}Invalid choice{Colors.NC}")
                    except ValueError:
                        logger.info(f"{Colors.RED}Please enter a number{Colors.NC}")
            
            # Variant selection for Axion
            if self.options.rom == "axion" and not self.options.variant:
                logger.info(f"{Colors.CYAN}Variant: {Colors.GREEN}1){Colors.NC} Vanilla {Colors.GREEN}2){Colors.NC} GMS {Colors.GREEN}3){Colors.NC} Both")
                while True:
                    try:
                        choice = int(input("Choice (1-3): "))
                        if choice == 1:
                            self.options.variant = "vanilla"
                            break
                        elif choice == 2:
                            self.options.variant = "gms"
                            break
                        elif choice == 3:
                            self.options.variant = "both"
                            break
                        else:
                            logger.info(f"{Colors.RED}Invalid choice{Colors.NC}")
                    except ValueError:
                        logger.info(f"{Colors.RED}Please enter a number{Colors.NC}")
            
            # Output path selection
            logger.info(f"{Colors.CYAN}Output path: {Colors.GREEN}1){Colors.NC} Server {Colors.GREEN}2){Colors.NC} Local")
            while True:
                try:
                    choice = int(input("Choice (1-2): "))
                    if choice == 1:
                        self.options.use_server_path = True
                        break
                    elif choice == 2:
                        self.options.use_server_path = False
                        break
                    else:
                        logger.info(f"{Colors.RED}Invalid choice{Colors.NC}")
                except ValueError:
                    logger.info(f"{Colors.RED}Please enter a number{Colors.NC}")
            
            # Skip sync option
            skip_choice = input("Skip repo sync? (y/n): ")
            self.options.skip_sync = skip_choice.lower() == 'y'
            
            # Clean build option
            clean_choice = input("Clean build? (y/n): ")
            self.options.clean_build = clean_choice.lower() == 'y'
            
            # Fastboot package option
            fastboot_choice = input("Build fastboot package? (y/n): ")
            self.options.build_fastboot = fastboot_choice.lower() == 'y'
        
        # Show build info
        logger.info(f"{Colors.BLUE}=== ROM Builder ==={Colors.NC}")
        
        # Get device name
        device_name = self.options.device
        if self.options.device in self.config.DEVICE_INFO:
            device_name = self.config.DEVICE_INFO[self.options.device].name
        
        # Show enhanced build info with clear separation between ROM variants and output types
        logger.info(f"{Colors.CYAN}Building:{Colors.NC} {self.options.rom} for {device_name}")
        
        # ROM variant info (only for Axion)
        if self.options.rom == "axion":
            if self.options.variant == "vanilla":
                var_display = "VANILLA (without Google apps)"
            elif self.options.variant == "gms":
                var_display = "GMS (with Google Mobile Services)"
            else:
                var_display = "BOTH (vanilla & GMS versions)"
            
            logger.info(f"{Colors.CYAN}ROM Variant:{Colors.NC} {var_display}")
            if self.options.variant == "both":
                logger.info(f"{Colors.CYAN}Build Order:{Colors.NC} VANILLA → GMS")
        
        # Output package types
        pkg_types = "OTA installation zip"
        if self.options.build_fastboot:
            pkg_types += " + Fastboot flashable package"
        logger.info(f"{Colors.CYAN}Output Packages:{Colors.NC} {pkg_types}")
        
        # Other build options
        path_type = "Server directory" if self.options.use_server_path else "Local (~/) directory"
        sync_type = "Skip source sync" if self.options.skip_sync else "Full source sync"
        build_type = "Clean build" if self.options.clean_build else "Incremental build"
        logger.info(f"{Colors.CYAN}Output Path:{Colors.NC} {path_type}")
        logger.info(f"{Colors.CYAN}Build Options:{Colors.NC} {sync_type}, {build_type}")
        
        # Setup environment
        if not self.setup_environment():
            return 1
        
        # Since we can't actually run the build due to sourcing limitations,
        # we'll just simulate the build process
        if self.options.rom == "axion":
            if self.options.variant == "both":
                self.build_axion("vanilla", self.options.device)
                self.build_axion("gms", self.options.device)
            else:
                self.build_axion(self.options.variant, self.options.device)
        else:  # lmodroid
            self.build_lmodroid(self.options.device)
        
        logger.info(f"{Colors.BLUE}=== Build simulation complete ==={Colors.NC}")
        logger.info(f"{Colors.YELLOW}NOTE: This is a simulation for demonstration purposes.{Colors.NC}")
        logger.info(f"{Colors.YELLOW}      For an actual build, use the bash script which can properly{Colors.NC}")
        logger.info(f"{Colors.YELLOW}      source the Android build environment.{Colors.NC}")
        
        # Show elapsed time
        self.show_elapsed_time()
        
        return 0


def main():
    """Main function to parse arguments and run the builder"""
    parser = argparse.ArgumentParser(description="ROM Builder")
    
    parser.add_argument("-r", "--rom", help="Specify ROM: axion or lmodroid")
    parser.add_argument("-d", "--device", help="Specify device: pipa or raven")
    parser.add_argument("-v", "--variant", help="Variant for Axion: vanilla, gms, or both")
    parser.add_argument("-n", "--non-interactive", action="store_true", help="Skip interactive prompts")
    parser.add_argument("-l", "--local-path", action="store_true", help="Use local path (~/) instead of server path")
    parser.add_argument("-s", "--skip-sync", action="store_true", help="Skip repo sync step")
    parser.add_argument("-c", "--clean", dest="clean_build", action="store_true", help="Force clean build")
    parser.add_argument("-f", "--fastboot", dest="build_fastboot", action="store_true", help="Build fastboot package")
    
    args = parser.parse_args()
    
    # Create options object from arguments
    options = BuildOptions(
        rom=args.rom or "",
        device=args.device or "",
        variant=args.variant or "",
        use_server_path=not args.local_path,
        skip_sync=args.skip_sync,
        clean_build=args.clean_build,
        build_fastboot=args.build_fastboot,
        interactive=not args.non_interactive
    )
    
    # Validate options
    if args.rom and args.rom not in Config.ROM_INFO:
        logger.error(f"{Colors.RED}Error: Invalid ROM '{args.rom}'. Valid options are: {', '.join(Config.ROM_INFO.keys())}{Colors.NC}")
        return 1
        
    if args.device and args.device not in Config.DEVICE_INFO:
        logger.error(f"{Colors.RED}Error: Invalid device '{args.device}'. Valid options are: {', '.join(Config.DEVICE_INFO.keys())}{Colors.NC}")
        return 1
        
    if args.variant and args.variant not in ["vanilla", "gms", "both"]:
        logger.error(f"{Colors.RED}Error: Invalid variant '{args.variant}'. Valid options are: vanilla, gms, both{Colors.NC}")
        return 1
    
    # Create and run the builder
    builder = RomBuilder(options)
    if args.rom and args.rom in Config.ROM_INFO:
        builder.rom_info = Config.ROM_INFO[args.rom]
    if args.device and args.device in Config.DEVICE_INFO:
        builder.device_info = Config.DEVICE_INFO[args.device]
    
    return builder.run()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Build canceled by user{Colors.NC}")
        sys.exit(130)