#!/usr/bin/env python3
"""
Startup script for the Portfolio Management Backend API
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn

    from backend.main import app as _app  # noqa: F401

    # Run the FastAPI app using import string so reload works reliably
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(project_root)],
    )
