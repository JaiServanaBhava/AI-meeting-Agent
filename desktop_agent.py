"""AI Chief of Staff — Standalone Desktop Agent with Automatic Meeting Detection.

Runs in terminal as a pure Python app, opens a sleek native Desktop Pop-Up Window
with modern HTML5/CSS3 UI (via pywebview), automatically detects Google Meet / Zoom,
records audio continuously, and autonomously executes the 5-Agent pipeline.

Works on both macOS and Windows.
"""

import os
import sys
import json
import time
import uuid
import shutil
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import quote, urlencode

# ── Telemetry suppression ──────────────────────────────────────────────────────
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["CREWAI_DISABLE_TRACKING"] = "true"

try:
    import crewai.telemetry.telemetry as _crewai_tm
    _crewai_tm.Telemetry._register_signal_handler = lambda *args, **kwargs: None
except Exception:
    pass

# ── Path setup ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# ── Desktop save folder on user's Desktop ─────────────────────────────────────
DESKTOP_FOLDER = Path.home() / "Desktop" / "ChiefOfStaff"
RECORDINGS_FOLDER = DESKTOP_FOLDER / "Recordings"
REPORTS_FOLDER = DESKTOP_FOLDER / "Reports"
MEMORIES_FILE = DESKTOP_FOLDER / "memories.json"

for _d in [RECORDINGS_FOLDER, REPORTS_FOLDER]:
    _d.mkdir(parents=True, exist_ok=True)

# ── Project imports ────────────────────────────────────────────────────────────
import config
from database.db import init_db, save_meeting_bundle
from services.detector import MeetingDetector
from services.recorder_service import BackgroundMeetingRecorder
from audio.transcriber import MeetingTranscriber
from agents.meeting_crew import ChiefOfStaffMeetingCrew
from memory.memory_manager import MemoryManager
from frontend.desktop_html import DESKTOP_HTML

try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False


# ── Desktop persistence helpers ────────────────────────────────────────────────

def safe_js(window_ref, fn_name: str, args_json: str = "", retries: int = 80, delay: float = 0.25):
    """Call a JavaScript window.fn_name safely.
    Waits until the page is off about:blank AND the function is defined.
    This is the only safe way to bridge Python->JS in pywebview."""
    if not window_ref:
        return
    call = f"window.{fn_name}({args_json})"
    for i in range(retries):
        try:
            url = window_ref.get_current_url() or ""
            # Wait while still on the initial blank page
            if not url or "about:blank" in url or url.strip() == "":
                time.sleep(delay)
                continue
            result = window_ref.evaluate_js(f"typeof window.{fn_name}")
            if result == "function":
                window_ref.evaluate_js(call)
                return
        except Exception:
            pass
        time.sleep(delay)
    # Final attempt regardless
    try:
        window_ref.evaluate_js(call)
    except Exception as e:
        print(f"[JS] Could not call {fn_name}: {e}")

def load_memories() -> dict:
    """Load saved stats and last-session data from desktop JSON file."""
    if MEMORIES_FILE.exists():
        try:
            return json.loads(MEMORIES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"meetings": [], "total_meetings": 0, "total_tasks": 0, "total_promises": 0}


def save_memories(memories: dict):
    """Persist memories to desktop JSON file."""
    try:
        MEMORIES_FILE.write_text(json.dumps(memories, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"[Memory] Warning: Could not save memories — {e}")


def save_report_to_desktop(bundle: dict):
    """Save a human-readable markdown report + the raw JSON to the Desktop folder."""
    safe_name = (bundle.get("title") or "Meeting").replace(" ", "_")[:60]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = REPORTS_FOLDER / f"{ts}_{safe_name}"

    # Markdown report
    tasks_md = "\n".join(
        f"  - [{t.get('priority','Med')}] {t.get('task','')} — {t.get('owner','')} (Due: {t.get('deadline','')})"
        for t in (bundle.get("action_items") or [])
    )
    decisions_md = "\n".join(f"  - {d}" for d in (bundle.get("key_decisions") or []))
    md = (
        f"# {bundle.get('title','Meeting Summary')}\n"
        f"**Date:** {bundle.get('created_at', 'Unknown')}\n\n"
        f"## Executive Summary\n{bundle.get('summary', '')}\n\n"
        f"## Key Decisions\n{decisions_md or '  (none)'}\n\n"
        f"## Action Items\n{tasks_md or '  (none)'}\n\n"
        f"## Transcript\n```\n{bundle.get('labeled_transcript', '')}\n```\n"
    )
    (base.with_suffix(".md")).write_text(md, encoding="utf-8")

    # JSON bundle
    (base.with_suffix(".json")).write_text(
        json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[Saved] 📂 Report saved to {REPORTS_FOLDER}")


class DesktopAgentAPI:
    """Python bridge exposed to the HTML/JavaScript Desktop Window."""

    def __init__(self, agent_controller: "StandaloneMeetingAgent"):
        self.agent = agent_controller

    def start_manual_recording(self):
        """Called when user clicks 'Start Recording' manually."""
        self.agent.start_recording(
            meeting_title="Manual Recording Session",
            app_name="Microphone",
            is_auto=False,
        )
        return {"status": "recording"}

    def stop_and_analyze(self):
        """Called when user clicks 'End Meeting & Analyze'."""
        self.agent.is_auto_recording = False
        self.agent._awaiting_candidate_exit = True
        threading.Thread(target=self.agent.stop_and_analyze, daemon=True).start()
        return {"status": "analyzing"}

    def run_demo_simulation(self):
        """Runs instant demo pipeline without needing a real meeting."""
        threading.Thread(target=self.agent.run_demo_pipeline, daemon=True).start()
        return {"status": "demo_running"}

    def clear_all_meetings(self):
        """Delete all meeting data and reset persisted desktop meeting memory."""
        if self.agent.recorder.is_recording() or self.agent._analyzing:
            return {"ok": False, "error": "Stop the active meeting before clearing data."}

        try:
            from database.db import clear_all_meetings

            if self.agent.recorder.is_monitoring():
                self.agent.recorder.stop_monitoring()
            self.agent._awaiting_candidate_exit = True
            clear_all_meetings()
            self.agent.memories = {
                "meetings": [],
                "total_meetings": 0,
                "total_tasks": 0,
                "total_promises": 0,
            }
            save_memories(self.agent.memories)
            return self.get_initial_data()
        except Exception as e:
            print(f"[API] Error clearing meeting data: {e}")
            return {"ok": False, "error": str(e)}

    def open_email_draft(self, recipients, subject: str, body: str):
        """Open a reviewed, prefilled email in the system's default mail app."""
        import re

        addresses = [str(value).strip() for value in (recipients or []) if str(value).strip()]
        if not addresses:
            return {"ok": False, "error": "Add at least one valid email address."}
        if any(
            not re.fullmatch(r"[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+", address)
            or address.rsplit("@", 1)[1].lower() in {"example.com", "example.org", "example.net"}
            for address in addresses
        ):
            return {"ok": False, "error": "Replace placeholder or invalid email addresses first."}

        mailto = "mailto:" + quote(",".join(addresses), safe="@,._+-")
        mailto += "?" + urlencode({"subject": str(subject or "")[:200], "body": str(body or "")[:12000]})
        try:
            if webbrowser.open(mailto, new=1):
                return {"ok": True}
            return {"ok": False, "error": "No default email app could open the draft."}
        except Exception as e:
            print(f"[Email] Could not open default mail app: {e}")
            return {"ok": False, "error": str(e)}

    def set_auto_detect(self, enabled: bool):
        """Toggles auto-detection on or off."""
        self.agent.auto_detect_enabled = bool(enabled)
        return {"auto_detect": self.agent.auto_detect_enabled}

    def save_api_key(self, key: str):
        """Writes GEMINI_API_KEY to the .env file and activates it immediately."""
        key = (key or "").strip()
        if not key:
            return {"ok": False, "error": "Empty key"}

        env_path = BASE_DIR / ".env"
        try:
            if env_path.exists():
                content = env_path.read_text(encoding="utf-8")
                if "GEMINI_API_KEY=" in content:
                    import re as _re
                    content = _re.sub(
                        r"^GEMINI_API_KEY=.*$", f"GEMINI_API_KEY={key}", content, flags=_re.MULTILINE
                    )
                else:
                    content += f"\nGEMINI_API_KEY={key}\n"
            else:
                content = f"GEMINI_API_KEY={key}\n"

            env_path.write_text(content, encoding="utf-8")
        except Exception as e:
            print(f"[Settings] Could not write .env: {e}")
            return {"ok": False, "error": str(e)}

        # Activate immediately without restart
        os.environ["GEMINI_API_KEY"] = key
        import config as _cfg
        _cfg.GEMINI_API_KEY = key
        from services.gemini_service import GeminiService
        GeminiService._native_client = None  # reset cached client so it re-inits with new key
        print(f"[Settings] ✅ Gemini API key saved and activated.")
    def get_audio_status(self):
        """Returns real-time audio volume, dB level, and microphone activity."""
        try:
            return self.agent.recorder.get_audio_level()
        except Exception as e:
            return {"volume_percent": 0.0, "peak_db": -60.0, "is_recording": False, "is_active": False, "duration_seconds": 0}

    def get_initial_data(self):
        """Returns stats, latest meeting bundle, history, tasks, and commitments for immediate frontend hydration."""
        from database.db import (
            get_system_stats,
            get_latest_meeting_bundle,
            get_all_meetings,
            get_action_items,
            get_commitments,
        )
        try:
            stats = get_system_stats()
            latest_bundle = get_latest_meeting_bundle()
            if not latest_bundle and self.agent.memories.get("last_bundle"):
                latest_bundle = self.agent.memories.get("last_bundle")

            history = get_all_meetings()
            tasks = get_action_items()
            commitments = get_commitments()

            return {
                "ok": True,
                "stats": stats,
                "latest_bundle": latest_bundle,
                "history": history,
                "tasks": tasks,
                "commitments": commitments,
            }
        except Exception as e:
            print(f"[API] Error getting initial data: {e}")
            return {"ok": False, "error": str(e)}

    def get_meeting_history(self):
        """Returns list of all saved meetings from SQLite database."""
        from database.db import get_all_meetings
        try:
            return get_all_meetings()
        except Exception as e:
            print(f"[API] Error getting meeting history: {e}")
            return []

    def load_meeting(self, meeting_id: str):
        """Loads and returns full details of a specific past meeting."""
        from database.db import get_meeting_bundle_full
        try:
            bundle = get_meeting_bundle_full(meeting_id)
            if bundle:
                return {"ok": True, "bundle": bundle}
        except Exception as e:
            print(f"[API] Error loading meeting {meeting_id}: {e}")
        return {"ok": False}

    def get_action_items_board(self):
        """Returns all action items across all meetings for the task board."""
        from database.db import get_action_items
        try:
            return get_action_items()
        except Exception as e:
            print(f"[API] Error getting action items: {e}")
            return []

    def toggle_action_item_status(self, item_id: int, current_status: str):
        """Toggles action item between Completed and Pending."""
        from database.db import update_action_item_status, get_action_items
        try:
            new_status = "Completed" if current_status != "Completed" else "Pending"
            update_action_item_status(int(item_id), new_status)
            return {"ok": True, "new_status": new_status, "items": get_action_items()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_commitments_board(self):
        """Returns all tracked cross-meeting commitments."""
        from database.db import get_commitments
        try:
            return get_commitments()
        except Exception as e:
            print(f"[API] Error getting co
                  mmitments: {e}")
            return []

    def ask_gemini_threaded(self, query: str, meeting_id: Optional[str] = None):
        """Runs Gemini Q&A in a dedicated background thread without freezing pywebview UI."""
        query = (query or "").strip()
        if not query:
            return {"ok": False, "error": "Query cannot be empty"}

        def _worker():
            try:
                from services.gemini_service import GeminiService
                from memory.memory_manager import MemoryManager
                from database.db import get_meeting_bundle_full
                
                recent_bundle = None
                if meeting_id:
                    recent_bundle = get_meeting_bundle_full(meeting_id)
                if not recent_bundle:
                    recent_bundle = self.agent.memories.get("last_bundle", {})

                mem_context = ""
                try:
                    mem_context = MemoryManager().get_past_context()
                except Exception:
                    pass

                prompt = (
                    "You are the AI Chief of Staff, an intelligent meeting executive assistant.\n"
                    "Answer the user's question clearly, helpfully, and concisely with markdown formatting.\n\n"
                    f"--- RECENT MEETING CONTEXT ---\n"
                    f"Title: {recent_bundle.get('title', 'Recent Meeting')}\n"
                    f"Summary: {recent_bundle.get('summary', 'None')}\n"
                    f"Key Decisions: {json.dumps(recent_bundle.get('key_decisions', []))}\n"
                    f"Action Items: {json.dumps(recent_bundle.get('action_items', []))}\n"
                    f"Commitments: {json.dumps(recent_bundle.get('commitments', []))}\n"
                    f"Transcript excerpt: {str(recent_bundle.get('labeled_transcript', ''))[:2500]}\n\n"
                    f"--- HISTORICAL MEMORY CONTEXT ---\n"
                    f"{mem_context}\n\n"
                    f"--- USER QUESTION ---\n"
                    f"{query}\n\n"
                    "Executive Response:"
                )

                answer = GeminiService.generate_text(prompt)
                if self.agent.window:
                    payload = {"ok": True, "query": query, "answer": answer}
                    safe_js(self.agent.window, "receiveGeminiChatResponse", json.dumps(payload))
            except Exception as e:
                print(f"[Gemini CoPilot] Worker error: {e}")
                if self.agent.window:
                    payload = {"ok": False, "query": query, "error": str(e)}
                    safe_js(self.agent.window, "receiveGeminiChatResponse", json.dumps(payload))

        threading.Thread(target=_worker, daemon=True, name="GeminiChatWorker").start()
        return {"status": "dispatched"}



class StandaloneMeetingAgent:
    """Orchestrates detection, recording, analysis, and the desktop window."""

    def __init__(self):
        print("[Init] Setting up database...")
        init_db()
        self.detector = MeetingDetector()
        self.recorder = BackgroundMeetingRecorder()
        self.window: Optional[Any] = None
        self.is_auto_recording = False
        self.auto_detect_enabled = True
        self._analyzing = False          # prevents double pipeline runs
        self.active_meeting_title = "Meeting"
        self.active_app_name = "Desktop"
        self._stop_scanner = False
        self._last_meeting_seen_at = 0.0
        self._awaiting_candidate_exit = False
        self.auto_start_audio_seconds = 2.0
        self.auto_stop_silence_seconds = 60.0
        self.auto_stop_missing_seconds = 8.0

        # Load persisted memories
        self.memories = load_memories()
        print(f"[Init] 📂 Desktop folder: {DESKTOP_FOLDER}")
        print(f"[Init] 🧠 Loaded {self.memories.get('total_meetings', 0)} meetings from memory")

    def start(self):
        """Launches the desktop popup window and background detection loop."""
        print("=" * 65)
        print("🎙️  AI Chief of Staff — Autonomous Desktop Coordinator")
        print("=" * 65)
        print(f"• Reports will be saved to: {REPORTS_FOLDER}")
        print("• Monitoring for Google Meet & Zoom in background...")
        print("• Press Ctrl+C in terminal anytime to stop.\n")

        # Start fast detection loop in its own daemon thread
        scanner_thread = threading.Thread(
            target=self._scanner_loop, name="MeetingScanner", daemon=True
        )
        scanner_thread.start()

        if WEBVIEW_AVAILABLE:
            api = DesktopAgentAPI(self)

            # Pre-seed initial SQLite data directly into HTML so UI is hydrated instantly on launch
            try:
                init_data = api.get_initial_data()
                preloaded_js = f"window.__PRELOADED_DATA__ = {json.dumps(init_data)};"
                html_payload = DESKTOP_HTML.replace("/* __INITIAL_DATA_PLACEHOLDER__ */", preloaded_js)
            except Exception as e:
                print(f"[Init] Preload notice: {e}")
                html_payload = DESKTOP_HTML

            self.window = webview.create_window(
                title="AI Chief of Staff | Your Autonomous Meeting Secretary",
                html=html_payload,
                js_api=api,
                width=1240,
                height=820,
                min_size=(960, 640),
                background_color="#060b18",
            )

            def _on_loaded():
                """Push latest saved stats and meeting bundle, waiting until the page is ready."""
                from database.db import get_system_stats, get_latest_meeting_bundle
                try:
                    stats = get_system_stats()
                    last = get_latest_meeting_bundle() or self.memories.get("last_bundle")
                    if self.window:
                        safe_js(self.window, "updateMetrics", json.dumps(stats))
                        if last:
                            safe_js(self.window, "renderResults", json.dumps(last) + ", true")
                except Exception as e:
                    print(f"[UI] On-loaded error: {e}")

            # Register with pywebview Window loaded event
            try:
                self.window.events.loaded += _on_loaded
            except Exception:
                pass

            # Background fallback: fires after a delay to guarantee hydration
            def _background_fallback():
                time.sleep(2.0)
                _on_loaded()

            threading.Thread(target=_background_fallback, daemon=True).start()
            webview.start()
        else:
            print("[Warning] pywebview not installed. Run: pip install pywebview")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass

    # ── Scanner loop ────────────────────────────────────────────────────────────

    def _scanner_loop(self):
        """Verify meeting candidates against microphone activity before recording."""
        while not self._stop_scanner:
            if not self.auto_detect_enabled or self._analyzing:
                if self.recorder.is_monitoring():
                    self.recorder.stop_monitoring()
                time.sleep(2.0)
                continue

            try:
                now = time.time()
                is_candidate, title, app = self.detector.scan_for_meeting()

                if is_candidate:
                    self._last_meeting_seen_at = now
                    if self._awaiting_candidate_exit:
                        pass
                    elif self.recorder.is_recording():
                        if self.is_auto_recording:
                            audio = self.recorder.get_audio_level()
                            silent_for = now - audio.get("last_activity_time", 0.0)
                            if silent_for >= self.auto_stop_silence_seconds:
                                print("\n[Radar] ⏹️  Meeting audio has been quiet; stopping recording.")
                                self._finish_auto_meeting()
                    else:
                        try:
                            if not self.recorder.is_monitoring():
                                self.active_meeting_title = title or "Meeting"
                                self.active_app_name = app or "Microphone"
                                self.recorder.start_monitoring()

                            audio = self.recorder.get_audio_level()
                            if audio.get("activity_seconds", 0.0) >= self.auto_start_audio_seconds:
                                print(f"\n[Radar] 🔴 Meeting audio confirmed: '{title}' ({app})")
                                self.start_recording(title, app, is_auto=True)
                        except Exception as e:
                            print(f"[Radar] Could not monitor microphone: {e}")
                            self.recorder.stop_monitoring()
                else:
                    self._awaiting_candidate_exit = False
                    if self.recorder.is_monitoring():
                        self.recorder.stop_monitoring()

                    if self.is_auto_recording and self.recorder.is_recording():
                        missing_for = now - self._last_meeting_seen_at
                        if missing_for >= self.auto_stop_missing_seconds:
                            print(f"\n[Radar] ⏹️  Meeting tab or app ended: '{self.active_meeting_title}'")
                            self._finish_auto_meeting()
            except Exception as e:
                print(f"[Radar] Error in scan: {e}")

            time.sleep(2.0)

    def _finish_auto_meeting(self):
        self.is_auto_recording = False
        self._awaiting_candidate_exit = True
        self._analyzing = True
        threading.Thread(target=self.stop_and_analyze, daemon=True, name="Pipeline").start()

    # ── Recording ───────────────────────────────────────────────────────────────

    def start_recording(self, meeting_title: str, app_name: str, is_auto: bool = False):
        """Starts background audio recording and updates the UI."""
        self.active_meeting_title = meeting_title or "Meeting"
        self.active_app_name = app_name or "Microphone"
        self.is_auto_recording = is_auto

        self.recorder.start_recording(meeting_title=self.active_meeting_title)

        if self.window:
            safe_title = self.active_meeting_title.replace("'", "\\'")
            safe_app = self.active_app_name.replace("'", "\\'")
            safe_js(self.window, "setMeetingState", f"'RECORDING', '{safe_title}', '{safe_app}'")

    # ── Stop & Analyse ──────────────────────────────────────────────────────────

    def stop_and_analyze(self):
        """
        Stops recording, saves audio, runs the 5-agent pipeline,
        saves results to Desktop, and pushes the UI update.
        Thread-safe: sets _analyzing=True at start, clears it at end.
        """
        self._analyzing = True
        try:
            self._do_stop_and_analyze()
        finally:
            self._analyzing = False

    def _do_stop_and_analyze(self):
        if self.window:
            safe_js(self.window, "setMeetingState", "'ANALYZING', '', ''")
            safe_js(self.window, "setStep", "'stt', 'working'")

        audio_path = self.recorder.stop_recording()
        meeting_id = f"mtg_{uuid.uuid4().hex[:8]}"

        # Copy audio to Desktop Recordings folder
        if audio_path and Path(audio_path).exists():
            dest = RECORDINGS_FOLDER / Path(audio_path).name
            try:
                shutil.copy2(audio_path, dest)
                print(f"[Saved] 🎵 Audio saved to {dest}")
            except Exception as e:
                print(f"[Saved] Audio copy warning: {e}")

        print(f"[Pipeline] Transcribing audio...")

        # Step 1: Transcribe & Diarize
        transcriber = MeetingTranscriber()
        raw_tx, labeled_tx, _ = transcriber.transcribe_and_diarize(audio_path)

        if self.window:
            safe_js(self.window, "setStep", "'stt', 'done'")
            safe_js(self.window, "setStep", "'speakers', 'done'")
            safe_js(self.window, "setStep", "'memory', 'working'")

        # Step 2: Memory Retrieval
        print("[Pipeline] Loading past commitments from memory...")
        mem_mgr = MemoryManager()
        past_context = mem_mgr.get_past_context()

        if self.window:
            safe_js(self.window, "setStep", "'memory', 'done'")
            safe_js(self.window, "setStep", "'summary', 'working'")
            safe_js(self.window, "setStep", "'tasks', 'working'")

        # Step 3: Run Multi-Agent Crew
        print("[Pipeline] Running AI Chief of Staff crew (5 agents)...")
        crew = ChiefOfStaffMeetingCrew()
        results = crew.run_pipeline(labeled_tx)

        if self.window:
            safe_js(self.window, "setStep", "'summary', 'done'")
            safe_js(self.window, "setStep", "'tasks', 'done'")
            safe_js(self.window, "setStep", "'calendar', 'working'")
            safe_js(self.window, "setStep", "'email', 'working'")

        bundle = {
            "meeting_id": meeting_id,
            "title": self.active_meeting_title,
            "raw_transcript": raw_tx,
            "labeled_transcript": labeled_tx,
            "summary": results.get("summary", "Meeting processed successfully."),
            "key_decisions": results.get("key_decisions", []),
            "action_items": results.get("action_items", []),
            "email_drafts": results.get("email_drafts", []),
            "calendar_suggestions": results.get("calendar_suggestions", []),
            "commitments": results.get("new_commitments", []),
            "audio_path": str(audio_path) if audio_path else None,
            "created_at": datetime.now().strftime("%b %d, %Y - %I:%M %p"),
        }

        # Step 4: Persist in SQLite
        print("[Pipeline] Saving to database...")
        save_meeting_bundle(
            meeting_id=bundle["meeting_id"],
            title=bundle["title"],
            raw_transcript=bundle["raw_transcript"],
            labeled_transcript=bundle["labeled_transcript"],
            summary=bundle["summary"],
            key_decisions=bundle["key_decisions"],
            action_items=bundle["action_items"],
            email_drafts=bundle["email_drafts"],
            calendar_suggestions=bundle["calendar_suggestions"],
            commitments=bundle["commitments"],
            audio_path=bundle["audio_path"],
        )

        # Step 5: Save report to Desktop folder
        save_report_to_desktop(bundle)

        # Step 6: Update memories JSON on Desktop
        self.memories["total_meetings"] = self.memories.get("total_meetings", 0) + 1
        self.memories["total_tasks"] = (
            self.memories.get("total_tasks", 0) + len(bundle.get("action_items", []))
        )
        self.memories["total_promises"] = (
            self.memories.get("total_promises", 0) + len(bundle.get("commitments", []))
        )
        self.memories["last_meeting"] = bundle.get("created_at", "")
        self.memories["last_bundle"] = bundle   # so it auto-loads on next launch
        save_memories(self.memories)

        print("[Pipeline] 🎉 Done! Updating desktop window...")

        if self.window:
            safe_js(self.window, "setStep", "'calendar', 'done'")
            safe_js(self.window, "setStep", "'email', 'done'")
            safe_js(self.window, "renderResults", json.dumps(bundle))
            stats = {
                "total_meetings": self.memories.get("total_meetings", 0),
                "total_tasks": self.memories.get("total_tasks", 0),
                "total_promises": self.memories.get("total_promises", 0),
                "last_meeting": self.memories.get("last_meeting", ""),
            }
            safe_js(self.window, "updateMetrics", json.dumps(stats))
            safe_js(self.window, "setMeetingState", "'IDLE', '', ''")

    # ── Demo pipeline ───────────────────────────────────────────────────────────

    def run_demo_pipeline(self):
        """Simulates an instant meeting run with rich sample data for demonstration."""
        if self.window:
            safe_js(self.window, "setMeetingState", "'ANALYZING', '', ''")

        # Simulate step-by-step progress with small delays
        for step, delay in [("stt", 0.6), ("speakers", 0.6), ("memory", 0.8),
                             ("summary", 1.0), ("tasks", 0.8), ("calendar", 0.7), ("email", 0.7)]:
            if self.window:
                safe_js(self.window, "setStep", f"'{step}', 'working'")
            time.sleep(delay)
            if self.window:
                safe_js(self.window, "setStep", f"'{step}', 'done'")

        demo_tx = (
            "Speaker A (Sathwik): Team, in our last meeting I committed to completing the UI mockups "
            "by Friday — I'm happy to report they're ready with glassmorphism styling and animations.\n\n"
            "Speaker B (Alice): That's great Sathwik! I will deliver the database schema migrations by next "
            "Monday at 5 PM. This unblocks the backend team.\n\n"
            "Speaker C (Bob): Perfect. I will integrate the Gemini 3.8 Flash API client by Wednesday. "
            "I suggest we hold a coordination sync next Thursday at 2 PM to review everything.\n\n"
            "Speaker A (Sathwik): Agreed. Let's also set a final review the following Monday morning "
            "before we go live. Any objections? Alright — that's decided."
        )

        print("[Demo] Running AI pipeline on sample transcript...")
        crew = ChiefOfStaffMeetingCrew()
        results = crew.run_pipeline(demo_tx)

        meeting_id = f"demo_{uuid.uuid4().hex[:6]}"
        bundle = {
            "meeting_id": meeting_id,
            "title": "Sprint Review — Demo Meeting",
            "raw_transcript": demo_tx,
            "labeled_transcript": demo_tx,
            "summary": results.get(
                "summary",
                "The team reviewed sprint progress. Sathwik delivered the UI mockups on time. "
                "Alice is committed to delivering the database migrations by Monday 5 PM. "
                "Bob will integrate the Gemini API by Wednesday. Two follow-up syncs were agreed."
            ),
            "key_decisions": results.get("key_decisions", [
                "UI mockups accepted as delivered — no revisions needed",
                "Database migration deadline set: Monday 5 PM",
                "Coordination sync scheduled: Next Thursday 2 PM",
                "Final review before go-live: Monday morning",
            ]),
            "action_items": results.get("action_items", [
                {"task": "Deliver SQLite schema migrations", "owner": "Alice",
                 "deadline": "Monday 5 PM", "priority": "High"},
                {"task": "Integrate Gemini 3.8 Flash API client", "owner": "Bob",
                 "deadline": "Wednesday", "priority": "High"},
                {"task": "Send meeting summary to all attendees", "owner": "Sathwik",
                 "deadline": "Today", "priority": "Medium"},
            ]),
            "email_drafts": results.get("email_drafts", [{
                "recipient_name": "Sprint Team",
                "recipient_email": "team@example.com",
                "subject": "Sprint Review — Action Items & Next Steps",
                "body": (
                    "Hi team,\n\nGreat progress in today's sprint review. Here's a quick summary:\n\n"
                    "✅ Sathwik has delivered the UI mockups — approved and ready.\n"
                    "📋 Alice to complete DB migrations by Monday 5 PM.\n"
                    "📋 Bob to integrate Gemini API by Wednesday.\n"
                    "📅 Coordination sync: Next Thursday at 2 PM.\n"
                    "📅 Final go-live review: Following Monday morning.\n\n"
                    "Please confirm attendance for both scheduled syncs.\n\n"
                    "Best,\nAI Chief of Staff"
                ),
            }]),
            "calendar_suggestions": results.get("calendar_suggestions", [
                {"proposed_title": "Coordination Sync", "suggested_slot": "Thursday 2:00 PM",
                 "participants": ["Sathwik", "Alice", "Bob"]},
                {"proposed_title": "Go-Live Final Review", "suggested_slot": "Following Monday 9:00 AM",
                 "participants": ["Sathwik", "Alice", "Bob"]},
            ]),
            "commitments": results.get("new_commitments", [
                {"person": "Alice", "commitment": "Deliver SQLite schema migrations",
                 "deadline": "Monday 5 PM", "status": "Open"},
                {"person": "Bob", "commitment": "Integrate Gemini 3.8 Flash API",
                 "deadline": "Wednesday", "status": "Open"},
            ]),
            "created_at": datetime.now().strftime("%b %d, %Y - %I:%M %p"),
        }

        # Save to DB & Desktop
        save_meeting_bundle(
            meeting_id=bundle["meeting_id"],
            title=bundle["title"],
            raw_transcript=bundle["raw_transcript"],
            labeled_transcript=bundle["labeled_transcript"],
            summary=bundle["summary"],
            key_decisions=bundle["key_decisions"],
            action_items=bundle["action_items"],
            email_drafts=bundle["email_drafts"],
            calendar_suggestions=bundle["calendar_suggestions"],
            commitments=bundle["commitments"],
        )
        save_report_to_desktop(bundle)

        self.memories["total_meetings"] = self.memories.get("total_meetings", 0) + 1
        self.memories["total_tasks"] = self.memories.get("total_tasks", 0) + len(bundle["action_items"])
        self.memories["total_promises"] = self.memories.get("total_promises", 0) + len(bundle["commitments"])
        self.memories["last_meeting"] = bundle["created_at"]
        self.memories["last_bundle"] = bundle
        save_memories(self.memories)

        if self.window:
            safe_js(self.window, "renderResults", json.dumps(bundle))
            stats = {
                "total_meetings": self.memories["total_meetings"],
                "total_tasks": self.memories["total_tasks"],
                "total_promises": self.memories["total_promises"],
                "last_meeting": self.memories["last_meeting"],
            }
            safe_js(self.window, "updateMetrics", json.dumps(stats))
            safe_js(self.window, "setMeetingState", "'IDLE', '', ''")


if __name__ == "__main__":
    agent = StandaloneMeetingAgent()
    agent.start()
