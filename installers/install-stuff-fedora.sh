#!/bin/bash

#enable-rpmfusion
sudo dnf install https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm

#Sublime-text
sudo rpm -v --import https://download.sublimetext.com/sublimehq-rpm-pub.gpg
sudo dnf config-manager --add-repo https://download.sublimetext.com/rpm/dev/x86_64/sublime-text.repo

#install-everything
sudo dnf install sublime-text papirus-icon-theme vlc google-roboto-fonts.noarch meld gparted telegram-desktop chromium htop neofetch numix-icon-theme arc-theme numix-icon-theme-circle gnome-tweaks

#enable-flatpak
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
sudo dnf install flatpak
