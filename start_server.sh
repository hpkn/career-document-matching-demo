#!/bin/bash

echo "========================================"
echo "PQ Analysis Engine - MVP Server"
echo "========================================"
echo ""

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Virtual environment not found. Creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "Starting Flask server..."
echo "Frontend URL: http://localhost:8501"
echo "API URL: http://localhost:8501/api/health"
echo ""

python server.py
