"""
Cairo Care — Frontend UI Entrypoint
====================================
Launches the unified Streamlit user interface.

Usage:
    streamlit run frontend.py
    # or:
    streamlit run src/frontend/app.py
"""
import os
import sys
import runpy

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

frontend_main = os.path.join(ROOT_DIR, "src", "frontend", "app.py")
runpy.run_path(frontend_main, run_name="__main__")