"""
Report generation and calculation utilities.

This module provides:
- Form layout definitions for UI rendering
- Project summary text generation
- Career calculation logic (days, months, years, scoring)
- Aggregation of multiple projects for final report
"""
from typing import Dict, Any, List
import pandas as pd
from rules_config import CHECKBOX_RULES
from datetime import datetime

# ---- 1. Logical form layout (mirrors the paper form) ----
# (기존 FORM_LAYOUT... 생략)
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
            {
                "title": "3.2 하천 세부공종",
                "options": [
                    {"rule_id": "sangju.field.river.detail.maintenance", "label": "하천정비"},
                    {"rule_id": "sangju.field.river.detail.maintenance_nat", "label": "하천정비(국가)"},
                    {"rule_id": "sangju.field.river.detail.maintenance_loc", "label": "하천정비(지방)"},
                    {"rule_id": "sangju.field.river.detail.nat_loc", "label": "국가하천 · 지방하천"},
                    {"rule_id": "sangju.field.river.detail.disaster", "label": "재해위험지구정비 하천"},
                    {"rule_id": "sangju.field.river.detail.civil_60", "label": "토목분야(체크공종 제외) 60%"},
                ],
            },
            {
                "title": "3.3 상수도·하수도 세부공종",
                "options": [
                    {"rule_id": "sangju.field.water.detail.supply", "label": "상수도 / 상수도시설"},
                    {"rule_id": "sangju.field.water.detail.supply_sewage", "label": "상하수도 / 상수관로 / 정수장"},
                    {"rule_id": "sangju.field.water.detail.drainage", "label": "배수관 / 배수시설 / 배수지 / 급수관"},
                    {"rule_id": "sangju.field.water.detail.sewage_pipe", "label": "오수관로 / 분뇨처리시설"},
                    {"rule_id": "sangju.field.water.detail.sewage_facility", "label": "하수시설 / 하수종말처리장 등"},
                    {"rule_id": "sangju.field.water.detail.sewage_final", "label": "하수종말처리시설"},
                    {"rule_id": "sangju.field.water.detail.purify_facility", "label": "정수시설"},
                    {"rule_id": "sangju.field.water.detail.transmission_pipe", "label": "송수관로"},
                    {"rule_id": "sangju.field.water.detail.sewer_pipe", "label": "하수관로"},
                    {"rule_id": "sangju.field.water.detail.purify_process", "label": "정수처리"},
                    {"rule_id": "sangju.field.water.detail.transmission_facility", "label": "송수시설"},
                    {"rule_id": "sangju.field.water.detail.storm_pipe", "label": "우수관로"},
                    {"rule_id": "sangju.field.water.detail.drainage_facility", "label": "배수처리시설"},
                    {"rule_id": "sangju.field.water.detail.waste_water", "label": "폐수종말처리"},
                    {"rule_id": "sangju.field.water.detail.civil_60", "label": "토목분야(체크공종 제외) 60%"},
                ],
            },
            {
                "title": "3.4 철도 세부공종",
                "options": [
                    {"rule_id": "sangju.field.railway.detail.railway", "label": "철도"},
                    {"rule_id": "sangju.field.railway.detail.roadbed_facility", "label": "철도노반시설"},
                    {"rule_id": "sangju.field.railway.detail.roadbed", "label": "철도노반"},
                    {"rule_id": "sangju.field.railway.detail.subway", "label": "지하철"},
                    {"rule_id": "sangju.field.railway.detail.light_rail", "label": "경전철"},
                    {"rule_id": "sangju.field.railway.detail.general_rail", "label": "일반철도"},
                    {"rule_id": "sangju.field.railway.detail.urban_rail", "label": "도시철도"},
                    {"rule_id": "sangju.field.railway.detail.general_bridge", "label": "일반교량"},
                    {"rule_id": "sangju.field.railway.detail.bridge", "label": "교량"},
                    {"rule_id": "sangju.field.railway.detail.tunnel", "label": "터널"},
                    {"rule_id": "sangju.field.railway.detail.facilities_combined", "label": "철도[노반·궤도시설]"},
                    {"rule_id": "sangju.field.railway.detail.track_60", "label": "철도궤도... 60%"},
                    {"rule_id": "sangju.field.railway.detail.track_40", "label": "철도궤도... 40%"},
                    {"rule_id": "sangju.field.railway.detail.civil_60", "label": "토목분야(체크공종 제외) 60%"},
                ],
            },
            {
                "title": "3.5 단지 세부공종",
                "options": [
                    {"rule_id": "sangju.field.complex.detail.land_dev", "label": "단지조성"},
                    {"rule_id": "sangju.field.complex.detail.housing_dev", "label": "택지개발"},
                    {"rule_id": "sangju.field.complex.detail.industrial_dev", "label": "산업단지조성공사"},
                    {"rule_id": "sangju.field.complex.detail.site_prep", "label": "부지조성공사"},
                    {"rule_id": "sangju.field.complex.detail.civil_etc_60", "label": "토목분야(기타) 60%"},
                ],
            },
            {
                "title": "3.6 항만 세부공종",
                "options": [
                    {"rule_id": "sangju.field.port.detail.port", "label": "항만"},
                    {"rule_id": "sangju.field.port.detail.port_coast", "label": "항만및해안"},
                    {"rule_id": "sangju.field.port.detail.quay", "label": "안벽"},
                    {"rule_id": "sangju.field.port.detail.breakwater", "label": "방파제"},
                    {"rule_id": "sangju.field.port.detail.site_prep", "label": "부지조성"},
                    {"rule_id": "sangju.field.port.detail.civil_etc_60", "label": "토목분야(기타) 60%"},
                ],
            },
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
            # ... (rest of your form layout is correct) ...
            {
                "title": "1. 평가 방법",
                "options": [
                    {"rule_id": "tech.eval.same_as_sangju", "label": "상주 평가 방식과 동일"},
                    {"rule_id": "tech.eval.use_specialty", "label": "참여분야의 전문분야 작성"},
                ],
            },
            {
                "title": "2.1 참여일 / 인정일 선택",
                "options": [
                    {"rule_id": "date.use_participation", "label": "참여일"},
                    {"rule_id": "date.use_recognition", "label": "인정일"},
                ],
            },
            {
                "title": "2.2 경력 작성에 포함시킬 발주처 선택",
                "options": [
                    {"rule_id": "orderer.article2_6", "label": "제2조6항"},
                    {"rule_id": "orderer.private", "label": "민간사업"},
                ],
            },
            {
                "title": "2.3 공종 선택 (전문분야)",
                "options": [
                    {"rule_id": "tech.field.road_airport", "label": "도로및공항"},
                    {"rule_id": "tech.field.structure", "label": "토목구조"},
                    {"rule_id": "tech.field.geotech", "label": "토질지질"},
                    {"rule_id": "tech.field.civil_construct", "label": "토목시공"},
                    {"rule_id": "tech.field.railway", "label": "철도삭도"},
                    {"rule_id": "tech.field.water", "label": "상하수도"},
                    {"rule_id": "tech.field.water_resource", "label": "수자원개발"},
                    {"rule_id": "tech.field.safety", "label": "건설안전"},
                    {"rule_id": "tech.field.landscape", "label": "조경계획"},
                    {"rule_id": "tech.field.port", "label": "항만및해안"},
                    {"rule_id": "tech.field.machine", "label": "기계"},
                    {"rule_id": "tech.field.construct_machine", "label": "건설기계"},
                    {"rule_id": "tech.field.hvac", "label": "공조냉동기계"},
                    {"rule_id": "tech.field.agri_civil", "label": "농어업토목"},
                    {"rule_id": "tech.field.survey", "label": "측량및지형공간정보"},
                    {"rule_id": "tech.field.quality", "label": "토목품질시험"},
                    {"rule_id": "tech.field.ground", "label": "지질및지반"},
                    {"rule_id": "tech.field.arch_structure", "label": "건축구조"},
                    {"rule_id": "tech.field.arch_mech", "label": "건축기계설비"},
                    {"rule_id": "tech.field.arch_construct", "label": "건축시공"},
                    {"rule_id": "tech.field.arch_quality", "label": "건축품질시험"},
                    {"rule_id": "tech.field.transport", "label": "교통"},
                    {"rule_id": "tech.field.urban", "label": "도시계획"},
                ],
            },
        ],
    },

    "상주 직무분야1": {
        "title": "상주 직무분야 1",
        "questions": [
            {
                "title": "1. 평가 방법",
                "options": [
                    {"rule_id": "duty_field1.eval.by_duty", "label": "직무분야로 평가"},
                    {"rule_id": "duty_field1.eval.same_as_sangju", "label": "상주 해당분야 평가 방식과 동일"},
                ],
            },
            {
                "title": "2. 직무분야로 평가시 직무 선택",
                "options": [
                    {"rule_id": "duty_field1.field.civil", "label": "토목"},
                    {"rule_id": "duty_field1.field.architecture", "label": "건축"},
                    {"rule_id": "duty_field1.field.machine", "label": "기계"},
                    {"rule_id": "duty_field1.field.safety", "label": "안전관리"},
                ],
            },
            {
                "title": "3. 참여일 / 인정일 선택",
                "options": [
                    {"rule_id": "date.use_participation", "label": "참여일"},
                    {"rule_id": "date.use_recognition", "label": "인정일"},
                ],
            },
            {
                "title": "4. 경력 작성에 포함시킬 발주처 선택",
                "options": [
                    {"rule_id": "orderer.article2_6", "label": "제2조6항"},
                    {"rule_id": "orderer.private", "label": "민간사업"},
                    {"rule_id": "orderer.blank", "label": "발주처 빈칸"},
                ],
            },
            {
                "title": "5. 담당업무 선택",
                "options": [
                    {"rule_id": "duty_field1.duty.cmc_resident", "label": "건설사업관리(상주)"},
                    {"rule_id": "duty_field1.duty.cmc_design_phase", "label": "건설사업관리(설계단계)"},
                    {"rule_id": "duty_field1.duty.cmc_support", "label": "건설사업관리(기술지원)"},
                    {"rule_id": "duty_field1.duty.supervision", "label": "시공감리"},
                    {"rule_id": "duty_field1.duty.director_supervision", "label": "감독관리감독"},
                    {"rule_id": "duty_field1.duty.construction_supervision", "label": "공사감독설계감독"},
                    {"rule_id": "duty_field1.duty.construction", "label": "시공"},
                    {"rule_id": "duty_field1.duty.construction_mgmt", "label": "시공총괄"},
                    {"rule_id": "duty_field1.duty.site_admin", "label": "현장공무"},
                    {"rule_id": "duty_field1.duty.site_planning", "label": "현장총괄계획"},
                    {"rule_id": "duty_field1.duty.test_inspection", "label": "시험검사"},
                    {"rule_id": "duty_field1.duty.maintenance", "label": "유지관리"},
                    {"rule_id": "duty_field1.duty.design", "label": "설계"},
                    {"rule_id": "duty_field1.duty.basic_design", "label": "기본설계"},
                    {"rule_id": "duty_field1.duty.detailed_design", "label": "실시설계"},
                    {"rule_id": "duty_field1.duty.feasibility_study", "label": "타당성조사"},
                    {"rule_id": "duty_field1.duty.technical_advice", "label": "기술자문"},
                    {"rule_id": "duty_field1.duty.safety_inspection", "label": "안전점검"},
                    {"rule_id": "duty_field1.duty.detailed_safety", "label": "정밀안전진단"},
                ],
            },
            {
                "title": "6. 경력 인정사항",
                "options": [
                    {"rule_id": "duty_field1.recognition.include_blank_field", "label": "공종 빈칸도 적용"},
                    {"rule_id": "duty_field1.recognition.include_blank_duty", "label": "담당업무 빈칸도 적용"},
                    {"rule_id": "duty_field1.recognition.only_filled", "label": "공종 및 담당업무 기재된 사업만 적용"},
                ],
            },
        ],
    },

    "상주 직무분야2": {
        "title": "상주 직무분야 2",
        "questions": [
            {
                "title": "1. 평가 방법",
                "options": [
                    {"rule_id": "duty_field2.eval.by_duty", "label": "직무분야로 평가"},
                    {"rule_id": "duty_field2.eval.same_as_sangju", "label": "상주 해당분야 평가 방식과 동일"},
                ],
            },
            {
                "title": "2. 직무분야로 평가시 직무 선택",
                "options": [
                    {"rule_id": "duty_field2.field.civil", "label": "토목"},
                    {"rule_id": "duty_field2.field.architecture", "label": "건축"},
                    {"rule_id": "duty_field2.field.machine", "label": "기계"},
                    {"rule_id": "duty_field2.field.landscape", "label": "조경"},
                    {"rule_id": "duty_field2.field.safety", "label": "안전관리"},
                ],
            },
            {
                "title": "3. 참여일 / 인정일 선택",
                "options": [
                    {"rule_id": "date.use_participation", "label": "참여일"},
                    {"rule_id": "date.use_recognition", "label": "인정일"},
                ],
            },
            {
                "title": "4. 경력 작성에 포함시킬 발주처 선택",
                "options": [
                    {"rule_id": "orderer.article2_6", "label": "제2조6항"},
                    {"rule_id": "orderer.private", "label": "민간사업"},
                    {"rule_id": "orderer.blank", "label": "발주처 빈칸"},
                ],
            },
            {
                "title": "5. 담당업무 선택",
                "options": [
                    {"rule_id": "duty_field2.duty.cmc_resident", "label": "건설사업관리(상주)"},
                    {"rule_id": "duty_field2.duty.cmc_design_phase", "label": "건설사업관리(설계단계)"},
                    {"rule_id": "duty_field2.duty.cmc_support", "label": "건설사업관리(기술지원)"},
                    {"rule_id": "duty_field2.duty.supervision", "label": "시공감리"},
                    {"rule_id": "duty_field2.duty.director", "label": "감독"},
                    {"rule_id": "duty_field2.duty.mgmt_supervision", "label": "관리감독"},
                    {"rule_id": "duty_field2.duty.construction_supervision", "label": "공사감독"},
                    {"rule_id": "duty_field2.duty.design_supervision", "label": "설계감독"},
                    {"rule_id": "duty_field2.duty.construction", "label": "시공"},
                    {"rule_id": "duty_field2.duty.construction_mgmt", "label": "시공총괄"},
                    {"rule_id": "duty_field2.duty.site_admin", "label": "현장공무"},
                    {"rule_id": "duty_field2.duty.site_mgmt", "label": "현장총괄"},
                    {"rule_id": "duty_field2.duty.planning", "label": "계획"},
                    {"rule_id": "duty_field2.duty.test", "label": "시험"},
                    {"rule_id": "duty_field2.duty.inspection", "label": "검사"},
                    {"rule_id": "duty_field2.duty.maintenance", "label": "유지관리"},
                    {"rule_id": "duty_field2.duty.design", "label": "설계"},
                    {"rule_id": "duty_field2.duty.basic_design", "label": "기본설계"},
                    {"rule_id": "duty_field2.duty.detailed_design", "label": "실시설계"},
                    {"rule_id": "duty_field2.duty.feasibility_study", "label": "타당성조사"},
                    {"rule_id": "duty_field2.duty.technical_advice", "label": "기술자문"},
                    {"rule_id": "duty_field2.duty.safety_inspection", "label": "안전점검"},
                    {"rule_id": "duty_field2.duty.detailed_safety", "label": "정밀안전진단"},
                ],
            },
            {
                "title": "6. 경력 인정사항",
                "options": [
                    {"rule_id": "duty_field2.recognition.include_blank_field", "label": "공종 빈칸도 적용"},
                    {"rule_id": "duty_field2.recognition.include_blank_duty", "label": "담당업무 빈칸도 적용"},
                    {"rule_id": "duty_field2.recognition.only_filled", "label": "공종 및 담당업무 기재된 사업만 적용"},
                ],
            },
        ],
    },
}


def get_form_layout() -> Dict[str, Any]:
    return FORM_LAYOUT

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


# --- [새로 추가된 헬퍼 함수] ---

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

def _calculate_days(start_str: str, end_str: str) -> int:
    """
    시작일과 종료일 사이의 일수 계산 (종료일 포함)

    Args:
        start_str: 시작일 문자열
        end_str: 종료일 문자열

    Returns:
        일수 (종료일 포함, 유효하지 않은 경우 0)
    """
    start_date = _parse_date(start_str)
    end_date = _parse_date(end_str)

    if not start_date or not end_date:
        return 0

    if end_date < start_date:
        print(f"[WARN] 종료일이 시작일보다 이릅니다: {start_str} ~ {end_str}")
        return 0

    return (end_date - start_date).days + 1  # 종료일 포함 +1

def _days_to_months(days: int) -> int:
    """
    일수를 개월로 변환

    변환 공식: round(days / 30.6)
    (30.6은 평균 월 일수로 1년 = 365.25일 / 12개월)

    Args:
        days: 일수

    Returns:
        개월 수 (정수)
    """
    if days <= 0:
        return 0
    return round(days / 30.6)

def _days_to_year_month_str(total_days: int) -> str:
    """
    일수를 'X년 Y월' 문자열로 변환

    Args:
        total_days: 총 일수

    Returns:
        'X년 Y월' 형식의 문자열
    """
    if total_days <= 0:
        return "0년 0월"
    total_months = _days_to_months(total_days)
    years = total_months // 12
    months = total_months % 12
    return f"{years}년 {months}월"

# --- [수정된 메인 계산 함수] ---

def get_project_calculations(projects_df: pd.DataFrame) -> Dict[str, Any]:
    """
    AI가 추출한 *여러 프로젝트(DataFrame)*를 기반으로
    사용자가 요청한 PDF 양식의 계산을 *합산*하여 UI용 딕셔너리를 반환합니다.
    """
    
    # --- 1. 집계 변수 초기화 ---
    total_score_days = 0
    total_job_days = 0 # 직무분야는 100% 가중치
    relevant_list = []
    other_list = []
    all_project_records_str = []
    all_roles = set()
    
    if projects_df.empty:
        # 프로젝트가 하나도 없으면 빈 템플릿 반환
        return {
            "career_details": {
                "성명": "(정보 없음)", "분야": "(정보 없음)", "현재까지 경력": "0년 0월",
                "평점": "0점", "total_score_months": 0, "해당분야 용역참여실적": [],
                "해당분야 이외 참여실적": [], "classification_label": "정보 없음", "weight": 0
            },
            "job_field_details": {
                "책임건설사업관리기술인": "(정보 없음)", "직무분야": "", "현재까지 경력": "0년 0월",
                "평점": "0점", "total_job_months": 0, "용역참여실적": []
            }
        }

    # --- 2. DataFrame을 반복하며 모든 프로젝트 합산 ---
    for _, project_series in projects_df.iterrows():
        # AI 추출 데이터 가져오기
        start_date = project_series.get("start_date", "")
        end_date = project_series.get("end_date", "")
        project_name = project_series.get("project_name", "(사업명 없음)")
        client = project_series.get("client_raw", "(발주처 없음)")
        roles = project_series.get("roles", [])
        
        # 100% vs 60% 분류 로직 (규칙 기반)
        is_60_percent_rule = project_series.get("recognition_rate_rule") == "civil_60"
        weight = 0.6 if is_60_percent_rule else 1.0

        # 실제 참여 일수 계산
        actual_days = _calculate_days(start_date, end_date)
        
        # 가중치를 적용한 '환산 일수'
        score_days = round(actual_days * weight)
        
        # 합산
        total_score_days += score_days
        total_job_days += actual_days # 직무 경력은 실제 일수 합산
        all_roles.update(roles)

        # 리스트에 추가
        project_record = {
            "용역명": project_name,
            "발주기관": client,
            "참여기간": f"{start_date} ~ {end_date} ({actual_days}일)"
        }
        if is_60_percent_rule:
            other_list.append(project_record)
        else:
            relevant_list.append(project_record)
            
        all_project_records_str.append(
            f"{project_name} ({client}, {start_date}~{end_date}, {actual_days}일)"
        )

    # --- 3. '경력 사항' 최종 계산 ---
    total_score_months = _days_to_months(total_score_days)
    total_career_str = f"{_days_to_year_month_str(total_score_days)} (환산 {total_score_days}일 = {total_score_months}개월)"

    score_raw = total_score_months * 0.176
    score = min(score_raw, 12.0) # 최대 12점
    score_str = f"{score:.1f}점"

    # --- 4. '직무 분야' 최종 계산 ---
    # 직무분야는 가중치 없이 실제 일수 사용
    job_total_months = _days_to_months(total_job_days)
    job_career_str = f"{_days_to_year_month_str(total_job_days)} ({total_job_days}일 = {job_total_months}개월)"
    
    job_field_str = ", ".join(sorted(list(all_roles)))
    
    # 직무 평점 (Broad 6점 vs Limited 3점)
    # 프록시 로직: PDF 예제(10개)를 기준으로, 5개 이상이면 Broad(6점)
    is_broad_scope = len(all_roles) >= 5 
    job_score_str = "6점 (광범위)" if is_broad_scope else "3점 (제한적)"

    # --- 5. 최종 결과 딕셔너리 조합 (UI 렌더링용) ---
    # 첫 번째 프로젝트에서 engineer_name 가져오기
    engineer_name = projects_df.iloc[0].get("engineer_name", "(AI 추출)")

    output = {
        "career_details": {
            "성명": engineer_name,  # AI가 추출한 실제 이름 사용
            "분야": projects_df.iloc[0].get("primary_original_field", "정보 없음"), # 첫 번째 프로젝트의 분야를 대표로 사용
            "현재까지 경력": total_career_str, # 환산 경력
            "평점": score_str,
            "total_score_months": total_score_months,
            "해당분야 용역참여실적": relevant_list,
            "해당분야 이외 참여실적": other_list,
            "classification_label": "✅ 해당 분야(100%) 및 ⚪ 비해당 분야(60%) 합산",
            "weight": weight # 마지막 프로젝트의 weight (참고용)
        },
        "job_field_details": {
            "책임건설사업관리기술인": engineer_name,  # 추출된 실제 이름 사용
            "직무분야": job_field_str,
            "현재까지 경력": job_career_str, # 실제 경력
            "평점": job_score_str,
            "total_job_months": job_total_months,
            "용역참여실적": all_project_records_str
        }
    }
    return output


def get_project_calculations_as_json(projects_df: pd.DataFrame, engineer_name: str = None) -> Dict[str, Any]:
    """
    프로젝트 데이터를 JSON 형식으로 변환 (API/파일 출력용)

    Expected JSON 구조에 맞춰 데이터를 포맷팅합니다.

    Args:
        projects_df: 프로젝트 DataFrame
        engineer_name: 기술인 성명 (선택사항)

    Returns:
        JSON 형식의 딕셔너리
    """
    if projects_df.empty:
        return {}

    # 기존 계산 로직 재사용
    total_score_days = 0
    total_job_days = 0
    relevant_list = []
    other_list = []
    all_roles = set()

    for _, project_series in projects_df.iterrows():
        start_date = project_series.get("start_date", "")
        end_date = project_series.get("end_date", "")
        project_name = project_series.get("project_name", "(사업명 없음)")
        client = project_series.get("client_raw", "(발주처 없음)")
        roles = project_series.get("roles", [])

        is_60_percent_rule = project_series.get("recognition_rate_rule") == "civil_60"
        weight = 0.6 if is_60_percent_rule else 1.0

        actual_days = _calculate_days(start_date, end_date)
        score_days = round(actual_days * weight)

        total_score_days += score_days
        total_job_days += actual_days
        all_roles.update(roles)

        # JSON 형식으로 프로젝트 기록 생성
        project_record = {
            "project_name": project_name,
            "client": client,
            "period": f"{start_date} ~ {end_date}",
            "days": f"{actual_days}일"
        }

        if is_60_percent_rule:
            other_list.append(project_record)
        else:
            relevant_list.append(project_record)

    # 계산
    total_score_months = _days_to_months(total_score_days)
    relevant_days = sum([_calculate_days(p.get("period", " ~ ").split(" ~ ")[0],
                                         p.get("period", " ~ ").split(" ~ ")[1])
                         for p in relevant_list])
    relevant_months = _days_to_months(relevant_days)

    other_days_raw = sum([_calculate_days(p.get("period", " ~ ").split(" ~ ")[0],
                                          p.get("period", " ~ ").split(" ~ ")[1])
                          for p in other_list])
    other_days_weighted = round(other_days_raw * 0.6)
    other_months = _days_to_months(other_days_weighted)

    score_raw = total_score_months * 0.176
    score = min(score_raw, 12.0)

    job_total_months = _days_to_months(total_job_days)
    job_field_str = ", ".join(sorted(list(all_roles)))
    is_broad_scope = len(all_roles) >= 5
    job_score_value = 6 if is_broad_scope else 3

    # 이름 결정
    name = engineer_name if engineer_name else projects_df.iloc[0].get("engineer_name", "(AI 추출)")
    field = projects_df.iloc[0].get("primary_original_field", "해당 분야")

    # JSON 구조 생성
    result = {
        "participating_engineer_career_history": {
            "title": "참여기술인 경력 사항",
            "division": "책임건설사업관리기술인",
            "name": name,
            "field": field,
            "relevant_field_career": _days_to_year_month_str(relevant_days),
            "total_career": _days_to_year_month_str(total_score_days),
            "total_score": f"{score:.0f}점",
            "total_days": f"{total_score_days:,}일",
            "total_months": f"{total_score_months}개월",
            "relevant_field_projects": relevant_list,
            "relevant_subtotal_days": f"{relevant_days}일",
            "relevant_subtotal_months": f"{relevant_months}개월",
            "other_field_projects": other_list,
            "other_subtotal_calculation": f"{other_days_raw}일 × 60% = {other_days_weighted}일",
            "other_subtotal_months": f"{other_months}개월"
        },
        "participating_engineer_job_field_history": {
            "title": "참여기술인 직무분야 실적",
            "engineer_name": name,
            "evaluation_1_6_points": {
                "division": "참여기술인",
                "name": name,
                "career": _days_to_year_month_str(total_job_days),
                "score": f"{job_score_value}점",
                "job_fields": job_field_str,
                "total_days": f"{total_job_days:,}일",
                "total_months": f"{job_total_months}개월",
                "projects": relevant_list + other_list  # 모든 프로젝트
            },
            "evaluation_2_3_points": {
                "division": "참여기술인",
                "name": name,
                "career": _days_to_year_month_str(total_job_days),
                "score": "3점",
                "job_fields": job_field_str,
                "total_days": f"{total_job_days:,}일",
                "total_months": f"{job_total_months}개월",
                "projects": relevant_list + other_list  # 모든 프로젝트
            }
        }
    }

    return result