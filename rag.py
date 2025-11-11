# rag.py
import json
from typing import Dict, Any, List
import re
import requests
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from config import INDEX_DIR, OLLAMA_BASE_URL, OLLAMA_MODEL


def _load_vectorstore() -> FAISS:
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
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
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
        return "{}" # Return empty object on error
    except Exception as e:
        print(f"[RAG] ERROR: Failed to call Ollama: {e}")
        return "{}"


def get_raw_project_data(query: str, top_k: int = 10) -> Dict[str, Any]:
    """
    Synthesizes all data into ONE project object, now supporting
    multiple fields and roles as lists.
    """
    vectorstore = _load_vectorstore()

    print(f"[RAG] Searching FAISS (k={top_k}) for query: {query!r}")
    docs = vectorstore.similarity_search(query, k=top_k)

    if not docs:
        print("[RAG] No documents found.")
        return {}

    context_text = "\n\n---\n\n".join(
        f"[CHUNK {i+1} from {d.metadata.get('source', 'unknown')}]\n{d.page_content}"
        for i, d in enumerate(docs)
    )

    # --- THIS IS YOUR NEW, UPDATED PROMPT ---
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
        - 일부 항목은 **여러 개 선택(복수 선택)** 이 가능하므로, 해당되는 값이 여러 개이면 **배열(list)** 로 모두 포함합니다.

        필드 정의:
        - "project_name": string  
        - 가장 정확한 전체 공사명 (단일 값)
        - "client": string  
        - 발주처 이름 (단일 값이 가장 자연스러우나, 복수라면 대표 발주처를 선택)
        - "start_date": string  
        - 가장 이른 시작일, YYYY-MM-DD 형식 (모르면 ""(빈 문자열))
        - "end_date": string  
        - 가장 늦은 종료일, YYYY-MM-DD 형식 (모르면 ""(빈 문자열))

        - "original_fields": string[]  
        - 해당 프로젝트가 속하는 모든 주요 공종/분야 (예: ["하수도", "상수도", "수자원개발"])
        - "primary_original_field": string  
        - 위 original_fields 중에서 **가장 핵심적인 1개** (예: "하수도")

        - "roles": string[]  
        - 문서에서 확인되는 모든 담당업무 (예: ["건설사업관리(기술지원)", "시공감리"])
        - "primary_role": string  
        - 위 roles 중에서 **가장 주된 담당업무 1개** (예: "건설사업관리(기술지원)")

        작성 규칙:
        - 날짜를 알 수 없으면 ""(빈 문자열)로 둡니다.
        - 공종/담당업무는 문서 내용과 가장 가까운 표현을 사용하되,
        문장형이 아닌 **짧은 라벨 형태**로 작성합니다. (예: "건설사업관리(기술지원)", "하수도")
        - 여러 값이 명확히 보이면 반드시 original_fields, roles에 **모두 포함**하세요.

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
        "original_fields": ["상수도", "하수도", "수자원개발"],
        "primary_original_field": "하수도",
        "roles": ["건설사업관리(기술지원)", "시공감리"],
        "primary_role": "건설사업관리(기술지원)"
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