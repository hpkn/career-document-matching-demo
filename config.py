import os
from pathlib import Path



BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
PDF_DIR = DATA_DIR / 'source_pdfs'
INDEX_DIR = DATA_DIR / 'faiss_index'


#Make sure folders exist


PDF_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)


#ANTROPIC API KEY
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if ANTHROPIC_API_KEY is None:
    print("[WARN] ANTHROPIC_API_KEY environment variable not set")
    print("     export ANTHROPIC_API_KEY='your_key_here'")
#Model Con
