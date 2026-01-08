# Deployment Guide - Switching from Streamlit to Flask

## Problem
The staging server is still running Streamlit instead of the new Flask web interface.

## Solution
Update the systemd service to run Flask instead of Streamlit.

---

## Steps to Deploy

### 1. Push Changes to Git
```bash
# On your local machine
git add .
git commit -m "Switch from Streamlit to Flask web interface"
git push origin main
```

### 2. Deploy to Staging Server
```bash
# SSH into the staging server
ssh rsteam@your-staging-server

# Navigate to the project directory
cd /home/rsteam/repositories/career-document-matching-demo

# Pull latest changes
git pull origin main

# Run the deployment script (first time only)
chmod +x deploy_to_staging.sh
./deploy_to_staging.sh
```

The deployment script will:
- ✅ Install the new systemd service file
- ✅ Reload systemd daemon
- ✅ Stop the old Streamlit service
- ✅ Update Python dependencies
- ✅ Start the new Flask service
- ✅ Enable auto-start on boot

### 3. Verify Deployment
```bash
# Check service status
sudo systemctl status career-demo.service

# View live logs
sudo journalctl -u career-demo.service -f

# Test the endpoint
curl http://localhost:8501/api/health
# Should return: {"status":"ok","message":"PQ Analysis API is running"}
```

### 4. Test in Browser
Visit: https://ai-test.rs-team.com

You should now see the new Flask web interface instead of Streamlit.

---

## What Changed

### Before (Streamlit)
- Service ran: `streamlit run app.py --server.port 8501`
- Interface: Streamlit UI
- Port: 8501

### After (Flask)
- Service runs: `python server.py`
- Interface: Modern HTML/JavaScript frontend
- Port: 8501 (same port for URL compatibility)

---

## Future Updates

After the initial deployment, for any code changes:

```bash
# On staging server
cd /home/rsteam/repositories/career-document-matching-demo
git pull origin main
./fix_and_restart.sh
```

This will:
- Stop the service
- Restart with new code
- Show live logs

---

## Troubleshooting

### Service won't start
```bash
# Check detailed logs
sudo journalctl -u career-demo.service -n 50 --no-pager

# Check if port is already in use
sudo lsof -i :8501
```

### Permission errors
```bash
# Ensure correct ownership
sudo chown -R rsteam:rsteam /home/rsteam/repositories/career-document-matching-demo

# Ensure service file has correct permissions
sudo chmod 644 /etc/systemd/system/career-demo.service
```

### Python dependencies missing
```bash
# Activate venv and reinstall
cd /home/rsteam/repositories/career-document-matching-demo
source .venv/bin/activate
pip install -r requirements.txt
```

### Rollback to Streamlit (if needed)
```bash
# Edit the service file
sudo nano /etc/systemd/system/career-demo.service

# Change ExecStart line to:
# ExecStart=/home/rsteam/repositories/career-document-matching-demo/.venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart career-demo.service
```

---

## Files Reference

- `career-demo.service` - Systemd service configuration (template)
- `deploy_to_staging.sh` - Initial deployment script
- `fix_and_restart.sh` - Quick restart script for updates
- `server.py` - Flask web server (new)
- `app.py` - Streamlit app (legacy)
