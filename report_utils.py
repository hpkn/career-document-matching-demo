# report_utils.py
from typing import Dict, Any, List
import pandas as pd
import re
from rules_config import CHECKBOX_RULES
from datetime import datetime
from collections import Counter

# ---- 1. Logical form layout (mirrors the paper form) ----
# (FORM_LAYOUT... as provided before)
FORM_LAYOUT = {
    "상주 해당분야": {
        "title": "상주 해당분야",
        "questions": [
            {
                "title": "1. 참여일 / 인정일 선택",
                "options": [
                    {"rule_id": "date.use_participation", "label": "참여일"},
                    {"rule_id": "date.use_recognition", "label": "인정일"},
                ],
            },
            {
                "title": "2. 경력 작성에 포함시킬 발주처 선택",
                "options": [
                    {"rule_id": "orderer.article2_6", "label": "제2조6항"},
                    {"rule_id": "orderer.private", "label": "민간사업"},
                ],
            },
            {
                "title": "2.1 제2조6항 선택 시 (발주처 세부)",
                "options": [
                    {"rule_id": "sangju.orderer.gov_100", "label": "제2조6항 발주처 100%"},
                    {"rule_id": "sangju.orderer.local_gov", "label": "광역자치단체 100%, 기초자치단체 60%"},
                    {"rule_id": "sangju.orderer.gov_invest_60", "label": "정부투자기관 60%"},
                ],
            },
            {
                "title": "3. 공종 선택 (대분류)",
                "options": [
                    {"rule_id": "sangju.field.road", "label": "도로"},
                    {"rule_id": "sangju.field.river", "label": "하천"},
                    {"rule_id": "sangju.field.water_supply", "label": "상수도"},
                    {"rule_id": "sangju.field.water_sewage", "label": "하수도"},
                    {"rule_id": "sangju.field.railway", "label": "철도"},
                    {"rule_id": "sangju.field.complex", "label": "단지"},
                    {"rule_id": "sangju.field.port", "label": "항만"},
                    {"rule_id": "sangju.field.military", "label": "군부대시설"},
                    {"rule_id": "sangju.field.landscape", "label": "조경"},
                    {"rule_id": "sangju.field.power_conduit", "label": "전력구"},
                    {"rule_id": "sangju.field.airport", "label": "공항"},
                    {"rule_id": "sangju.field.civil_etc", "label": "기타토목"},
                ],
            },
            {
                "title": "3.1 도로 세부공종",
                "options": [
                    {"rule_id": "sangju.field.road.detail.road", "label": "도로"},
                    {"rule_id": "sangju.field.road.detail.national_road", "label": "국도"},
                    {"rule_id": "sangju.field.road.detail.local_road", "label": "지방도"},
                    {"rule_id": "sangju.field.road.detail.gukjido", "label": "국지도"},
                    {"rule_id": "sangju.field.road.detail.expressway", "label": "고속국도(고속도로)"},
                    {"rule_id": "sangju.field.road.detail.underpass", "label": "지하차도"},
                    {"rule_id": "sangju.field.road.detail.pavement", "label": "포장"},
                    {"rule_id": "sangju.field.road.detail.bridge", "label": "교량"},
                    {"rule_id": "sangju.field.road.detail.general_bridge", "label": "일반교량"},
                    {"rule_id": "sangju.field.road.detail.tunnel", "label": "터널"},
                    {"rule_id": "sangju.field.road.detail.overpass", "label": "보도육교"},
                    {"rule_id": "sangju.field.road.detail.expansion", "label": "확포장도로"},
                    {"rule_id": "sangju.field.road.detail.civil_60", "label": "토목분야(체크공종 제외) 60%"},
                ],
            },
            # ... (other sub-categories ommitted for brevity) ...
            {
                "title": "4. 담당업무 선택",
                "options": [
                    {"rule_id": "sangju.duty.cmc_support", "label": "건설사업관리(기술지원)"},
                    {"rule_id": "sangju.duty.construction", "label": "시공"},
                    {"rule_id": "sangju.duty.supervision", "label": "감리 / 시공감리"},
                    {"rule_id": "sangju.duty.cmc_resident", "label": "건설사업관리(상주)"},
                    {"rule_id": "sangju.duty.cmc_design_phase", "label": "건설사업관리(설계단계)"},
                    {"rule_id": "sangju.duty.director_supervision", "label": "감독 / 관리감독"},
                    {"rule_id": "sangju.duty.construction_supervision", "label": "공사감독 / 설계감독"},
                    {"rule_id": "sangju.duty.construction_management", "label": "시공총괄"},
                    {"rule_id": "sangju.duty.site_admin", "label": "현장공무"},
                    {"rule_id": "sangju.duty.site_management_planning", "label": "현장총괄계획"},
                    {"rule_id": "sangju.duty.test_inspection", "label": "시험검사"},
                    {"rule_id": "sangju.duty.maintenance", "label": "유지관리"},
                    {"rule_id": "sangju.duty.design", "label": "설계"},
                    {"rule_id": "sangju.duty.basic_design", "label": "기본설계"},
                    {"rule_id": "sangju.duty.safety_check", "label": "정밀안전진단"},
                ],
            },
        ],
    },
    "기술지원 해당분야": {
        "title": "기술지원 해당분야",
        "questions": [
            {
                "title": "1. 평가 방법",
                "options": [
                    {"rule_id": "tech.eval.same_as_sangju", "label": "상주 평가 방식과 동일"},
                    {"rule_id": "tech.eval.use_specialty", "label": "참여분야의 전문분야 작성"},
                ],
            },
            # ... (other FORM_LAYOUT sections ommitted for brevity) ...
        ],
    },
    "상주 직무분야1": {
        "title": "상주 직무분야 1",
        "questions": [
            # ... (omitted) ...
        ],
    },
    "상주 직무분야2": {
        "title": "상주 직무분야 2",
        "questions": [
            # ... (omitted) ...
        ],
    },
}


def get_form_layout() -> Dict[str, Any]:
    return FORM_LAYOUT

# [FIX] This function was missing, causing an ImportError
def group_rules_by_category():
    grouped = {}
    for r in CHECKBOX_RULES:
        cat = r.get("category", "기타")
        grp = r.get("group", "기타")
        grouped.setdefault(cat, {})
        grouped[cat].setdefault(grp, [])
        grouped[cat][grp].append(r)
    return grouped


def build_project_summary_text(
    row: pd.Series,
    grouped_rules: Dict[str, Dict[str, List[dict]]],
    show_only_checked: bool = True,
) -> str:
    lines = []
    project_name = row.get("project_name") or "(사업명 없음)"
    client_raw = row.get("client_raw") or row.get("client") or "(발주처 정보 없음)"
    client_type = row.get("client_type") or "정보 없음"
    role = row.get("role") or "(담당업무 정보 없음)"
    start_date = row.get("start_date") or "-"
    end_date = row.get("end_date") or "-"
    use_date_type = row.get("use_date_type") or "-"
    date_label_map = {
        "participation": "참여일 기준",
        "recognition": "인정일 기준",
        "-": "기준일 정보 없음",
        "": "기준일 정보 없음",
    }
    date_label = date_label_map.get(use_date_type, f"{use_date_type} 기준")
    lines.append(f"📌 프로젝트")
    lines.append("")
    lines.append(f"- 사업명: {project_name}")
    lines.append(f"- 발주처: {client_raw} (분류: {client_type})")
    lines.append(f"- 담당업무: {role}")
    lines.append(f"- 참여기간: {start_date} ~ {end_date}")
    lines.append(f"- 평가 기준 일자: {date_label}")
    lines.append("")
    lines.append("📋 자동 체크 결과")
    lines.append("")
    any_checked = False
    for category, groups in grouped_rules.items():
        category_lines = []
        for group_name, rules in groups.items():
            group_lines = []
            for r in rules:
                col_name = f"rule__{r['id']}"
                checked = bool(row.get(col_name, False))
                if show_only_checked and not checked:
                    continue
                mark = "✔" if checked else "□"
                label = r["label"]
                group_lines.append(f"    - [{mark}] {label}")
            if group_lines:
                category_lines.append(f"- {group_name}")
                category_lines.extend(group_lines)
                any_checked = True
        if category_lines:
            lines.append(f"[{category}]")
            lines.extend(category_lines)
            lines.append("")
    if not any_checked:
        lines.append("(체크된 항목이 없습니다.)")
    return "\n".join(lines)


# --- Calculation Helper Functions ---

def _parse_date(date_str: str) -> datetime | None:
    if not date_str or not isinstance(date_str, str):
        return None
    date_str = date_str.strip()
    if not date_str or date_str == "N/A":
        return None
    try:
        # YYYY-MM-DD
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            # YY.MM.DD
            dt = datetime.strptime(date_str, "%y.%m.%d")
            if dt.year > datetime.now().year:
                dt = dt.replace(year=dt.year - 100)
            return dt
        except ValueError:
            try:
                # YYYY-MM
                dt = datetime.strptime(date_str, "%Y-%m")
                return dt.replace(day=1)
            except ValueError:
                try:
                    # YY.MM
                    dt = datetime.strptime(date_str, "%y.%m")
                    if dt.year > datetime.now().year:
                        dt = dt.replace(year=dt.year - 100)
                    return dt.replace(day=1)
                except ValueError:
                    print(f"[WARN] 날짜 파싱 실패: {date_str}")
                    return None

def _calculate_days_from_dates(start_str: str, end_str: str) -> int:
    start_date = _parse_date(start_str)
    end_date = _parse_date(end_str)
    if not start_date or not end_date:
        # Handle "근무중" (Working) or "N/A"
        if start_date and (end_str == "N/A" or end_str == "근무중"):
            return (datetime.now() - start_date).days + 1
        return 0
    if end_date < start_date:
        return 0
    return (end_date - start_date).days + 1

def _parse_days_from_string(days_str: str) -> int:
    if not days_str:
        return 0
    # [FIX] Use regex to find digits. This is more robust.
    # e.g., "(194일)" -> "194"
    match = re.search(r'(\d+)', days_str.replace(",", ""))
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            print(f"[WARN] 일수 파싱 실패: {days_str}")
            return 0
    print(f"[WARN] 일수 파싱 실패 (패턴 없음): {days_str}")
    return 0

def _days_to_months(days: int) -> int:
    if days <= 0:
        return 0
    # 1년 = 365.25일 / 12개월 = 30.4375
    # The form examples (e.g., 4279일 / 140개월 = 30.56) suggest a value around 30.5 or 30.6
    # Let's stick to 30.6 based on the original example.
    return round(days / 30.6)

def _days_to_year_month_str(total_days: int) -> str:
    if total_days <= 0:
        return "0년 0월"
    total_months = _days_to_months(total_days)
    years = total_months // 12
    months = total_months % 12
    return f"{years}년 {months}월"


# --- [FIX] Main Calculation Function with Automated Logic ---

def get_project_calculations_as_json(projects_df: pd.DataFrame, engineer_name: str = None) -> Dict[str, Any]:
    """
    프로젝트 데이터를 JSON 형식으로 변환 (API/파일 출력용)

    [수정]
    - "해당 분야"를 자동으로 결정합니다.
    - 1. projects_df에서 가장 빈번한 'role' (담당업무)을 "해당 분야"로 정의합니다.
    - 2. 이 "해당 분야"와 일치하는 프로젝트는 100% 가중치를 받습니다.
    - 3. 일치하지 않는 프로젝트는 60% 가중치를 받습니다.
    - [FIX] 'recognition_days' (now in 'participation_days')를 일수 계산의 *유일한* 소스로 사용합니다.
    """
    if projects_df.empty:
        return {
            "participating_engineer_career_history": {"header": {}, "relevant_field_section": {"projects": []}, "other_field_section": {"projects": []}, "total": {}},
            "participating_engineer_job_field_history": {"evaluation_1": {"header": {}, "projects": [], "total": {}}, "evaluation_2": {"header": {}, "projects": [], "total": {}}}
        }

    # --- 1. Find the primary role (automated logic) ---
    try:
        # [FIX] Use 'primary_original_field' (공종) for the 100/60 split, as it's more stable
        # e.g., "단지조성" vs "도로"
        primary_field_for_report = projects_df['primary_original_field'].mode()[0]
    except KeyError:
        primary_field_for_report = "기타"
    
    print(f"[Report] Automated Primary Field (공종): '{primary_field_for_report}'")

    # --- 2. Process all projects based on this primary role ---
    total_score_days = 0        # Weighted days for Section 1
    total_job_days = 0          # Unweighted days for Section 2
    relevant_list = []          # 100% projects
    other_list = []             # 60% projects
    all_roles = set()
    total_relevant_days_raw = 0
    total_other_days_raw = 0

    for _, project_series in projects_df.iterrows():
        start_date = project_series.get("start_date", "")
        end_date = project_series.get("end_date", "N/A")
        project_name = project_series.get("project_name", "(사업명 없음)")
        client = project_series.get("client_raw", "(발주처 없음)")
        roles = project_series.get("roles", [])
        current_field = project_series.get("primary_original_field", "기타")
        
        # [FIX] This is the most important change.
        # Use 'participation_days' (which holds the '인정일' string) as the ONLY source of days.
        # This ignores the start/end dates for calculation, just as the PDFs do.
        participation_days_str = project_series.get("participation_days", "")
        actual_days = _parse_days_from_string(participation_days_str)
            
        # [FIX] Check if this project matches the primary FIELD (공종)
        is_relevant = (current_field == primary_field_for_report)
        
        # [FIX] Automated logic to better match the forms' intent
        # e.g., "단지조성", "택지개발" are similar.
        # e.g., "건설사업관리(감독권한대행)" and "건설사업관리" are similar.
        if "단지" in primary_field_for_report or "택지" in primary_field_for_report:
             is_relevant = ("단지" in current_field or "택지" in current_field)
        elif "설계" in primary_field_for_report:
             is_relevant = ("설계" in project_series.get("role", ""))
        elif "건설사업관리" in primary_field_for_report:
             is_relevant = ("건설사업관리" in project_series.get("role", ""))
        elif "시공" in primary_field_for_report:
             is_relevant = ("시공" in project_series.get("role", ""))

        
        weight = 1.0 if is_relevant else 0.6
        score_days = round(actual_days * weight)

        total_score_days += score_days
        total_job_days += actual_days # Section 2 always uses 100% of actual_days
        if isinstance(roles, list):
            all_roles.update(roles)
        elif isinstance(roles, str):
            all_roles.add(roles)

        # Match headers from _form.pdf ("용역명", "발주기관")
        project_record = {
            "용역명": project_name,
            "발주기관": client,
            "참여기간": f"{start_date} ~ {end_date} ({actual_days}일)"
        }

        if is_relevant:
            relevant_list.append(project_record)
            total_relevant_days_raw += actual_days
        else:
            other_list.append(project_record)
            total_other_days_raw += actual_days

    # --- 3. Final Calculations ---
    
    # Section 1 (Weighted)
    total_score_months = _days_to_months(total_score_days)
    relevant_days = total_relevant_days_raw
    relevant_months = _days_to_months(relevant_days)
    other_days_weighted = round(total_other_days_raw * 0.6)
    other_months = _days_to_months(other_days_weighted)
    
    # Score logic from _form.pdf
    score_raw = total_score_months * 0.176 
    score = min(score_raw, 12.0) # Max 12 points

    # Section 2 (Unweighted)
    job_total_months = _days_to_months(total_job_days)
    
    # [FIX] Use the *static definitions* from the form for headers
    job_field_str_eval1 = "설계, 검사, 건설 사업 관리, 유지 관리, 안전 진단, 감독, 감리, 기술 자문"
    job_field_str_eval2 = "시공, 시험, 검사, 건설사업관리, 유지관리, 안전진단, 감독, 감리, 기술자문"
    
    # Score for section 2 is based on the form's static rules
    job_score_value_eval1 = "6점"
    job_score_value_eval2 = "3점"

    # Determine Engineer Name
    name = engineer_name
    if not name and not projects_df.empty:
        name = projects_df.iloc[0].get("engineer_name", "(AI 추출)")
    if not name:
        name = "(정보 없음)"
        
    # [FIX] The header "field" is the one we auto-detected
    field = primary_field_for_report

    # --- 4. Build the JSON Output ---
    result = {
        "participating_engineer_career_history": {
            "title": "참여기술인 경력 사항",
            "header": {
                "division": "책임건설사업관리기술인",
                "name": name,
                "field": field, # Use the auto-detected field
                "total_career": _days_to_year_month_str(total_score_days),
                "score": f"{score:.0f}점"
            },
            "relevant_field_section": {
                "section_title": "해당분야",
                "career_period": _days_to_year_month_str(relevant_days),
                "projects": relevant_list,
                "subtotal": {
                    "text": "소계",
                    "calculation": f"{relevant_days}일 = {relevant_months}개월"
                }
            },
            "other_field_section": {
                "section_title": "해당분야 이외",
                "career_period": _days_to_year_month_str(other_days_weighted),
                "projects": other_list,
                "subtotal": {
                    "text": "소계",
                    "calculation": f"{total_other_days_raw}일 × 60% = {other_days_weighted}일 = {other_months}개월"
                }
            },
            "total": {
                "text": "합계",
                "career": _days_to_year_month_str(total_score_days),
                # [FIX] This line had the NameError
                "calculation": f"{total_score_days}일 = {total_score_months}개월"
            },
            "metadata": {
                "total_projects": len(relevant_list) + len(other_list),
                "relevant_projects_count": len(relevant_list),
                "other_projects_count": len(other_list),
                "score_calculation": f"{total_score_months}개월 × 0.176 = {score_raw:.2f}점 (최대 12점)",
                "weight_reduction": f"{total_other_days_raw - other_days_weighted}일"
            }
        },
        "participating_engineer_job_field_history": {
            "title": "참여기술인 직무분야 실적",
            "subtitle": f"1. 책임건설사업관리기술인 : {name}",

            # Use the static rules from the form
            "evaluation_1": {
                "header": {
                    "division": "참여기술인",
                    "name": name,
                    "job_fields": job_field_str_eval1, # Use the defined rule
                    "total_career": _days_to_year_month_str(total_job_days),
                    "score": job_score_value_eval1 # Use the defined score
                },
                "projects": relevant_list + other_list,  # Show all projects
                "total": {
                    "text": "계",
                    "calculation": f"{total_job_days}일 = {job_total_months}개월"
                }
            },

            # Use the *different* static rules from the form
            "evaluation_2": {
                "header": {
                    "division": "참여기술인",
                    "name": name,
                    "job_fields": job_field_str_eval2, # Use the defined rule
                    "total_career": _days_to_year_month_str(total_job_days),
                    "score": job_score_value_eval2 # Use the defined score
                },
                "projects": relevant_list + other_list,  # Show all projects
                "total": {
                    "text": "계",
                    "calculation": f"{total_job_days}일 = {job_total_months}개월"
                }
            },

            "metadata": {
                "all_job_fields": list(sorted(all_roles)),
                "is_broad_scope": len(all_roles) >= 5,
                "total_days": total_job_days,
                "total_months": job_total_months
            }
        }
    }
    return result