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

# Recommended model for Korean structured extraction
# gpt-oss:120b-cloud
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:27b")

# You can override with:
# export OLLAMA_MODEL="gemma:4b"
# export OLLAMA_MODEL="llama3:13b"


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