# PQ Analysis Engine - MVP

Construction career document matching and PQ (Pre-Qualification) analysis system with AI-powered extraction and evaluation.

## Features

- **기준 정보 관리**: Upload and analyze RFP/PQ criteria documents
- **경력 데이터 분석**: Extract career data from PDF documents using OCR and AI
- **최종 평가 리포트**: Generate comprehensive evaluation reports with matching criteria

## Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment support
- Tesseract OCR (for PDF text extraction)
- Ollama (for local LLM processing)

### Installation

1. Clone the repository
2. Create and activate virtual environment:

```bash
# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

### Option 1: Web Interface (MVP) - **Recommended**

The new Flask-based web interface provides a modern, user-friendly experience:

**Windows:**
```bash
start_server.bat
```

**Linux/Mac:**
```bash
chmod +x start_server.sh
./start_server.sh
```

**Or manually:**
```bash
python server.py
```

Then access the web interface at: **http://localhost:8501**

API documentation available at: **http://localhost:8501/api/health**

### Option 2: Streamlit Interface (Legacy)

**Note:** The Flask server now uses port 8501 (previously used by Streamlit) for staging server compatibility. To run the legacy Streamlit interface, use a different port:

```bash
streamlit run app.py --server.port 8502 --server.address 127.0.0.1
```

Access at: **http://localhost:8502**

## Production Deployment

### Online Service
- Running as systemd service: `sudo systemctl reload career-demo.service`
- Access URL: https://ai-test.rs-team.com

## API Endpoints

The Flask server provides the following REST API endpoints:

- `GET /` - Serve the web interface
- `GET /api/health` - Health check
- `POST /api/upload-criteria` - Upload criteria documents (Step 1)
- `POST /api/update-criteria` - Update criteria checkboxes
- `POST /api/upload-career` - Upload career documents (Step 2)
- `POST /api/generate-report` - Generate final evaluation report (Step 3)
- `GET /api/session/<session_id>` - Get session data

## Project Structure

```
├── server.py              # Flask web server (NEW)
├── app.py                 # Streamlit app (legacy)
├── publics/
│   └── index.html        # Web frontend
├── config.py             # Configuration
├── ingest.py             # PDF ingestion and processing
├── rag.py                # RAG implementation
├── llm_helper.py         # LLM integration
├── rules_engine.py       # Business rules
├── semantic_normalizer.py # Data normalization
└── report_utils.py       # Report generation

```

## Workflow

1. **Upload Criteria** (기준 정보 관리)
   - Upload RFP/PQ PDF documents
   - AI extracts and analyzes criteria
   - Review and adjust checkboxes

2. **Extract Career Data** (경력 데이터 분석)
   - Upload career certificate PDF
   - OCR + LLM extracts structured data
   - Review extracted records

3. **Generate Report** (최종 평가 리포트)
   - Apply criteria to career data
   - Generate evaluation report
   - View relevant/other project classifications

## Technologies

- **Backend**: Flask, Python
- **Frontend**: HTML, TailwindCSS, JavaScript
- **AI/ML**: LangChain, Anthropic Claude, Ollama
- **OCR**: PyMuPDF, Tesseract
- **Vector DB**: FAISS
- **Legacy UI**: Streamlit

## License

Proprietary
