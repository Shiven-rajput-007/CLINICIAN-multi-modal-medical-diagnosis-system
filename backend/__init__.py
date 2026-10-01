"""
Backend package initialization.
Configures python system path and module aliases for seamless root-level
and backend-level import resolution across local and containerized/Render deployments.
"""
import sys
from pathlib import Path

# Add backend directory to sys.path so 'app' is directly discoverable
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent

for _p in [str(_CURRENT_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Expose app module
try:
    from . import app  # noqa: F401
    if "backend.app" not in sys.modules and "app" in sys.modules:
        sys.modules["backend.app"] = sys.modules["app"]
except ImportError:
    pass
