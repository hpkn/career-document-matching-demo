#!/bin/bash

# --- CONFIGURATION ---
# 1. STOP: Stop the running service
#    (You must replace 'career-demo.service' with your actual service name)
echo "--- Stopping the service... ---"
sudo systemctl stop career-demo.service

# 2. CLEAN: Delete all old data, PDFs, and the stale FAISS index
#    (This forces the app to re-process the new file)
echo "--- Cleaning old data, PDFs, and FAISS index... ---"
rm -f /home/rsteam/repositories/career-document-matching-demo/data/pdfs/*
rm -f /home/rsteam/repositories/career-document-matching-demo/data/faiss_index/*
rm -f /home/rsteam/repositories/career-document-matching-demo/data/llm_debug_context.txt
rm -f /home/rsteam/repositories/career-document-matching-demo/data/llm_debug_response.json

echo "--- Clean complete. ---"

# 3. RESTART: Restart the service to load all the new code
echo "--- Restarting the service... ---"
sudo systemctl restart career-demo.service

# 4. VIEW LOGS: Show the live logs so you can see what happens next
echo "--- Showing live logs (Press Ctrl+C to stop)... ---"
sudo journalctl -u career-demo.service -f -e