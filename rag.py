import json
import re
from typing import Dict, Any, List
from collections import Counter
import requests
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from config import INDEX_DIR, OLLAMA_BASE_URL, OLLAMA_MODEL, DATA_DIR


def _load_vectorstore(index_folder_name: str) -> FAISS:
    """
    [MODIFIED] Loads a specific FAISS vector store from a named folder.
    """
    folder_path = str(INDEX_DIR / index_folder_name)
    print(f"[RAG] Loading FAISS index from: {folder_path}")
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={"device": "cpu"},
    )
    vectorstore = FAISS.load_local(
        folder_path=folder_path,
        embeddings=embeddings,
        allow_dangerous_deserialization=True,
    )
    return vectorstore

def _call_ollama(prompt: str) -> str:
    """
    Calls the Ollama chat API with a system message to enforce JSON array output.
    """
    # ... (same as before)
    url = f"{OLLAMA_BASE_URL}/api/chat"
    system_msg = """You are a precise data extraction system that ONLY outputs JSON arrays.

CRITICAL RULES:
1. ALWAYS output a JSON array: [ ... ]
2. NEVER output a single object: { ... }
3. Even with one item, output: [{...}]  NOT  {...}
4. Extract ACTUAL data from the document - NEVER copy example placeholders
5. Extract ALL items from tables - NEVER extract just one row when multiple exist
6. Return pure JSON with no markdown, no explanations, no code blocks"""

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.0},
    }

    print(f"[RAG] Calling Ollama: {url} / model={OLLAMA_MODEL}")
    try:
        resp = requests.post(url, json=payload, timeout=120) # 2 min timeout
        resp.raise_for_status()
        data = resp.json()
        text = data.get("message", {}).get("content", "")
        return text.strip()
    except requests.exceptions.ConnectionError:
        print("\n" + "="*50)
        print("ERROR: Could not connect to Ollama.")
        print(f"Please ensure Ollama is running at {OLLAMA_BASE_URL}")
        print("You can run it with: `ollama serve`")
        print("="*50 + "\n")
        return "[]" # Return empty list on error
    except Exception as e:
        print(f"[RAG] ERROR: Failed to call Ollama: {e}")
        return "[]"

def _parse_and_clean_llm_response(raw_text: str) -> List[Dict[str, Any]]:
    """
    [NEW] Robust parser to clean and parse LLM JSON output.
    Fixes invalid escape chars.
    """
    print(f"[RAG] LLM response length: {len(raw_text)} characters")
    print(f"[RAG] LLM response preview (200 chars): {raw_text[:200]}...")

    # Debug: Save full LLM response to file for inspection
    debug_path = DATA_DIR / "llm_debug_response.json"
    try:
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(raw_text)
        print(f"[RAG] Full LLM response saved to: {debug_path}")
    except Exception as e:
        print(f"[RAG] Failed to save debug response: {e}")

    # Check for empty/minimal response
    if len(raw_text) < 10 or raw_text.strip() in ["{}", "[]", ""]:
        print("[RAG] WARNING: LLM returned empty/minimal response!")
        return []

    # --- JSON Parsing Logic ---
    sanitized = raw_text.strip()
    if sanitized.startswith("```json"):
        sanitized = sanitized[7:]
        if sanitized.endswith("```"):
            sanitized = sanitized[:-3]
        sanitized = sanitized.strip()
    
    # [FIX] Clean invalid escape sequences (like \1) before parsing
    sanitized = re.sub(r'\\(\d)', r'\1', sanitized)
    
    data = None
    try:
        data = json.loads(sanitized)
    except json.JSONDecodeError as e:
        print(f"[RAG] WARN: Full parse failed ({e}). Attempting partial parse.")
        try:
            failed_at_char = e.pos
            sanitized_partial = sanitized[:failed_at_char].strip()
            data = json.loads(sanitized_partial)
            print(f"[RAG] Parsed partially (up to char {failed_at_char}).")
        except Exception as e2:
            print(f"[RAG] ERROR: Partial parse also failed: {e2}")
            print(f"--- Raw output from Ollama ---\n{raw_text}\n-------------------")
            print(f"--- Sanitized output ---\n{sanitized}\n-------------------")
            return [] # Return empty list on total failure

    # Type check: ensure data is a list
    if not isinstance(data, list):
        print(f"[RAG] ERROR: Parsed JSON is not a list as requested by prompt.")
        if isinstance(data, dict):
            print("[RAG] WARN: Data was a dict, wrapping in list.")
            data = [data]
        else:
            return []

    print(f"[RAG] Parsed {len(data)} project item(s) from AI.")
    return data


# --- [MODIFIED] Step 1: RUDF Extraction ---

def get_raw_project_data(query: str, top_k: int = 25, index_folder_name: str = "faiss_index") -> List[Dict[str, Any]]:
    """
    [MODIFIED] Performs RAG on a *specific* FAISS index.
    Used for Step 1.
    """
    try:
        vectorstore = _load_vectorstore(index_folder_name)
    except Exception as e:
        print(f"[RAG] ERROR: Failed to load index '{index_folder_name}'. {e}")
        return []

    print(f"[RAG] Searching FAISS (k={top_k}) for query: {query!r}")
    docs = vectorstore.similarity_search(query, k=top_k)

    if not docs:
        print("[RAG] WARNING: No documents found in FAISS index!")
        return []

    print(f"[RAG] Retrieved {len(docs)} document chunks from FAISS")
    
    source_counts = Counter(d.metadata.get('source', 'unknown') for d in docs)
    print(f"[RAG] Chunks by source: {dict(source_counts)}")

    context_text = "\n\n---\n\n".join(
        f"[CHUNK {i+1} from {d.metadata.get('source', 'unknown')}]\n{d.page_content}"
        for i, d in enumerate(docs)
    )

    print(f"[RAG] Total context length: {len(context_text)} characters")

    # --- [MODIFIED] Using the generic "smart" prompt from before ---
    prompt = f"""You are a precise data extraction system.
Your task is to extract all career history from the provided text.

1.  First, find the engineer's name (성명) from the "인적사항" (Personal Info) section on the first few pages.
2.  Second, scan the document for **TWO** tables: "1. 기술경력" (Technical Career) and "2. 건설사업관리 및 감리경력" (CM/Supervision).
3.  Extract **EVERY SINGLE project** from **BOTH** tables.
4.  **CRITICAL:** For each project, find the "참여기간" (participation period). It has two lines.
    - The first line has the `start_date` and `end_date`.
    - The second line has the `(인정일) (참여일)`. You MUST extract the **first** value, the **인정일 (recognition days)**.
5.  Return a JSON array `[...]` containing one object for every project found.

**JSON Structure:**
{{
  "engineer_name": "The engineer's name from Step 1",
  "project_name": "사업명 (Project Name)",
  "client": "발주자 (Client)",
  "start_date": "YYYY-MM-DD (from the first line of the period)",
  "end_date": "YYYY-MM-DD (from the first line of the period)",
  "recognition_days": "The **인정일** (Recognition Days) from the second line (e.g., '194일')",
  "job_field": "직무분야 (Job Field, e.g., '토목')",
  "role": "담당업무 (Role, e.g., '설계')",
  "source_table": "The name of the table it came from (e.g., '1. 기술경력')"
}}

**RULES:**
- IGNORE projects named "본사/감리부" or "본사".
- The `engineer_name` must be the same for all entries.
- If an end date is "근무중" (Working), use "N/A".
- Convert all dates to "YYYY-MM-DD" format.
- Ensure all strings are valid JSON strings and properly escape special characters.
- Extract ALL projects from all relevant tables.

Return ONLY the JSON array.
"""

    raw_text = _call_ollama(prompt)
    data = _parse_and_clean_llm_response(raw_text)
    
    # --- Validation and Filtering ---
    valid_data = []
    for project in data:
        project_name = project.get("project_name", "").strip()
        client = project.get("client", "").strip()

        if not project_name or not client:
            print(f"[RAG] WARN: Skipping invalid project - name: '{project_name}', client: '{client}'")
            continue
        if "본사" in project_name or "감리부" in project_name:
            print(f"[RAG] WARN: Skipping internal department entry: '{project_name}'")
            continue
        valid_data.append(project)

    if len(valid_data) < len(data):
        print(f"[RAG] Filtered {len(data) - len(valid_data)} invalid projects, {len(valid_data)} valid projects remaining")

    return valid_data


# --- [NEW] Step 2: OCR Text Extraction ---

def extract_tech_data_from_ocr(ocr_text: str) -> List[Dict[str, Any]]:
    """
    [NEW] Extracts projects from a raw OCR text chunk.
    This does NOT use FAISS. It passes the full text to the LLM.
    """
    
    # This prompt is highly specific to the Step 2 requirements
    prompt = f"""You are a data extraction expert.
        You will be given the raw OCR text from a single page titled "1. 기술경력".
        Your task is to extract all project rows from this text.

        === OCR TEXT START ===
        {ocr_text}
        === OCR TEXT END ===

        Extract the following fields for EACH project row:
        1.  `start_date`: The start date (e.g., `1981.02.11`)
        2.  `end_date`: The end date (e.g., `1981.05.31`)
        3.  `recognition_days`: The "인정일" (the first set of days in parentheses, e.g., `(110일)`)
        4.  `project_name`: The "사업명" (e.g., "구례교가설공사실시설계")
        5.  `job_field`: The "직무분야" (e.g., "토목")
        6.  `role`: The "담당업무" (e.g., "설계")
        7.  `client`: The "발주자 | 공사종류" (Combine them, e.g., "광주지방국토관리청 일반교량")
        8.  `position`: The "직위" (e.g., "사원")

        **CRITICAL RULES:**
        - IGNORE any rows for "본사/감리부" or "본사".
        - Convert all dates to "YYYY-MM-DD" format.
        - `recognition_days` MUST be the **인정일** (the first value in parentheses).
        - Return a JSON array `[...]`, with one object per project.

        Return ONLY the JSON array.
    """
    
    raw_text = _call_ollama(prompt)
    data = _parse_and_clean_llm_response(raw_text)
    return data