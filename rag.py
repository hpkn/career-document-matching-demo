"""
RAG (Retrieval-Augmented Generation) module for project data extraction.

This module:
- Loads FAISS vector index of document embeddings
- Retrieves relevant document chunks via similarity search
- Uses Ollama LLM to extract structured project data from text
- Returns parsed JSON with project information
"""
import json
from typing import Dict, Any, List
import requests
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from config import INDEX_DIR, OLLAMA_BASE_URL, OLLAMA_MODEL, DATA_DIR


def _load_vectorstore() -> FAISS:
# ... 기존 코드 ...
    print(f"[RAG] Loading FAISS index from: {INDEX_DIR}")
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={"device": "cpu"},
    )
    vectorstore = FAISS.load_local(
        folder_path=str(INDEX_DIR),
        embeddings=embeddings,
        allow_dangerous_deserialization=True,
    )
    return vectorstore

def _call_ollama(prompt: str) -> str:
# ... 기존 코드 ...
    url = f"{OLLAMA_BASE_URL}/api/chat"

    # Add system message to enforce JSON array output
    system_msg = "You are a data extraction assistant. You MUST output a valid JSON array starting with [ and ending with ]. NEVER output a single object. ALWAYS output an array of objects, even if there is only one item."

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "format": "json", # Request JSON format
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


def get_raw_project_data(query: str, top_k: int = 25) -> List[Dict[str, Any]]: # [수정] 반환 타입이 List[Dict], top_k 증가
# ... 기존 코드 ...
    """
    Synthesizes all data into a LIST of project objects.
    """
    vectorstore = _load_vectorstore()

    print(f"[RAG] Searching FAISS (k={top_k}) for query: {query!r}")
    docs = vectorstore.similarity_search(query, k=top_k)

    if not docs:
        print("[RAG] WARNING: No documents found in FAISS index!")
        print("[RAG] This means either:")
        print("[RAG]   1. Index is empty (no PDFs were processed)")
        print("[RAG]   2. Embeddings failed to create")
        print("[RAG]   3. Index file is corrupted")
        return []

    print(f"[RAG] Retrieved {len(docs)} document chunks from FAISS")
    print(f"[RAG] First chunk preview (100 chars): {docs[0].page_content[:100]}...")

    # Debug: Show how many chunks from each source
    from collections import Counter
    source_counts = Counter(d.metadata.get('source', 'unknown') for d in docs)
    print(f"[RAG] Chunks by source: {dict(source_counts)}")

    context_text = "\n\n---\n\n".join(
        f"[CHUNK {i+1} from {d.metadata.get('source', 'unknown')}]\n{d.page_content}"
        for i, d in enumerate(docs)
    )

    print(f"[RAG] Total context length: {len(context_text)} characters")

    # Debug: Save context to file for inspection
    context_debug_path = DATA_DIR / "llm_debug_context.txt"
    try:
        with open(context_debug_path, "w", encoding="utf-8") as f:
            f.write(context_text)
        print(f"[RAG] Context saved to: {context_debug_path}")
    except Exception as e:
        print(f"[RAG] Failed to save context: {e}")

    # Debug: Check if engineer name pattern exists in retrieved chunks
    import re
    name_patterns = [r'성명[:\s]*([가-힣]{2,4})', r'이름[:\s]*([가-힣]{2,4})', r'성\s*명[:\s]*([가-힣]{2,4})']
    found_names = []
    for pattern in name_patterns:
        matches = re.findall(pattern, context_text)
        if matches:
            found_names.extend(matches)
    if found_names:
        print(f"[RAG] Found potential engineer names in chunks: {set(found_names)}")
    else:
        print(f"[RAG] WARNING: No engineer name pattern found in retrieved chunks!")
        print(f"[RAG] This may indicate the name is not in the top chunks or uses different format.")
        print(f"[RAG] Suggestion: Check {context_debug_path} to see what text was retrieved")

    # --- [수정] 프롬프트가 단일 객체가 아닌 'JSON 리스트'를 요청하도록 변경 ---
    prompt = f"""You are extracting construction project career data from Korean documents.

        DOCUMENT CHUNKS:
        {context_text}

        TASK: Extract ALL construction projects from the "기술경력" section ONLY into a JSON array.

        CRITICAL SECTION FILTERING:
        - ONLY extract projects from section "1. 기술경력" (Technical Career)
        - IGNORE section "2. 건설사업관리" (Construction Management)
        - IGNORE any sections about "감리", "감독", "건설사업관리"
        - Focus on the table rows under "1. 기술경력"

        STEP 1 - FIND ENGINEER NAME (성명):
        The engineer's name appears in headers with patterns like:
        - "성명: 정환철" or "성영: 정환철" (OCR may misread 성명 as 성영)
        - "이름: 정환철"
        - Look for "성명", "성영", "이름" followed by ":" and a Korean name

        CRITICAL: Korean names are typically 3 characters (e.g., "정환철", "김철수", "이영희")
        - Extract the COMPLETE 3-character name
        - This name is THE SAME for ALL projects

        STEP 2 - FIND ALL PROJECTS FROM "1. 기술경력" SECTION:
        Each project is a separate row in the table under "1. 기술경력".
        Extract these fields for EACH project row:

        Required fields (extract ALL available information):
        - engineer_name: Use the COMPLETE name from STEP 1 (SAME for all projects, usually 3 characters)
        - project_name: Full project/contract name (사업명, 용역명, 공사명) - extract the COMPLETE name
        - client: Ordering organization (발주처, 발주기관, 발주청) - extract the COMPLETE organization name
        - start_date: Start date (YYYY-MM-DD format) - MUST have a value, search carefully
        - end_date: End date (YYYY-MM-DD format) - MUST have a value, search carefully in the same row
        - original_fields: Array of work types (공종, 분야) - can be multiple, extract ALL mentioned
        - primary_original_field: Main work type (주공종) - typically first or most prominent
        - roles: Array of job roles (담당업무, 직책) - can be multiple, extract ALL mentioned
        - primary_role: Main job role (주담당업무) - typically first or most prominent

        CRITICAL FOR DATES:
        - Each project row has BOTH start date AND end date
        - Look for date pairs like "2020.02.20 ~ 2021.03.15" or "2005.03.31 ~ 2005.07.29"
        - Convert ALL dates to YYYY-MM-DD format
        - VALIDATE: Days must be 01-31, months must be 01-12
        - If day is invalid (e.g., "84"), correct it (e.g., use last day of month)

        DATE CONVERSION RULES:
        - "2005.03.31" → "2005-03-31"
        - "05.03.31" → "2005-03-31" (assume 20xx for 00-23, 19xx for 24-99)
        - "2005.04.01" → "2005-04-01"
        - If end date is incomplete or invalid, estimate based on typical project duration
        - NEVER output invalid dates like "2021-12-84" (day 84 doesn't exist!)

        EXAMPLE OUTPUT (for 2 projects):
        [
        {{"engineer_name":"홍길동","project_name":"학성교가설공사","client":"울산시청","start_date":"1995-01-23","end_date":"1997-08-31","original_fields":["도로","교량"],"primary_original_field":"교량","roles":["설계","감리"],"primary_role":"설계"}},
        {{"engineer_name":"홍길동","project_name":"번영로번영교신설공사","client":"울산광역시","start_date":"1998-03-01","end_date":"2000-12-31","original_fields":["교량"],"primary_original_field":"교량","roles":["감리"],"primary_role":"감리"}}
        ]

        CRITICAL OUTPUT RULES:
        1. Output MUST be a JSON ARRAY starting with [ and ending with ]
        2. NEVER output a single object - ALWAYS wrap in array brackets
        3. Extract ALL projects from "1. 기술경력" section (typically 5-15 projects)
        4. Each project MUST have both start_date and end_date in YYYY-MM-DD format
        5. Dates MUST be valid (days 01-31, months must be 01-12)
        6. Use THE SAME engineer_name for all projects
        7. NO markdown, NO explanations, NO extra text
        8. Output ONLY the raw JSON array

        EXAMPLE - Your output MUST look like this:
        [
        {{"engineer_name":"정환철","project_name":"광양항서측인입철일괄임찰공사기본설계","client":"LG건설(주)","start_date":"2005-03-31","end_date":"2005-05-31","original_fields":["토목","설계"],"primary_original_field":"토목","roles":["설계"],"primary_role":"설계"}},
        {{"engineer_name":"정환철","project_name":"군장국가상업탄지후안도로건설공사","client":"삼성물산(주)","start_date":"2005-06-01","end_date":"2005-09-20","original_fields":["토목","설계"],"primary_original_field":"토목","roles":["설계"],"primary_role":"설계"}}
        ]

        Begin extraction from "1. 기술경력" section:
    """

    raw_text = _call_ollama(prompt)

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

    # Check for empty/minimal response indicating model failure
    if len(raw_text) < 10 or raw_text.strip() in ["{}", "[]", ""]:
        print("\n" + "="*70)
        print("WARNING: LLM returned empty/minimal response!")
        print("="*70)
        print(f"Current model: {OLLAMA_MODEL}")
        print("")
        print("This usually means the model is too small for this task.")
        print("The gemma3:4b model may struggle with complex Korean text extraction.")
        print("")
        print("RECOMMENDED SOLUTIONS:")
        print("1. Try a larger model:")
        print("   ollama pull gemma2:9b")
        print("   ollama pull qwen2.5:7b")
        print("   ollama pull llama3.1:8b")
        print("")
        print("2. Then update config.py or set environment variable:")
        print("   export OLLAMA_MODEL=gemma2:9b")
        print("   # or edit config.py: OLLAMA_MODEL = 'gemma2:9b'")
        print("")
        print("3. Restart the Streamlit app")
        print("="*70 + "\n")

    # --- [수정된 파싱 로직] ---
    sanitized = raw_text.strip()

    # 간단한 마크다운 블록 제거
    if sanitized.startswith("```json"):
        sanitized = sanitized[7:]
        if sanitized.endswith("```"):
            sanitized = sanitized[:-3]
        sanitized = sanitized.strip()
    
    data = None
    try:
        # 1. 전체 문자열 파싱 시도
        data = json.loads(sanitized)
    
    except json.JSONDecodeError as e:
        # 2. "Extra data" 오류 발생 시, 오류 지점까지만 잘라서 다시 파싱
        print(f"[RAG] WARN: Full parse failed ({e}). Attempting partial parse.")
        try:
            failed_at_char = e.pos
            sanitized_partial = sanitized[:failed_at_char].strip()
            data = json.loads(sanitized_partial)
            print(f"[RAG] Parsed partially (up to char {failed_at_char}).")
        except Exception as e2:
            # 3. 부분 파싱도 실패하면, 원본 오류를 발생시켜 streamlit에 표시
            print(f"[RAG] ERROR: Partial parse also failed: {e2}")
            print(f"--- Raw output from Ollama ---")
            print(raw_text)
            print(f"--- Sanitized partial attempt ---")
            print(sanitized_partial)
            print(f"---------------------------------")
            raise e # 원본 오류(e)를 다시 발생시킴

    # 4. 파싱 후 타입 체크
    if not isinstance(data, list):
        print(f"[RAG] ERROR: Parsed JSON is not a list as requested by prompt.")
        print(f"--- Raw output from Ollama ---")
        print(raw_text)
        print(f"--- Parsed data ---")
        print(data)
        print(f"---------------------------------")
        
        # AI가 실수로 List[Dict] 대신 Dict를 반환한 경우, 리스트로 감싸줌
        if isinstance(data, dict):
            print("[RAG] WARN: Data was a dict, wrapping in list.")
            data = [data]
        else:
            return [] # 그 외의 경우(예: 문자열, 숫자)는 빈 리스트 반환

    print(f"[RAG] Parsed {len(data)} project item(s) from AI.")

    # Debug: Print detailed extraction summary
    if data and len(data) > 0:
        first_project = data[0].get("project_name", "(no name)")
        engineer_name = data[0].get("engineer_name", "(no name)")
        print(f"[RAG] Engineer name extracted: {engineer_name}")
        print(f"[RAG] First project extracted: {first_project}")

        # Show all project names for verification
        all_projects = [p.get("project_name", "(no name)") for p in data]
        print(f"[RAG] All {len(all_projects)} projects extracted:")
        for i, pname in enumerate(all_projects, 1):
            print(f"[RAG]   {i}. {pname}")

        # Validate and warn about common issues
        issues_found = []
        for i, project in enumerate(data, 1):
            # Check for missing end dates
            if not project.get("end_date") or project.get("end_date", "").strip() == "":
                issues_found.append(f"  Project {i} ({project.get('project_name', 'unknown')}): Missing end_date")

            # Check for truncated engineer names (< 3 chars for Korean names)
            eng_name = project.get("engineer_name", "")
            if eng_name and len(eng_name) < 3 and any('\uac00' <= c <= '\ud7a3' for c in eng_name):
                issues_found.append(f"  Project {i}: Engineer name '{eng_name}' seems truncated (Korean names are usually 3 characters)")

            # Check for empty client
            if not project.get("client") or project.get("client", "").strip() == "":
                issues_found.append(f"  Project {i}: Missing client information")

        if issues_found:
            print(f"[RAG] WARNING: Data quality issues detected:")
            for issue in issues_found:
                print(f"[RAG] {issue}")
            print(f"[RAG] Suggestion: The LLM may need more context. Consider:")
            print(f"[RAG]   - Checking if the PDF has clear table structure")
            print(f"[RAG]   - Increasing top_k to retrieve more chunks")
            print(f"[RAG]   - Verifying OCR quality in terminal logs")
    else:
        print(f"[RAG] WARNING: No projects extracted!")

    return data