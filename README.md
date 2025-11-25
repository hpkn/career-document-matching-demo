<!-- Active the environment -->
python3 -m venv .venv
source .venv/bin/activate

streamlit run app.py

sudo systemctl reload career-demo.service
