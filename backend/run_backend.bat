@echo off
title PreciousEdu FastAPI Backend
cd /d "%~dp0"
echo Starting PreciousEdu FastAPI Backend on http://localhost:8000 ...
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
