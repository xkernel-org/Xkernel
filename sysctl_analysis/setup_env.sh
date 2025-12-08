#!/bin/bash

# Setup UV virtual environment for sysctl_analysis

# Create virtual environment with uv
uv venv

# Activate the virtual environment
source .venv/bin/activate

# Install required packages
uv pip install pandas matplotlib numpy jupyter

echo "Environment setup complete!"
echo "To activate the environment, run: source .venv/bin/activate"
