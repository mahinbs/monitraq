#!/bin/bash

# DICOM Analyzer Startup Script
# This script ensures the correct environment is set up to avoid protobuf conflicts

echo "🏥 Starting DICOM Analyzer with proper environment..."

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH to prioritize virtual environment packages
export PYTHONPATH=./venv/lib/python3.10/site-packages:$PYTHONPATH

# Start the application
python run.py
