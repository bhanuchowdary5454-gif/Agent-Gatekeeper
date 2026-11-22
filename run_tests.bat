@echo off
title AirGuard AI - Automated Tests
cd /d "%~dp0"
echo Running AirGuard AI Test Suite...
"C:\Users\bhanu\anaconda3\python.exe" test_airguard.py
pause
