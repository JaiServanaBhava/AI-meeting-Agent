"""Central Configuration for AI Chief of Staff Meeting Assistant."""

import os
import sys
from pathlib import Path

# Disable CrewAI telemetry completely to avoid thread signal registration issues in Streamlit
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["CREWAI_DISABLE_TRACKING"] = "true"

# Monkey-patch Telemetry._register_signal_handler to prevent ValueError in Streamlit worker threads
try:
    import crewai.telemetry.telemetry as _crewai_tm
    _crewai_tm.Telemetry._register_signal_handler = lambda *args, **kwargs: None
except Exception:
    pass

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Load .env from current directory or parent directory
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if DOTENV_AVAILABLE:
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH)
    else:
        load_dotenv()
elif ENV_PATH.exists():
    # Simple built-in parser for .env if python-dotenv is not installed
    try:
        with open(ENV_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass


# Google Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

# Audio and Transcription Settings
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
HF_TOKEN = os.getenv("HF_TOKEN", "")

# Database
DB_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "database/meetings.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Audio Storage Folders
RECORDINGS_DIR = BASE_DIR / "audio" / "recordings"
UPLOADS_DIR = BASE_DIR / "audio" / "uploads"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# SMTP Credentials (Optional)
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_RECEIVER = os.getenv("SMTP_RECEIVER", "")
