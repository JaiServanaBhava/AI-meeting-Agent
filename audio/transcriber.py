"""Speech-to-Text Transcription — Gemini Native Audio (primary) with robust fallback.

Strategy:
  1. Gemini 2.5 Flash native audio transcription (cloud, fast, no GPU needed)
  2. If Gemini fails, try local Whisper (lazy import, catches NumPy incompatibility)
  3. If both fail, return an "audio captured" notice with file info so the pipeline
     still runs and the user sees their recording was saved even without a transcript.

torch/whisper are imported lazily inside methods — never at module load time —
so importing this module never crashes even if torch/whisper have numpy mismatches.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import config


class MeetingTranscriber:
    """Orchestrates Gemini native transcription with Whisper fallback."""

    def __init__(self, model_name: str = ""):
        self.model_name = model_name or config.WHISPER_MODEL
        self._model = None

    # ── Whisper (lazy, catches NumPy 2.x crash) ─────────────────────────────

    def _get_model(self):
        """Loads the Whisper model lazily — catches NumPy/torch import errors."""
        if self._model is not None:
            return self._model
        try:
            import whisper  # noqa: PLC0415
            self._model = whisper.load_model(self.model_name)
        except Exception as exc:
            print(f"[Transcriber] Whisper unavailable ({type(exc).__name__}); will use Gemini or fallback.")
            self._model = None
        return self._model

    def _get_diarizer(self):
        from audio.diarizer import SpeakerDiarizer  # noqa: PLC0415
        return SpeakerDiarizer()

    # ── Main entry point ─────────────────────────────────────────────────────

    def transcribe_and_diarize(
        self, audio_path: Optional[Path]
    ) -> Tuple[str, str, List[Dict[str, Any]]]:
        """Transcribes audio using best available method.

        Returns:
            (raw_transcript, speaker_labeled_transcript, segments_list)
        """
        p = Path(str(audio_path)) if audio_path else None

        # ── 1. Gemini Native (fastest, works without GPU, no NumPy issues) ──
        api_key = config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        if api_key and p and p.exists():
            try:
                from services.gemini_service import GeminiService  # noqa
                audio_bytes = p.read_bytes()
                mime_map = {
                    "wav": "audio/wav", "mp3": "audio/mp3", "m4a": "audio/m4a",
                    "webm": "audio/webm", "ogg": "audio/ogg", "flac": "audio/flac",
                }
                mime_type = mime_map.get(p.suffix.lower().lstrip("."), "audio/wav")
                labeled_text = GeminiService.transcribe_audio_native(audio_bytes, mime_type=mime_type)
                if labeled_text and len(labeled_text.strip()) > 10:
                    raw_text = "\n".join(
                        line.split(":", 1)[-1].strip() if ":" in line else line
                        for line in labeled_text.splitlines()
                    ).strip()
                    print("[Transcriber] ✅ Gemini native transcription successful.")
                    return raw_text, labeled_text, []
            except Exception as e:
                print(f"[Transcriber] Gemini native failed ({e}), trying Whisper...")

        # ── 2. Local Whisper (fallback, catches NumPy 2.x incompatibility) ──
        if p and p.exists():
            model = self._get_model()
            if model is not None:
                try:
                    result = model.transcribe(str(p), word_timestamps=True)
                    raw_text = result.get("text", "").strip()
                    raw_segments = [
                        {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
                        for s in result.get("segments", []) if s.get("text", "").strip()
                    ]
                    try:
                        diarizer = self._get_diarizer()
                        labeled = diarizer.diarize_segments(p, raw_segments)
                        blocks, curr_spk, curr_lines = [], None, []
                        for seg in labeled:
                            spk = seg.get("speaker", "Speaker A")
                            txt = seg.get("text", "")
                            if spk != curr_spk:
                                if curr_spk:
                                    blocks.append(f"{curr_spk}: {' '.join(curr_lines)}")
                                curr_spk, curr_lines = spk, [txt]
                            else:
                                curr_lines.append(txt)
                        if curr_spk and curr_lines:
                            blocks.append(f"{curr_spk}: {' '.join(curr_lines)}")
                        labeled_transcript = "\n\n".join(blocks) or raw_text
                    except Exception:
                        labeled_transcript = raw_text

                    print("[Transcriber] ✅ Whisper transcription successful.")
                    return raw_text, labeled_transcript, []
                except Exception as exc:
                    print(f"[Transcriber] Whisper transcription failed ({exc})")

        # ── 3. Audio-saved fallback ──────────────────────────────────────────
        # Both Gemini and Whisper unavailable. Return an informative message
        # so the pipeline still runs and shows the user their audio is saved.
        if p and p.exists():
            size_kb = round(p.stat().st_size / 1024)
            msg = (
                f"[Audio Captured — Transcription Pending]\n\n"
                f"Your meeting audio was recorded and saved:\n"
                f"  📁 File: {p.name}\n"
                f"  📦 Size: {size_kb} KB\n\n"
                f"To enable AI transcription, please:\n"
                f"  1. Click ⚙️ API Key in the app header\n"
                f"  2. Enter your Gemini API key (free at aistudio.google.com)\n\n"
                f"Once the key is saved, re-run analysis on this recording."
            )
            return msg, msg, []

        # ── 4. No audio at all — demo mode ──────────────────────────────────
        demo = (
            "Speaker A (Sathwik): Team, I completed the UI redesign as promised. "
            "The glassmorphism dashboard is ready for review.\n\n"
            "Speaker B (Alice): Excellent! I will deliver the database migrations "
            "by Monday 5 PM. That unblocks the whole backend team.\n\n"
            "Speaker C (Bob): I will integrate the Gemini API client by Wednesday. "
            "Let's sync Thursday at 2 PM to review everything before go-live."
        )
        return demo, demo, []
