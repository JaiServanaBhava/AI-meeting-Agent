"""Convenience launcher for the Chief of Staff Streamlit App."""

import os
import sys
from pathlib import Path

# Disable CrewAI telemetry completely to avoid thread signal registration issues in Streamlit
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["CREWAI_DISABLE_TRACKING"] = "true"

try:
    import crewai.telemetry.telemetry as _crewai_tm
    _crewai_tm.Telemetry._register_signal_handler = lambda *args, **kwargs: None
except Exception:
    pass

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import and execute the main frontend app
from frontend.app import *
