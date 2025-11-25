# ======================================================================
# ingest.py  — FINAL VERSION (Option C: Full OpenCV Table Segmentation)
# ======================================================================

import os
import io
import re
import fitz
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from PIL import Image
import faiss
import easyocr
from semantic_normalizer import normalize_project, normalize_tech_data_df
from rules_engine import apply_all_checkbox_rules
from rag import extract_clean_json_from_llm
import pytesseract
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from config import PDF_DIR, INDEX_DIR, DATA_DIR, STEP1_INDEX_DIR, STEP2_INDEX_DIR
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from pathlib import Path
try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber not installed. Run: pip install pdfplumber")
    exit(1)

# import fitz  # PyMuPDF
# import pytesseract
# from PIL import Image
# import io
# from config import STEP1_INDEX_DIR, STEP2_INDEX_DIR
# =====================================================================
# GLOBAL OCR READER
# =====================================================================
reader = easyocr.Reader(["ko", "en"], gpu=False)

DATE = re.compile(r"(\d{4}[.\-/]\d{2}[.\-/]\d{2})")
DATE_RANGE = re.compile(r"(\d{4}[.\-/]\d{2}[.\-/]\d{2}).*?(\d{4}[.\-/]\d{2}[.\-/]\d{2})")
DAYS = re.compile(r"(\d+)\s*일")
DATE_RE = re.compile(r"(\d{4}[.,/-]\s*\d{2}[.,/-]\s*\d{2})")
DAY_RE = re.compile(r"(\d+)\s*일")


# Keywords that indicate project header
HEADER_HINTS = [
    "공사", "용역", "개발", "조성", "건설", "사업", "공원", "공항", "단지",
    "도로", "교량", "철도", "센터", "감리", "CM"
]

# 발주자 keywords
AGENCY_HINTS = [
    "시청", "군청", "구청", "광역시", "공사", "공단", "청", "재단", "국토",
    "한국도로공사", "인천국제공항공사"
]

# 직무분야 keywords
JOB_FIELD = ["토목", "건축", "기계", "조경", "전기"]

# 직위
POSITION = ["사원", "대리", "과장", "차장", "부장", "주임"]



def clear_pdfs():
    """Deletes all files in the PDF directory."""
    print("[CLEANUP] Deleting old PDFs...")
    deleted_count = 0
    for f in Path(PDF_DIR).glob("*.pdf"):
        try:
            f.unlink()
            deleted_count += 1
        except Exception as e:
            print(f"Failed to delete {f}: {e}")
    print(f"Deleted {deleted_count} PDFs.")

def clear_index():
    """Deletes all files in the FAISS index directory."""
    print("[CLEANUP] Deleting old FAISS index...")
    deleted_count = 0
    for f in Path(STEP1_INDEX_DIR).glob("*.*"): # Match .faiss and .pkl
        try:
            f.unlink()
            deleted_count += 1
        except Exception as e:
            print(f"Failed to delete {f}: {e}")
    print(f"Deleted {deleted_count} index files.")
def normalize_project_name(name: str) -> str:
    import re
    if not isinstance(name, str):
        return ""

    txt = name.replace("\n", " ").replace("\t", " ").strip()
    txt = re.sub(r"[\'\"`]", "", txt)
    txt = re.sub(r"[-_=]+", " ", txt)
    txt = re.sub(r"[^\w\uAC00-\uD7A3\s]", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    txt = re.sub(r":$", "", txt)

    # OCR typo fixes
    txt = txt.replace("도로딪공항", "도로및공항")
    txt = txt.replace("374,58KM", "374.58km")
    txt = txt.replace("부지조성7 19", "부지조성 719")

    # Category mapping (evaluation-aligned)
    if "감리" in txt:
        return txt
    if "건설사업관리" in txt or "사업관리" in txt:
        return "건설사업관리"
    if "단지조성" in txt or "부지조성" in txt:
        return "단지조성"
    if "교량" in txt:
        return "교량공사"
    if "도로" in txt:
        return "도로"
    if "공항" in txt:
        return "공항공사"
    if "하천" in txt:
        return "하천정비"
    if "근린공원" in txt:
        return "근린공원 조성"
    if "업무시설" in txt:
        return "업무시설"

    return txt

def merge_overlapping_periods(df):
    """
    Merge duplicate project records for correct evaluation:
    - same normalized 사업명
    - same 발주기관 (if available)
    - overlapping or adjacent 기간
    """
    if df.empty:
        return df

    df = df.copy()

    df["start_dt"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["end_dt"]   = pd.to_datetime(df["end_date"],   errors="coerce")

    df = df.dropna(subset=["start_dt", "end_dt"])

    merged_rows = []

    for (proj, inst), group in df.groupby(["사업명", "발주기관"], dropna=False):

        group = group.sort_values("start_dt")

        cur_start = None
        cur_end = None
        cur_base = None

        for idx, row in group.iterrows():

            if cur_start is None:
                cur_start = row["start_dt"]
                cur_end   = row["end_dt"]
                cur_base  = row
                continue

            # Overlap or adjacent detection
            if row["start_dt"] <= cur_end + pd.Timedelta(days=1):
                cur_end = max(cur_end, row["end_dt"])
            else:
                merged_rows.append({
                    **cur_base,
                    "start_date": cur_start.strftime("%Y-%m-%d"),
                    "end_date": cur_end.strftime("%Y-%m-%d"),
                    "참여일수": (cur_end - cur_start).days + 1
                })
                cur_start = row["start_dt"]
                cur_end   = row["end_dt"]
                cur_base  = row

        # final commit
        merged_rows.append({
            **cur_base,
            "start_date": cur_start.strftime("%Y-%m-%d"),
            "end_date": cur_end.strftime("%Y-%m-%d"),
            "참여일수": (cur_end - cur_start).days + 1
        })

    return pd.DataFrame(merged_rows)

def normalize_date(raw):
    if not raw:
        return ""
    s = raw.replace("/", ".").replace("-", ".")
    parts = s.split(".")
    if len(parts) != 3:
        return ""
    y, m, d = parts
    if len(m) == 1: m = "0" + m
    if len(d) == 1: d = "0" + d
    try:
        datetime.strptime(f"{y}.{m}.{d}", "%Y.%m.%d")
        return f"{y}-{m}-{d}"
    except:
        return ""


def diff_days(start, end):
    try:
        s = datetime.strptime(start, "%Y-%m-%d")
        e = datetime.strptime(end, "%Y-%m-%d")
        return (e - s).days
    except:
        return 0

def warn(msg: str):
    print(f"[WARN] {msg}")


def err(msg: str):
    print(f"[ERROR] {msg}")


# --- Common Builder ---
def _build_faiss_index(docs, save_path):
    if not docs: return False

    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={"device": "cpu"}
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],
    )

    split_docs = splitter.split_documents(docs)

    # -----------------------
    #  ❗ FIX: remove empty docs
    # -----------------------
    cleaned = [d for d in split_docs if d.page_content and d.page_content.strip()]

    if not cleaned:
        print("[INGEST] No valid text chunks found after cleaning.")
        return False

    vectorstore = FAISS.from_documents(cleaned, embeddings)
    vectorstore.save_local(str(save_path))
    print(f"[INGEST] Index built at {save_path} with {len(cleaned)} chunks")
    return True

# --- STEP 1: Native Extraction ---
def ingest_step1_multiple(pdf_paths: List[str]) -> bool:
    print("[Step 1] Starting Native Extraction for multiple files...")
    all_docs = []
    
    for pdf_path in pdf_paths:
        try:
            doc = fitz.open(pdf_path)
            for i, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    all_docs.append(Document(
                        page_content=text,
                        metadata={"source": str(pdf_path), "page": i + 1, "type": "native"}
                    ))
        except Exception as e:
            print(f"[Step 1 Error] Failed to read {pdf_path}: {e}")

    if not all_docs:
        print("[Step 1] No native text found.")
        return False
        
    return _build_faiss_index(all_docs, STEP1_INDEX_DIR)




# ---------------------------------------------------------------------------------------------------------------------------------
# ================================================ NEW DATA EXTRACTION STEP 2 ============================================================
#----------------------------------------------------------------------------------------------------------------------------------

def build_faiss_index_step2(df: pd.DataFrame):

    if df.empty:
        warn("[Step3] Empty DataFrame passed to FAISS.")
        return None, None

    vecs = []

    for _, row in df.iterrows():
        try:
            num = float(row.get("참여일수", 0))
        except:
            num = 0.0
        vecs.append(np.array([num], dtype="float32"))

    mat = np.vstack(vecs).astype("float32")

    index = faiss.IndexFlatL2(mat.shape[1])
    index.add(mat)

    return index, mat


@dataclass
class CareerEntry:
    """Data structure for a single career entry"""
    # Person info
    person_name: str = ""
    
    # Case 1 - Dates and Days
    participation_period_start: str = ""
    participation_period_end: str = ""
    recognized_days: str = ""
    participated_days: str = ""
    
    # Case 2 - Project Details (4 lines)
    project_name: str = ""  # Line 1
    client: str = ""  # Line 2 left
    project_type: str = ""  # Line 2 right
    project_overview: str = ""  # Line 3
    applied_method: str = ""  # Line 4 left
    applied_convergence_tech: str = ""  # Line 4 right
    
    # Case 3 - Technical Fields (4 lines)
    job_field: str = ""  # Line 1
    specialty_field: str = ""  # Line 2
    responsibility_level: str = ""  # Line 3
    applied_new_tech: str = ""  # Line 4
    
    # Case 4 - Role and Financial (4 lines)
    assigned_task: str = ""  # Line 1
    position: str = ""  # Line 2
    project_amount_million_won: str = ""  # Line 3
    facility_type: str = ""  # Line 4
    
    # Metadata
    page_number: int = 0
    entry_number: int = 0
    
    def to_dict(self):
        return asdict(self)



DATE_PATTERN = r'\d{4}\.\d{1,2}\.\d{1,2}'
DAYS_PATTERN = r'\((\d+)일?\)'
NUMBER_PATTERN = r'[\d,]+'

def extract_person_name(page_texts, career_pages) -> str:
    """
    Extract person name (성명) from the first career section page
    Format: 성명 : 이고현 or 성명: 이고현 or 성명 이고현
    """
    if not career_pages:
        return ""
    
    # Get first career page
    first_page = career_pages[0]
    text = page_texts.get(first_page, "")
    
    if not text:
        return ""
    
    # Look for patterns like "성명 : NAME" or "성명: NAME" or "성명 NAME"
    patterns = [
        r'성명\s*[:：]\s*([가-힣]+)',  # 성명 : 이고현 or 성명: 이고현
        r'성명\s+([가-힣]+)',          # 성명 이고현
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip()
            if name and len(name) >= 2:  # Korean names are usually 2-4 characters
                print(f"  Found person name: {name}")
                return name
    
    print("  Warning: Could not find person name (성명)")
    return ""

def extract_text_from_pdf(pdf_path) -> Dict[int, str]:
    """Extract text from PDF pages"""
    page_texts = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            page_texts[page_num] = text
            
    return page_texts

def find_career_section(page_texts: Dict[int, str]) -> List[int]:
    """Find pages containing '1. 기술경력' section"""
    career_pages = []
    
    for page_num, text in page_texts.items():
        if '1. 기술경력' in text or '1.기술경력' in text:
            career_pages.append(page_num)
        elif career_pages:  # We're in the section
            # Check if we've moved to next section
            if re.search(r'\n\s*[2-9]\.\s*[가-힣]+', text):
                break
            career_pages.append(page_num)
            
    return career_pages

def extract_tables_from_page(pdf_path, page_num: int) -> List[List[List]]:
    """Extract all tables from a page"""
    with pdfplumber.open(pdf_path) as pdf:
        if page_num > len(pdf.pages):
            return []
        
        page = pdf.pages[page_num - 1]
        tables = page.extract_tables()
        return tables if tables else []

def find_header_row(table: List[List]) -> int:
    """
    Find Case 1 (header row) which contains '참여기간'
    Returns row index or -1 if not found
    """
    for i, row in enumerate(table):
        if not row:
            continue
        
        # Check if this row contains Case 1 keys
        row_text = ' '.join([str(cell) if cell else '' for cell in row])
        if '참여기간' in row_text:
            return i
    
    return -1

def parse_table_structure(table: List[List], page_num: int) -> List[CareerEntry]:
    """
    Parse table structure:
    - First row (index 0): Field names (keys) for all 4 cases
    - Subsequent rows grouped by 4: Each group of 4 rows = 1 entry
    
    Example:
    Row 0: [사업명, None, 직무분야, 담당업무]  <- Keys
    Row 1: [발주자, 공사종류, 전문분야, 직위]  <- Keys
    Row 2: [개요, None, 책임정도, 금액]       <- Keys
    Row 3: [공법, 융복합, 신기술, 시설물]      <- Keys
    Row 4-7: Entry 1 data (4 rows)
    Row 8-11: Entry 2 data (4 rows)
    ...
    """
    entries = []
    
    if not table or len(table) < 5:  # Need at least header (4 rows) + 1 entry (4 rows)
        return entries
    
    print(f"  Table has {len(table)} rows × {len(table[0]) if table[0] else 0} columns")
    
    # First 4 rows are keys
    header_rows = table[0:4]
    
    # Remaining rows are data, grouped by 4
    data_rows = table[4:]
    num_entries = len(data_rows) // 4
    
    print(f"  Extracting {num_entries} entries (each entry = 4 rows)")
    
    # Extract each entry
    for entry_idx in range(num_entries):
        start_row = 4 + (entry_idx * 4)
        entry_rows = table[start_row:start_row + 4]
        
        if len(entry_rows) < 4:
            continue
        
        entry = extract_entry_from_row_group(
            header_rows, entry_rows, page_num, entry_idx + 1
        )
        if entry:
            entries.append(entry)
    
    return entries

def extract_entry_from_row_group(
    header_rows: List[List],
    entry_rows: List[List],
    page_num: int,
    entry_num: int
) -> Optional[CareerEntry]:
    """
    Extract a single entry from a group of 4 data rows
    
    header_rows[0]: [사업명, None, 직무분야, 담당업무]
    header_rows[1]: [발주자, 공사종류, 전문분야, 직위]
    header_rows[2]: [개요, None, 책임정도, 금액]
    header_rows[3]: [공법, 융복합, 신기술, 시설물]
    
    entry_rows[0]: [value1, value2, value3, value4] for row 1 keys
    entry_rows[1]: [value1, value2, value3, value4] for row 2 keys
    entry_rows[2]: [value1, value2, value3, value4] for row 3 keys
    entry_rows[3]: [value1, value2, value3, value4] for row 4 keys
    """
    entry = CareerEntry(page_number=page_num, entry_number=entry_num)
    
    # Map each column in the 4 rows to the corresponding fields
    for row_idx in range(4):
        if row_idx >= len(header_rows) or row_idx >= len(entry_rows):
            continue
        
        header_row = header_rows[row_idx]
        data_row = entry_rows[row_idx]
        
        # Process each column
        for col_idx, field_name in enumerate(header_row):
            if not field_name or col_idx >= len(data_row):
                continue
            
            field_name = str(field_name).strip()
            cell_value = data_row[col_idx]
            cell_value = str(cell_value).strip() if cell_value else ""
            
            if not cell_value:
                continue
            
            # Map based on field name
            _map_field_to_entry(field_name, cell_value, entry)
    
    # Validate entry - check if it has meaningful data
    if entry.project_name or entry.client or entry.assigned_task:
        return entry
    
    return None

def _map_field_to_entry(field_name: str, cell_value: str, entry: CareerEntry):
    """Map a field name and value to the entry object"""
    
    # Case 2: Project Details
    if '사업명' in field_name:
        entry.project_name = cell_value
    
    elif '발주자' in field_name:
        entry.client = cell_value
    
    elif '공사종류' in field_name or '종류' in field_name:
        entry.project_type = cell_value
    
    elif '개요' in field_name or '공사(용역)개요' in field_name:
        entry.project_overview = cell_value
    
    elif '적용 공법' in field_name or '공법' in field_name:
        entry.applied_method = cell_value
    
    elif '융ㆍ복합' in field_name or '융복합' in field_name:
        entry.applied_convergence_tech = cell_value
    
    # Case 3: Technical Fields
    elif '직무분야' in field_name or '직무' in field_name:
        entry.job_field = cell_value
    
    elif '전문분야' in field_name or '전문' in field_name:
        entry.specialty_field = cell_value
    
    elif '책임정도' in field_name or '책임' in field_name:
        entry.responsibility_level = cell_value
    
    elif '신기술' in field_name or '적용 신기술' in field_name:
        entry.applied_new_tech = cell_value
    
    # Case 4: Role and Financial
    elif '담당업무' in field_name or '담당' in field_name:
        entry.assigned_task = cell_value
    
    elif '직위' in field_name:
        entry.position = cell_value
    
    elif '금액' in field_name or '공사(용역)금액' in field_name:
        # Extract number
        numbers = re.findall(NUMBER_PATTERN, cell_value)
        if numbers:
            entry.project_amount_million_won = numbers[0].replace(',', '')
    
    elif '시설물' in field_name or '시설물 종류' in field_name:
        entry.facility_type = cell_value

def extract_all_entries(pdf_path) -> List[CareerEntry]:
    """Main extraction method"""
    print("Extracting text from PDF...")
    page_texts = extract_text_from_pdf(pdf_path)
    
    print("Finding career section...")
    career_pages = find_career_section(page_texts)
    
    if not career_pages:
        print("Warning: '1. 기술경력' section not found in PDF")
        return []
    
    print(f"Found career section in {len(career_pages)} page(s): {career_pages}")
    
    print("\nExtracting person name (성명)...")
    person_name = extract_person_name(page_texts, career_pages)
    
    all_entries = []
    
    for page_num in career_pages:
        print(f"\nProcessing page {page_num}...")
        
        # Get page text for date extraction
        page_text = page_texts.get(page_num, "")
        
        # Extract tables
        tables = extract_tables_from_page(pdf_path, page_num)
        
        if not tables:
            print(f"  No tables found on page {page_num}")
            continue
        
        print(f"  Found {len(tables)} table(s)")
        
        # Process each table
        for table_idx, table in enumerate(tables, 1):
            print(f"\n  Processing table {table_idx}...")
            entries = parse_table_structure(table, page_num)
            
            for entry in entries:
                entry.person_name = person_name
            # Try to extract dates for entries from page text if not in table
            if entries:
                print(f"  Extracting dates from page text...")
                dates_from_text = _extract_dates_from_text(page_text)
                print(f"  Found {len(dates_from_text)} date patterns")
                
                if dates_from_text:
                    print(f"  First date pattern: {dates_from_text[0]}")
                
                _assign_dates_to_entries(entries, dates_from_text)
                
                # Count how many entries now have dates
                entries_with_dates = sum(1 for e in entries if e.participation_period_start)
                print(f"  Entries with dates: {entries_with_dates}/{len(entries)}")
            
            print(f"  Extracted {len(entries)} entries from table {table_idx}")
            all_entries.extend(entries)
    
    entries = all_entries
    return all_entries

def _extract_dates_from_text(text: str) -> List[Tuple[str, str, str, str]]:
    """
    Extract dates and days from text
    Returns list of (start_date, end_date, recognized_days, participated_days)
    
    Date format in text:
    2008.10.09
        ~
    2009.12.31
    (449일)
    (449일)
    """
    dates_info = []
    
    # Split text into lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for date pattern
        date_match = re.search(DATE_PATTERN, line)
        
        if date_match:
            start_date = date_match.group()
            end_date = ""
            recognized_days = ""
            participated_days = ""
            
            # Look ahead for end date (usually within next 3 lines)
            for offset in range(1, 5):
                if i + offset < len(lines):
                    next_line = lines[i + offset]
                    
                    # Check for second date
                    if not end_date:
                        end_date_match = re.search(DATE_PATTERN, next_line)
                        if end_date_match:
                            end_date = end_date_match.group()
                    
                    # Check for days pattern
                    days_matches = re.findall(DAYS_PATTERN, next_line)
                    if days_matches:
                        if not recognized_days:
                            recognized_days = days_matches[0]
                        elif not participated_days and len(days_matches) > 0:
                            participated_days = days_matches[-1] if len(days_matches) > 1 else days_matches[0]
            
            # Look for days in the same line or nearby
            days_in_line = re.findall(DAYS_PATTERN, line)
            if days_in_line:
                if not recognized_days:
                    recognized_days = days_in_line[0]
                if len(days_in_line) > 1 and not participated_days:
                    participated_days = days_in_line[1]
            
            # Check next few lines for remaining days if still missing
            if start_date and not participated_days:
                for offset in range(1, 6):
                    if i + offset < len(lines):
                        days_matches = re.findall(DAYS_PATTERN, lines[i + offset])
                        if len(days_matches) >= 2:
                            recognized_days = days_matches[0]
                            participated_days = days_matches[1]
                            break
                        elif days_matches and not recognized_days:
                            recognized_days = days_matches[0]
                        elif days_matches and recognized_days and not participated_days:
                            participated_days = days_matches[0]
            
            if start_date:
                dates_info.append((start_date, end_date, recognized_days, participated_days))
                # Skip ahead to avoid re-processing the same date block
                i += 5
                continue
        
        i += 1
    
    return dates_info

def _assign_dates_to_entries(
    entries: List[CareerEntry], 
    dates_info: List[Tuple[str, str, str, str]]
):
    """Assign dates to entries that don't have them"""
    date_idx = 0
    
    for entry in entries:
        if not entry.participation_period_start and date_idx < len(dates_info):
            start, end, rec_days, part_days = dates_info[date_idx]
            entry.participation_period_start = start
            entry.participation_period_end = end
            entry.recognized_days = rec_days
            entry.participated_days = part_days
            date_idx += 1


def print_summary(entries):
    """Print extraction summary"""
    print("\n" + "="*80)
    print("EXTRACTION SUMMARY")
    print("="*80)
    print(f"Total entries found: {len(entries)}")
    
    if entries:
        # Group by page
        from collections import defaultdict
        by_page = defaultdict(int)
        for e in entries:
            by_page[e.page_number] += 1
        
        print(f"\nEntries per page:")
        for page_num in sorted(by_page.keys()):
            print(f"  Page {page_num}: {by_page[page_num]} entries")
        
        print(f"\n{'='*80}")
        print("FIRST ENTRY (detailed):")
        print('='*80)
        e = entries[0]
        print(f"Page {e.page_number}, Entry #{e.entry_number}")
        print(f"\n[Case 1: Participation Info]")
        print(f"  Period: {e.participation_period_start} ~ {e.participation_period_end}")
        print(f"  Recognized Days: {e.recognized_days}")
        print(f"  Participated Days: {e.participated_days}")
        
        print(f"\n[Case 2: Project Details]")
        print(f"  Project Name: {e.project_name}")
        print(f"  Client: {e.client}")
        print(f"  Type: {e.project_type}")
        print(f"  Overview: {e.project_overview[:50]}..." if len(e.project_overview) > 50 else f"  Overview: {e.project_overview}")
        print(f"  Method: {e.applied_method}")
        print(f"  Convergence Tech: {e.applied_convergence_tech}")
        
        print(f"\n[Case 3: Technical Fields]")
        print(f"  Job Field: {e.job_field}")
        print(f"  Specialty: {e.specialty_field}")
        print(f"  Responsibility: {e.responsibility_level}")
        print(f"  New Tech: {e.applied_new_tech}")
        
        print(f"\n[Case 4: Role & Financial]")
        print(f"  Assigned Task: {e.assigned_task}")
        print(f"  Position: {e.position}")
        print(f"  Amount: {e.project_amount_million_won} million won")
        print(f"  Facility Type: {e.facility_type}")
        
    print("="*80 + "\n")

def print_field_completeness(entries):
    """Print statistics on field completeness"""
    if not entries:
        return
    
    print("\n" + "="*80)
    print("FIELD COMPLETENESS ANALYSIS")
    print("="*80)
    
    fields = [
        ('participation_period_start', 'Case 1: Start Date'),
        ('participation_period_end', 'Case 1: End Date'),
        ('recognized_days', 'Case 1: Recognized Days'),
        ('participated_days', 'Case 1: Participated Days'),
        ('project_name', 'Case 2: Project Name'),
        ('client', 'Case 2: Client'),
        ('project_type', 'Case 2: Project Type'),
        ('project_overview', 'Case 2: Overview'),
        ('applied_method', 'Case 2: Method'),
        ('applied_convergence_tech', 'Case 2: Convergence Tech'),
        ('job_field', 'Case 3: Job Field'),
        ('specialty_field', 'Case 3: Specialty'),
        ('responsibility_level', 'Case 3: Responsibility'),
        ('applied_new_tech', 'Case 3: New Tech'),
        ('assigned_task', 'Case 4: Task'),
        ('position', 'Case 4: Position'),
        ('project_amount_million_won', 'Case 4: Amount'),
        ('facility_type', 'Case 4: Facility Type'),
    ]
    
    total = len(entries)
    
    for field_name, display_name in fields:
        filled = sum(1 for e in entries if getattr(e, field_name))
        percentage = (filled / total * 100) if total > 0 else 0
        status = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
        print(f"{status} {display_name:35s}: {filled:3d}/{total:3d} ({percentage:5.1f}%)")
    
    print("="*80 + "\n")


def to_json(entries) -> str:
    """Export entries to JSON"""
    data = {
        'total_entries': len(entries),
        'entries': [entry.to_dict() for entry in entries]
    }
    
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    return json_str

def main_extractor(pdf_path):
    """Example usage"""

    # Extract entries
    entries = extract_all_entries(pdf_path)
    
    print_summary(entries)
    # Print field completeness
    print_field_completeness(entries)

    
    json_response = to_json(entries)
    
    json_response = json.loads(json_response)

    # print(json_response['entries'])
    
    return entries


# =====================================================================
# STEP 3 — FAISS
# =====================================================================
import pandas as pd
import re
from rules_config import CHECKBOX_RULES


def group_rules_by_category():
    grouped = {}
    for r in CHECKBOX_RULES:
        cat = r.get("category", "기타")
        grp = r.get("group", "기타")
        grouped.setdefault(cat, {}).setdefault(grp, []).append(r)
    return grouped

# ==================================== NEW STEP 3 ================================================================================

# ---- 1. SCORING LOGIC (From Guide PDF Page 6) ----

def _get_experience_score(years: float) -> float:
    """
    (가) 해당분야 경력 평가 (Max 12 points)
    """
    if years >= 15: return 12.0
    elif years >= 13: return 11.0
    elif years >= 11: return 10.0
    elif years >= 9: return 9.0
    else: return 8.0

def _get_job_performance_score_a(years: float) -> float:
    """
    (나) 직무분야 실적 - Type A: 설계, 건설사업관리, 감리 등 (Max 6 points)
    """
    if years >= 12: return 6.0
    elif years >= 10: return 5.4
    elif years >= 8: return 4.8
    elif years >= 6: return 4.2
    else: return 3.6

def _get_job_performance_score_b(years: float) -> float:
    """
    (나) 직무분야 실적 - Type B: 시공, 시험, 안전진단 등 (Max 3 points)
    """
    if years >= 7: return 3.0
    elif years >= 5: return 2.7
    elif years >= 4: return 2.4
    elif years >= 2: return 2.1
    else: return 1.8

# =========================================================
# 2. FORM LAYOUT & HELPERS (For Step 1 UI)
# =========================================================

# =========================================================
# 3. FINAL REPORT GENERATION (Step 3 Logic)
# =========================================================


def classify_relevance(primary_field: str, project_name: str, project_type: str) -> bool:
    name = str(project_name)
    ptype = str(project_type)

    if primary_field == "토목":
        if any(k in name for k in ["도로", "교량", "터널", "포장"]) or \
            any(k in ptype for k in ["도로", "교량", "터널"]):
            return True
        if "하천" in name or "하천" in ptype:
            return True
        if any(k in name for k in ["정수장", "상수도", "하수", "관로"]):
            return True

    # Extendable for 건축/기계/조경 분야 later
    return False


def get_final_report_json(step2_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates Step 3 Report Data based on extracted rows.
    Includes PDF-based relevance classification.
    """

    if not step2_data:
        return {}

    df = pd.DataFrame(step2_data)

    # Detect primary job field (토목 most common)
    try:
        df['clean_field'] = df['job_field'].astype(str).apply(lambda x: x.split()[0])
        primary_field = df['clean_field'].mode()[0]
    except:
        primary_field = "토목"

    try:
        engineer_name = df['person_name'].mode()[0]
    except:
        engineer_name = "Unknown"

    relevant_projects = []
    other_projects = []

    total_days_exp = 0
    total_days_job_a = 0
    total_days_job_b = 0

    for _, row in df.iterrows():
        # Parse 인정일수
        raw_days = str(row.get('recognized_days', '0'))
        d_match = re.search(r'(\d+)', raw_days)
        days = int(d_match.group(1)) if d_match else 0

        # PDF-based classification
        project_name = row.get("project_name", "")
        project_type = row.get("project_type", "")

        is_relevant = classify_relevance(primary_field, project_name, project_type)

        weight = 1.0 if is_relevant else 0.6
        weighted_days = int(days * weight)

        proj = {
            "용역명": project_name,
            "발주기관": f"{row.get('client', '')} {project_type}",
            "참여기간": f"{row.get('participation_period_start')} ~ {row.get('participation_period_end')}",
            "인정일수": f"{days}일 (적용: {weighted_days}일)",
            "담당업무": row.get("position", "")
        }

        if is_relevant:
            relevant_projects.append(proj)
        else:
            other_projects.append(proj)

        total_days_exp += weighted_days

        role = str(row.get('position', ''))
        if any(k in role for k in ['설계', '감리', 'CM', '감독', '자문', '유지관리']):
            total_days_job_a += weighted_days
        elif any(k in role for k in ['시공', '안전', '품질', '시험']):
            total_days_job_b += weighted_days
        else:
            total_days_job_a += weighted_days

    years_exp = total_days_exp / 365.0
    years_job_a = total_days_job_a / 365.0
    years_job_b = total_days_job_b / 365.0

    score_exp = _get_experience_score(years_exp)
    score_job_a = _get_job_performance_score_a(years_job_a)
    score_job_b = _get_job_performance_score_b(years_job_b)

    total_job_score = min(score_job_a + score_job_b, 9.0)
    final_total_score = score_exp + total_job_score

    return {
        "career_history": {
            "header": {
                "division": "책임건설사업관리기술인",
                "name": engineer_name,
                "field": primary_field,
                "total_career": f"{years_exp:.1f}년 ({total_days_exp}일)",
                "score": f"{final_total_score:.2f}점",
                "details": {
                    "exp_score": f"{score_exp}점 (경력 {years_exp:.1f}년)",
                    "job_score": f"{total_job_score:.1f}점 (A:{score_job_a} + B:{score_job_b})"
                }
            },
            "relevant": relevant_projects,
            "other": other_projects
        }
    }
