"""
Configuration module for career recognition automation system.

Defines directory paths, model settings, and ensures required directories exist.
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Data subdirectories
RAW_UPLOAD_DIR = DATA_DIR / "uploads_raw"  # Original uploaded files (HWP/PDF)
PDF_DIR = DATA_DIR / "pdfs"                # PDF files for ingestion
INDEX_DIR = DATA_DIR / "faiss_index"       # FAISS vector index storage

# Ensure directories exist
RAW_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

# LLM Configuration - Using Ollama (local model)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# IMPORTANT: gemma3:4b is too small for Korean text extraction
# Use a larger model for accurate results:
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")  # Recommended for Korean
# Alternative models: "gemma2:9b", "llama3.1:8b"

# Note: Cloud API keys (Anthropic, OpenAI) are commented out
# Uncomment and set environment variables if switching to cloud models
# ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


