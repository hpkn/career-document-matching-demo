# ============================================================
# STEP 3 – Official Technical Career Evaluation Engine
# Rewritten to match 1.최연식_form.pdf exactly
# ============================================================

import pandas as pd
from datetime import datetime
from rules_config import CHECKBOX_RULES
from typing import Dict, Any, List
import re 




# --------------------------------------------
# Utility: date difference
# --------------------------------------------
def _diff_days(start, end):
    try:
        s = pd.to_datetime(start)
        e = pd.to_datetime(end)
        d = (e - s).days + 1
        return max(d, 0)
    except:
        return 0


# --------------------------------------------
# Official "해당분야" classifier
# --------------------------------------------
def classify_domain(row):
    txt = f"{row['사업명']} {row['공사종류']} {row['직무분야']}".lower()

    domain_keywords = [
        "단지조성", "단지", "도로", "교량", "일반교량",
        "공항", "하천", "하천정비", "토목"
    ]

    if any(k in txt for k in domain_keywords):
        return "해당"  # 100%
    return "비해당"  # 60%


# --------------------------------------------
# Official 직무분야 classifier
# --------------------------------------------
def classify_job_domain(row):
    txt = f"{row['사업명']} {row['담당업무']}".lower()

    job_keywords = ["감리", "건설사업관리", "감독"]

    if any(k in txt for k in job_keywords):
        return True
    return False


# --------------------------------------------
# Official scoring function
# --------------------------------------------
def score_by_months(months):
    if months >= 180: return 6
    if months >= 150: return 5
    if months >= 120: return 4
    if months >= 90:  return 3
    if months >= 60:  return 2
    return 1


# ============================================================
# MAIN FUNCTION — Step 3 Evaluation
# ============================================================
def evaluate_step3(df_step2):
    """
    Stable Step 3 evaluation – ALWAYS returns summary/domain_table/job_table.
    Prevents KeyError when Step 2 extraction has missing or unusual fields.
    """

    # -------------------------------------------
    # 0) If df invalid → return empty evaluation
    # -------------------------------------------
    if df_step2 is None or df_step2.empty:
        return {
            "summary": {
                "해당_일수": 0,
                "해당_개월": 0,
                "비해당_일수": 0,
                "비해당_60%_일수": 0,
                "비해당_개월": 0,
                "총합계_일수": 0,
                "총합계_개월": 0,
                "평점": 0,
                "직무_일수": 0,
                "직무_개월": 0,
                "직무_평점": 0,
            },
            "domain_table": pd.DataFrame(),
            "job_table": pd.DataFrame(),
        }

    df = df_step2.copy()

    # -------------------------------------------
    # 1) Ensure required columns exist
    # -------------------------------------------
    for col in ["사업명", "발주기관", "start_date", "end_date", "참여일수"]:
        if col not in df.columns:
            df[col] = ""

    # -------------------------------------------
    # 2) Convert dates to real days
    # -------------------------------------------
    def _safe_days(start, end):
        try:
            s = pd.to_datetime(start)
            e = pd.to_datetime(end)
            if pd.isna(s) or pd.isna(e):
                return 0
            return max((e - s).days + 1, 0)
        except:
            return 0

    df["days"] = df.apply(lambda r: _safe_days(r["start_date"], r["end_date"]), axis=1)

    # -------------------------------------------
    # 3) Classify domain
    # -------------------------------------------
    def classify_domain(row):
        name = str(row["사업명"])
        if any(k in name for k in ["감리", "건설사업관리", "감독"]):
            return "해당"
        return "비해당"

    df["domain"] = df.apply(classify_domain, axis=1)

    해당_df = df[df["domain"] == "해당"]
    비해당_df = df[df["domain"] == "비해당"]

    # -------------------------------------------
    # 4) Summaries
    # -------------------------------------------
    해당_total_days = int(해당_df["days"].sum())
    비해당_total_days = int(비해당_df["days"].sum())
    비해당_weighted_days = int(비해당_total_days * 0.6)
    total_days = 해당_total_days + 비해당_weighted_days

    total_months = total_days // 30
    해당_months = 해당_total_days // 30
    비해당_months = 비해당_weighted_days // 30

    # -------------------------------------------
    # 5) 평점 규칙 (simple version)
    # -------------------------------------------
    if total_months >= 180: score = 6
    elif total_months >= 150: score = 5
    elif total_months >= 120: score = 4
    elif total_months >= 90:  score = 3
    elif total_months >= 60:  score = 2
    else: score = 1

    # 직무분야 평가
    job_df = df[df["사업명"].str.contains("감리|건설사업관리|감독", na=False)].copy()
    job_total_days = int(job_df["days"].sum())
    job_total_months = job_total_days // 30

    if job_total_months >= 180: job_score = 6
    elif job_total_months >= 150: job_score = 5
    elif job_total_months >= 120: job_score = 4
    elif job_total_months >= 90:  job_score = 3
    elif job_total_months >= 60:  job_score = 2
    else: job_score = 1

    # -------------------------------------------
    # 6) DOMAIN TABLE (matching printed PDF)
    # -------------------------------------------
    domain_table = pd.DataFrame({
        "용역명": df["사업명"],
        "발주기관": df["발주기관"],
        "참여기간": df["start_date"] + "~" + df["end_date"],
        "일수": df["days"],
        "분류": df["domain"],
    })

    # -------------------------------------------
    # 7) Final Summary
    # -------------------------------------------
    summary = {
        "해당_일수": 해당_total_days,
        "해당_개월": 해당_months,
        "비해당_일수": 비해당_total_days,
        "비해당_60%_일수": 비해당_weighted_days,
        "비해당_개월": 비해당_months,
        "총합계_일수": total_days,
        "총합계_개월": total_months,
        "평점": score,
        "직무_일수": job_total_days,
        "직무_개월": job_total_months,
        "직무_평점": job_score,
    }

    return {
        "summary": summary,
        "domain_table": domain_table,
        "job_table": job_df,
    }



def classify_for_checkboxes(df):
    """
    Reads df extracted from OCR and determines:
    - 공종(Domain)
    - 발주처 유형
    - 담당업무
    - 직무분야
    """

    combined = " ".join(df["사업명"].fillna("").astype(str)) + " " + \
                " ".join(df["발주기관"].fillna("").astype(str))

    result = {
        "도로": any(k in combined for k in ["도로", "국도", "지방도", "고속도로"]),
        "하천": any(k in combined for k in ["하천", "하천정비", "재해지구"]),
        "상수도": any(k in combined for k in ["상수", "정수장", "배수관"]),
        "하수도": any(k in combined for k in ["하수", "처리장", "오수"]),
        "철도": any(k in combined for k in ["철도", "지하철", "궤도"]),
        "단지": any(k in combined for k in ["단지조성", "택지", "부지조성"]),
        "항만": any(k in combined for k in ["항만", "안벽", "방파제"]),
        "조경": any(k in combined for k in ["공원", "조경"]),
        "공항": any(k in combined for k in ["공항"]),

        # 발주처 자동 판단
        "발주처_제조항": any(k in combined for k in [
            "국토관리청", "국토교통부", "국가", "정부", "한국도로공사"
        ]),
        "발주처_민간": any(k in combined for k in ["주식회사", "(주)"]),

        # 담당업무
        "감리": any(k in combined for k in ["감리", "책임감리"]),
        "건설사업관리": any(k in combined for k in ["건설사업관리"]),
        "시공": any(k in combined for k in ["시공"]),
        "설계": any(k in combined for k in ["설계"]),
    }

    return result



# # ---- 1. FORM STRUCTURE (Matches your provided structure) ----
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
    """Returns the form layout dictionary."""
    return FORM_LAYOUT

def group_rules_by_category():
    """Groups validation rules by category."""
    grouped = {}
    for r in CHECKBOX_RULES:
        cat = r.get("category", "기타")
        grp = r.get("group", "기타")
        grouped.setdefault(cat, {})
        grouped[cat].setdefault(grp, [])
        grouped[cat][grp].append(r)
    return grouped

# --- Calculation Helper Functions ---


