#!/bin/bash

			#Add Keys/Repo's#

			#Sublime
wget -qO - https://download.sublimetext.com/sublimehq-pub.gpg | sudo apt-key add -
sudo apt-get install apt-transport-https
echo "deb https://download.sublimetext.com/ apt/stable/" | sudo tee /etc/apt/sources.list.d/sublime-text.list

			#Spotify
curl -sS https://download.spotify.com/debian/pubkey.gpg | sudo apt-key add - 
curl -sS https://download.spotify.com/debian/pubkey_0D811D58.gpg | sudo apt-key add - 
echo "deb http://repository.spotify.com stable non-free" | sudo tee /etc/apt/sources.list.d/spotify.list

			#vscode
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
sudo sh -c 'echo "deb [arch=amd64 signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/vscode stable main" > /etc/apt/sources.list.d/vscode.list'

			#Plata
sudo add-apt-repository ppa:tista/plata-theme

			#IconPacks
sudo add-apt-repository ppa:papirus/papirus

			#Etc.


			#Installing#
			sudo apt update
			sudo apt-get install sublime-text plata-theme papirus-icon-theme vlc psensor fonts-roboto ttf-mscorefonts-installer meld gparted code telegram-desktop spotify-client


			#BC
			wget https://www.scootersoftware.com/bcompare-4.3.5.24893_amd64.deb
			sudo apt-get install gdebi-core
			sudo gdebi bcompare-4.3.5.24893_amd64.deb

exit
