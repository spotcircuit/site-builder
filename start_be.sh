#!/bin/bash
cd "$(dirname "$0")/backend"
echo "Starting Site Builder Backend on port 9405..."
uv run python main.py
