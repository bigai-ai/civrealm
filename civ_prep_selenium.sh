#!/bin/bash

sudo apt-get install docker.io docker firefox jq curl

echo "Creating docker usergroup and adding current user"

sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker

echo "Pull standard docker for freeciv/freeciv-web"

docker pull freeciv/freeciv-web

echo "Downloading geckodriver ..."

json=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest)
url=$(echo "$json" | jq -r '[.assets[].browser_download_url | select(contains("linux64.tar.gz"))][0]')

curl -s -L "$url" | tar -xz
chmod +x geckodriver

echo "Installation complete!"