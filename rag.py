# rag.py
import json
from typing import List, Dict, Any

import requests
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from config import INDEX_DIR, OLLAMA_BASE_URL, OLLAMA_MODEL


def _load_vectorstore() -> FAISS:
    """
    Load the FAISS index created by ingest.py.
    """
    print(f"[RAG] Loading FAISS index from: {INDEX_DIR}")
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={"device": "cpu"},
    )
    vectorstore = FAISS.load_local(
        folder_path=str(INDEX_DIR),
        embeddings=embeddings,
        allow_dangerous_deserialization=True,  # OK for local demo
    )
    return vectorstore


def _call_ollama(prompt: str) -> str:
    """
    Call a local Ollama model via HTTP and return the text response.
    """
    url = f"{OLLAMA_BASE_URL}/api/chat"

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {
            "temperature": 0.0  # make it as deterministic as possible
        },
    }

    print(f"[RAG] Calling Ollama at {url} with model '{OLLAMA_MODEL}'...")
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()

    text = data.get("message", {}).get("content", "")
    return text.strip()


def get_raw_facts(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Main RAG function:
        1. Search FAISS index with the query.
        2. Take top_k chunks as context.
        3. Ask Ollama to extract project history as structured JSON.

    Returns: List of project dicts.
    """
    vectorstore = _load_vectorstore()

    print(f"[RAG] Searching for top {top_k} chunks for query: {query!r}")
    docs = vectorstore.similarity_search(query, k=top_k)

    if not docs:
        print("[RAG] No documents found in vector store for this query.")
        return []

    context_text = "\n\n---\n\n".join(
        f"[CHUNK {i+1}]\n{d.page_content}"
        for i, d in enumerate(docs)
    )

    # 💡 IMPORTANT:
    # We request all fields that your CHECKBOX_RULES might use:
    # - project_name, client, role, original_field, start/end dates
    # - participation_date / recognition_date / use_date_type
    # - recognition_rate_rule, specialty, duty_field1/2, tech_eval_method, etc.
    prompt = f"""
        당신은 한국 건설/토목 경력 서류를 읽고 **정형화된 프로젝트 이력**을 뽑아주는 도우미입니다.

        아래는 여러 개의 문서에서 뽑은 관련 텍스트입니다.  
        이 텍스트만을 근거로 프로젝트 경력 정보를 JSON 배열로 정리해 주세요.

        [컨텍스트 시작]
        {context_text}
        [컨텍스트 끝]

        요구사항:
        - 위 컨텍스트에 등장하는 프로젝트/공사 경력을 찾아서 JSON 배열로 출력합니다.
        - 각 프로젝트 항목은 아래 필드를 포함해야 합니다. (모를 경우 null 허용)

        필드 정의:
        - "project_name": string 또는 null
            - 사업명 / 공사명
        - "client": string 또는 null
            - 발주처 (국가, 지방자치단체, OO시청, 민간회사 등)
        - "start_date": string 또는 null
            - 참여 시작일
        - "end_date": string 또는 null
            - 참여 종료일
        - "original_field": string 또는 null
            - 원래 공종/분야 (예: "도로", "하천", "상수도", "하수도", "철도", "단지", "항만", "군부대시설", "조경", "기타토목", "전력구", "공항" 등)
        - "role": string 또는 null
            - 담당업무 (예: "시공", "감리", "건설사업관리(상주)", "건설사업관리(기술지원)", "설계", "유지관리" 등)
        - "participation_date": string 또는 null
            - 참여일 (필요하면 start_date와 동일하게 둘 수 있음)
        - "recognition_date": string 또는 null
            - 인정일 (필요하면 end_date와 동일하게 둘 수 있음)
        - "use_date_type": string 또는 null
            - 경력 평가 시 사용할 기준.
            - "participation" 또는 "recognition" 중 하나를 추천하거나, 판단이 어려우면 null.
        - "recognition_rate_rule": string 또는 null
            - 경력 인정 비율 판단에 필요한 힌트. 예:
                - "civil_60" (토목분야(체크공종제외)60%)
                - "track_60", "track_40"
                - "civil_etc_60" 등
            컨텍스트에서 비율 관련 단서가 없으면 null.
        - "specialty": string 또는 null
            - 기술지원 해당분야에서 사용할 전문분야 (예: "도로및공항", "토목구조", "토질지질", "건설안전", "조경계획", "항만및해안", ...)
        - "tech_eval_method": string 또는 null
            - 기술지원 평가 방법.
            - 예: "same_as_sangju" (상주 평가 방식과 동일), "use_specialty" (참여분야의 전문분야 작성) 등.
        - "duty_field1": string 또는 null
            - 상주 직무분야1 평가에 사용할 직무분야 (예: "토목", "건축", "기계", "안전관리" 등)
        - "duty_field1_eval_method": string 또는 null
            - 직무분야1 평가 방법. 예:
                - "by_duty" (직무분야로 평가)
                - "same_as_sangju" (상주 해당분야 평가 방식과 동일)
        - "duty_field1_recognition_rule": string 또는 null
            - 직무분야1 경력 인정 기준. 예:
                - "include_blank_field"
                - "include_blank_duty"
                - "only_filled"
        - "duty_field2": string 또는 null
            - 상주 직무분야2 평가에 사용할 직무분야 (예: "토목", "건축", "기계", "조경", "안전관리" 등)
        - "duty_field2_eval_method": string 또는 null
        - "duty_field2_recognition_rule": string 또는 null
        - "raw_text": string
            - 해당 프로젝트 경력을 설명하는 원문 텍스트 요약 (출처 문장을 그대로 쓰거나 요약 가능)

        출력 형식(매우 중요):
        - 반드시 **JSON 배열**만 출력하세요.
        - 마크다운(````json`, ````, `###` 등) 절대 금지.
        - 자연어 설명 문장 금지.
        - "..."(생략 기호) 사용 금지. 모르는 값은 null로 두세요.
        - 최대 10개 항목까지만 출력.

        예시 형식 (예시는 설명용이며, 실제 값은 컨텍스트 기반으로 채우세요):

        [
        {{
            "project_name": "OO 도로 확포장 공사",
            "client": "서울특별시 OO구청",
            "start_date": "2019-01-01",
            "end_date": "2020-06-30",
            "original_field": "도로",
            "role": "시공",
            "participation_date": "2019-01-01",
            "recognition_date": "2020-06-30",
            "use_date_type": "participation",
            "recognition_rate_rule": "civil_60",
            "specialty": null,
            "tech_eval_method": null,
            "duty_field1": "토목",
            "duty_field1_eval_method": "by_duty",
            "duty_field1_recognition_rule": "only_filled",
            "duty_field2": null,
            "duty_field2_eval_method": null,
            "duty_field2_recognition_rule": null,
            "raw_text": "서울특별시 OO구청 발주 도로 확포장 공사에 시공 기술자로 참여..."
        }}
        ]

        위 예시는 형식만 참고하세요. 실제 결과는 컨텍스트에 기반하여 작성해야 합니다.
    """

    raw_text = _call_ollama(prompt)

    # Some models still try to add explanation or extra text.
    # We try to isolate the JSON array by looking for the first "[" and last "]".
    sanitized = raw_text.strip()
    first_bracket = sanitized.find("[")
    last_bracket = sanitized.rfind("]")

    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        sanitized = sanitized[first_bracket : last_bracket + 1]

    # Just in case the model still put "..." somewhere, replace them with null
    sanitized = sanitized.replace("...", "null")

    try:
        data = json.loads(sanitized)
        # If it's a single dict instead of a list, wrap it
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            raise ValueError("Parsed JSON is not a list.")
        # Filter out any None items
        data = [item for item in data if item is not None]
    except Exception as e:
        print("[RAG] Failed to parse JSON from Ollama. Raw output:")
        print(raw_text)
        print("[RAG] Sanitized attempt:")
        print(sanitized)
        raise e

    print(f"[RAG] Parsed {len(data)} project items from Ollama.")
    return data
