"""Speaker Diarization Engine.

pyannote.audio is completely optional — it is only imported inside the
diarize_segments() method if an HF_TOKEN is provided.  If pyannote is
absent or the token is missing the heuristic clustering fallback runs
automatically without any heavy ML imports at module load time.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, List, Dict, Any, Optional

import config


class SpeakerDiarizer:
    """Identifies and clusters speakers as Speaker A, Speaker B, Speaker C."""

    def __init__(self, hf_token: Optional[str] = None):
        self.hf_token = hf_token or config.HF_TOKEN
        self._pipeline = None          # loaded lazily only when needed
        self._pipeline_attempted = False  # guard: only try loading once

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def diarize_segments(
        self,
        audio_path: Optional[Path],
        segments: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Maps speech segments to Speaker A, Speaker B, Speaker C...

        Tries pyannote.audio acoustic clustering first (requires HF_TOKEN +
        the pyannote package).  Falls back transparently to heuristic
        turn-taking analysis when pyannote is unavailable.
        """
        if not segments:
            return []

        # Only attempt pyannote if we have a token AND a real audio file
        if self.hf_token and audio_path and Path(audio_path).exists():
            pipeline = self._get_pipeline()
            if pipeline:
                try:
                    return self._apply_pyannote(audio_path, segments, pipeline)
                except Exception as exc:
                    print(f"[Diarizer] pyannote execution failed ({exc}), using heuristic.")

        return self._heuristic_clustering(segments)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_pipeline(self):
        """Lazily loads pyannote pipeline — never imports at module level."""
        if self._pipeline_attempted:
            return self._pipeline

        self._pipeline_attempted = True
        try:
            # Import pyannote ONLY here — not at module level
            from pyannote.audio import Pipeline  # noqa: PLC0415
            self._pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.hf_token,
            )
        except Exception as exc:
            print(f"[Diarizer] pyannote unavailable ({type(exc).__name__}), heuristic will be used.")
            self._pipeline = None

        return self._pipeline

    def _apply_pyannote(self, audio_path: Path, segments: List[Dict], pipeline) -> List[Dict]:
        diarization = pipeline(str(audio_path))
        raw_labels = sorted({spk for _, _, spk in diarization.itertracks(yield_label=True)})

        speaker_map = {
            raw_spk: f"Speaker {chr(65 + i)}"
            for i, raw_spk in enumerate(raw_labels)
        }

        turns = [
            (turn.start, turn.end, speaker_map[spk])
            for turn, _, spk in diarization.itertracks(yield_label=True)
        ]

        for seg in segments:
            best_spk = "Speaker A"
            best_overlap = 0.0
            for t_start, t_end, spk_label in turns:
                overlap = max(0.0, min(seg["end"], t_end) - max(seg["start"], t_start))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_spk = spk_label
            seg["speaker"] = best_spk

        return segments

    def _heuristic_clustering(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Conversational turn-taking heuristic (Speaker A, B, C rotation)."""
        speakers = ["Speaker A", "Speaker B", "Speaker C"]
        current_idx = 0
        last_end = 0.0

        for seg in segments:
            gap = seg["start"] - last_end
            text = seg.get("text", "").strip()

            transition_phrases = (
                "Thanks", "Agreed", "I think", "Regarding",
                "Yes", "No", "Alright", "Sure", "Good point",
            )
            if gap > 1.2 or (text.startswith(transition_phrases) and gap > 0.5):
                current_idx = (current_idx + 1) % len(speakers)

            seg["speaker"] = speakers[current_idx]
            last_end = seg["end"]

        return segments
