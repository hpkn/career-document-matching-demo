from typing import List, Dict, Any

def _norm(text) -> str:
    """
    텍스트를 정규화하여 안전한 문자열로 변환

    Args:
        text: 정규화할 값 (any type)

    Returns:
        정규화된 문자열 (None은 빈 문자열로 변환)
    """
    if text is None:
        return ""
    return str(text).strip()

# --- 1) 발주처 분류 ---
def classify_client_type(client_raw: str) -> str:
    """
    발주처 이름으로부터 발주처 유형을 분류

    Args:
        client_raw: 발주처 원본 이름

    Returns:
        발주처 분류 (국가, 광역자치단체, 기초자치단체, 정부투자기관, 민간, 기타)
    """
    if not client_raw:
        return "기타"
    s = client_raw.replace(" ", "") 

    if any(k in s for k in ["기초자치단체", "시청", "구청", "군청", "군"]): 
        return "기초자치단체"
    if any(k in s for k in ["광역자치단체", "도청", "특별시", "광역시", "경기도", "경기도건설본부"]):
        return "광역자치단체"
    if any(k in s for k in ["정부투자기관", "공사", "공단", "한국도로공사"]):
        return "정부투자기관"
    if any(k in s for k in ["국토교통부", "국토관리청", "국가", "환경부"]):
        return "국가"
    if any(k in s for k in ["주식회사", "(주)", "㈜", "유한회사"]):
        return "민간"
    return "기타"

# --- 2) 공종(대분류) 추론 (이제 사용되지 않음, AI가 직접 제공) ---
# infer_original_field 함수는 AI 프롬프트가 개선되어 더 이상 필요하지 않습니다.

# --- 3) 평가 방식 및 규칙 추론 (DEMO LOGIC) ---
def infer_logic_fields(project: Dict[str, Any]) -> Dict[str, Any]:
    """
    AI가 제공한 'primary' 필드를 기반으로 논리 필드를 설정

    프로젝트의 주요 공종(primary_original_field)을 기반으로
    직무분야, 전문분야, 평가방법 등을 자동으로 추론합니다.

    Args:
        project: 정규화된 프로젝트 딕셔너리

    Returns:
        추론된 논리 필드 딕셔너리
    """
    logic_fields = {}
    
    # --- FIX: AI가 제공한 'primary' 필드를 기반으로 추론 ---
    primary_field = project.get("primary_original_field", "기타토목")
    
    # 1. '직무분야' (Duty Field) 매핑
    civil_fields = ["도로", "하천", "상수도", "하수도", "철도", "단지", "항만", "기타토목", "토목"]
    if primary_field in civil_fields:
        duty_field_map = "토목"
    elif primary_field == "조경":
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
    }
    
    # 3. 양식의 기본값 설정
    logic_fields["use_date_type"] = "participation"
    logic_fields["duty_field1_eval_method"] = "by_duty"
    logic_fields["duty_field1"] = duty_field_map 
    logic_fields["duty_field2_eval_method"] = "same_as_sangju"
    logic_fields["duty_field2"] = duty_field_map
    logic_fields["tech_eval_method"] = "use_specialty"
    logic_fields["specialty"] = specialty_map.get(primary_field, "토목시공") 
    logic_fields["duty_field1_recognition_rule"] = "only_filled"
    logic_fields["duty_field2_recognition_rule"] = "only_filled"

    # 4. 발주처 60% 규칙 적용
    client_type = project.get("client_type", "기타")
    if client_type in ["기초자치단체", "정부투자기관"]:
        logic_fields["recognition_rate_rule"] = "civil_60" 
    
    return logic_fields

# --- 4) 메인 정규화 함수 ---
def normalize_project(raw_project: Dict[str, Any]) -> Dict[str, Any]:
    """
    AI가 추출한 원본 데이터를 받아 규칙 엔진이 사용하기 쉽도록 정제하고 보강합니다.
    """
    if not raw_project:
        return {}
    
    p_norm = dict(raw_project) 
    
    # 1. 발주처 정규화
    client_raw = _norm(p_norm.get("client"))
    client_type = classify_client_type(client_raw)
    p_norm["client_raw"] = client_raw
    p_norm["client_type"] = client_type
    p_norm["client"] = f"{client_raw} {client_type}" 

    # 2. 공종 및 역할 필드 정규화 (리스트로 처리)
    # AI가 'original_field' 대신 'original_fields'와 'primary_original_field'를 반환합니다.
    # rules_engine이 'original_fields' 리스트를 직접 사용할 수 있도록 정규화합니다.
    raw_fields = p_norm.get("original_fields", [])
    primary_field = p_norm.get("primary_original_field")
    if primary_field and primary_field not in raw_fields:
        raw_fields.append(primary_field)
    p_norm["original_fields"] = list(set([_norm(f) for f in raw_fields if _norm(f)]))

    # 역할(roles)에 대해서도 동일하게 처리
    raw_roles = p_norm.get("roles", [])
    primary_role = p_norm.get("primary_role")
    if primary_role and primary_role not in raw_roles:
        raw_roles.append(primary_role)
    p_norm["roles"] = list(set([_norm(r) for r in raw_roles if _norm(r)]))

    # 'original_field'는 'primary_original_field'로 대체 (하위 호환성)
    p_norm["original_field"] = _norm(primary_field)
    p_norm["role"] = _norm(primary_role)

    # 3. 논리 필드 추가 (primary_field 기준)
    logic_fields = infer_logic_fields(p_norm)
    p_norm.update(logic_fields) 
    
    print(f"[Normalizer] Enriched 1 project with logic fields.")
    return p_norm