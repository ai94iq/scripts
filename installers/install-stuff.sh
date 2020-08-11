#!/bin/bash

zenity --question --text="Do you want to bloat your system?" --no-wrap
if [ $? = 0 ]; then

			#Add Keys/Repo's#

			#Sublime
			wget -qO - https://download.sublimetext.com/sublimehq-pub.gpg | sudo apt-key add -
			sudo apt-get install apt-transport-https
			echo "deb https://download.sublimetext.com/ apt/stable/" | sudo tee /etc/apt/sources.list.d/sublime-text.list

			#Plata
			sudo add-apt-repository ppa:tista/plata-theme

			#IconPacks
			sudo add-apt-repository ppa:papirus/papirus

			#Wine
			sudo dpkg --add-architecture i386
			wget -O - https://dl.winehq.org/wine-builds/winehq.key | sudo apt-key add -
			sudo add-apt-repository 'deb https://dl.winehq.org/wine-builds/ubuntu/ focal main'

			#Etc.


			#Installing#
			sudo apt update
			sudo apt-get install sublime-merge spotify-client plata-theme papirus-icon-theme chromium-browser geany geany-plugins gimp vlc psensor fonts-roboto ttf-mscorefonts-installer deluge uget codeblocks meld gparted playonlinux winehq-stable fortune-mod figlet htop cmatrix neofetch aria2 curl ncdu python3-pip python3-venv zip unzip gdebi-core

			#BC
			wget https://www.scootersoftware.com/bcompare-4.3.5.24893_amd64.deb
			sudo gdebi bcompare-4.3.5.24893_amd64.deb

exit
fi