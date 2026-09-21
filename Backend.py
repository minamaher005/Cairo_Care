"""
Cairo Care — Backend Server Entrypoint
=======================================
Launches the FastAPI application.

Usage:
    python Backend.py
    uvicorn Backend:app --reload --port 8000
"""
import os
import sys

# Ensure repository root is in Python sys.path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.backend.app import app  # noqa: E402

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("Backend:app", host="0.0.0.0", port=8000, reload=True)
