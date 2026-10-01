@echo off
echo =======================================================
echo Starting Multi-Modal Medical Diagnosis Assistant Backend
echo =======================================================

cd /d "%~dp0backend"
call ..\.venv\Scripts\activate.bat

echo Running Alembic database migrations...
alembic upgrade head
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Database migrations failed.
    pause
    exit /b %ERRORLEVEL%
)

echo Starting FastAPI application server at http://127.0.0.1:8000 ...
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
