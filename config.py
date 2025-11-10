# config.py
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

RAW_UPLOAD_DIR = DATA_DIR / "uploads_raw"   # HWP/PDF as uploaded
PDF_DIR = DATA_DIR / "source_pdfs"          # PDFs used for ingestion
INDEX_DIR = DATA_DIR / "faiss_index"        # FAISS index

# Ensure directories exist
RAW_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

# Anthropic API Key
# ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
# if ANTHROPIC_API_KEY is None:
#     print("[WARN] ANTHROPIC_API_KEY is not set. Set it with:")
#     print("       export ANTHROPIC_API_KEY='your-key-here'")
    
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if OPENAI_API_KEY is None:
#     print("[WARN] OPENAI_API_KEY is not set. Set it with:")
#     print("       export OPENAI_API_KEY='your-key-here'")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")

