@echo off
cd /d "%~dp0backend"
if not exist venv (
  py -m venv venv
)
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
start http://127.0.0.1:5000
python app.py
pause
