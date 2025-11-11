# report_utils.py
from typing import Dict, Any, List
import pandas as pd
from rules_config import CHECKBOX_RULES

# ---- 1. Logical form layout (mirrors the paper form) ----
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