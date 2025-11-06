from pathlib import Path
from typing import List


from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings



from config import PDF_DIR, INDEX_DIR


def load_pdfs(pdf_dir: Path) -> List[str]:
    """Load all PDFs from the PDF_DIR and return their file paths."""
    
    docs = []
    for pdf_path in pdf_dir.glob("*.pdf"):
        print(f"[INGEST] Loading {pdf_path.name}")
        loader = PyPDFLoader(str(pdf_path))
        docs.extend(loader.load())
    return docs



def build_and_save_index():
    print(f"[INGEST] Loading PDFs from {PDF_DIR}")
    docs = load_pdfs(PDF_DIR)
    
    if not docs:
        print("[INGEST] No PDF documents found. Exiting.")
        return
    
    print(f"[INGEST] {len(docs)} documents loaded")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
    )
    
    split_docs = text_splitter.split_documents(docs)
    print(f"[INGEST] Split into {len(split_docs)} chunks")
    print("[INGEST] Creating embeddings and building FAISS index")
    
    
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={"device": "cpu"},
    )
    
    print("[INGEST] Splitting documents into chunks")
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    
    print(f"[INGEST] Saving FAISS index to {INDEX_DIR}")
    vectorstore.save_local(str(INDEX_DIR))
    
if __name__ == "__main__":
    build_and_save_index()
    
    