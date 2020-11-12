#!/bin/bash


#Sublime-text
sudo rpm -v --import https://download.sublimetext.com/sublimehq-rpm-pub.gpg
sudo zypper addrepo -g -f https://download.sublimetext.com/rpm/stable/x86_64/sublime-text.repo

#Install-everything
sudo zypper in arc-icon-theme materia-gtk-theme papirus-icon-theme paper-icon-theme cinnamon-theme-plata telegram-theme-plata gtk2-metatheme-plata gtk3-metatheme-plata gtk4-metatheme-plata metatheme-plata-common chromium htop neofetch git sublime-text thermald

#Spotify-flatpak
sudo zypper in flatpak
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install flathub com.spotify.Client
