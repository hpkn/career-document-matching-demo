import streamlit as st
import pandas as pd
import uuid
from config import PDF_DIR, STEP1_INDEX_DIR
from ingest import ingest_step1_multiple, get_final_report_json, main_extractor, clear_pdfs, clear_index
from rag import get_step1_data
from report_utils import get_form_layout
from semantic_normalizer import normalize_project
from rules_engine import apply_all_checkbox_rules

st.set_page_config(page_title="Career Analysis Pipeline", layout="wide")
st.title("Construction Career Analysis (Analysis Engine)")

if 'step' not in st.session_state: st.session_state.step = 1
if 'step' not in st.session_state: st.session_state.step = 2
if 'step2_records' not in st.session_state: st.session_state.step2_records = []
if 'step1_norm_data' not in st.session_state: st.session_state.step1_norm_data = None
if 'step1_rules' not in st.session_state: st.session_state.step1_rules = None

def prev_step():
    st.session_state.step -= 1
    
def reset_app():
    st.session_state.step = 1
    st.session_state.step2_records = []
    st.session_state.step1_norm_data = None
    st.session_state.step1_rules = None

# --- STEP 1: Checkbox Guide (Native Text) ---
# --- STEP 1: Checkbox Guide ---
if st.session_state.step == 1:
    st.header("Step 1: 경력인정 적용 가이드 (자동 체크)")
    
    clear_pdfs()
    clear_index()
    uploaded_files = st.file_uploader("PDF 업로드", type=["pdf"], accept_multiple_files=True)
    
    if uploaded_files and st.button("자동체크 실행"):
        with st.spinner("Analyzing..."):
            PDF_DIR.mkdir(parents=True, exist_ok=True)
            saved_paths = []
            for f in uploaded_files:
                path = PDF_DIR / f"s1_{uuid.uuid4().hex}.pdf"
                with open(path, "wb") as out: out.write(f.read())
                saved_paths.append(str(path))

            if ingest_step1_multiple(saved_paths):
                # Use the function name requested
                query = "모든 프로젝트 이력을 하나의 JSON 객체로 종합"
                raw_data = get_step1_data(query)
                
                if raw_data:
                    norm = normalize_project(raw_data)
                    st.session_state.step1_norm_data = norm
                    
                    st.session_state.step1_rules = apply_all_checkbox_rules(norm)
                else:
                    st.error("데이터 추출 실패.")
            else:
                st.error("텍스트를 찾을 수 없습니다.")

    if st.session_state.step1_norm_data:
        norm = st.session_state.step1_norm_data
        rules = st.session_state.step1_rules
        layout = get_form_layout()

        st.info(f"**기술인:** {norm.get('engineer_name')} | **직무:** {norm.get('role')}")
        st.markdown("---")
        
        # RENDER LOOP
        for sec_key, section in layout.items():
            st.subheader(section.get("title", sec_key))
            
            if "questions" in section:
                for q_idx, question in enumerate(section["questions"]):
                    st.markdown(f"**{question['title']}**")
                    options = question.get("options", [])
                    cols = st.columns(4)
                    
                    for i, opt in enumerate(options):
                        rule_id = opt.get('rule_id') or opt.get('id')
                        rule_key = f"rule__{rule_id}"
                        is_checked = rules.get(rule_key, False)
                        widget_key = f"{sec_key}_{q_idx}_{i}_{rule_id}"
                        
                        cols[i % 4].checkbox(opt['label'], value=is_checked, key=widget_key, disabled=True)
                    st.markdown("")
            st.markdown("---")

        if st.button("다음 단계로 (Next)"):
            st.session_state.step = 2
            st.rerun()



# --- STEP 2: Hybrid Table Extraction (Direct OCR -> LLM) ---
# elif st.session_state.step == 2:

if st.session_state.step == 2:
    st.header("Step 2: 상세 경력 추출 (Page-by-Page)")
    uploaded_file = st.file_uploader("PDF 파일 업로드 (기술경력)", type=["pdf"], key="s2")
    
    if uploaded_file and st.button("경력 추출 실행"):
        with st.spinner("페이지별 데이터 추출 중..."):
            path = PDF_DIR / f"s2_{uuid.uuid4().hex}.pdf"
            with open(path, "wb") as f: f.write(uploaded_file.read())
            
            records = main_extractor(path)
            
            
            if records:
                st.session_state.step2_records = records
                if not records: st.warning("데이터를 찾을 수 없습니다.")
            else:
                st.error("OCR 실패.")

    if st.session_state.step2_records:
        st.success(f"추출된 데이터: {len(st.session_state.step2_records)}건")
        df = pd.DataFrame(st.session_state.step2_records)
        
        disp = pd.DataFrame()
        
        disp ['참여기간']= df.get('participation_period_start', '')+ "~" + df.get('participation_period_end', '')
        disp ['인정일']= df.get('recognized_days', '')
        disp ['참여일']= df.get('participated_days', '')
        disp ['사업명']= df.get('project_name', '')
        disp ['발주자']= df.get('client', '')
        disp ['공사종류']= df.get('project_type', '')
        disp ['공사(용역)개요']= df.get('project_overview', '')
        disp ['적용공법']= df.get('applied_method', '')
        disp ['적용_융_복합건설기술']= df.get('applied_convergence_tech', '')
        disp ['직무분야']= df.get('job_field', '')
        disp ['전문분야']= df.get('specialty_field', '')
        disp ['책임정도']= df.get('responsibility_level', '')
        disp ['적용신기술']= df.get('applied_new_tech', '')
        disp ['담당업무']= df.get('assigned_task', '')
        disp ['직위']= df.get('position', '')
        disp ['공사(용역)금액(백만원)']= df.get('project_amount_million_won', '')
        disp ['시설물종류']= df.get('facility_type', '')
        disp ['성명'] = df.get('person_name', '')
        # disp ['']= df.get('page_number', '')
        # disp ['']= df.get('entry_number', '')
        
        # def calc_confidence(row):
        #     score = 1.0
        #     if not row.get('project_name'): score -= 0.3
        #     if not row.get('start_date'): score -= 0.3
        #     if not row.get('client'): score -= 0.2
        #     return f"{max(0, score):.1f}"
            
        # disp['confidence'] = df.apply(calc_confidence, axis=1)
        
        st.dataframe(disp, use_container_width=True)

        if st.button("Next → Step 3"):
            st.session_state.step = 3
            st.rerun()
            
    if st.button("Back"):
        st.session_state.step = 1
        st.rerun()



# --- STEP 3 ---
# ... (Imports and setup) ...

# --- STEP 3 ---
elif st.session_state.step == 3:
    st.header("Step 3: 최종 평가 리포트 (사업수행능력평가)")
    
    report = get_final_report_json(st.session_state.step2_records)
    
    if report:
        career = report.get('career_history', {})
        h = career.get('header', {})
        
        st.subheader(f"📋 {h.get('division', '평가 결과')} | {h.get('name', '')}")
        
        # Top Level Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("성명", h.get('name', '-'))
        c2.metric("주 직무분야", h.get('field', '-'))
        c3.metric("환산 경력", h.get('total_career', '-'))
        c4.metric("종합 평점", h.get('score', '-'))
        
        # Detailed Score Breakdown
        details = h.get('details', {})
        st.info(f"**점수 상세:** 해당분야 경력 {details.get('exp_score', '-')} + 직무분야 실적 {details.get('job_score', '-')}")
        
        st.divider()
        
        # Project Tables
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### ✅ 해당분야 (100%)")
            if career.get('relevant'):
                st.dataframe(pd.DataFrame(career['relevant']), hide_index=True, use_container_width=True)
            else:
                st.caption("실적 없음")
        with c2:
            st.markdown("### ⚪ 기타 (60%)")
            if career.get('other'):
                st.dataframe(pd.DataFrame(career['other']), hide_index=True, use_container_width=True)
            else:
                st.caption("실적 없음")

    if st.button("처음으로 (Restart)"):
        reset_app()
        st.rerun()
    
    st.button("← Back", on_click=prev_step)
    # Back button is handled in the sidebar or main flow usually, but can be added here
    # if st.button("← Back"): 
    #     st.session_state.step = 2
    #     st.rerun()