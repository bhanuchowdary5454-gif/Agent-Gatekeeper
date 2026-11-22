@echo off
title AirGuard AI - Delta Air Lines Gatekeeper
cd /d "%~dp0"
echo Starting AirGuard AI Streamlit Dashboard...
"C:\Users\bhanu\anaconda3\python.exe" -m streamlit run app.py
pause
