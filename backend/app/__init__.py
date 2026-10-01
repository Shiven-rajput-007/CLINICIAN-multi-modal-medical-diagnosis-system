"""
Multi-Modal Medical Diagnosis Assistant App Package.
Provides dual module aliasing so imports under 'app' and 'backend.app'
resolve seamlessly across environments.
"""
import sys

if "backend.app" not in sys.modules:
    sys.modules["backend.app"] = sys.modules[__name__]
