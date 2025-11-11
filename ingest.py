# ingest.py
import os
import json
from typing import List
from pathlib import Path
import streamlit as st 

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from config import PDF_DIR, INDEX_DIR, DATA_DIR # DATA_DIR 추가

def clear_pdfs():
    """Deletes all files in the PDF directory."""
    print("[CLEANUP] Deleting old PDFs...")
    deleted_count = 0
    for f in Path(PDF_DIR).glob("*.pdf"):
        try:
            f.unlink()
            deleted_count += 1
        except Exception as e:
            print(f"Failed to delete {f}: {e}")
    print(f"Deleted {deleted_count} PDFs.")

def clear_index():
    """Deletes all files in the FAISS index directory."""
    print("[CLEANUP] Deleting old FAISS index...")
    deleted_count = 0
    for f in Path(INDEX_DIR).glob("*.*"): # Match .faiss and .pkl
        try:
            f.unlink()
            deleted_count += 1
        except Exception as e:
            print(f"Failed to delete {f}: {e}")
    print(f"Deleted {deleted_count} index files.")


def load_pdfs_from_folder(folder: str) -> List:
    docs = []
    pdf_files_found = False
    
    # --- FIX: Load the UUID-to-Name map ---
    name_map_path = DATA_DIR / "uuid_name_map.json"
    name_map = {}
    if name_map_path.exists():
        with open(name_map_path, "r", encoding="utf-8") as f:
            name_map = json.load(f)
    
    for fname in os.listdir(folder):
        if not fname.lower().endswith(".pdf"):
            continue
        pdf_files_found = True
        path = os.path.join(folder, fname)
        print(f"[INGEST] Loading {fname} (Original: {name_map.get(fname, 'Unknown')})")
        loader = PyPDFLoader(path)
        try:
            loaded_docs = loader.load()
            
            # --- FIX: Overwrite the 'source' metadata with the original name ---
            original_name = name_map.get(fname, fname)
            for doc in loaded_docs:
                doc.metadata["source"] = original_name
                
            docs.extend(loaded_docs)
        except Exception as e:
            print(f"Error loading {fname}: {e}")
            st.error(f"{fname} 파일을 읽는 중 오류 발생: {e}")
            
    if not pdf_files_found:
        print("[INGEST] No PDF files found in data/pdfs/ folder.")
        st.warning("data/pdfs/ 폴더에 PDF 파일이 없습니다. 먼저 파일을 업로드해주세요.")
        
    return docs


def build_index():
    # 1. Clear ONLY the old index
    clear_index()
    
    print(f"[INGEST] Loading PDFs from {PDF_DIR}")
    docs = load_pdfs_from_folder(str(PDF_DIR))

    if not docs:
        print("[INGEST] No documents loaded, skipping index build.")
        return # Stop if no documents were loaded

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],
    )
    split_docs = splitter.split_documents(docs)
    print(f"[INGEST] Total chunks: {len(split_docs)}")

    embeddings = HuggingFaceEmbeddings( 
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={"device": "cpu"},
    )

    vectorstore = FAISS.from_documents(split_docs, embeddings)
    vectorstore.save_local(str(INDEX_DIR))
    print(f"[INGEST] Saved FAISS index to {INDEX_DIR}")


if __name__ == "__main__":
    build_index()