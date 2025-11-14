import os
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any
import streamlit as st
import pandas as pd
from config import PDF_DIR, DATA_DIR # DATA_DIR 추가
from ingest import build_index, clear_pdfs, clear_index # clear_index 임포트
# [수정] get_raw_project_data만 임포트합니다.
from rag import get_raw_project_data 
from semantic_normalizer import normalize_project
from rules_engine import apply_all_checkbox_rules
# [수정] 새로운 계산 함수 임포트
from report_utils import (
    group_rules_by_category,
    build_project_summary_text,
    get_form_layout,
    get_project_calculations,
    get_project_calculations_as_json
)


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

# Initialize session state for tracking processed files
if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()

# This block now cleans, saves, AND builds the index all at once.
if uploaded_files:
    # Create a unique hash of current uploaded files
    current_files_hash = hash(tuple(f.name for f in uploaded_files))

    # Only process if this is a NEW set of files
    if current_files_hash not in st.session_state.processed_files:
        saved_files_map = {}
        with st.spinner("파일을 처리하고 AI 메모리를 생성하는 중..."):

            # 1. Clear all old PDFs AND the old index
            clear_pdfs()
            clear_index()

            # 2. Save new files with UUID names
            for f in uploaded_files:
                original_name = f.name
                file_extension = Path(original_name).suffix

                # Create a short, unique filename
                safe_name = f"{uuid.uuid4().hex}{file_extension}"
                save_path = PDF_DIR / safe_name

                with open(save_path, "wb") as out:
                    out.write(f.read())

                saved_files_map[safe_name] = original_name

            # 3. Save the name map for the ingest script
            map_save_path = DATA_DIR / "uuid_name_map.json"
            with open(map_save_path, "w", encoding="utf-8") as f_map:
                json.dump(saved_files_map, f_map, ensure_ascii=False, indent=2)

            # 4. Build new index immediately
            build_index()

            # Mark these files as processed
            st.session_state.processed_files.add(current_files_hash)

        st.sidebar.success(f"✅ {len(saved_files_map)}개 파일로 AI 메모리 생성 완료!")
        st.sidebar.info("이제 '분석 실행' 버튼을 누르세요.")
    else:
        # Files already processed, just show status
        st.sidebar.success(f"✅ {len(uploaded_files)}개 파일 준비됨")
        st.sidebar.info("'분석 실행' 버튼을 누르세요.")


st.sidebar.header("2. 분석 실행")
st.sidebar.caption("업로드된 파일의 내용을 종합하여 양식을 채웁니다.")

run_button = st.sidebar.button("✔️ 양식 자동 채우기 실행")


# --- Main action ----------------------------------------------------
if run_button:
    try:
        with st.spinner("AI가 문서를 분석하고 경력을 추출 중입니다... 잠시만 기다려 주세요."):
            query = "모든 프로젝트 이력을 JSON 리스트로 종합"
            # [수정] 이제 raw_project_data는 리스트(List[Dict])입니다.
            raw_project_data: List[Dict[str, Any]] = get_raw_project_data(query)

        if not raw_project_data:
            st.error("추출된 프로젝트 이력이 없습니다. PDF 파일을 업로드했는지 확인해 주세요.")
            st.info("터미널/콘솔 로그를 확인하여 PDF 처리 상태를 확인하세요.")
        elif len(raw_project_data) == 1 and not raw_project_data[0].get("project_name"):
            st.error("프로젝트 정보가 비어있습니다. AI가 문서에서 프로젝트를 추출하지 못했습니다.")
            st.warning("가능한 원인:")
            st.write("- PDF가 이미지 스캔본이고 OCR이 실패했을 수 있습니다")
            st.write("- PDF에 프로젝트 정보가 포함되지 않았을 수 있습니다")
            st.write("- AI 모델(Ollama)이 응답하지 않거나 오류가 발생했습니다")
            st.info("터미널/콘솔에서 [INGEST]와 [RAG] 로그를 확인하세요.")
        else:
            # [수정] 모든 프로젝트를 순회하며 정규화 및 규칙 적용
            all_projects_rules = []
            for raw_project in raw_project_data:
                normalized_project = normalize_project(raw_project)
                project_rules_series = apply_all_checkbox_rules(normalized_project)
                all_projects_rules.append(project_rules_series)
            
            # [수정] 리스트를 DataFrame으로 변환
            projects_df = pd.DataFrame(all_projects_rules)
            
            # [수정] 결과 1은 첫 번째 프로젝트를 대표로 사용
            project_rules_series = all_projects_rules[0]


            # --- [결과 1: 체크박스 폼] ---
            st.subheader("결과 1: 경력인정 가이드 자동 체크 (대표 프로젝트 기준)")
            st.caption(f"총 {len(projects_df)}개의 프로젝트가 추출되었습니다. 아래는 첫 번째 프로젝트의 자동 체크 결과입니다.")

            form_layout = get_form_layout()
            grouped_rules = group_rules_by_category()

            def render_checkbox_row(checked: bool, label: str) -> str:
                box = "☑" if checked else "☐"
                return f"{box} {label}"

            st.markdown("---")
            
            # AI가 추출한 핵심 정보 변수들 (대표 프로젝트 기준)
            project_name = project_rules_series.get("project_name") or "(사업명 없음)"
            client_raw = project_rules_series.get("client_raw") or project_rules_series.get("client") or "(발주처 정보 없음)"
            client_type = project_rules_series.get("client_type") or "정보 없음"
            role = project_rules_series.get("role") or "(담당업무 정보 없음)" # 'primary_role'이 여기에 할당됨
            start_date = project_rules_series.get("start_date") or "-"
            end_date = project_rules_series.get("end_date") or "-"
            use_date_type = project_rules_series.get("use_date_type") or "-"
            primary_field = project_rules_series.get("primary_original_field") or "(주 공종 정보 없음)"

            date_label_map = {
                "participation": "참여일 기준",
                "recognition": "인정일 기준",
                "-": "기준일 정보 없음",
                "": "기준일 정보 없음",
            }
            date_label = date_label_map.get(use_date_type, f"{use_date_type} 기준")

            st.markdown(
                f"""
    **📌 대표 프로젝트 기본 정보 (AI 추출)**

    - 사업명: **{project_name}**
    - 발주처: **{client_raw}** (분류: {client_type})
    - 담당업무: **{role}**
    - 참여기간: **{start_date} ~ {end_date}**
    - 평가 기준 일자: **{date_label}**
    """
            )
            st.markdown("")

            # 체크박스 폼 렌더링 (대표 프로젝트 기준)
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

            # [수정] 텍스트 요약은 모든 프로젝트를 합산하는 로직이 필요하나,
            # 우선 대표 프로젝트의 요약만 표시하도록 유지 (기존 로직)
            with st.expander("텍스트 형식 요약 보기 (대표 프로젝트)", expanded=False):
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
                label="📥 텍스트 리포트 다운로드 (대표 프로젝트)",
                data=export_text,
                file_name="경력인정_자동판정_리포트_대표.txt",
                mime="text/plain",
            )
            
            # --- [결과 2: 요청하신 PDF 양식의 텍스트 리포트 (모든 프로젝트 합산)] ---
            
            st.markdown("---")
            st.header("결과 2: 참여기술인 경력 사항 (전체 프로젝트 합산)")
            st.caption("AI가 추출한 모든 프로젝트 정보를 기반으로 평점 및 경력을 자동 계산한 결과입니다.")
            
            # [수정] report_utils의 함수에 단일 Series가 아닌 전체 DataFrame을 전달
            try:
                calc_data = get_project_calculations(projects_df)
                d_career = calc_data["career_details"]
                d_job = calc_data["job_field_details"]

                # --- 1. 경력 사항 렌더링 ---
                st.subheader("참여기술인 경력 사항")
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("성명", d_career["성명"])
                col2.metric("분야", d_career["분야"])
                col3.metric("총 환산 경력", f"{d_career['total_score_months']} 개월")
                col4.metric("경력 평점", d_career["평점"])
                st.caption(f"환산 기준 경력: {d_career['현재까지 경력']}")
                
                # [수정] "해당"과 "비해당"을 별도로 렌더링
                st.markdown(f"**{d_career['classification_label']}**")
                
                with st.expander(f"✅ 해당분야 용역참여실적 ({len(d_career['해당분야 용역참여실적'])}건)"):
                    if not d_career['해당분야 용역참여실적']:
                        st.info("해당 분야 실적이 없습니다.")
                    for record in d_career['해당분야 용역참여실적']:
                        st.markdown(f"• **{record['용역명']}** ({record['발주기관']}, {record['참여기간']})")
                
                with st.expander(f"⚪ 해당분야 이외 참여실적 ({len(d_career['해당분야 이외 참여실적'])}건)"):
                    if not d_career['해당분야 이외 참여실적']:
                        st.info("해당 분야 이외 실적이 없습니다.")
                    for record in d_career['해당분야 이외 참여실적']:
                        st.markdown(f"• **{record['용역명']}** ({record['발주기관']}, {record['참여기간']})")

                
                # --- 2. 직무분야 실적 렌더링 ---
                st.subheader("참여기술인 직무분야 실적")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("성명", d_job["책임건설사업관리기술인"])
                col2.metric("총 직무 경력", f"{d_job['total_job_months']} 개월")
                col3.metric("직무 평점", d_job["평점"])
                st.caption(f"총 실제 경력: {d_job['현재까지 경력']}")

                with st.expander("포함된 직무 분야 (AI 추출)"):
                    st.write(d_job["직무분야"])
                
                with st.expander(f"관련 용역 참여 실적 ({len(d_job['용역참여실적'])}건)"):
                    for record_str in d_job["용역참여실적"]:
                        st.markdown(f"• {record_str}")

                # --- 3. JSON 다운로드 버튼 추가 ---
                st.markdown("---")
                st.subheader("📥 JSON 다운로드")

                try:
                    json_data = get_project_calculations_as_json(projects_df)
                    import json
                    json_string = json.dumps(json_data, ensure_ascii=False, indent=2)

                    st.download_button(
                        label="📥 경력 사항 JSON 다운로드",
                        data=json_string,
                        file_name="경력인정_결과.json",
                        mime="application/json",
                    )

                    # JSON 미리보기
                    with st.expander("JSON 미리보기"):
                        st.json(json_data)

                except Exception as json_error:
                    st.error(f"JSON 생성 중 오류: {json_error}")
                    import traceback
                    st.error(traceback.format_exc())

            except Exception as e:
                st.error(f"경력 요약본 생성 중 오류 발생: {e}")
                import traceback
                st.error(traceback.format_exc())

            # --- [로직 끝] ---
            
    except RuntimeError as e:
        if "No such file or directory" in str(e):
            st.error("FAISS 인덱스 파일을 찾을 수 없습니다. 먼저 PDF 파일을 업로드해주세요.")
        else:
            st.error(f"오류 발생: {e}")
    except Exception as e:
        st.error(f"예상치 못한 오류 발생: {e}")

else:
    st.info("좌측 사이드바에서 PDF를 업로드하면 분석이 시작됩니다.")