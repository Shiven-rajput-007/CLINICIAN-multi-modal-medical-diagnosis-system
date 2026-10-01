"""
Production entrypoint for FastAPI backend.
Exposes the real production application from app.main.
Ensures universal compatibility whether Render or Docker runs:
  uvicorn backend.main:app --host 0.0.0.0 --port $PORT
or
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
"""
import sys
from pathlib import Path

# Ensure backend directory and project root are discoverable
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent

for _p in [str(_CURRENT_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.main import app, settings  # Re-export production FastAPI application

if __name__ == "__main__":
    import uvicorn
    host = settings.server_host
    port = settings.server_port
    uvicorn.run("backend.main:app", host=host, port=port, reload=settings.DEBUG)
