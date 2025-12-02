"""
config.py
---------------------------------------------------------
Global configuration for the 3-step Streamlit workflow.

This file defines:
    - Base directories
    - Upload & PDF folders
    - FAISS index directories (step-specific)
    - OCR settings
    - Ollama LLM settings
---------------------------------------------------------
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# ---------------------------------------------------------
# Base Project Directory
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# PDF & RAW Uploads
# ---------------------------------------------------------
RAW_UPLOAD_DIR = DATA_DIR / "uploads_raw"     # HWP, original user uploads
PDF_DIR = DATA_DIR / "pdfs"                   # Normalized PDFs
INDEX_DIR = DATA_DIR / "faiss_index"          # FAISS index storage

RAW_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# OCR Settings
# ---------------------------------------------------------
TESSERACT_LANG = "kor+eng"    # Korean + English OCR
OCR_DPI_SCALE = 2.0           # 2x resolution
OCR_MIN_TEXT_CHARS = 30       # If native text < X chars → run OCR

TESS_LANG = "kor+eng"

# DPI scaling for OCR (higher = better recognition)

# ---------------------------------------------------------
# Ollama LLM Settings
# ---------------------------------------------------------
# When not set, defaults to local llama3
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Recommended model for Korean structured extraction (Step 1 & 2)
# gpt-oss:120b-cloud - Best for complex Korean text understanding
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")

# Model for Step 3 classification
# Use same model as Step 1/2 for consistency, or a faster model for speed
OLLAMA_MODEL_STEP3 = os.getenv("OLLAMA_MODEL_STEP3", "gemma3:4b")

# Skip LLM for Step 3 and use keyword-only matching (instant, deterministic)
# Set to "true" for fastest processing, "false" to use LLM
STEP3_SKIP_LLM = os.getenv("STEP3_SKIP_LLM", "true").lower() == "true"

# Number of parallel workers for LLM batch processing
# Higher = faster but more load on Ollama server
# Set to 1 for sequential processing (safest)
STEP3_LLM_WORKERS = int(os.getenv("STEP3_LLM_WORKERS", "4"))

# ---------------------------------------------------------
# Environment Settings
# ---------------------------------------------------------
# Set to "production" for GPU-accelerated processing
# Set to "development" for CPU-only processing (default)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT == "production"

# GPU device for production (cuda:0, cuda:1, etc.)
GPU_DEVICE = os.getenv("GPU_DEVICE", "cuda:0")

# You can override with:
# export ENVIRONMENT=production
# export GPU_DEVICE=cuda:0
# export OLLAMA_MODEL="gemma:4b"
# export OLLAMA_MODEL="llama3:13b"
# export OLLAMA_MODEL_STEP3="llama3:8b"
# export STEP3_SKIP_LLM=true
# export STEP3_LLM_WORKERS=4


# ---------------------------------------------------------
# FAISS Embedding Model
# ---------------------------------------------------------
EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"

# Used in ingest.py and rag.py


# ---------------------------------------------------------
# File Size Limits (Optional)
# ---------------------------------------------------------
MAX_UPLOAD_MB = 100    # Streamlit upload cap
STEP1_INDEX_DIR = DATA_DIR / "step1_index_native"
STEP2_INDEX_DIR =  DATA_DIR / "step2_index_native"