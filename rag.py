import json
import re
from typing import Dict, Any, List
from collections import Counter
import requests
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from openai import OpenAI
from config import STEP1_INDEX_DIR, OLLAMA_BASE_URL, OLLAMA_MODEL, STEP2_INDEX_DIR, IS_PRODUCTION, GPU_DEVICE
from datetime import datetime


def _get_embedding_device():
    """Get the appropriate device for embeddings based on environment."""
    if IS_PRODUCTION:
        try:
            import torch
            if torch.cuda.is_available():
                print(f"[RAG] Production mode: Using GPU ({GPU_DEVICE})")
                return GPU_DEVICE
            else:
                print("[RAG] Production mode: CUDA not available, falling back to CPU")
                return "cpu"
        except ImportError:
            print("[RAG] Production mode: PyTorch not installed, using CPU")
            return "cpu"
    else:
        return "cpu"


def warn(msg: str):
    print(f"[WARN] {msg}")

def err(msg: str):
    print(f"[ERROR] {msg}")

def _extract_json_block(text: str) -> str:
    """
    Extract JSON substring from LLM output even when polluted with text.
    """
    try:
        start = text.index("{")
        end = text.rindex("}")
        return text[start:end + 1]
    except Exception:
        warn("[RAG] Could not find valid JSON block. Returning raw text.")
        return text.strip()


def _repair_common_json_errors(text: str) -> str:
    """
    Attempt to fix common broken JSON issues returned by LLM:
    - trailing commas
    - single quotes
    - missing braces
    """
    s = text.strip()

    # Replace single quotes with double
    s = s.replace("'", "\"")

    # Remove trailing commas before ]
    s = re.sub(r",\s*]", "]", s)
    # Remove trailing commas before }
    s = re.sub(r",\s*}", "}", s)

    return s


def _safe_json_parse(text: str) -> Dict[str, Any]:
    """
    Attempts multiple passes to parse JSON.
    """
    try:
        return json.loads(text)
    except Exception:
        pass

    repaired = _repair_common_json_errors(text)
    try:
        return json.loads(repaired)
    except Exception as e:
        err(f"[RAG] JSON parsing failed: {e}")
        return {}
    
def parse_date_strict(date_str):
    """Parses dates from PDF formats."""
    if not date_str: return None
    clean = re.sub(r'[^\d.-]', '', str(date_str))
    for fmt in ('%Y-%m-%d', '%Y.%m.%d', '%y.%m.%d', '%y-%m-%d'):
        try:
            dt = datetime.strptime(clean, fmt)
            if dt.year < 100:
                dt = dt.replace(year=(1900 + dt.year) if dt.year > 50 else (2000 + dt.year))
            return dt
        except: continue
    return None

def validate_row(row):
    """Fixes common extraction errors (e.g. days mismatch)."""
    s_dt = parse_date_strict(row.get('start_date'))
    e_dt = parse_date_strict(row.get('end_date'))
    
    # Get extracted days
    raw_days = str(row.get('recognition_days', '0'))
    match = re.search(r'(\d+)', raw_days.replace(',', ''))
    recog_days = int(match.group(1)) if match else 0
    
    if s_dt and e_dt:
        calc_days = (e_dt - s_dt).days + 1
        
        # Fix: If extracted days are wildly different from calendar days (e.g. > 30 days diff)
        # This fixes the "1997.08.15~1997.08.16 -> 936 days" error.
        if abs(recog_days - calc_days) > 30:
            row['recognition_days'] = str(calc_days)
            row['confidence'] = "0.8 (Auto-Corrected Days)"
        else:
            row['confidence'] = "1.0"
            
    return row

def _get_vectorstore(index_path):
    """Loads the FAISS index from the specific path."""
    print(f"[RAG] Loading FAISS index from: {index_path}") # Debug print
    device = _get_embedding_device()
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={"device": device}
    )
    return FAISS.load_local(str(index_path), embeddings, allow_dangerous_deserialization=True)

def _call_ollama(prompt: str) -> str:
    """Calls Ollama API."""
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "You are a precise JSON extractor."},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.0, "num_ctx": 16000},
    }

    print(f"[RAG] Calling Ollama: {url} / model={OLLAMA_MODEL}")
    try:
        resp = requests.post(url, json=payload, timeout=300)
        if resp.status_code != 200:
            print(f"[RAG] ERROR: Ollama returned status {resp.status_code}: {resp.text[:500]}")
            return "{}"
        try:
            json_resp = resp.json()
        except Exception as parse_err:
            print(f"[RAG] ERROR: Failed to parse Ollama response as JSON: {parse_err}")
            print(f"[RAG] Raw response: {resp.text[:500]}")
            return "{}"
        return json_resp.get("message", {}).get("content", "")
    except Exception as e:
        print(f"[RAG] ERROR: Failed to call Ollama: {e}")
        return "{}"


def _call_ollama_direct(prompt: str) -> str:
    """Direct call to Ollama for Step 2."""
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "You are a data extraction engine for Korean Construction Career Certificates (KHEA). Output ONLY JSON."},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.0, "num_ctx": 8192} 
    }
    try:
        resp = requests.post(url, json=payload, timeout=300)
        return resp.json().get("message", {}).get("content", "")
    except Exception as e:
        print(f"[RAG] Error: {e}")
        return ""

def _get_llm():
    try:
        return OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    except Exception as e:
        err(f"[RAG] Failed to init LLM client: {e}")
        return None
    
    
JSON_PROMPT = """
당신은 건설/토목 경력 PDF 문서를 JSON으로 구조화하는 전문가입니다.

아래는 PDF에서 추출한 텍스트입니다.
이 텍스트에는 여러 개의 프로젝트가 섞여 있을 수 있습니다.

PDF에서 발견되는 모든 프로젝트를 다음 JSON 구조로 출력하세요:

{
  "projects": [
    {
      "project_name": "",
      "client": "",
      "client_raw": "",
      "start_date": "",
      "end_date": "",
      "participation_days": "",
      "role": "",
      "primary_original_field": ""
    }
  ]
}

규칙:
- JSON만 출력. 설명 문구 금지.
- 빈 값이라도 필드를 반드시 포함.
- 날짜는 YYYY-MM-DD 또는 YYYY-MM 형식 유지.
- client_raw는 가능한 원문 그대로 추출.

아래는 원문 텍스트입니다:
---------------------------------
{{TEXT}}
---------------------------------
"""
def extract_clean_json_from_llm(raw_text: str) -> Dict[str, Any]:
    """
    Step 1 LLM caller:
    - Sends raw PDF text → LLM
    - Extracts JSON block
    - Repairs + parses JSON
    """
    client = _get_llm()
    if client is None:
        err("[RAG] No LLM client available.")
        return {"projects": []}

    prompt = JSON_PROMPT.replace("{{TEXT}}", raw_text[:15000])  # prevent overload

    try:
        resp = client.chat.completions.create(
            model="llama3.1:latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
    except Exception as e:
        err(f"[RAG] LLM call failed: {e}")
        return {"projects": []}

    if not resp or not resp.choices:
        warn("[RAG] LLM returned no choices.")
        return {"projects": []}

    content = resp.choices[0].message.content.strip()

    json_block = _extract_json_block(content)
    data = _safe_json_parse(json_block)

    if not isinstance(data, dict):
        warn("[RAG] LLM output is not a dict; wrapping empty.")
        return {"projects": []}

    if "projects" not in data:
        # sometimes model outputs single project object
        if all(k in data for k in ["project_name", "client"]):
            warn("[RAG] LLM returned a single project; converting → list.")
            data = {"projects": [data]}
        else:
            warn("[RAG] LLM output missing 'projects' key. Returning empty.")
            return {"projects": []}

    # Ensure list format
    projects = data.get("projects", [])
    if isinstance(projects, dict):
        warn("[RAG] Projects was dict; wrapping into list.")
        projects = [projects]

    return {"projects": projects}

def get_raw_project_data(query: str, top_k: int = 25) -> List[Dict[str, Any]]:
    """Generic wrapper to maintain compatibility if needed."""
    return get_step2_table() # Default to table extraction logic


def _parse_json_robust(text: str):
    """
    Extracts JSON object or array from text using Regex.
    Fixes issues where LLM adds markdown or conversational filler.
    """
    if not text: return None
    
    # 1. Remove Markdown code blocks
    clean_text = re.sub(r"```json|```", "", text).strip()
    
    # 2. Try to find the outer-most JSON structure ({...})
    # This regex looks for the first '{' and the last '}'
    dict_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
    if dict_match:
        try:
            return json.loads(dict_match.group(0))
        except: pass

    # 3. Fallback: Try parsing the raw cleaned text
    try:
        return json.loads(clean_text)
    except:
        pass
        
    print(f"[RAG] JSON Parsing Failed. Raw text: {text[:100]}...")
    return None
# --- STEP 1 DATA EXTRACTOR ---
def get_step1_data(query: str, top_k: int = 50):
    try:
        vs = _get_vectorstore(STEP1_INDEX_DIR)
        docs = vs.similarity_search(query, k=top_k)
        context = "\n\n".join([d.page_content for d in docs])

        # Improved prompt with specific vocabulary guidance
        prompt = f"""
        당신은 한국 건설/토목 경력 서류를 읽고 **하나의 종합적인 프로젝트 이력**을 만들어내는 도우미입니다.

        아래는 여러 개의 문서에서 뽑은 관련 텍스트입니다.
        이 텍스트들은 **모두 하나의 동일한 프로젝트**에 대한 내용입니다.
        모든 텍스트를 종합하여 이 프로젝트에 대한 **단일 JSON 객체**를 생성해 주세요.

        [컨텍스트 시작]
        {context}
        [컨텍스트 끝]

        요구사항:
        - 각 필드에 대해 가장 정확하고 포괄적인 정보를 찾아서 채워주세요.
        - **복수 선택(List)** 가능: 해당되는 값이 여러 개이면 배열(list)로 모두 포함합니다.
        - 문서에서 명시적으로 언급된 값만 포함하세요. 추측하지 마세요.

        필드 정의:
        - "project_name": string (가장 정확한 공사명)
        - "client": string (대표 발주처)
        - "clients": string[] (문서에 등장하는 모든 발주처 리스트)
        - "start_date": string (YYYY-MM-DD)
        - "end_date": string (YYYY-MM-DD)
        - "original_fields": string[] (공종/분야 리스트 - 아래 허용 값 중에서만 선택)
        - "primary_original_field": string (핵심 공종 1개)
        - "roles": string[] (담당업무 리스트 - 아래 허용 값 중에서만 선택)
        - "primary_role": string (주된 담당업무 1개)
        - "engineer_name": string (기술인 성명)

        **original_fields 허용 값 (공종):**
        도로, 하천, 상수도, 하수도, 철도, 단지, 항만, 군부대시설, 조경, 기타토목, 전력구, 공항, 교량, 터널, 상하수도

        **roles 허용 값 (담당업무):**
        건설사업관리(기술지원), 시공, 감리, 시공감리, 건설사업관리(상주), 건설사업관리, 건설사업관리(설계단계),
        감독, 관리감독, 감독권한대행, 공사감독, 설계감독, 시공총괄, 현장공무, 현장총괄, 현장총괄계획, 계획,
        시험검사, 시험, 검사, 유지관리, 설계, 기본설계, 실시설계, 타당성조사, 기술자문, 안전점검, 정밀안전진단

        규칙:
        - original_fields는 위 허용 값 중에서만 선택하세요. 프로젝트명에 "상수도", "하수도" 등이 포함되면 해당 공종을 선택합니다.
        - roles는 위 허용 값 중에서만 선택하세요. 문서에서 "설계", "감리", "시공" 등의 키워드를 찾아 매칭합니다.
        - 문서에서 찾을 수 없는 경우 빈 배열 []을 사용하세요.

        출력 형식(중요):
        - 반드시 JSON 객체({{ ... }}) 하나만 출력합니다.
        """
        
        raw_text = _call_ollama(prompt)

        if not raw_text or raw_text == "{}":
            print("[RAG] Step 1: Empty response from Ollama")
            return {}

        print(f"[RAG] Step 1: Got {len(raw_text)} chars from Ollama")

        sanitized = re.sub(r"```json|```", "", raw_text).strip()

        # Find JSON
        match = re.search(r'\{.*\}', sanitized, re.DOTALL)
        if match:
            sanitized = match.group(0)
        else:
            print(f"[RAG] Step 1: No JSON object found in response: {sanitized[:200]}")
            return {}

        data = json.loads(sanitized)
        if isinstance(data, dict): return data
        if isinstance(data, list) and data: return data[0]
        return {}
        
    except Exception as e:
        print(f"[RAG] Step 1 Error: {e}")
        return {}

# --- STEP 2 DATA EXTRACTOR ---
def get_step2_table():
    """Extracts the full project table for Step 2."""
    try:
        vs = _get_vectorstore(STEP2_INDEX_DIR)
        # Reduced k slightly to 40 to prevent context overflow/empty response
        docs = vs.similarity_search("참여기간 사업명 직무분야 담당업무 발주자 공사종류 직위 인정일 참여일", k=40)
        context = "\n".join([d.page_content for d in docs])

        if not context.strip():
            print("[RAG] Warning: No context found in index.")
            return []

        prompt = f"""You are a data extraction engine.
        
        TASK: Extract ALL rows from the '1. 기술경력' or '2. 건설사업관리' table in the context.
        
        Extract these exact fields:
        1. engineer_name (Name from header)
        2. start_date (YYYY-MM-DD from period)
        3. end_date (YYYY-MM-DD from period)
        4. recognition_days (일정일: The FIRST number in parentheses e.g., '(365일)' -> 365)
        5. participation_days (참여일수: The SECOND number in parentheses e.g., '(1000일)' -> 1000. If only one, use that)
        6. project_name (사업명)
        7. job_field (직무분야)
        8. role (담당업무)
        9. client (발주자)
        10. construction_type (공사종류)
        11. rank (직위)
        12. confidence (A number 0.0 to 1.0 indicating confidence)

        CRITICAL RULES:
        - Use the engineer name found in the text (e.g. 김수걸, 최연식).
        - Ignore rows with '본사' or '대기'.
        - Output must be valid JSON.
        
        Return a JSON ARRAY of objects: [ {{...}}, {{...}} ]
        
        Context: 
        {context}
        """
        
        res = _call_ollama(prompt)
        
        # --- Robust Cleaning & Parsing ---
        # 1. Remove markdown code blocks
        res = re.sub(r"```json|```", "", res).strip()
        
        # 2. Remove invalid escapes (common source of crashes)
        res = re.sub(r'\\', '', res)
        
        # 3. Check if empty
        if not res:
            print("[RAG] Error: LLM returned empty response.")
            return []

        # 4. Try Parsing
        try:
            data = json.loads(res)
        except json.JSONDecodeError as e:
            print(f"[RAG] JSON Parse Error: {e}")
            print(f"[RAG] Raw Output causing error: {res[:500]}...") # Log first 500 chars
            return []

        # 5. Structure Validation
        if isinstance(data, dict):
            # Handle case where LLM wraps list in a key like {"projects": [...]}
            for k in data: 
                if isinstance(data[k], list): return data[k]
            return []
            
        return data if isinstance(data, list) else []
        
    except Exception as e:
        print(f"[RAG] General Error in Step 2: {e}")
        return []
    
# With OCR
# --- Step 2: Page-by-Page Processing ---
def process_step2_text(pages_text: list):
    if not pages_text: return []

    print(f"[Step 2] Processing {len(pages_text)} pages...")
    all_extracted_rows = []

    for idx, page_content in enumerate(pages_text):
        if len(page_content) < 50: continue

        prompt = f"""
        Analyze this SINGLE PAGE of a Korean Career Certificate.
        Extract rows from the '기술경력' or '건설사업관리' table.

        PAGE TEXT:
        {page_content}
        
        EXTRACTION RULES:
        1. **Anchor:** Every valid row MUST have a date range (e.g. "2010.05.01 ~ 2012.02.28").
        2. **Project Name:** Extract the full project name (e.g. "학성교가설 및 접속도로 개설공사").
        3. **Client:** Extract the Client Name (e.g. "울산시청").
        4. **Days:** Extract 'recognition_days' from the first number in brackets e.g. (936일).

        OUTPUT FORMAT (JSON List):
        [
            {{
                "start_date": "YYYY-MM-DD",
                "end_date": "YYYY-MM-DD",
                "recognition_days": "936",
                "project_name": "Name",
                "client": "Client",
                "construction_type": "Type",
                "job_field": "Field",
                "role": "Role",
                "rank": "Rank"
            }}
        ]
        
        Return ONLY JSON.
        """
        
        response = _call_ollama_direct(prompt)
        
        try:
            clean = re.sub(r"```json|```", "", response).strip()
            clean = re.sub(r'\\(\d)', r'\1', clean)
            
            page_data = json.loads(clean)
            
            if isinstance(page_data, dict):
                for k in page_data:
                    if isinstance(page_data[k], list): 
                        page_data = page_data[k]; break
            
            if isinstance(page_data, list):
                for row in page_data:
                    # Filter empty rows
                    if not row.get('project_name'): continue
                    if not re.search(r'\d', str(row.get('start_date', ''))): continue
                    
                    # Apply Validation Fix
                    row = validate_row(row)
                    all_extracted_rows.append(row)
                
        except Exception as e:
            print(f"    [Warn] Failed page {idx+1}: {e}")
            continue

    # Deduplicate
    unique_rows = {}
    for row in all_extracted_rows:
        key = f"{row.get('start_date')}_{row.get('project_name')}"
        if key not in unique_rows:
            unique_rows[key] = row
        else:
            if len(str(row)) > len(str(unique_rows[key])):
                unique_rows[key] = row
                
    final_list = list(unique_rows.values())
    
    try:
        final_list.sort(key=lambda x: x.get('start_date', '0000'), reverse=True)
    except: pass

    return final_list


def _load_vectorstore(INDEX) -> FAISS:
    print(f"[RAG] Loading FAISS index from: {INDEX}")
    device = _get_embedding_device()
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={"device": device},
    )
    vectorstore = FAISS.load_local(
        folder_path=str(INDEX),
        embeddings=embeddings,
        allow_dangerous_deserialization=True,
    )
    return vectorstore

def get_raw_project_data(query: str, top_k: int = 10) -> Dict[str, Any]:
    """
    Synthesizes all data into ONE project object, now supporting
    multiple fields and roles as lists.
    """
    vectorstore = _load_vectorstore(STEP1_INDEX_DIR)

    print(f"[RAG] Searching FAISS (k={top_k}) for query: {query!r}")
    docs = vectorstore.similarity_search(query, k=top_k)

    if not docs:
        print("[RAG] No documents found.")
        return {}

    context_text = "\n\n---\n\n".join(
        f"[CHUNK {i+1} from {d.metadata.get('source', 'unknown')}]\n{d.page_content}"
        for i, d in enumerate(docs)
    )

    # --- Improved prompt with strict vocabulary ---
    prompt = f"""
        당신은 한국 건설/토목 경력 서류를 읽고 **하나의 종합적인 프로젝트 이력**을 만들어내는 도우미입니다.

        아래는 여러 개의 문서에서 뽑은 관련 텍스트입니다.
        이 텍스트들은 **모두 하나의 동일한 프로젝트**에 대한 내용입니다.
        모든 텍스트를 종합하여 이 프로젝트에 대한 **단일 JSON 객체**를 생성해 주세요.

        [컨텍스트 시작]
        {context_text}
        [컨텍스트 끝]

        요구사항:
        - 모든 컨텍스트를 종합하여 **단 하나의 JSON 객체**를 출력합니다.
        - 각 필드에 대해 가장 정확하고 포괄적인 정보를 찾아서 채워주세요.
        - 문서에서 명시적으로 언급된 값만 포함하세요. 추측하지 마세요.

        필드 정의:
        - "project_name": string (가장 정확한 전체 공사명)
        - "client": string (대표 발주처)
        - "start_date": string (YYYY-MM-DD 형식, 모르면 "")
        - "end_date": string (YYYY-MM-DD 형식, 모르면 "")
        - "original_fields": string[] (공종/분야 리스트 - 아래 허용 값 중에서만 선택)
        - "primary_original_field": string (핵심 공종 1개)
        - "roles": string[] (담당업무 리스트 - 아래 허용 값 중에서만 선택)
        - "primary_role": string (주된 담당업무 1개)

        **original_fields 허용 값 (공종):**
        도로, 하천, 상수도, 하수도, 철도, 단지, 항만, 군부대시설, 조경, 기타토목, 전력구, 공항, 교량, 터널, 상하수도

        **roles 허용 값 (담당업무):**
        건설사업관리(기술지원), 시공, 감리, 시공감리, 건설사업관리(상주), 건설사업관리, 건설사업관리(설계단계),
        감독, 관리감독, 감독권한대행, 공사감독, 설계감독, 시공총괄, 현장공무, 현장총괄, 현장총괄계획, 계획,
        시험검사, 시험, 검사, 유지관리, 설계, 기본설계, 실시설계, 타당성조사, 기술자문, 안전점검, 정밀안전진단

        규칙:
        - original_fields는 위 허용 값 중에서만 선택하세요. 프로젝트명에 "상수도", "하수도" 등이 포함되면 해당 공종을 선택합니다.
        - roles는 위 허용 값 중에서만 선택하세요. 문서에서 "설계", "감리", "시공" 등의 키워드를 찾아 매칭합니다.
        - 문서에서 찾을 수 없는 경우 빈 배열 []을 사용하세요.

        출력 형식(중요):
        - 반드시 JSON 객체({{ ... }}) 하나만 출력합니다.
        - 배열(List) 전체가 아니라, **최상위에 단일 객체**입니다.
        - 마크다운(````json` 등) 금지, 설명 문장 금지.

        예시 형식:

        {{
        "project_name": "OO 노후상수관망 정비사업 통합건설사업관리용역",
        "client": "화순군",
        "start_date": "2023-01-01",
        "end_date": "2025-12-31",
        "original_fields": ["상수도", "하수도"],
        "primary_original_field": "상수도",
        "roles": ["설계", "감리"],
        "primary_role": "설계"
        }}
        """

    raw_text = _call_ollama(prompt)

    # Clean up the response from the LLM
    sanitized = raw_text.strip()
    
    # Look for single braces
    first_brace = sanitized.find("{")
    last_brace = sanitized.rfind("}")
    
    if first_brace == -1 or last_brace == -1 or last_brace < first_brace:
        print(f"[RAG] ERROR: No valid JSON object found in LLM response.")
        print(f"Raw output:\n{raw_text}")
        return {} # Return empty dict

    sanitized = sanitized[first_brace:last_brace + 1]
    
    try:
        data = json.loads(sanitized)
        if not isinstance(data, dict):
            raise ValueError("Parsed JSON is not a dictionary")
        
    except Exception as e:
        print(f"[RAG] ERROR: Failed to parse JSON object from Ollama.")
        print(f"Raw output:\n{raw_text}")
        print(f"Sanitized output:\n{sanitized}")
        raise e

    print(f"[RAG] Parsed 1 project item from AI.")
    return data