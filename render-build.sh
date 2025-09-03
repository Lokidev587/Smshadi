#!/bin/bash
set -o errexit

# Install Chrome and Chromedriver for Render
apt-get update
apt-get install -y chromium-browser chromium-chromedriver

# Install Python dependencies
pip install -r requirements.txt
