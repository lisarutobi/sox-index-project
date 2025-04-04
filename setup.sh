#!/bin/bash
set -euo pipefail

# Install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip curl

# Create project structure
mkdir -p ~/sox-index-project/{data/historical,scraper,dashboard,scripts}

# Install Python dependencies
pip3 install dash pandas plotly

# Set up git repository
git init ~/sox-index-project
