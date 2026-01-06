@echo off
chcp 65001 >nul
pushd "%~dp0"
python -m streamlit --version >nul 2>&1 || pip install -r requirements.txt
start "" http://localhost:8501/
streamlit run Home.py --server.headless true
