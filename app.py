# app.py
import os
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any
import streamlit as st
import pandas as pd
from config import PDF_DIR, DATA_DIR # DATA_DIR 추가
from ingest import build_index, clear_pdfs, clear_index # clear_index 임포트
from rag import get_raw_project_data
from semantic_normalizer import normalize_project
from rules_engine import apply_all_checkbox_rules
from report_utils import group_rules_by_category, build_project_summary_text, get_form_layout


st.set_page_config(page_title="경력인정 자동완성 데모", layout="wide")

st.title("경력인정 자동완성 Demo")

st.markdown("""
이 데모는 **업무 관련 PDF 파일**을 기반으로 프로젝트 경력을 추출하고,  
경력인정 가이드에 따라 **자동으로 체크박스를 판단**해 주는 시스템의 프로토타입입니다.

- 좌측: 파일 업로드 및 분석
- 우측: AI 추출 결과와 자동 체크 결과 요약
""")


# --- Sidebar: file upload & ingest ---------------------------------
st.sidebar.header("1. 분석할 파일 업로드")
st.sidebar.caption("여기에 프로젝트 파일(계약서, 공고 등)을 업로드하세요. 업로드 즉시 AI 메모리가 생성됩니다.")

uploaded_files = st.sidebar.file_uploader(
    "파일 업로드 (이전 파일은 삭제됩니다)",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

# This block now cleans, saves, AND builds the index all at once.
if uploaded_files:
    saved_files_map = {} # UUID와 원본 이름을 매핑할 딕셔너리
    with st.spinner("파일을 처리하고 AI 메모리를 생성하는 중..."):
        
        # 1. Clear all old PDFs AND the old index
        clear_pdfs()
        clear_index() # 인덱스도 함께 삭제
        
        # 2. Save new files with UUID names
        for f in uploaded_files:
            original_name = f.name
            file_extension = Path(original_name).suffix
            
            # --- FIX: Create a short, unique filename ---
            safe_name = f"{uuid.uuid4().hex}{file_extension}"
            save_path = PDF_DIR / safe_name
            
            with open(save_path, "wb") as out:
                out.write(f.read())
            
            saved_files_map[safe_name] = original_name # 맵에 저장
        
        # 3. Save the name map for the ingest script
        map_save_path = DATA_DIR / "uuid_name_map.json"
        with open(map_save_path, "w", encoding="utf-8") as f_map:
            json.dump(saved_files_map, f_map, ensure_ascii=False, indent=2)
            
        # 4. Build new index immediately
        build_index()
    
    st.sidebar.success(f"{len(saved_files_map)}개 파일로 AI 메모리 생성 완료.")
    st.sidebar.info("이제 '분석 실행' 버튼을 누르세요.")


# This button is now combined in the uploader
# if st.sidebar.button("인덱스 다시 만들기 (FAISS 재구성)"):
#     with st.spinner("PDF를 읽고 인덱스를 생성 중입니다..."):
#         build_index()
#     st.sidebar.success("인덱스 재구성이 완료되었습니다.")


st.sidebar.header("2. 분석 실행")
st.sidebar.caption("업로드된 파일의 내용을 종합하여 양식을 채웁니다.")

run_button = st.sidebar.button("✔️ 양식 자동 채우기 실행")


# --- Main action ----------------------------------------------------
if run_button:
    try:
        with st.spinner("AI가 문서를 분석하고 경력을 추출 중입니다... 잠시만 기다려 주세요."):
            query = "모든 프로젝트 이력을 하나의 JSON 객체로 종합"
            raw_project_data: Dict[str, Any] = get_raw_project_data(query)

        if not raw_project_data:
            st.error("추출된 프로젝트 이력이 없습니다. PDF 파일을 업로드했는지 확인해 주세요.")
        else:
            normalized_project = normalize_project(raw_project_data)

            project_rules_series: pd.Series = apply_all_checkbox_rules(normalized_project)

            st.subheader("실제 양식과 비슷한 체크박스 화면")
            st.caption("프로젝트 정보를 기반으로 '경력인정 적용 가이드' 양식에 자동 체크한 결과입니다.")

            form_layout = get_form_layout()
            grouped_rules = group_rules_by_category()

            def render_checkbox_row(checked: bool, label: str) -> str:
                box = "☑" if checked else "☐"
                return f"{box} {label}"

            st.markdown("---")
            
            project_name = project_rules_series.get("project_name") or "(사업명 없음)"
            client_raw = project_rules_series.get("client_raw") or project_rules_series.get("client") or "(발주처 정보 없음)"
            client_type = project_rules_series.get("client_type") or "정보 없음"
            role = project_rules_series.get("role") or "(담당업무 정보 없음)"
            start_date = project_rules_series.get("start_date") or "-"
            end_date = project_rules_series.get("end_date") or "-"
            use_date_type = project_rules_series.get("use_date_type") or "-"

            date_label_map = {
                "participation": "참여일 기준",
                "recognition": "인정일 기준",
                "-": "기준일 정보 없음",
                "": "기준일 정보 없음",
            }
            date_label = date_label_map.get(use_date_type, f"{use_date_type} 기준")

            st.markdown(
                f"""
    **📌 프로젝트 기본 정보**

    - 사업명: **{project_name}**
    - 발주처: **{client_raw}** (분류: {client_type})
    - 담당업무: **{role}**
    - 참여기간: **{start_date} ~ {end_date}**
    - 평가 기준 일자: **{date_label}**
    """
            )
            st.markdown("")

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

            with st.expander("텍스트 형식 요약 보기 (옵션)", expanded=False):
                summary_text = build_project_summary_text(
                    project_rules_series,
                    grouped_rules,
                    show_only_checked=True,
                )
                st.markdown(f"```text\n{summary_text}\n```")

            export_text = build_project_summary_text(
                project_rules_series, 
                grouped_rules, 
                show_only_checked=True
            )

            st.download_button(
                label="📥 텍스트 리포트 다운로드 (백업용)",
                data=export_text,
                file_name="경력인정_자동판정_리포트.txt",
                mime="text/plain",
            )
            
    except RuntimeError as e:
        if "No such file or directory" in str(e):
            st.error("FAISS 인덱스 파일을 찾을 수 없습니다. 먼저 PDF 파일을 업로드해주세요.")
        else:
            st.error(f"오류 발생: {e}")
    except Exception as e:
        st.error(f"예상치 못한 오류 발생: {e}")

else:
    st.info("좌측 사이드바에서 PDF를 업로드하면 분석이 시작됩니다.")
    
    
    
    # $75.00 -> 1 million Tokens
    # $0.002 per 1K tokens
    