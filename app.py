# app.py
import shutil
from pathlib import Path

import streamlit as st

from config import PDF_DIR, INDEX_DIR
from ingest import build_and_save_index
from rag import get_raw_facts
from rules_engine import apply_all_checkbox_rules


def save_uploaded_files(uploaded_files, target_dir: Path):
    target_dir.mkdir(parents=True, exist_ok=True)
    for f in uploaded_files:
        dest = target_dir / f.name
        with dest.open("wb") as out:
            out.write(f.read())
        st.write(f"📄 Saved: {dest.name}")


def main():
    st.set_page_config(page_title="경력인정 자동완성 데모", page_icon="🧾", layout="wide")
    st.title("🧾 경력인정 자동완성 데모 (RAG + Rules + Ollama)")

    st.markdown(
        """
이 데모는 **PDF로부터 경력 데이터를 추출(RAG)** 하고,  
**규칙 엔진으로 체크박스를 자동 판정**하는 PoC입니다.  
모든 처리는 로컬 머신에서 수행되며, LLM은 **Ollama**를 사용합니다.
"""
    )

    # ---------------------------
    # 1) PDF 업로드 및 인덱싱
    # ---------------------------
    st.header("1️⃣ PDF 업로드 및 인덱싱 (Ingest)")

    uploaded_pdfs = st.file_uploader(
        "비즈니스 관련 PDF 파일을 업로드하세요 (여러 개 가능)",
        type=["pdf"],
        accept_multiple_files=True,
    )

    col_ingest_btn, col_clear = st.columns(2)

    with col_ingest_btn:
        if st.button("📥 인덱스 생성 / 재생성 (Ingest 실행)"):
            if not uploaded_pdfs:
                st.warning("먼저 PDF 파일을 업로드하세요.")
            else:
                # Clear old PDFs
                for old_pdf in PDF_DIR.glob("*.pdf"):
                    old_pdf.unlink()

                st.write(f"📁 업로드한 PDF를 {PDF_DIR} 에 저장합니다...")
                save_uploaded_files(uploaded_pdfs, PDF_DIR)

                with st.spinner("PDF 텍스트 추출 및 벡터 인덱스 생성 중..."):
                    build_and_save_index()
                st.success("✅ 인덱스 생성 완료!")

    with col_clear:
        if st.button("🧹 기존 인덱스 삭제"):
            if INDEX_DIR.exists():
                shutil.rmtree(INDEX_DIR)
            INDEX_DIR.mkdir(parents=True, exist_ok=True)
            st.success("✅ 인덱스 디렉토리를 초기화했습니다.")

    st.markdown("---")

    # ---------------------------
    # 2) 경력 자동 계산 (RAG + Rules)
    # ---------------------------
    st.header("2️⃣ 경력 자동 계산 (RAG + Rules Engine)")

    query_default = "모든 프로젝트 이력을 JSON 형식으로 추출"
    user_query = st.text_input(
        "질의어 (Query)",
        value=query_default,
        help="RAG 검색에 사용할 한글 질의입니다.",
    )

    if st.button("🧠 경력 자동 추출 및 체크박스 판정"):
        with st.spinner("AI가 파일을 분석하고 규칙을 적용하는 중입니다..."):
            try:
                raw_facts = get_raw_facts(user_query)
                rules_df = apply_all_checkbox_rules(raw_facts)
            except Exception as e:
                st.error(f"에러 발생: {e}")
                return

        st.subheader("🔍 AI가 추출한 원본 프로젝트 이력 (Raw JSON)")
        st.json(raw_facts)

        st.subheader("✅ 체크된 규칙 ID (요약)")
        st.dataframe(rules_df[["project_name", "client", "checked_rule_ids"]])

        st.subheader("📊 전체 상세 결과 (모든 rule__ 컬럼 포함)")
        st.dataframe(rules_df)


if __name__ == "__main__":
    main()
