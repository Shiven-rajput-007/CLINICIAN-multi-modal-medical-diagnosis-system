@echo off
echo =======================================================
echo Starting Multi-Modal Medical Diagnosis Assistant Frontend
echo =======================================================

cd /d "%~dp0\frontend"
echo Starting Vite development server at http://localhost:5173 ...
npm run dev
