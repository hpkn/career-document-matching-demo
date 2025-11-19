# app.py

import os
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any
import streamlit as st
import pandas as pd
from config import PDF_DIR, DATA_DIR, INDEX_DIR
from ingest import build_index, find_tech_page, ocr_page
from rag import get_raw_project_data, extract_tech_data_from_ocr
from semantic_normalizer import normalize_project, normalize_tech_data_df
from rules_engine import apply_all_checkbox_rules
from report_utils import (
    group_rules_by_category,
    build_project_summary_text,
    get_form_layout,
    get_project_calculations_as_json
)

# --- Session State Initialization ---------------------------------
# This is the core of the new 3-step logic
if "step" not in st.session_state:
    st.session_state.step = 1
if "rudf_file_processed" not in st.session_state:
    st.session_state.rudf_file_processed = False
if "rudf_projects_df" not in st.session_state:
    st.session_state.rudf_projects_df = None
if "tech_file_path" not in st.session_state:
    st.session_state.tech_file_path = None
if "tech_projects_df" not in st.session_state:
    st.session_state.tech_projects_df = None
if "final_projects_df" not in st.session_state:
    st.session_state.final_projects_df = None
if "run_id" not in st.session_state:
    st.session_state.run_id = str(uuid.uuid4()) # Used to create unique index folders per run

st.set_page_config(page_title="경력인정 자동완성 데모", layout="wide")
st.title("경력인정 자동완성 Demo")

# --- Helper Functions -------------------------------------------
def reset_session():
    """Resets the entire session state to start over."""
    st.session_state.step = 1
    st.session_state.rudf_file_processed = False
    st.session_state.rudf_projects_df = None
    st.session_state.tech_file_path = None
    st.session_state.tech_projects_df = None
    st.session_state.final_projects_df = None
    st.session_state.run_id = str(uuid.uuid4())
    # We don't clear the data/pdfs or index here, as a new run_id creates a new path

# --- Main App UI --------------------------------------------------

# Use columns for layout
col1, col2 = st.columns([1, 2])

# --- [COLUMN 1] - Sidebar / Control Panel ---
with col1:
    st.header("처리 단계")
    if st.button(" 처음부터 다시 시작 (Reset)"):
        reset_session()
        st.experimental_rerun()

    # --- STEP 1: RUDF Upload (NO OCR) -----------------------------
    with st.expander("Step 1: RUDF 파일 업로드 (OCR 없음)", expanded=(st.session_state.step == 1)):
        st.markdown("""
        메인 경력 증명서 파일을 업로드합니다.
        이 단계는 **OCR을 사용하지 않고** 텍스트를 추출하여 **'결과 1'** (체크박스 가이드)을 생성합니다.
        """)
        
        uploaded_rudf_file = st.file_uploader(
            "RUDF 파일 (경력 증명서)",
            type=["pdf"],
            accept_multiple_files=False,
            key="rudf_uploader"
        )

        if uploaded_rudf_file and not st.session_state.rudf_file_processed:
            with st.spinner("Step 1: RUDF 파일을 처리하고 AI 메모리 생성 중 (OCR 없음)..."):
                
                # Create a unique index path for this run
                index_folder_name = f"faiss_index_rudf_{st.session_state.run_id}"
                
                # Save the file
                file_ext = Path(uploaded_rudf_file.name).suffix
                save_name = f"{uuid.uuid4().hex}{file_ext}"
                save_path = PDF_DIR / save_name
                with open(save_path, "wb") as f:
                    f.write(uploaded_rudf_file.read())
                
                file_map = {save_name: uploaded_rudf_file.name}

                # Build FAISS index *without* OCR
                build_index(file_map, index_folder_name, use_ocr=False)

                # Run RAG to get data for '결과 1'
                query = "기술경력 및 건설사업관리 경력 테이블에서 모든 프로젝트 추출"
                raw_project_data = get_raw_project_data(query, top_k=50, index_folder_name=index_folder_name)

                if raw_project_data:
                    # Normalize and apply rules
                    all_projects_rules = []
                    for raw_project in raw_project_data:
                        normalized_project = normalize_project(raw_project) # Use original normalize
                        project_rules_series = apply_all_checkbox_rules(normalized_project)
                        all_projects_rules.append(project_rules_series)
                    
                    st.session_state.rudf_projects_df = pd.DataFrame(all_projects_rules)
                    st.session_state.rudf_file_processed = True
                    st.session_state.step = 2
                    st.experimental_rerun()
                else:
                    st.error("RUDF 파일에서 프로젝트 데이터를 추출하지 못했습니다.")

    # --- STEP 2: 기술경력 Upload (WITH OCR) -----------------------
    with st.expander("Step 2: 기술경력 파일 업로드 (OCR)", expanded=(st.session_state.step == 2)):
        st.markdown("""
        '1. 기술경력' 테이블이 포함된 상세 PDF 파일을 업로드합니다.
        이 단계는 해당 페이지만 **OCR로 처리**하여 프로젝트 목록을 추출합니다.
        """)
        
        uploaded_tech_file = st.file_uploader(
            "'1. 기술경력' PDF 파일",
            type=["pdf"],
            accept_multiple_files=False,
            key="tech_uploader"
        )
        
        if uploaded_tech_file:
            with st.spinner("Step 2: '1. 기술경력' 페이지를 찾아 OCR로 처리하는 중..."):
                # Save the file
                file_ext = Path(uploaded_tech_file.name).suffix
                save_name = f"{uuid.uuid4().hex}{file_ext}"
                save_path = PDF_DIR / save_name
                with open(save_path, "wb") as f:
                    f.write(uploaded_tech_file.read())
                
                st.session_state.tech_file_path = str(save_path)

                # 1. Find the target page
                page_num = find_tech_page(st.session_state.tech_file_path)
                
                # 2. OCR only that page
                ocr_text = ocr_page(st.session_state.tech_file_path, page_num)
                
                # 3. Extract data from the OCR'd text
                raw_tech_data = extract_tech_data_from_ocr(ocr_text)

                if raw_tech_data:
                    # Convert to DataFrame and store in session state
                    df = pd.DataFrame(raw_tech_data)
                    
                    # Rename columns to match the user's requested table headers
                    column_map = {
                        "start_date": "참여기간 (시작일)",
                        "end_date": "참여기간 (종료일)",
                        "recognition_days": "인정일",
                        "project_name": "사업명",
                        "job_field": "직무분야",
                        "role": "담당업무",
                        "client": "발주자 | 공사종류",
                        "position": "직위"
                    }
                    df_display = df.rename(columns=column_map)
                    
                    # Ensure all requested columns are present
                    display_headers = ["참여기간 (시작일)", "참여기간 (종료일)", "인정일", "사업명", "직무분야", "담당업무", "발주자 | 공사종류", "직위"]
                    for col in display_headers:
                        if col not in df_display.columns:
                            df_display[col] = "N/A"
                    
                    st.session_state.tech_projects_df = df[column_map.keys()] # Store with original keys
                    st.session_state.step = 3
                    st.experimental_rerun()
                else:
                    st.error("'1. 기술경력' 테이블에서 데이터를 추출하지 못했습니다.")

# --- [COLUMN 2] - Main Display Area ---
with col2:
    if st.session_state.step == 1:
        st.info("Step 1: 좌측에서 RUDF 파일을 업로드하세요.")
    
    # --- Display for Step 1 Results / Step 2 Prompt ---
    if st.session_state.step >= 2:
        st.header("결과 1: 경력인정 가이드 자동 체크 (RUDF 기준)")
        st.caption(f"총 {len(st.session_state.rudf_projects_df)}개의 프로젝트가 RUDF 파일에서 추출되었습니다. 아래는 첫 번째 프로젝트의 자동 체크 결과입니다.")
        
        # Render Checkbox Guide (same as your old code)
        project_rules_series = st.session_state.rudf_projects_df.iloc[0]
        form_layout = get_form_layout()
        grouped_rules = group_rules_by_category()
        
        def render_checkbox_row(checked: bool, label: str) -> str:
            box = "☑" if checked else "☐"
            return f"{box} {label}"

        st.markdown("---")
        for section_key, section in form_layout.items():
            st.markdown(f"#### 🧾 {section['title']}")
            for q in section["questions"]:
                st.markdown(f"**{q['title']}**")
                options = q["options"]
                num_cols = min(len(options), 4)
                cols = st.columns(num_cols)
                for i, opt in enumerate(options):
                    col = cols[i % num_cols]
                    rid = opt["rule_id"]
                    col_name = f"rule__{rid}"
                    checked = bool(project_rules_series.get(col_name, False))
                    with col:
                        st.markdown(render_checkbox_row(checked, opt["label"]))
                st.markdown("")
        
        st.markdown("---")
        if st.session_state.step == 2:
            st.info("Step 2: 좌측에서 '1. 기술경력' PDF 파일을 업로드하세요.")
            
    # --- Display for Step 2 Results / Step 3 Prompt ---
    if st.session_state.step == 3:
        st.header("Step 2: OCR 추출 결과 (기술경력)")
        st.caption("'1. 기술경력' 페이지에서 OCR로 추출된 데이터입니다.")
        
        # Display the table with the requested headers
        df_display = st.session_state.tech_projects_df.rename(columns={
            "start_date": "참여기간 (시작일)",
            "end_date": "참여기간 (종료일)",
            "recognition_days": "인정일",
            "project_name": "사업명",
            "job_field": "직무분야",
            "role": "담당업무",
            "client": "발주자 | 공사종류",
            "position": "직위"
        })
        st.dataframe(df_display)
        
        if st.button("Step 3: 최종 산출물 생성"):
            with st.spinner("Step 3: 최종 산출물을 생성하는 중..."):
                # Normalize the data from STEP 2
                st.session_state.final_projects_df = normalize_tech_data_df(st.session_state.tech_projects_df)
                st.session_state.step = 4 # Move to final step
                st.experimental_rerun()
                
    # --- Display for Step 3 Results ---
    if st.session_state.step == 4:
        st.header("Step 3: 최종 산출물 (Form 포맷)")
        st.caption("Step 2에서 추출된 데이터를 기반으로 최종 리포트를 생성했습니다.")
        
        try:
            # Generate the final JSON report using the Step 2 data
            json_data = get_project_calculations_as_json(st.session_state.final_projects_df)
            
            career_history = json_data.get("participating_engineer_career_history", {})
            job_history = json_data.get("participating_engineer_job_field_history", {})

            # --- 1. 참여기술인 경력 사항 (Render Final Report) ---
            st.subheader("📋 " + career_history.get("title", "참여기술인 경력 사항"))

            header = career_history.get("header", {})
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("구분", header.get("division", ""))
            col2.metric("성명", header.get("name", ""))
            col3.metric("분야", header.get("field", ""))
            col4.metric("현재까지 경력", header.get("total_career", ""))
            col5.metric("평점", header.get("score", ""))

            st.markdown("---")

            # Relevant field (100%)
            relevant_section = career_history.get("relevant_field_section", {})
            st.markdown(f"### ✅ {relevant_section.get('section_title', '해당분야')} ({relevant_section.get('career_period', '')})")
            relevant_projects = relevant_section.get("projects", [])
            if relevant_projects:
                st.dataframe(pd.DataFrame(relevant_projects), use_container_width=True, hide_index=True)
                subtotal = relevant_section.get("subtotal", {})
                st.caption(f"**{subtotal.get('text', '소계')}**: {subtotal.get('calculation', '')}")
            else:
                st.info("해당 분야 실적이 없습니다.")

            st.markdown("---")

            # Other field (60%)
            other_section = career_history.get("other_field_section", {})
            st.markdown(f"### ⚪ {other_section.get('section_title', '해당분야 이외')} ({other_section.get('career_period', '')})")
            other_projects = other_section.get("projects", [])
            if other_projects:
                st.dataframe(pd.DataFrame(other_projects), use_container_width=True, hide_index=True)
                subtotal = other_section.get("subtotal", {})
                st.caption(f"**{subtotal.get('text', '소계')}**: {subtotal.get('calculation', '')}")
            else:
                st.info("해당 분야 이외 실적이 없습니다.")

            st.markdown("---")

            # Total
            total = career_history.get("total", {})
            st.markdown(f"### 📊 {total.get('text', '합계')}")
            col1, col2 = st.columns(2)
            col1.metric("총 경력", total.get("career", ""))
            col2.metric("계산", total.get("calculation", ""))

            # --- 2. 참여기술인 직무분야 실적 ---
            st.markdown("---")
            st.subheader("📋 " + job_history.get("title", "참여기술인 직무분야 실적"))
            st.caption(job_history.get("subtitle", ""))

            # Evaluation 1
            eval1 = job_history.get("evaluation_1", {})
            eval1_header = eval1.get("header", {})
            st.markdown(f"### 평가 1 ({eval1_header.get('score', '6점')})")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("구분", eval1_header.get("division", ""))
            c2.metric("성명", eval1_header.get("name", ""))
            c3.metric("현재까지 경력", eval1_header.get("total_career", ""))
            c4.metric("평점", eval1_header.get("score", ""))
            st.markdown(f"**직무분야**: {eval1_header.get('job_fields', '')}")
            eval1_projects = eval1.get("projects", [])
            if eval1_projects:
                st.dataframe(pd.DataFrame(eval1_projects), use_container_width=True, hide_index=True)
                total1 = eval1.get("total", {})
                st.caption(f"**{total1.get('text', '계')}**: {total1.get('calculation', '')}")

            st.markdown("---")

            # Evaluation 2
            eval2 = job_history.get("evaluation_2", {})
            eval2_header = eval2.get("header", {})
            st.markdown(f"### 평가 2 ({eval2_header.get('score', '3점')})")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("구분", eval2_header.get("division", ""))
            c2.metric("성명", eval2_header.get("name", ""))
            c3.metric("현재까지 경력", eval2_header.get("total_career", ""))
            c4.metric("평점", eval2_header.get("score", ""))
            st.markdown(f"**직무분야**: {eval2_header.get('job_fields', '')}")
            st.caption("※ 설계 제외")
            eval2_projects = eval2.get("projects", [])
            if eval2_projects:
                st.dataframe(pd.DataFrame(eval2_projects), use_container_width=True, hide_index=True)
                total2 = eval2.get("total", {})
                st.caption(f"**{total2.get('text', '계')}**: {total2.get('calculation', '')}")

            # --- 3. JSON Download Button ---
            st.markdown("---")
            st.subheader("📥 JSON 다운로드")
            json_string = json.dumps(json_data, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 경력 사항 JSON 다운로드",
                data=json_string,
                file_name="경력인정_결과.json",
                mime="application/json",
            )
            with st.expander("JSON 미리보기"):
                st.json(json_data)

        except Exception as e:
            st.error(f"최종 산출물 생성 중 오류 발생: {e}")
            import traceback
            st.error(traceback.format_exc())