# ingest.py
import os
import re
import json
from typing import List, Dict
from pathlib import Path
import shutil
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
from llm_helper import normalize_chunks_with_llm # Note: This is still disabled by flag

# Feature flag for LLM normalization
USE_LLM_NORMALIZE = False

# --- OCR settings (used only in ocr_page now) ---
MIN_TEXT_CHARS = 30       # Minimum chars to consider page as "has text"
OCR_DPI_SCALE = 2.0       # DPI multiplier for OCR (higher = better quality, slower)
TESS_LANG = "kor+eng"     # Tesseract language models to use

# --- Utility Functions (unchanged) ---
def clear_pdfs() -> int:
    # ... (same as before)
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
    # ... (same as before, but we might want to clear specific folders)
    print("[CLEANUP] Deleting ALL FAISS index folders...")
    deleted_count = 0
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    for f in Path(INDEX_DIR).glob("faiss_index_*"): # Clear all run-specific folders
        if f.is_dir():
            try:
                shutil.rmtree(f)
                deleted_count += 1
            except Exception as e:
                print(f"[CLEANUP] Failed to delete {f}: {e}")
    print(f"[CLEANUP] Deleted {deleted_count} index folders.")
    return deleted_count

def _pixmap_to_pil(pix: fitz.Pixmap) -> Image.Image:
    # ... (same as before)
    if pix.alpha:
        pix = fitz.Pixmap(pix, 0)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img

def _clean_text(text: str) -> str:
    # ... (same as before)
    text = text.replace("\x0c", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

# --- [NEW] Step 2: OCR Specific Page Logic ---

def find_tech_page(pdf_path: str) -> int:
    """
    Finds the page number containing the string "1. 기술경력".
    Uses NATIVE text extraction (no OCR).
    """
    print(f"[INGEST] Finding '1. 기술경력' page in {pdf_path}")
    try:
        with fitz.open(pdf_path) as doc:
            for i, page in enumerate(doc):
                text = page.get_text("text")
                if "1. 기술경력" in text:
                    print(f"[INGEST] Found '1. 기술경력' on page {i+1}")
                    return i # Returns 0-based index
    except Exception as e:
        print(f"[INGEST] Error finding page: {e}")

    print(f"[WARN] '1. 기술경력' page not found, falling back to page 1.")
    return 0 # Fallback to first page (0-indexed)

def ocr_page(pdf_path: str, page_num: int) -> str:
    """
    Performs OCR on a single, specific page from a PDF.
    """
    print(f"[INGEST] Performing OCR on page {page_num + 1} of {pdf_path}")
    try:
        with fitz.open(pdf_path) as doc:
            page = doc.load_page(page_num)
            mat = fitz.Matrix(OCR_DPI_SCALE, OCR_DPI_SCALE)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pil = _pixmap_to_pil(pix)
            text = pytesseract.image_to_string(pil, lang=TESS_LANG)
            return _clean_text(text)
    except Exception as e:
        print(f"[INGEST] Error during single-page OCR: {e}")
        return ""

# --- [MODIFIED] Step 1: NO-OCR PDF Loading Logic ---

def ocr_pdf_to_docs(pdf_path: str, source_name: str) -> List[Document]:
    """
    (This function is now only called by hybrid_load_pdf if use_ocr=True)
    """
    # ... (same as before)
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

def hybrid_load_pdf(pdf_path: str, source_name: str, use_ocr: bool = True) -> List[Document]:
    """
    [MODIFIED] Hybrid PDF loading with a flag to disable OCR.
    
    If use_ocr=False, this acts as a simple native text extractor.
    """
    # 1) Native extraction
    try:
        loader = PyPDFLoader(pdf_path)
        native_docs = loader.load()  # one Document per page
    except Exception as e:
        print(f"[INGEST] Native extraction failed for {source_name}: {e}")
        native_docs = []

    if not use_ocr:
        print(f"[INGEST] {source_name}: OCR disabled. Using native text only.")
        for i, d in enumerate(native_docs):
            d.metadata.setdefault("source", source_name)
            d.metadata.update({"page": i + 1, "extraction": "native-no-ocr"})
        return [d for d in native_docs if d.page_content and d.page_content.strip()]

    # --- OCR-enabled logic (same as before) ---
    if not native_docs:
        print(f"[INGEST] {source_name}: No native text found, using full OCR")
        return ocr_pdf_to_docs(pdf_path, source_name)

    ocr_replacements: Dict[int, Document] = {}
    ocr_page_count = 0
    native_page_count = 0

    with fitz.open(pdf_path) as pdf:
        for i, d in enumerate(native_docs):
            raw = (d.page_content or "").strip()
            if len(raw) >= MIN_TEXT_CHARS:
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
                d.metadata.setdefault("source", source_name)
                d.metadata.update({"page": i + 1, "extraction": "native-empty"})

    merged: List[Document] = []
    for i, d in enumerate(native_docs):
        merged.append(ocr_replacements.get(i, d))

    merged = [d for d in merged if d.page_content and d.page_content.strip()]
    print(f"[INGEST] {source_name}: {native_page_count} pages native, {ocr_page_count} pages OCR, {len(merged)} total pages")
    return merged


def load_pdfs_from_folder(folder: str, use_ocr: bool = True) -> List[Document]:
    """
    [MODIFIED] Loads all PDFs from the folder, passing the use_ocr flag.
    """
    docs: List[Document] = []
    pdf_files_found = False

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
            loaded_docs = hybrid_load_pdf(path, original_name, use_ocr=use_ocr)
            if not loaded_docs:
                print(f"[INGEST] {fname}: No text extracted.")
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


# --- [MODIFIED] Main Index Building Function ---

def build_index(file_map: Dict[str, str], index_folder_name: str, use_ocr: bool = True):
    """
    [MODIFIED] Builds a FAISS index from the PDFs in PDF_DIR.
    
    Args:
        file_map: Map of {uuid_name: original_name} (only used for logging).
        index_folder_name: The subfolder within INDEX_DIR to save this index.
        use_ocr: Whether to enable OCR fallback.
    """
    
    # 1. Set and clear the specific index directory
    target_index_dir = INDEX_DIR / index_folder_name
    if target_index_dir.exists():
        shutil.rmtree(target_index_dir)
    target_index_dir.mkdir(parents=True, exist_ok=True)
    print(f"[INGEST] Building index in: {target_index_dir}")

    print(f"[INGEST] Loading PDFs from {PDF_DIR} (OCR: {use_ocr})")
    docs = load_pdfs_from_folder(str(PDF_DIR), use_ocr=use_ocr)
    if not docs:
        print("[INGEST] No documents loaded, skipping index build.")
        return

    # 2. Split documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300,
        separators=["\n\n", "\n", " ", ""],
    )
    split_docs = splitter.split_documents(docs)
    split_docs = [d for d in split_docs if d.page_content and d.page_content.strip()]
    print(f"[INGEST] Total chunks: {len(split_docs)}")

    if not split_docs:
        raise ValueError("[INGEST] No text chunks after splitting. Check loaders.")

    # 3. LLM normalization (if enabled)
    if USE_LLM_NORMALIZE:
        split_docs = normalize_chunks_with_llm(split_docs)

    # 4. Embeddings & FAISS
    print(f"[INGEST] Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={"device": "cpu"},
    )
    print(f"[INGEST] Creating FAISS index from {len(split_docs)} chunks...")
    vectorstore = FAISS.from_documents(split_docs, embeddings)

    print(f"[INGEST] Saving index to {target_index_dir}...")
    vectorstore.save_local(str(target_index_dir))
    print(f"[INGEST] ✅ FAISS index saved successfully!")