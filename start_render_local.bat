@echo off
cd /d %~dp0
py -m pip install -r backend\requirements.txt
py -m backend.app
pause
