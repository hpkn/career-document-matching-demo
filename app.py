import streamlit as st
import pandas as pd
import uuid
import re
from config import PDF_DIR, STEP1_INDEX_DIR
from ingest import ingest_step1_multiple, get_final_report_json, get_final_report_with_llm, main_extractor, clear_pdfs, clear_index
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
if 'step3_report' not in st.session_state: st.session_state.step3_report = None

def prev_step():
    st.session_state.step -= 1
    # Clear Step 3 cache when going back so it regenerates with new data
    st.session_state.step3_report = None

def reset_app():
    st.session_state.step = 1
    st.session_state.step2_records = []
    st.session_state.step1_norm_data = None
    st.session_state.step1_rules = None
    st.session_state.step3_report = None

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
        
        # RENDER LOOP - Editable checkboxes
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
                        widget_key = f"{sec_key}_{q_idx}_{i}_{rule_id}"

                        # Get current value - prefer widget state, fallback to rules
                        if widget_key in st.session_state:
                            current_value = st.session_state[widget_key]
                        else:
                            current_value = rules.get(rule_key, False)

                        # Editable checkbox
                        new_value = cols[i % 4].checkbox(opt['label'], value=current_value, key=widget_key)
                        # Always sync to step1_rules
                        st.session_state.step1_rules[rule_key] = new_value
                    st.markdown("")
            st.markdown("---")

        # Next button on the right
        col_left, col_right = st.columns([4, 1])
        with col_right:
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

    # Back on left, Next on right
    col_left, col_right = st.columns([1, 1])
    with col_left:
        if st.button("← Back", key="step2_back"):
            st.session_state.step = 1
            st.rerun()
    with col_right:
        if st.session_state.step2_records:
            if st.button("Next → Step 3", key="step2_next"):
                st.session_state.step = 3
                st.rerun()



# --- STEP 3 ---
# ... (Imports and setup) ...

# --- STEP 3 ---
elif st.session_state.step == 3:
    st.header("Step 3: 최종 평가 리포트 (사업수행능력평가)")

    # Use cached report if available (avoids re-running LLM on every interaction)
    if st.session_state.step3_report is None:
        # Use LLM-based report generation with Step 1 rules filtering
        step1_rules_raw = st.session_state.step1_rules
        step2_records = st.session_state.step2_records or []

        # Convert step1_rules to dict if it's a pandas Series or other type
        if step1_rules_raw is None:
            step1_rules = {}
        elif hasattr(step1_rules_raw, 'to_dict'):
            step1_rules = step1_rules_raw.to_dict()
        elif isinstance(step1_rules_raw, dict):
            step1_rules = step1_rules_raw
        else:
            step1_rules = {}

        # Convert CareerEntry objects to dicts if needed
        step2_data = []
        for record in step2_records:
            if hasattr(record, 'to_dict'):
                step2_data.append(record.to_dict())
            elif isinstance(record, dict):
                step2_data.append(record)

        # Use LLM function if we have step1 rules with any True values, otherwise fallback to default
        has_checked_rules = bool(step1_rules) and any(v for v in step1_rules.values() if v is True)

        if has_checked_rules:
            with st.spinner("LLM으로 평가 리포트 생성 중..."):
                st.session_state.step3_report = get_final_report_with_llm(step1_rules, step2_data)
        else:
            st.session_state.step3_report = get_final_report_json(step2_data)

    report = st.session_state.step3_report
    
    if report:
        career = report.get('career_history', {})
        h = career.get('header', {})

        st.subheader(f"📋 {h.get('division', '평가 결과')} | {h.get('name', '')}")

        # Top Level Metrics (removed 환산 경력 and 종합 평점)
        summary = h.get('summary', {})

        # Calculate total 인정일수 for 해당분야
        relevant_total_days = 0
        if career.get('relevant'):
            for proj in career['relevant']:
                days_str = str(proj.get('인정일수', '0'))
                # Extract numeric value from string like "365일"
                match = re.search(r'(\d+)', days_str.replace(',', ''))
                if match:
                    relevant_total_days += int(match.group(1))

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("성명", h.get('name', '-'))
        c2.metric("주 직무분야", h.get('field', '-'))
        c3.metric("해당분야 건수", summary.get('relevant_count', 0))
        c4.metric("경력기간 (인정일)", f"{relevant_total_days:,}일")
        c5.metric("기타 건수", summary.get('other_count', 0))

        st.divider()

        # Display Applied Filter Conditions
        st.markdown("### 경력 인정 기준")

        filter_conditions = h.get('filter_conditions', {})
        applied_rules = h.get('applied_rules', [])

        if filter_conditions or applied_rules:
            # Show filter conditions in a structured way (공종, 담당업무, 직무분야)
            filter_cols = st.columns(3)

            with filter_cols[0]:
                if filter_conditions.get('construction_types'):
                    st.markdown(f"**공종:** {', '.join(filter_conditions['construction_types'])}")
                else:
                    st.markdown("**공종:** -")

            with filter_cols[1]:
                if filter_conditions.get('roles'):
                    roles_display = ', '.join(filter_conditions['roles'][:5])
                    if len(filter_conditions.get('roles', [])) > 5:
                        roles_display += '...'
                    if filter_conditions.get('include_blank_duty'):
                        roles_display += " (빈칸 허용)"
                    st.markdown(f"**담당업무:** {roles_display}")
                else:
                    st.markdown("**담당업무:** -")

            with filter_cols[2]:
                if filter_conditions.get('job_fields'):
                    st.markdown(f"**직무분야:** {', '.join(filter_conditions['job_fields'])}")
                else:
                    st.markdown("**직무분야:** -")

            # Show applied rules summary
            if applied_rules:
                with st.expander("적용된 규칙 상세 보기", expanded=False):
                    for rule in applied_rules[:20]:  # Limit to 20 rules
                        st.markdown(f"- {rule}")
                    if len(applied_rules) > 20:
                        st.caption(f"... 외 {len(applied_rules) - 20}개")
        else:
            st.info("필터 조건이 적용되지 않았습니다. 모든 프로젝트가 '기타'로 분류됩니다.")

        # Data Breakdown Section
        breakdown = report.get('data_breakdown', {})
        if breakdown:
            with st.expander("📊 데이터 분석 (Step 2 원본 데이터)", expanded=False):
                st.caption(f"총 {breakdown.get('total_records', 0)}건의 경력 데이터")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("**공종 분포:**")
                    pt_data = breakdown.get('project_type', {})
                    if pt_data:
                        for val, count in sorted(pt_data.items(), key=lambda x: -x[1])[:10]:
                            st.caption(f"• {val}: {count}건")
                        if len(pt_data) > 10:
                            st.caption(f"  ... 외 {len(pt_data) - 10}개")
                    else:
                        st.caption("데이터 없음")

                with col2:
                    st.markdown("**담당업무 분포:**")
                    at_data = breakdown.get('assigned_task', {})
                    if at_data:
                        for val, count in sorted(at_data.items(), key=lambda x: -x[1])[:10]:
                            st.caption(f"• {val}: {count}건")
                        if len(at_data) > 10:
                            st.caption(f"  ... 외 {len(at_data) - 10}개")
                    else:
                        st.caption("데이터 없음")

                with col3:
                    st.markdown("**직무분야 분포:**")
                    jf_data = breakdown.get('job_field', {})
                    if jf_data:
                        for val, count in sorted(jf_data.items(), key=lambda x: -x[1])[:10]:
                            st.caption(f"• {val}: {count}건")
                        if len(jf_data) > 10:
                            st.caption(f"  ... 외 {len(jf_data) - 10}개")
                    else:
                        st.caption("데이터 없음")

        st.divider()

        # Project Tables
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"### ✅ 해당분야 ({summary.get('relevant_count', 0)}건)")
            if career.get('relevant'):
                st.dataframe(pd.DataFrame(career['relevant']), hide_index=True, use_container_width=True)
            else:
                st.caption("실적 없음")
        with c2:
            st.markdown(f"### ⚪ 기타 ({summary.get('other_count', 0)}건)")
            if career.get('other'):
                st.dataframe(pd.DataFrame(career['other']), hide_index=True, use_container_width=True)
            else:
                st.caption("실적 없음")

    # Back on left, Restart on right
    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.button("← Back", on_click=prev_step, key="step3_back")
    with col_right:
        if st.button("처음으로 (Restart)", key="step3_restart"):
            reset_app()
            st.rerun()