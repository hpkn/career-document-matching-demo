"""
LLM helper module for text normalization using Ollama.

Provides functions to clean and normalize OCR-extracted text
using local LLM models via Ollama API.
"""
import hashlib
import requests
from typing import List
from langchain_core.documents import Document

from config import OLLAMA_BASE_URL, OLLAMA_MODEL

# Feature flag: Enable/disable LLM normalization
# WARNING: Enabling this will significantly slow down indexing
USE_LLM_NORMALIZE = False  # Disabled by default for performance 


# LLM_CACHE_PATH = DATA_DIR / "llm"

def ollama_generate(prompt: str, timeout: int = 60) -> str:
    """
    Calls Ollama /api/generate endpoint.

    Args:
        prompt: The text prompt to send to the model
        timeout: Request timeout in seconds (default: 60)

    Returns:
        Generated text response from the model

    Raises:
        requests.exceptions.RequestException: If the request fails
    """
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=timeout
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
    except requests.exceptions.Timeout:
        print(f"[LLM] Request timeout after {timeout}s")
        raise
    except requests.exceptions.ConnectionError:
        print(f"[LLM] Cannot connect to Ollama at {OLLAMA_BASE_URL}")
        print("[LLM] Ensure Ollama is running: ollama serve")
        raise
    except Exception as e:
        print(f"[LLM] Unexpected error: {e}")
        raise

def _hash_text(text: str) -> str:
    """Generate SHA256 hash for text (used for caching)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_text_via_llm(text: str) -> str:
    """
    Normalize OCR text using LLM to fix common OCR errors.

    Fixes:
    - Broken line breaks and hyphenation
    - Extra whitespace
    - Header/footer artifacts
    - OCR noise

    Args:
        text: Raw OCR-extracted text

    Returns:
        Normalized text (or original if normalization fails)
    """
    
    if not text or not text.strip():
        return text
    
    key = _hash_text(text) 
    
    prompt = f""""You are a text normalizer for OCR outputs.
    - Fix broken spacing and line-break hyphenations (e.g., "de-\nfault" -> "default").
    - Remove page headers/footers/artifacts if obviously repeated noise.
    - Keep the original meaning; DO NOT summarize or omit real content.
    - Return PLAIN TEXT only (no markdown, no explanations).

    Input OCR text:
    \"\"\"{text}\"\"\""""

    try:
        normalized = ollama_generate(prompt)
        # very light cleanup
        normalized = normalized.replace("\u000c", " ").strip()
    except Exception as e:
        # Fallback: if Ollama fails, return original text
        print(f"[LLM] Normalize failed: {e}")
        normalized = text

    # cache[key] = normalized
    # _save_llm_cache(cache)
    return normalized


def normalize_chunks_with_llm(split_docs: List[Document]) -> List[Document]:
    """
    Normalize a list of document chunks using LLM.

    Small chunks (<120 chars) are skipped to save processing time.
    Normalized chunks are marked with llm_normalized=True in metadata.

    Args:
        split_docs: List of document chunks

    Returns:
        List of normalized document chunks
    """
    if not USE_LLM_NORMALIZE:
        print("[LLM] LLM normalization is disabled (USE_LLM_NORMALIZE=False)")
        return split_docs

    print(f"[LLM] Normalizing {len(split_docs)} document chunks...")
    normalized_docs: List[Document] = []

    for i, d in enumerate(split_docs):
        txt = d.page_content or ""
        # Skip tiny chunks (often headings or short fragments)
        if len(txt) < 120:
            normalized_docs.append(d)
            continue

        try:
            cleaned = normalize_text_via_llm(txt)
            if cleaned and cleaned != txt:
                # Keep original metadata + mark as normalized
                md = {**(d.metadata or {}), "llm_normalized": True}
                normalized_docs.append(Document(page_content=cleaned, metadata=md))
            else:
                normalized_docs.append(d)
        except Exception as e:
            # On error, keep original document
            print(f"[LLM] Failed to normalize chunk {i+1}: {e}")
            normalized_docs.append(d)

    print(f"[LLM] Normalization complete")
    return normalized_docs