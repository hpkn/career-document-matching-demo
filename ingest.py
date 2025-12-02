# ======================================================================
# ingest.py  — FINAL VERSION (Option C: Full OpenCV Table Segmentation)
# =====================================================================
import re
import numpy as np
import pandas as pd
from datetime import datetime
import faiss
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from config import PDF_DIR, INDEX_DIR, DATA_DIR, STEP1_INDEX_DIR, STEP2_INDEX_DIR
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import pandas as pd
from rules_config import CHECKBOX_RULES
import fitz

try:
    import pdfplumber
except ImportError:
    raise ImportError("pdfplumber not installed. Run: pip install pdfplumber") 

# =====================================================================
# GLOBAL OCR READER
# =====================================================================
# reader = easyocr.Reader(["ko", "en"], gpu=False)

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


def diff_days(start, end) -> int:
    try:
        s = datetime.strptime(start, "%Y-%m-%d")
        e = datetime.strptime(end, "%Y-%m-%d")
        return (e - s).days
    except:
        return 0

def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def err(msg: str) -> None:
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
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_num > len(pdf.pages):
                return []
            
            page = pdf.pages[page_num - 1]
            tables = page.extract_tables()
            return tables if tables else []
    except Exception as e:
        print(f"[ERROR] Failed to extract tables from page {page_num}: {e}")
        return []
    
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


def get_data_breakdown(step2_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """
    Analyze Step 2 data and return breakdown of values by field.

    Returns: {
        'project_type': {'하천': 45, '교량': 38, '도로': 52, ...},
        'assigned_task': {'감독': 120, '설계': 80, '시공': 45, ...},
        'job_field': {'토목': 250, '건축': 20, ...}
    }
    """
    from collections import Counter

    if not step2_data:
        return {}

    # Count values for each field
    project_types = Counter()
    assigned_tasks = Counter()
    job_fields = Counter()
    clients = Counter()

    for record in step2_data:
        # Project type (공종)
        pt = str(record.get('project_type', '') or '').strip()
        if pt:
            project_types[pt] += 1

        # Assigned task (담당업무)
        at = str(record.get('assigned_task', '') or '').strip()
        if at:
            assigned_tasks[at] += 1

        # Job field (직무분야)
        jf = str(record.get('job_field', '') or '').strip()
        if jf:
            job_fields[jf] += 1

        # Client (발주처)
        cl = str(record.get('client', '') or '').strip()
        if cl:
            clients[cl] += 1

    return {
        'project_type': dict(project_types),
        'assigned_task': dict(assigned_tasks),
        'job_field': dict(job_fields),
        'client': dict(clients),
        'total_records': len(step2_data)
    }


def _call_ollama_for_classification(prompt: str) -> str:
    """Call Ollama API for Step 3 classification using faster model."""
    import requests
    from config import OLLAMA_BASE_URL, OLLAMA_MODEL_STEP3

    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL_STEP3,
        "messages": [
            {"role": "system", "content": "You are a Korean construction career classifier. Output ONLY valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.0, "num_ctx": 16000},
    }

    print(f"[Step3 LLM] Calling Ollama ({OLLAMA_MODEL_STEP3}) for classification...")
    try:
        resp = requests.post(url, json=payload, timeout=60)  # Reduced to 60 seconds
        if resp.status_code != 200:
            print(f"[Step3 LLM] ERROR: Ollama returned status {resp.status_code}")
            return "{}"
        return resp.json().get("message", {}).get("content", "")
    except Exception as e:
        print(f"[Step3 LLM] ERROR: {e}")
        return "{}"


def _classify_projects_with_keywords(
    projects: List[Dict[str, Any]],
    filter_criteria: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Classify projects using keyword matching only (fast, deterministic).

    Returns list of projects with added 'is_relevant' and 'match_reason' fields.
    """
    construction_types = filter_criteria.get("construction_types", [])
    roles = filter_criteria.get("roles", [])
    job_fields = filter_criteria.get("job_fields", [])
    include_blank_duty = filter_criteria.get("include_blank_duty", False)

    for p in projects:
        p['is_relevant'] = False
        p['match_reason'] = ""

        text = f"{p.get('project_name', '')} {p.get('project_type', '')} {p.get('project_overview', '')}".lower()
        task = f"{p.get('assigned_task', '')} {p.get('position', '')}".lower()
        job = p.get('job_field', '').lower() or "토목"  # Default to 토목 if empty

        matched_reasons = []
        checks = []

        # Check construction types
        if construction_types:
            matched_ct = [ct for ct in construction_types if ct.lower() in text]
            if matched_ct:
                checks.append(True)
                matched_reasons.append(f"공종: {matched_ct[0]}")
            else:
                checks.append(False)

        # Check roles
        if roles:
            if include_blank_duty and not task.strip():
                checks.append(True)
                matched_reasons.append("담당업무: (빈칸 허용)")
            else:
                matched_role = [r for r in roles if r.lower() in task]
                if matched_role:
                    checks.append(True)
                    matched_reasons.append(f"담당업무: {matched_role[0]}")
                else:
                    checks.append(False)

        # Check job fields
        if job_fields:
            matched_jf = [jf for jf in job_fields if jf.lower() in job]
            if matched_jf:
                checks.append(True)
                matched_reasons.append(f"직무분야: {matched_jf[0]}")
            else:
                checks.append(False)

        if checks and all(checks):
            p['is_relevant'] = True
            p['match_reason'] = ", ".join(matched_reasons)

    return projects


def _classify_batch_with_llm(
    batch: List[Dict[str, Any]],
    batch_start_idx: int,
    filter_criteria: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Classify a single batch of projects with LLM using strict AND logic.

    Args:
        batch: List of projects in this batch
        batch_start_idx: The starting index of this batch in the original list
        filter_criteria: Filter criteria for classification

    Returns:
        The batch with is_relevant and match_reason fields added
    """
    # Build compact project list for this batch
    project_lines = []
    for i, p in enumerate(batch):
        line = f"{i}|{p.get('project_name', '')[:60]}|{p.get('project_type', '')}|{p.get('assigned_task', '')}|{p.get('job_field', '')}"
        project_lines.append(line)

    projects_text = "\n".join(project_lines)

    # Extract criteria from filter_criteria
    construction_types = filter_criteria.get("construction_types", [])
    roles = filter_criteria.get("roles", [])
    job_fields = filter_criteria.get("job_fields", [])

    # Build explicit keyword lists for strict matching
    ct_keywords = ', '.join(f'"{ct}"' for ct in construction_types) if construction_types else "없음"
    role_keywords = ', '.join(f'"{r}"' for r in roles) if roles else "없음"
    jf_keywords = ', '.join(f'"{jf}"' for jf in job_fields) if job_fields else "없음"

    prompt = f"""**키워드 매칭 분류 (AND 조건 - 모든 조건 필수)**

검색할 키워드:
- 공종 키워드: [{ct_keywords}]
- 담당업무 키워드: [{role_keywords}]
- 직무분야 키워드: [{jf_keywords}]

**분류 규칙:**
1. 공종: "사업명" 또는 "공사종류" 열에 공종 키워드 중 하나가 **문자열로 포함**되어야 함
   - 예: "하수도정비사업"에 "하수도" 포함 → 충족
   - 예: "국도건설공사"에 "하수도" 미포함 → 불충족
2. 담당업무: "담당업무" 열에 담당업무 키워드 중 하나가 **문자열로 포함**되어야 함
3. 직무분야: "직무분야" 열이 직무분야 키워드 중 하나를 **포함**해야 함 (빈칸이면 "토목"으로 간주)

**중요**: 세 조건 모두 충족해야 r=1. 하나라도 불충족시 r=0.

프로젝트 (i|사업명|공사종류|담당업무|직무분야):
{projects_text}

각 프로젝트 검사:
- i=0: 사업명/공사종류에 {ct_keywords} 중 하나 포함? 담당업무에 {role_keywords} 중 하나 포함? 직무분야에 {jf_keywords} 포함?
- 모두 충족시만 r=1, reason에 매칭된 키워드만 기재
- 하나라도 불충족시 r=0, reason에 "공종 불충족" 또는 "담당업무 불충족" 등 기재

JSON만 출력 (설명 금지):
[{{"i":0,"r":0,"reason":"공종 불충족"}},{{"i":1,"r":1,"reason":"공종:하수도,담당업무:감독,직무분야:토목"}}]"""

    response = _call_ollama_for_classification(prompt)

    # Parse LLM response
    try:
        response = re.sub(r"```json|```", "", response).strip()
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            response = match.group(0)

        results = json.loads(response)

        # Apply results to batch
        for r in results:
            idx = r.get("i", r.get("index", -1))
            is_rel = r.get("r", r.get("is_relevant", 0))
            reason = r.get("reason", "")
            if 0 <= idx < len(batch):
                batch[idx]['is_relevant'] = bool(is_rel) if isinstance(is_rel, int) else is_rel
                batch[idx]['match_reason'] = reason

    except Exception as e:
        print(f"[Step3 LLM] Batch parse error: {e}, using keyword matching for this batch")
        # Fallback to keyword-based matching for this batch
        batch = _classify_projects_with_keywords(batch, filter_criteria)

    # POST-VALIDATION: Override LLM results with strict keyword check
    # This ensures LLM doesn't mark non-matching projects as relevant
    for p in batch:
        if p.get('is_relevant', False):
            # Verify with keyword matching
            text = f"{p.get('project_name', '')} {p.get('project_type', '')}".lower()
            task = f"{p.get('assigned_task', '')}".lower()
            job = p.get('job_field', '').lower() or "토목"

            # Check construction_types - MUST contain keyword
            ct_match = False
            matched_ct = ""
            if construction_types:
                for ct in construction_types:
                    if ct.lower() in text:
                        ct_match = True
                        matched_ct = ct
                        break
            else:
                ct_match = True  # No filter = pass

            # Check roles - MUST contain keyword
            role_match = False
            matched_role = ""
            if roles:
                for r in roles:
                    if r.lower() in task:
                        role_match = True
                        matched_role = r
                        break
            else:
                role_match = True  # No filter = pass

            # Check job_fields - MUST contain keyword
            jf_match = False
            matched_jf = ""
            if job_fields:
                for jf in job_fields:
                    if jf.lower() in job:
                        jf_match = True
                        matched_jf = jf
                        break
            else:
                jf_match = True  # No filter = pass

            # All must match (AND logic)
            if ct_match and role_match and jf_match:
                # Build accurate reason
                reasons = []
                if matched_ct:
                    reasons.append(f"공종:{matched_ct}")
                if matched_role:
                    reasons.append(f"담당업무:{matched_role}")
                if matched_jf:
                    reasons.append(f"직무분야:{matched_jf}")
                p['match_reason'] = ",".join(reasons) if reasons else p.get('match_reason', '')
            else:
                # LLM was wrong - override to not relevant
                p['is_relevant'] = False
                p['match_reason'] = ""

    return batch


def _classify_projects_with_llm(
    projects: List[Dict[str, Any]],
    filter_criteria: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Use LLM to classify projects with detailed match reasons.
    Processes in batches with parallel execution for speed.

    Returns list of projects with added 'is_relevant' and 'match_reason' fields.
    """
    from config import STEP3_SKIP_LLM, STEP3_LLM_WORKERS
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import copy

    BATCH_SIZE = 20  # Process 20 projects at a time
    MAX_WORKERS = STEP3_LLM_WORKERS  # Number of parallel LLM requests

    if not projects:
        return []

    # Build criteria lists
    construction_types = filter_criteria.get("construction_types", [])
    roles = filter_criteria.get("roles", [])
    job_fields = filter_criteria.get("job_fields", [])

    if not construction_types and not roles and not job_fields:
        # No criteria, mark all as 기타
        for p in projects:
            p['is_relevant'] = False
            p['match_reason'] = ""
        return projects

    # Skip LLM if configured - use fast keyword matching
    if STEP3_SKIP_LLM:
        print(f"[Step3] Using keyword matching (STEP3_SKIP_LLM=true)")
        return _classify_projects_with_keywords(projects, filter_criteria)

    # Prepare batches
    batches = []
    total_batches = (len(projects) + BATCH_SIZE - 1) // BATCH_SIZE
    for batch_num in range(total_batches):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, len(projects))
        # Deep copy to avoid mutation issues in parallel execution
        batch = [copy.deepcopy(p) for p in projects[start_idx:end_idx]]
        batches.append((batch_num, start_idx, batch))

    print(f"[Step3 LLM] Processing {len(projects)} projects in {total_batches} batches (parallel workers: {MAX_WORKERS})")

    # Process batches in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_batch = {
            executor.submit(_classify_batch_with_llm, batch, start_idx, filter_criteria): batch_num
            for batch_num, start_idx, batch in batches
        }

        for future in as_completed(future_to_batch):
            batch_num = future_to_batch[future]
            try:
                classified_batch = future.result()
                results[batch_num] = classified_batch
                print(f"[Step3 LLM] Batch {batch_num + 1}/{total_batches} complete")
            except Exception as e:
                print(f"[Step3 LLM] Batch {batch_num + 1} failed: {e}, using keyword fallback")
                # Fallback to keyword matching for failed batch
                _, start_idx, batch = batches[batch_num]
                results[batch_num] = _classify_projects_with_keywords(batch, filter_criteria)

    # Reassemble in order
    classified_projects = []
    for batch_num in range(total_batches):
        classified_projects.extend(results.get(batch_num, []))

    return classified_projects


def get_final_report_with_llm(
    step1_rules: Dict[str, bool],
    step2_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate Step 3 report using LLM to filter Step 2 data based on Step 1 checked rules.

    Uses LLM for semantic matching instead of keyword-only matching for better accuracy.

    Args:
        step1_rules: Dict of rule_id -> bool (True = checked/applicable)
        step2_data: List of career entry dicts from Step 2

    Returns:
        Final report JSON with filtered results
    """
    if not step2_data:
        return {}

    # Extract checked rule IDs (remove "rule__" prefix)
    checked_rules = set(
        rule_id.replace("rule__", "")
        for rule_id, is_checked in step1_rules.items()
        if is_checked
    )

    if not checked_rules:
        print("[Step3] No checked rules found, showing all as 기타")
        return _build_report_from_filtered(step2_data, [], step2_data, [])

    # Build filter criteria from checked rules
    print(f"[Step3] Checked rules: {checked_rules}")
    filter_criteria = _extract_filter_criteria(checked_rules)
    print(f"[Step3] Filter criteria: {filter_criteria}")
    print(f"[Step3] construction_types={filter_criteria.get('construction_types')}")
    print(f"[Step3] roles={filter_criteria.get('roles')}")
    print(f"[Step3] job_fields={filter_criteria.get('job_fields')}")

    # Convert to DataFrame for easier processing
    df = pd.DataFrame(step2_data)

    print(f"[Step3 LLM] Total records to classify: {len(df)}")

    # Get engineer name and primary field
    try:
        engineer_name = df['person_name'].mode()[0]
    except (KeyError, IndexError):
        engineer_name = "Unknown"

    try:
        df['clean_field'] = df['job_field'].astype(str).apply(lambda x: x.split()[0])
        primary_field = df['clean_field'].mode()[0]
    except (KeyError, IndexError):
        primary_field = "토목"

    # Convert DataFrame to list of dicts for LLM classification
    projects_list = df.to_dict('records')

    # Use LLM to classify projects
    classified_projects = _classify_projects_with_llm(projects_list, filter_criteria)

    # Separate into relevant and other
    relevant_projects = []
    other_projects = []
    applied_rules_display = []

    for proj in classified_projects:
        if proj.get('is_relevant', False):
            relevant_projects.append({
                "용역명": proj.get("project_name", ""),
                "발주기관": proj.get("client", ""),
                "공사종류": proj.get("project_type", ""),
                "직무분야": proj.get("job_field", ""),
                "참여기간": f"{proj.get('participation_period_start', '')} ~ {proj.get('participation_period_end', '')}",
                "인정일수": f"{proj.get('recognized_days', '')}일",
                "담당업무": proj.get("assigned_task", "") or proj.get("position", ""),
                "적용규칙": proj.get("match_reason", "")
            })
            if proj.get("match_reason"):
                applied_rules_display.append(proj.get("match_reason"))
        else:
            other_projects.append({
                "용역명": proj.get("project_name", ""),
                "발주기관": proj.get("client", ""),
                "공사종류": proj.get("project_type", ""),
                "직무분야": proj.get("job_field", ""),
                "참여기간": f"{proj.get('participation_period_start', '')} ~ {proj.get('participation_period_end', '')}",
                "인정일수": f"{proj.get('recognized_days', '')}일",
                "담당업무": proj.get("assigned_task", "") or proj.get("position", "")
            })

    # Build applied rules description for display
    applied_rules_summary = list(set(applied_rules_display))

    print(f"[Step3 LLM] Classification complete: {len(relevant_projects)} 해당분야, {len(other_projects)} 기타")

    return {
        "career_history": {
            "header": {
                "division": "책임건설사업관리기술인",
                "name": engineer_name,
                "field": primary_field,
                "filter_conditions": filter_criteria,
                "applied_rules": applied_rules_summary,
                "summary": {
                    "relevant_count": len(relevant_projects),
                    "other_count": len(other_projects),
                    "total_count": len(relevant_projects) + len(other_projects)
                }
            },
            "relevant": relevant_projects,
            "other": other_projects
        },
        "data_breakdown": get_data_breakdown(step2_data)
    }


def _extract_filter_criteria(checked_rules: set) -> Dict[str, Any]:
    """
    Extract filtering criteria from checked rule IDs.

    Mapping from Step 1 to filtering:
    1. 기간 -> 인정일/참여일 selection (informational)
    3. 공사종류 -> Main category filter
    3.1. 세부공종 -> Detail category filter (AND with 공종)
    4. 담당업무 -> Role filter
    5. 직무분야 -> Job field filter

    상주 직무분야1:
    - 평가 방법: always select
    - 직무분야: filter
    - 담당업무: filter

    상주 직무분야2:
    - 직무분야로 평가: always use
    - 직무분야: filter
    - 담당업무: filter
    - 담당업무 빈칸도 적용: special handling

    Returns dict with filter criteria.
    """
    criteria = {
        "date_type": None,
        "client_types": [],
        "client_filter": None,
        "construction_types": [],
        "detail_types": [],
        "roles": [],
        "job_fields": [],
        "specialty_fields": [],
        "include_blank_duty": False,  # 담당업무 빈칸도 적용
        "include_blank_field": False,  # 공종 빈칸도 적용
    }

    # Map rules to criteria
    for rule in CHECKBOX_RULES:
        rule_id = rule.get("id", "")
        if rule_id not in checked_rules:
            continue

        category = rule.get("category", "")
        group = rule.get("group", "")
        logic = rule.get("logic", {})
        keywords = logic.get("keywords", [])
        label = rule.get("label", "")

        # 1. Date type selection (기간) - informational only
        if rule_id == "date.use_participation":
            criteria["date_type"] = "participation"
        elif rule_id == "date.use_recognition":
            criteria["date_type"] = "recognition"

        # 3. Construction type (공종) - from 상주 해당분야
        if "공종" in group and "세부" not in group and "상주 해당분야" in category:
            criteria["construction_types"].extend(keywords)

        # 3.1. Detail construction type (세부공종)
        if "세부공종" in group:
            criteria["detail_types"].extend(keywords)

        # 4. Roles (담당업무) - from any category
        if "담당업무" in group:
            criteria["roles"].extend(keywords)

        # 5. Job fields (직무분야) - from 상주 직무분야1 or 상주 직무분야2
        if "직무분야" in category:
            if "직무분야" in group or "직무" in group:
                criteria["job_fields"].extend(keywords)
            # Also check 담당업무 in 직무분야 categories
            if "담당업무" in group:
                criteria["roles"].extend(keywords)

        # 6. Specialty fields (기술지원 전문분야)
        if "기술지원" in category and "공종" in group:
            criteria["specialty_fields"].extend(keywords)

        # Special handling: 담당업무 빈칸도 적용
        if "담당업무 빈칸도 적용" in label:
            criteria["include_blank_duty"] = True

        # Special handling: 공종 빈칸도 적용
        if "공종 빈칸도 적용" in label:
            criteria["include_blank_field"] = True

    # Remove duplicates
    for key in ["client_types", "construction_types", "detail_types", "roles", "job_fields", "specialty_fields"]:
        criteria[key] = list(set(criteria[key]))

    return criteria


def _check_project_matches_criteria(
    project: Dict[str, Any],
    criteria: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Check if a project matches the filter criteria using AND logic.

    Mapping Logic (ALL selected criteria must match):
    1. 기간 -> 인정일/참여일 (informational only, doesn't filter)
    3. 공종 -> Must match if selected
    4. 담당업무 -> Must match if selected
    5. 직무분야 -> Must match if selected

    Returns:
        {"is_relevant": bool, "matched_rules": list of matched rule descriptions}
    """
    matched_rules = []

    # Helper function for keyword matching
    def matches_keywords(value: str, keywords: List[str]) -> bool:
        if not value or not keywords:
            return False
        value_lower = str(value).lower()
        return any(kw.lower() in value_lower for kw in keywords)

    def get_matched_keyword(value: str, keywords: List[str]) -> str:
        if not value or not keywords:
            return ""
        value_lower = str(value).lower()
        for kw in keywords:
            if kw.lower() in value_lower:
                return kw
        return ""

    # Track which criteria need to be checked and their results
    criteria_checks = {}

    # Extract project fields - check multiple possible field names
    project_type = str(project.get("project_type", "") or "")
    project_name = str(project.get("project_name", "") or "")
    project_overview = str(project.get("project_overview", "") or "")
    assigned_task = str(project.get("assigned_task", "") or "")
    position = str(project.get("position", "") or "")
    job_field = str(project.get("job_field", "") or "")
    specialty = str(project.get("specialty_field", "") or "")

    # Combine all searchable text for construction type matching
    all_text = f"{project_type} {project_name} {project_overview}".lower()

    # Fallback for job_field - try to infer from specialty or use default
    if not job_field.strip():
        if specialty:
            for kw in ["토목", "건축", "기계", "조경", "안전"]:
                if kw in specialty:
                    job_field = kw
                    break
        # If still empty and we have other civil engineering indicators, assume 토목
        if not job_field.strip():
            civil_keywords = ["도로", "교량", "터널", "하천", "상수", "하수", "철도", "단지", "항만"]
            if any(kw in all_text for kw in civil_keywords):
                job_field = "토목"

    # 3. Check construction type (공종) - REQUIRED if selected
    # Search in: project_type, project_name, project_overview
    if criteria.get("construction_types"):
        matched = matches_keywords(project_type, criteria["construction_types"]) or \
                  matches_keywords(project_name, criteria["construction_types"]) or \
                  matches_keywords(project_overview, criteria["construction_types"])
        criteria_checks["construction_type"] = matched
        if matched:
            matched_kw = get_matched_keyword(project_type, criteria["construction_types"]) or \
                         get_matched_keyword(project_name, criteria["construction_types"]) or \
                         get_matched_keyword(project_overview, criteria["construction_types"])
            matched_rules.append(f"공종: {matched_kw}")

    # 4. Check roles (담당업무) - REQUIRED if selected
    # Search in: assigned_task, position, and also project_overview (sometimes role is embedded there)
    if criteria.get("roles"):
        # Check if 담당업무 빈칸도 적용 is enabled
        include_blank = criteria.get("include_blank_duty", False)

        if include_blank and not assigned_task.strip() and not position.strip():
            # Empty task is allowed
            criteria_checks["role"] = True
            matched_rules.append("담당업무: (빈칸 허용)")
        else:
            matched = matches_keywords(assigned_task, criteria["roles"]) or \
                      matches_keywords(position, criteria["roles"]) or \
                      matches_keywords(project_overview, criteria["roles"])
            criteria_checks["role"] = matched
            if matched:
                matched_kw = get_matched_keyword(assigned_task, criteria["roles"]) or \
                             get_matched_keyword(position, criteria["roles"]) or \
                             get_matched_keyword(project_overview, criteria["roles"])
                matched_rules.append(f"담당업무: {matched_kw}")

    # 5. Check job fields (직무분야) - REQUIRED if selected
    if criteria.get("job_fields"):
        matched = matches_keywords(job_field, criteria["job_fields"])
        criteria_checks["job_field"] = matched
        if matched:
            matched_kw = get_matched_keyword(job_field, criteria["job_fields"])
            matched_rules.append(f"직무분야: {matched_kw}")

    # 6. Check specialty fields (전문분야) - DISABLED
    # Only filter by 공종, 담당업무, 직무분야
    # if criteria.get("specialty_fields"):
    #     matched = matches_keywords(specialty, criteria["specialty_fields"])
    #     criteria_checks["specialty"] = matched
    #     if matched:
    #         matched_kw = get_matched_keyword(specialty, criteria["specialty_fields"])
    #         matched_rules.append(f"전문분야: {matched_kw}")

    # Determine if project is relevant using AND logic
    # All selected criteria must match
    if not criteria_checks:
        # No criteria selected, nothing is relevant
        is_relevant = False
    else:
        # ALL criteria must be True (AND logic)
        is_relevant = all(criteria_checks.values())

    return {
        "is_relevant": is_relevant,
        "matched_rules": matched_rules if is_relevant else [],
        "criteria_checks": criteria_checks  # For debugging
    }


def _build_report_from_filtered(
    step2_data: List[Dict[str, Any]],
    relevant: List[Dict],
    other: List[Dict],
    applied_rules: List[str]
) -> Dict[str, Any]:
    """Build report structure from filtered data."""
    df = pd.DataFrame(step2_data) if step2_data else pd.DataFrame()

    try:
        engineer_name = df['person_name'].mode()[0] if not df.empty else "Unknown"
    except (KeyError, IndexError):
        engineer_name = "Unknown"

    try:
        primary_field = df['job_field'].mode()[0] if not df.empty else "토목"
    except (KeyError, IndexError):
        primary_field = "토목"

    return {
        "career_history": {
            "header": {
                "division": "책임건설사업관리기술인",
                "name": engineer_name,
                "field": primary_field,
                "applied_rules": applied_rules,
                "summary": {
                    "relevant_count": len(relevant),
                    "other_count": len(other),
                    "total_count": len(relevant) + len(other)
                }
            },
            "relevant": relevant,
            "other": other
        }
    }


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
