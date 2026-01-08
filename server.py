from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
import pandas as pd
from pathlib import Path
from config import PDF_DIR, STEP1_INDEX_DIR
from ingest import ingest_step1_multiple, get_final_report_json, get_final_report_with_llm, main_extractor, clear_pdfs, clear_index
from rag import get_step1_data
from report_utils import get_form_layout
from semantic_normalizer import normalize_project
from rules_engine import apply_all_checkbox_rules

app = Flask(__name__, static_folder='publics', static_url_path='')
CORS(app)

# Global state management (in production, use proper session management or database)
session_data = {}

def ensure_indices_exist():
    """Ensure FAISS index directories exist, create if missing"""
    try:
        STEP1_INDEX_DIR.mkdir(parents=True, exist_ok=True)
        # Check if index files exist, if not, initialize empty state
        faiss_file = STEP1_INDEX_DIR / "index.faiss"
        if not faiss_file.exists():
            print(f"[Server] Warning: FAISS index not initialized at {STEP1_INDEX_DIR}")
            print("[Server] Index will be created when first PDFs are uploaded")
    except Exception as e:
        print(f"[Server] Warning: Could not verify index directory: {e}")

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('publics', 'index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "PQ Analysis API is running"})

@app.route('/api/upload-criteria', methods=['POST'])
def upload_criteria():
    """
    Step 1: Upload PDF files for criteria extraction
    """
    try:
        if 'files' not in request.files:
            return jsonify({"error": "No files uploaded"}), 400

        files = request.files.getlist('files')
        if not files:
            return jsonify({"error": "No files selected"}), 400

        # Clear previous data
        clear_pdfs()
        clear_index()

        # Save uploaded files
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        saved_paths = []

        for file in files:
            if file.filename.endswith('.pdf'):
                path = PDF_DIR / f"s1_{uuid.uuid4().hex}.pdf"
                file.save(str(path))
                saved_paths.append(str(path))

        if not saved_paths:
            return jsonify({"error": "No valid PDF files uploaded"}), 400

        # Process PDFs
        if ingest_step1_multiple(saved_paths):
            query = "모든 프로젝트 이력을 하나의 JSON 객체로 종합"
            raw_data = get_step1_data(query)

            if raw_data:
                norm = normalize_project(raw_data)
                rules = apply_all_checkbox_rules(norm)

                # Convert pandas Series to dict if needed
                if hasattr(rules, 'to_dict'):
                    rules = rules.to_dict()
                elif not isinstance(rules, dict):
                    rules = dict(rules)

                # Store in session (use session ID in production)
                session_id = str(uuid.uuid4())
                session_data[session_id] = {
                    'step1_norm_data': norm,
                    'step1_rules': rules,
                    'step2_records': []
                }

                # Get form layout
                layout = get_form_layout()

                return jsonify({
                    "success": True,
                    "session_id": session_id,
                    "data": {
                        "engineer_name": norm.get('engineer_name'),
                        "role": norm.get('role'),
                        "layout": layout,
                        "rules": rules
                    }
                })
            else:
                return jsonify({"error": "데이터 추출 실패"}), 500
        else:
            return jsonify({"error": "텍스트를 찾을 수 없습니다"}), 500

    except ImportError as e:
        import traceback
        print(f"[Server] ImportError in upload_criteria: {traceback.format_exc()}")
        return jsonify({"error": f"Missing dependency: {str(e)}"}), 500
    except FileNotFoundError as e:
        import traceback
        print(f"[Server] FileNotFoundError in upload_criteria: {traceback.format_exc()}")
        return jsonify({"error": f"File not found: {str(e)}"}), 500
    except Exception as e:
        import traceback
        print(f"[Server] Error in upload_criteria: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/update-criteria', methods=['POST'])
def update_criteria():
    """
    Update criteria checkboxes
    """
    try:
        data = request.json
        session_id = data.get('session_id')
        updated_rules = data.get('rules', {})

        if session_id not in session_data:
            return jsonify({"error": "Invalid session"}), 400

        # Update rules
        session_data[session_id]['step1_rules'].update(updated_rules)

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload-career', methods=['POST'])
def upload_career():
    """
    Step 2: Upload career PDF and extract data
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        session_id = request.form.get('session_id')

        if not session_id or session_id not in session_data:
            return jsonify({"error": "Invalid session"}), 400

        if not file.filename.endswith('.pdf'):
            return jsonify({"error": "Only PDF files are allowed"}), 400

        # Save file
        path = PDF_DIR / f"s2_{uuid.uuid4().hex}.pdf"
        file.save(str(path))

        # Extract career data
        records = main_extractor(path)

        if records:
            # Convert to dict format
            records_dict = []
            for record in records:
                if hasattr(record, 'to_dict'):
                    records_dict.append(record.to_dict())
                elif isinstance(record, dict):
                    records_dict.append(record)

            session_data[session_id]['step2_records'] = records_dict

            return jsonify({
                "success": True,
                "count": len(records_dict),
                "records": records_dict
            })
        else:
            return jsonify({"error": "OCR 실패"}), 500

    except ImportError as e:
        import traceback
        print(f"[Server] ImportError in upload_career: {traceback.format_exc()}")
        return jsonify({"error": f"Missing dependency: {str(e)}"}), 500
    except FileNotFoundError as e:
        import traceback
        print(f"[Server] FileNotFoundError in upload_career: {traceback.format_exc()}")
        return jsonify({"error": f"File not found: {str(e)}"}), 500
    except Exception as e:
        import traceback
        print(f"[Server] Error in upload_career: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """
    Step 3: Generate final evaluation report
    """
    try:
        data = request.json
        session_id = data.get('session_id')

        if not session_id or session_id not in session_data:
            return jsonify({"error": "Invalid session"}), 400

        session = session_data[session_id]
        step1_rules = session.get('step1_rules', {})
        step2_records = session.get('step2_records', [])

        # Validate that we have career data (Step 2) before generating report
        if not step2_records:
            return jsonify({
                "error": "경력 데이터가 없습니다. 먼저 경력증명서를 업로드해주세요."
            }), 400

        # Convert rules to dict if needed
        if hasattr(step1_rules, 'to_dict'):
            step1_rules = step1_rules.to_dict()

        # Check if we have any rules
        has_checked_rules = bool(step1_rules) and any(v for v in step1_rules.values() if v is True)

        if has_checked_rules:
            report = get_final_report_with_llm(step1_rules, step2_records)
        else:
            report = get_final_report_json(step2_records)

        return jsonify({
            "success": True,
            "report": report
        })

    except ImportError as e:
        import traceback
        print(f"[Server] ImportError in generate_report: {traceback.format_exc()}")
        return jsonify({"error": f"Missing dependency: {str(e)}"}), 500
    except FileNotFoundError as e:
        import traceback
        print(f"[Server] FileNotFoundError in generate_report: {traceback.format_exc()}")
        return jsonify({"error": f"File not found: {str(e)}"}), 500
    except Exception as e:
        import traceback
        print(f"[Server] Error in generate_report: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """
    Get current session data
    """
    if session_id not in session_data:
        return jsonify({"error": "Session not found"}), 404

    session = session_data[session_id]
    return jsonify({
        "success": True,
        "data": {
            "has_step1": session.get('step1_norm_data') is not None,
            "has_step2": len(session.get('step2_records', [])) > 0,
            "step1_data": session.get('step1_norm_data'),
            "step2_count": len(session.get('step2_records', []))
        }
    })

if __name__ == '__main__':
    # Create required directories
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    STEP1_INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # Verify indices
    ensure_indices_exist()

    print("🚀 PQ Analysis API Server Starting...")
    print("📁 Frontend: http://localhost:8501")
    print("🔌 API: http://localhost:8501/api/health")
    print("⚠️  Auto-reload disabled for long-running OCR tasks")

    # Disable reloader to prevent interruption of long OCR tasks
    # Using port 8501 (same as Streamlit) for staging server compatibility
    app.run(host='0.0.0.0', port=8501, debug=True, use_reloader=False)
