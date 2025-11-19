from typing import List, Dict, Any
import pandas as pd

def _norm(text) -> str:
    """
    텍스트를 정규화하여 안전한 문자열로 변환
    """
    if text is None:
        return ""
    return str(text).strip()

# --- 1) 발주처 분류 ---
def classify_client_type(client_raw: str) -> str:
    """
    발주처 이름으로부터 발주처 유형을 분류
    """
    if not client_raw:
        return "기타"
    s = client_raw.replace(" ", "") 

    # Expanded keywords to handle all sample files
    if any(k in s for k in ["기초자치단체", "시청", "구청", "군청", "군", "세종특별자치시", "양주시", "평택시", "진천군", "괴산군", "성남시", "진도군", "아산시"]):
        return "기초자치단체"
    if any(k in s for k in ["광역자치단체", "도청", "특별시", "광역시", "경기도", "경기도건설본부", "충청남도", "전라남도", "경상북도", "인천광역시", "울산광역시"]):
        return "광역자치단체"
    if any(k in s for k in ["정부투자기관", "공사", "공단", "한국도로공사", "인천국제공항공사", "한국공항공사", "한국수자원공사", "한국농어촌공사", "한국토지주택공사", "한국환경공단", "한국철도시설공단", "농업기반공사"]):
        return "정부투자기관"
    if any(k in s for k in ["국토교통부", "국토관리청", "국가", "환경부", "제주지방국토관리청", "대전지방국토관리청", "원주지방환경청", "서울지방국토관리청", "부산지방국토관리청", "낙동강유역환경청", "익산지방국토관리청", "행정중심복합도시건설청"]):
        return "국가"
    if any(k in s for k in ["주식회사", "(주)", "㈜", "유한회사", "현대그린개발", "롯데케미칼", "삼성물산(주)", "현대건설(주)", "GS건설(주)"]):
        return "민간"
    return "기타"


# --- 2) [MODIFIED] Logic for RUDF data (Step 1) ---
def infer_logic_fields(project: Dict[str, Any]) -> Dict[str, Any]:
    """
    This function is now ONLY for Step 1 data.
    """
    logic_fields = {}
    primary_field = project.get("primary_original_field", "기타토목")
    
    specialty_map = {
        "도로": "도로및공항", "공항": "도로및공항", "철도": "철도삭도",
        "상수도": "상하수도", "하수도": "상하수도", "항만": "항만및해안",
        "하천": "수자원개발", "토목": "토목시공", "단지조성": "토목시공",
    }
    
    logic_fields["use_date_type"] = "participation"
    logic_fields["tech_eval_method"] = "use_specialty"
    logic_fields["specialty"] = specialty_map.get(primary_field, "토목시공")
    
    return logic_fields

# --- 3) [MODIFIED] Main Normalizer for RUDF data (Step 1) ---
def normalize_project(raw_project: Dict[str, Any]) -> Dict[str, Any]:
    """
    This function is now ONLY for Step 1 data (from RUDF RAG).
    It expects the 'recognition_days' field.
    """
    if not raw_project:
        return {}
    
    p_norm = dict(raw_project) 
    
    # 1. Classify Client
    client_raw = _norm(p_norm.get("client"))
    client_type = classify_client_type(client_raw)
    p_norm["client_raw"] = client_raw
    p_norm["client_type"] = client_type
    p_norm["client"] = f"{client_raw} {client_type}" 

    # 2. Normalize Fields and Roles
    job_field_str = _norm(p_norm.get("job_field"))
    p_norm["primary_original_field"] = job_field_str
    p_norm["original_fields"] = [job_field_str] if job_field_str else []
    p_norm["original_field"] = job_field_str # Fallback

    role_str = _norm(p_norm.get("role"))
    p_norm["primary_role"] = role_str
    roles_list = [role_str] if role_str else []
    if "감독권한대행" in role_str:
         roles_list.append("건설사업관리(상주)")
    elif "시공" in role_str:
         roles_list.append("시공")
    elif "설계" in role_str:
         roles_list.append("설계")
    p_norm["roles"] = list(set(roles_list))
    p_norm["role"] = role_str # Fallback

    # 3. Add Logic Fields
    p_norm["engineer_name"] = _norm(p_norm.get("engineer_name"))
    logic_fields = infer_logic_fields(p_norm)
    p_norm.update(logic_fields) 
    
    # 4. Map recognition_days -> participation_days for the calculation function
    p_norm["participation_days"] = _norm(p_norm.get("recognition_days", ""))
    
    # 5. Handle "N/A" end dates
    if p_norm.get("end_date") == "N/A":
        p_norm["end_date"] = "근무중"

    return p_norm

# --- 4) [NEW] Normalizer for Tech Data (Step 2) ---

def normalize_tech_data_df(tech_df: pd.DataFrame) -> pd.DataFrame:
    """
    [NEW] Normalizes the DataFrame from Step 2 (OCR extraction)
    to match the structure expected by the final report generator.
    """
    if tech_df.empty:
        return pd.DataFrame()
    
    # 1. Create a copy to avoid modifying the session state directly
    df = tech_df.copy()

    # 2. Rename/Map columns to match the 'normalize_project' output
    # 'recognition_days' is the '인정일' from the OCR
    # 'participation_days' is what the report function expects
    df["participation_days"] = df["recognition_days"].apply(_norm)
    
    # 'role' is '담당업무'
    df["role"] = df["role"].apply(_norm)
    
    # 'client' is '발주자 | 공사종류', use it as 'client_raw'
    df["client_raw"] = df["client"].apply(_norm)
    df["client_type"] = df["client_raw"].apply(classify_client_type)
    
    # 'job_field' is '직무분야'
    df["primary_original_field"] = df["job_field"].apply(_norm)
    
    # 'project_name' is '사업명'
    df["project_name"] = df["project_name"].apply(_norm)

    # Add 'engineer_name' from the first row to all rows
    if "engineer_name" in df.columns:
        df["engineer_name"] = df.iloc[0]["engineer_name"]
    else:
        df["engineer_name"] = "(이름 없음)"
        
    # Create the 'roles' list column
    def create_roles_list(role_str):
        roles_list = [role_str] if role_str else []
        if "감독권한대행" in role_str:
            roles_list.append("건설사업관리(상주)")
        elif "시공" in role_str:
            roles_list.append("시공")
        elif "설계" in role_str:
            roles_list.append("설계")
            
        return list(set(roles_list))

    df["roles"] = df["role"].apply(create_roles_list)
    
    print(f"[Normalize] Normalized {len(df)} projects from Step 2 OCR data.")
    
    return df