#!/bin/bash

sudo apt-get install docker.io docker firefox jq curl
INSTALL_DIR="/usr/local/bin"

json=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest)
url=$(echo "$json" | jq -r '.assets[].browser_download_url | select(contains("linux64"))')
curl -s -L $url | tar -xz
chmod +x geckodriver
sudo mv geckodriver "$INSTALL_DIR"
echo "installed geckodriver binary in $INSTALL_DIR"
