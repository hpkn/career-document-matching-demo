"""
Document ingestion module for PDF processing and FAISS index building.

This module handles:
- PDF text extraction (native + OCR fallback)
- OCR processing for image-based PDFs
- Document chunking and text splitting
- LLM-based text normalization
- FAISS vector index creation

The hybrid approach ensures reliable text extraction from both
text-based and scanned/image-based PDF documents.
"""
import os
import re
import json
from typing import List, Dict
from pathlib import Path

import streamlit as st

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from config import PDF_DIR, INDEX_DIR, DATA_DIR
from llm_helper import normalize_chunks_with_llm

# Feature flag for LLM normalization
# WARNING: Enabling this will significantly slow down indexing (5-10+ minutes)
# Only enable for heavily distorted OCR text
USE_LLM_NORMALIZE = False  # Changed from True to False for performance

def clear_pdfs() -> int:
    """
    Delete all PDF files in the PDF directory.

    Returns:
        Number of files deleted
    """
    print("[CLEANUP] Deleting old PDFs...")
    deleted_count = 0
    for f in Path(PDF_DIR).glob("*.pdf"):
        try:
            f.unlink()
            deleted_count += 1
        except Exception as e:
            print(f"[CLEANUP] Failed to delete {f}: {e}")
    print(f"[CLEANUP] Deleted {deleted_count} PDFs.")
    return deleted_count


def clear_index() -> int:
    """
    Delete all files in the FAISS index directory.

    Returns:
        Number of files deleted
    """
    print("[CLEANUP] Deleting old FAISS index...")
    deleted_count = 0
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    for f in Path(INDEX_DIR).glob("*.*"):  # Match .faiss, .pkl, etc.
        try:
            f.unlink()
            deleted_count += 1
        except Exception as e:
            print(f"[CLEANUP] Failed to delete {f}: {e}")
    print(f"[CLEANUP] Deleted {deleted_count} index files.")
    return deleted_count


# =========================
# OCR Configuration & Helpers
# =========================

# OCR settings
MIN_TEXT_CHARS = 30       # Minimum chars to consider page as "has text"
OCR_DPI_SCALE = 2.0       # DPI multiplier for OCR (higher = better quality, slower)
TESS_LANG = "kor+eng"     # Tesseract language models to use

def _pixmap_to_pil(pix: fitz.Pixmap) -> Image.Image:
    """
    Convert PyMuPDF Pixmap to PIL Image.

    Args:
        pix: PyMuPDF Pixmap object

    Returns:
        PIL Image object
    """
    if pix.alpha:  # Remove alpha channel if present
        pix = fitz.Pixmap(pix, 0)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img


def _clean_text(text: str) -> str:
    """
    Light cleanup of OCR-extracted text.

    Removes:
    - Form feed characters
    - Excessive whitespace
    - Multiple consecutive newlines

    Args:
        text: Raw OCR text

    Returns:
        Cleaned text
    """
    text = text.replace("\x0c", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def ocr_pdf_to_docs(pdf_path: str, source_name: str) -> List[Document]:
    """
    OCR the entire PDF file.

    Used when:
    - PDF is fully image-based
    - Native text extraction completely fails

    Args:
        pdf_path: Path to PDF file
        source_name: Original filename for metadata

    Returns:
        List of Document objects (one per page with text)
    """
    docs: List[Document] = []
    with fitz.open(pdf_path) as doc:
        total_pages = len(doc)
        print(f"[INGEST] {source_name}: Running OCR on {total_pages} pages...")
        for i, page in enumerate(doc):
            mat = fitz.Matrix(OCR_DPI_SCALE, OCR_DPI_SCALE)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pil = _pixmap_to_pil(pix)
            text = pytesseract.image_to_string(pil, lang=TESS_LANG)
            text = _clean_text(text)
            if text:
                docs.append(Document(
                    page_content=text,
                    metadata={"source": source_name, "page": i + 1, "extraction": "ocr"}
                ))
        print(f"[INGEST] {source_name}: OCR complete, extracted {len(docs)}/{total_pages} pages")
    return docs

def hybrid_load_pdf(pdf_path: str, source_name: str) -> List[Document]:
    """
    Hybrid PDF loading with intelligent OCR fallback.

    Strategy:
    1. Attempt native text extraction with PyPDFLoader
    2. For pages with insufficient text (<MIN_TEXT_CHARS), run OCR
    3. If native extraction completely fails, OCR entire document

    This ensures reliable text extraction from both text-based
    and scanned/image-based PDFs.

    Args:
        pdf_path: Path to PDF file
        source_name: Original filename for metadata

    Returns:
        List of Document objects with extracted text
    """
    # 1) Native extraction
    try:
        loader = PyPDFLoader(pdf_path)
        native_docs = loader.load()  # one Document per page
    except Exception as e:
        print(f"[INGEST] Native extraction failed for {source_name}: {e}")
        native_docs = []

    if not native_docs:
        # Entire file likely image-only: OCR the whole thing
        print(f"[INGEST] {source_name}: No native text found, using full OCR")
        return ocr_pdf_to_docs(pdf_path, source_name)

    # 2) OCR weak pages only
    ocr_replacements: Dict[int, Document] = {}
    ocr_page_count = 0
    native_page_count = 0

    with fitz.open(pdf_path) as pdf:
        for i, d in enumerate(native_docs):
            raw = (d.page_content or "").strip()
            if len(raw) >= MIN_TEXT_CHARS:
                # mark native extraction
                d.metadata.setdefault("source", source_name)
                d.metadata.update({"page": i + 1, "extraction": "native"})
                native_page_count += 1
                continue

            # OCR this page
            page = pdf.load_page(i)
            mat = fitz.Matrix(OCR_DPI_SCALE, OCR_DPI_SCALE)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pil = _pixmap_to_pil(pix)
            text = pytesseract.image_to_string(pil, lang=TESS_LANG)
            text = _clean_text(text)
            if text:
                ocr_replacements[i] = Document(
                    page_content=text,
                    metadata={"source": source_name, "page": i + 1, "extraction": "ocr"}
                )
                ocr_page_count += 1
            else:
                # keep empty native so we preserve structure, but mark it
                d.metadata.setdefault("source", source_name)
                d.metadata.update({"page": i + 1, "extraction": "native-empty"})

    # 3) Merge native + per-page OCR
    merged: List[Document] = []
    for i, d in enumerate(native_docs):
        merged.append(ocr_replacements.get(i, d))

    # Filter truly empty pages
    merged = [d for d in merged if d.page_content and d.page_content.strip()]

    # Log extraction summary
    print(f"[INGEST] {source_name}: {native_page_count} pages native text, {ocr_page_count} pages OCR, {len(merged)} total pages")

    return merged


def load_pdfs_from_folder(folder: str) -> List[Document]:
    docs: List[Document] = []
    pdf_files_found = False

    # Load UUID->Name map (optional)
    name_map_path = DATA_DIR / "uuid_name_map.json"
    name_map: Dict[str, str] = {}
    if name_map_path.exists():
        with open(name_map_path, "r", encoding="utf-8") as f:
            name_map = json.load(f)

    for fname in os.listdir(folder):
        if not fname.lower().endswith(".pdf"):
            continue
        pdf_files_found = True
        path = os.path.join(folder, fname)
        original_name = name_map.get(fname, fname)
        print(f"[INGEST] Loading {fname} (Original: {original_name})")

        try:
            loaded_docs = hybrid_load_pdf(path, original_name)
            if not loaded_docs:
                print(f"[INGEST] {fname}: No text extracted (native+OCR).")
                st.warning(f"{original_name}: 텍스트를 추출하지 못했습니다.")
                continue

            docs.extend(loaded_docs)
        except Exception as e:
            print(f"[INGEST] Error loading {fname}: {e}")
            st.error(f"{original_name} 파일을 읽는 중 오류 발생: {e}")

    if not pdf_files_found:
        print("[INGEST] No PDF files found in data/pdfs/ folder.")
        st.warning("data/pdfs/ 폴더에 PDF 파일이 없습니다. 먼저 파일을 업로드해주세요.")

    return docs


# BULD INDEX 
def build_index():
    # 1) Clear ONLY the old index
    clear_index()

    print(f"[INGEST] Loading PDFs from {PDF_DIR}")
    docs = load_pdfs_from_folder(str(PDF_DIR))
    if not docs:
        print("[INGEST] No documents loaded, skipping index build.")
        return

    # 2) Split documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,  # Increased from 1000 to capture more context (e.g., headers + project data)
        chunk_overlap=300,  # Increased from 200 to ensure overlap captures headers
        separators=["\n\n", "\n", " ", ""],
    )
    split_docs = splitter.split_documents(docs)
    # Remove empty chunks if any
    split_docs = [d for d in split_docs if d.page_content and d.page_content.strip()]
    print(f"[INGEST] Total chunks (pre-LLM): {len(split_docs)}")

    if not split_docs:
        raise ValueError("[INGEST] No text chunks after splitting. Check OCR or loaders.")

    # 3) LLM normalization (optional)
    if USE_LLM_NORMALIZE:
        split_docs = normalize_chunks_with_llm(split_docs)
        print(f"[INGEST] Chunks after LLM normalization: {len(split_docs)}")

    # 4) Embeddings & FAISS
    print(f"[INGEST] Loading embedding model (first time may take 1-2 min to download)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={"device": "cpu"},
    )
    print(f"[INGEST] Embedding model loaded successfully")

    print(f"[INGEST] Creating FAISS index from {len(split_docs)} chunks...")
    vectorstore = FAISS.from_documents(split_docs, embeddings)

    print(f"[INGEST] Saving index to {INDEX_DIR}...")
    vectorstore.save_local(str(INDEX_DIR))
    print(f"[INGEST] ✅ FAISS index saved successfully!")

if __name__ == "__main__":
    try:
        build_index()
        st.sidebar.success("인덱스 생성 완료.")
    except Exception as e:
        st.sidebar.error(f"인덱스 생성 중 오류: {e}")
        raise