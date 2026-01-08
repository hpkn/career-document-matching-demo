#!/bin/bash

echo "========================================="
echo "Deploy Flask Server to Staging"
echo "========================================="
echo ""

# Step 1: Copy the new service file to systemd directory
echo "--- Step 1: Installing new service file ---"
sudo cp career-demo.service /etc/systemd/system/career-demo.service
sudo chmod 644 /etc/systemd/system/career-demo.service

# Step 2: Reload systemd to recognize the new service configuration
echo "--- Step 2: Reloading systemd daemon ---"
sudo systemctl daemon-reload

# Step 3: Stop the old service
echo "--- Step 3: Stopping old service ---"
sudo systemctl stop career-demo.service

# Step 4: Install Python dependencies (if needed)
echo "--- Step 4: Checking dependencies ---"
if [ -d ".venv" ]; then
    echo "Virtual environment found, activating..."
    source .venv/bin/activate
    pip install -q -r requirements.txt
    echo "Dependencies updated"
else
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
fi

# Step 5: Enable and start the new service
echo "--- Step 5: Starting Flask server service ---"
sudo systemctl enable career-demo.service
sudo systemctl start career-demo.service

# Step 6: Check status
echo ""
echo "--- Deployment Complete! ---"
echo ""
echo "Service Status:"
sudo systemctl status career-demo.service --no-pager -l

echo ""
echo "To view logs, run:"
echo "  sudo journalctl -u career-demo.service -f"
echo ""
echo "Flask server should now be running on port 8501"
echo "Access at: https://ai-test.rs-team.com"
