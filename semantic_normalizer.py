from typing import List, Dict, Any
import pandas as pd
from datetime import datetime
import re 

def _norm(text: Any) -> str:
    """
    Safely converts any value to a normalized string.
    """
    if text is None:
        return ""
    return str(text).strip()
# --- 1) Client Classification ---
def classify_client_type(client_raw: str) -> str:
    """
    Classifies the client type based on keywords.
    """
    if not client_raw:
        return "기타"
    s = client_raw.replace(" ", "") 

    if any(k in s for k in ["기초자치단체", "시청", "구청", "군청", "군", "세종특별자치시", "양주시", "평택시", "진천군", "괴산군"]):
        return "기초자치단체"
    if any(k in s for k in ["광역자치단체", "도청", "특별시", "광역시", "경기도", "경기도건설본부", "충청남도", "전라남도", "경상북도", "인천광역시"]):
        return "광역자치단체"
    if any(k in s for k in ["정부투자기관", "공사", "공단", "한국도로공사", "인천국제공항공사", "한국공항공사", "한국수자원공사", "한국농어촌공사", "한국토지주택공사", "한국환경공단"]):
        return "정부투자기관"
    if any(k in s for k in ["국토교통부", "국토관리청", "국가", "환경부", "제주지방국토관리청", "대전지방국토관리청", "원주지방환경청", "서울지방국토관리청", "부산지방국토관리청", "낙동강유역환경청"]):
        return "국가"
    if any(k in s for k in ["주식회사", "(주)", "㈜", "유한회사", "현대그린개발", "롯데케미칼", "삼성물산(주)"]):
        return "민간"
    return "기타"


def _parse_date(date_str: str) -> datetime | None:
    """
    날짜 문자열을 datetime 객체로 변환

    지원 형식:
    - YYYY-MM-DD (예: 2023-01-15)
    - YY.MM.DD (예: 95.01.23)
    - YYYY-MM (예: 2013-11) → YYYY-MM-01로 변환
    - YY.MM (예: 95.01) → YYYY-MM-01로 변환

    Args:
        date_str: 날짜 문자열

    Returns:
        datetime 객체 또는 None (파싱 실패시)
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()
    if not date_str:
        return None

    try:
        # YYYY-MM-DD 형식 시도
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            # YY.MM.DD 형식 시도 (예: 95.01.23)
            dt = datetime.strptime(date_str, "%y.%m.%d")
            # 19xx년과 20xx년을 구분 (70년 기준)
            if dt.year > datetime.now().year:
                dt = dt.replace(year=dt.year - 100)  # 19xx
            return dt
        except ValueError:
            try:
                # YYYY-MM 형식 시도 (예: 2013-11)
                dt = datetime.strptime(date_str, "%Y-%m")
                return dt.replace(day=1)  # 1일로 설정
            except ValueError:
                try:
                    # YY.MM 형식 시도 (예: 95.01)
                    dt = datetime.strptime(date_str, "%y.%m")
                    if dt.year > datetime.now().year:
                        dt = dt.replace(year=dt.year - 100)
                    return dt.replace(day=1)
                except ValueError:
                    # 파싱 실패 시 로그 출력 (디버깅용)
                    print(f"[WARN] 날짜 파싱 실패: {date_str}")
                    return None
# --- 3) Main Normalizer ---
# --- 4) 메인 정규화 함수 ---



def infer_logic_fields(project: Dict[str, Any]) -> Dict[str, Any]:
    """
    AI가 제공한 'primary' 필드를 기반으로 논리 필드를 설정합니다.
    """
    logic_fields = {}
    
    # --- FIX: AI가 제공한 'primary' 필드를 기반으로 추론 ---
    primary_field = project.get("primary_original_field", "기타토목")
    
    # 1. '직무분야' (Duty Field) 매핑
    civil_fields = ["도로", "하천", "상수도", "하수도", "철도", "단지", "항만", "기타토목", "토목"]
    if any(f in primary_field for f in civil_fields):
        duty_field_map = "토목"
    elif "조경" in primary_field:
        duty_field_map = "조경"
    else:
        duty_field_map = "토목" # 기본값

    # 2. '전문분야' (Specialty) 매핑
    specialty_map = {
        "도로": "도로및공항",
        "철도": "철도삭도",
        "상수도": "상하수도",
        "하수도": "상하수도",
        "항만": "항만및해안",
        "하천": "수자원개발",
        "토목": "토목시공",
        "조경": "조경계획",
    }
    # Find best match for specialty
    matched_specialty = "토목시공" # Default
    for key, val in specialty_map.items():
        if key in primary_field:
            matched_specialty = val
            break
            
    # 3. 양식의 기본값 설정
    logic_fields["use_date_type"] = "participation"
    logic_fields["duty_field1_eval_method"] = "by_duty"
    logic_fields["duty_field1"] = duty_field_map 
    logic_fields["duty_field2_eval_method"] = "same_as_sangju"
    logic_fields["duty_field2"] = duty_field_map
    logic_fields["tech_eval_method"] = "use_specialty"
    logic_fields["specialty"] = matched_specialty
    logic_fields["duty_field1_recognition_rule"] = "only_filled"
    logic_fields["duty_field2_recognition_rule"] = "only_filled"

    # 4. 발주처 60% 규칙 적용 (Optional logic placeholder)
    # client_type = project.get("client_type", "기타")
    # if client_type in ["기초자치단체", "정부투자기관"]:
    #    logic_fields["recognition_rate_rule"] = "civil_60" 
    
    return logic_fields


def normalize_project(raw_project: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes AI output. Handles LISTS of fields/roles/clients.
    """
    if not isinstance(raw_project, dict): return {}
    p_norm = dict(raw_project) 
    
    # 1. Engineer Name
    p_norm["engineer_name"] = _norm(p_norm.get("engineer_name"))
    
    # 2. Clients (Consolidate)
    raw_clients = p_norm.get("clients", [])
    if isinstance(raw_clients, str): raw_clients = [raw_clients]
    if p_norm.get("client"): raw_clients.append(p_norm.get("client"))
    
    p_norm["clients"] = list(set([_norm(c) for c in raw_clients if _norm(c)]))
    # Set single representative client for display, but use 'clients' list for rules
    p_norm["client"] = p_norm.get("client") or (p_norm["clients"][0] if p_norm["clients"] else "")
    p_norm["client_raw"] = p_norm["client"]
    p_norm["client_type"] = classify_client_type(p_norm["client_raw"])

    # 3. Roles (Consolidate)
    raw_roles = p_norm.get("roles", [])
    if isinstance(raw_roles, str): raw_roles = [raw_roles]
    if p_norm.get("primary_role"): raw_roles.append(p_norm.get("primary_role"))
    
    p_norm["roles"] = list(set([_norm(r) for r in raw_roles if _norm(r)]))
    p_norm["role"] = p_norm.get("primary_role") or (p_norm["roles"][0] if p_norm["roles"] else "")

    # 4. Fields (Consolidate)
    raw_fields = p_norm.get("original_fields", [])
    if isinstance(raw_fields, str): raw_fields = [raw_fields]
    if p_norm.get("primary_original_field"): raw_fields.append(p_norm.get("primary_original_field"))
    
    p_norm["original_fields"] = list(set([_norm(f) for f in raw_fields if _norm(f)]))
    p_norm["primary_original_field"] = p_norm.get("primary_original_field") or (p_norm["original_fields"][0] if p_norm["original_fields"] else "")

    # 5. Logic Fields
    p_norm.update(infer_logic_fields(p_norm))

    return p_norm
def normalize_tech_data_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize Step-2 OCR DataFrame fields:
    - participation/recognition dates
    - days fields
    - text cleanup
    - ensure consistent column names
    """
    if df.empty:
        return df

    # Clean columns explicitly
    target_cols = [
        "참여기간",
        "일정일",
        "참여일수",
        "사업명",
        "직무분야",
        "담당업무",
        "발주자|공사종류",
        "직위",
        "confidence",
    ]

    for col in target_cols:
        if col not in df.columns:
            df[col] = ""

    # Normalize 기간 → start/end extraction
    df["start_date"] = df["참여기간"].apply(_extract_start_date)
    df["end_date"] = df["참여기간"].apply(_extract_end_date)

    # Normalize recognition_day
    df["인정일"] = df["일정일"].apply(_parse_date)

    # Normalize days
    df["참여일수"] = df["참여일수"].apply(lambda x: _safe_int(str(x)))

    # Clean text columns
    text_cols = ["사업명", "직무분야", "담당업무", "발주자|공사종류", "직위"]
    for c in text_cols:
        df[c] = df[c].astype(str).str.strip()

    # Default participation days if missing
    df["참여일수"] = df.apply(
        lambda r: r["참여일수"] if r["참여일수"] > 0 else _compute_days_from_dates(r["start_date"], r["end_date"]),
        axis=1,
    )

    return df

def _extract_start_date(period_str: str) -> str:
    if not period_str:
        return ""
    mm = re.search(r"(\d{4}[.\-/]\d{1,2}(?:[.\-/]\d{1,2})?)", period_str)
    if mm:
        return _parse_date(mm.group(1))
    return ""


def _extract_end_date(period_str: str) -> str:
    if not period_str:
        return ""
    matches = re.findall(r"(\d{4}[.\-/]\d{1,2}(?:[.\-/]\d{1,2})?)", period_str)
    if len(matches) >= 2:
        return _parse_date(matches[-1])
    return ""


def _compute_days_from_dates(s: str, e: str) -> int:
    """Compute participation days if dates exist."""
    ds = _parse_date(s)
    de = _parse_date(e)
    if not ds or not de:
        return 0

    try:
        d1 = datetime.strptime(ds, "%Y-%m-%d") if len(ds) == 10 else datetime.strptime(ds, "%Y-%m")
        d2 = datetime.strptime(de, "%Y-%m-%d") if len(de) == 10 else datetime.strptime(de, "%Y-%m")
        if d2 < d1:
            return 0
        return (d2 - d1).days + 1
    except:
        return 0
    
    
def _safe_int(val: Any) -> int:
    try:
        return int(str(val).strip())
    except:
        return 0
