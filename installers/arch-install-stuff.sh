#!/bin/bash

#sublime-text
curl -O https://download.sublimetext.com/sublimehq-pub.gpg && sudo pacman-key --add sublimehq-pub.gpg && sudo pacman-key --lsign-key 8A8F901A && rm sublimehq-pub.gpg
echo -e "\n[sublime-text]\nServer = https://download.sublimetext.com/arch/stable/x86_64" | sudo tee -a /etc/pacman.conf
sudo pacman -Syu sublime-text


#install-stuff
yay -Syu papirus-icon-theme meld gparted telegram-desktop google-chrome gdu ttf-ms-fonts noto-fonts-emoji appimagelauncher appstream appimage-manager appimage-thumbnailer-git appimage-appimage ocs-url htop neofetch plata-theme thermald lm_sensors psensor mate-terminal ttf-opensans drun intel-ucode-clear gtk-engine-murrine ttf-roboto marco flameshot spotify octopi-dev celluloid youtube-dl