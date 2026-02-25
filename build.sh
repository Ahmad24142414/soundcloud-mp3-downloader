#!/usr/bin/env bash
# Build script for Render deployment
# This script runs during the build phase

set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Note: For yt-dlp audio conversion, FFmpeg is required
# Render's native environment includes FFmpeg
echo "Build completed successfully!"
