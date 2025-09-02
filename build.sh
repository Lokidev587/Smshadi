#!/bin/bash

# Install Chrome dependencies
apt-get update
apt-get install -y wget gnupg2

# Add Google Chrome repository
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list

# Update and install Chrome
apt-get update
apt-get install -y google-chrome-stable

# Install Python requirements
pip install -r requirements.txt
