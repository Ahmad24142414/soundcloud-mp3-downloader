#!/usr/bin/env bash
# Build script for Render deployment
# This script runs during the build phase

set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install FFmpeg for audio conversion
apt-get update && apt-get install -y ffmpeg || echo "FFmpeg installation skipped (may already be available)"

echo "Build completed successfully!"
