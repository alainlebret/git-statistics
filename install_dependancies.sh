#!/usr/bin/env bash

# This script installs the required dependencies using pip.

set -e  # Stop execution if any command fails

# Check if python3 is available.
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is not installed. Please install Python 3."
    exit 1
fi

# Upgrade pip to the latest version.
python3 -m pip install --upgrade pip

# Install the required packages.
python3 -m pip install -r requirements.txt

echo "Dependencies installed successfully."
