"""Thread-safe background audio recorder for continuous meeting capture with real-time level metering."""

import os
import time
import queue
import threading
import math
from collections import deque
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import numpy as np
import sounddevice as sd
import soundfile as sf
import config


class BackgroundMeetingRecorder:
    """Records meeting audio in background thread with chunk streaming and real-time level metering."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._is_recording = False
        self._is_monitoring = False
        self._audio_queue = queue.Queue()
        self._stream: Optional[sd.InputStream] = None
        self._writer_thread: Optional[threading.Thread] = None
        self._current_file: Optional[Path] = None
        self._start_time: Optional[float] = None
        self._preroll = deque(maxlen=64)
        self._activity_seconds = 0.0
        
        # Real-time audio metering state
        self._current_volume: float = 0.0      # 0 to 100 percentage
        self._peak_db: float = -60.0            # decibels
        self._is_audio_active: bool = False     # True if voice detected
        self._last_active_time: float = 0.0

    def is_recording(self) -> bool:
        return self._is_recording

    def is_monitoring(self) -> bool:
        return self._is_monitoring

    def get_duration_seconds(self) -> int:
        if not self._is_recording or self._start_time is None:
            return 0
        return int(time.time() - self._start_time)

    def get_audio_level(self) -> Dict[str, Any]:
        """Returns the current real-time audio volume and activity status for the UI."""
        # Gentle decay if no new audio packet updated recently
        now = time.time()
        if now - self._last_active_time > 0.3:
            self._current_volume = max(0.0, self._current_volume * 0.8)
            if self._current_volume < 2.0:
                self._is_audio_active = False

        return {
            "volume_percent": round(self._current_volume, 1),
            "peak_db": round(self._peak_db, 1),
            "is_recording": self._is_recording,
            "is_active": self._is_audio_active,
            "duration_seconds": self.get_duration_seconds(),
            "activity_seconds": round(self._activity_seconds, 2),
            "last_activity_time": self._last_active_time,
            "is_monitoring": self._is_monitoring,
        }

    def start_monitoring(self) -> None:
        """Monitor microphone activity without creating or writing a recording."""
        if self._is_recording or self._is_monitoring:
            return

        self._audio_queue = queue.Queue()
        self._preroll.clear()
        self._activity_seconds = 0.0
        self._current_volume = 0.0
        self._is_monitoring = True
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=self._audio_callback,
        )
        try:
            self._stream.start()
        except Exception:
            self._is_monitoring = False
            self._stream = None
            raise

    def stop_monitoring(self) -> None:
        """Close the microphone activity monitor without saving audio."""
        if not self._is_monitoring or self._is_recording:
            return

        self._is_monitoring = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        self._preroll.clear()
        self._current_volume = 0.0
        self._is_audio_active = False
        self._activity_seconds = 0.0

    def _audio_callback(self, indata, frames, time_info, status):
        if indata is None or len(indata) == 0:
            return

        try:
            rms = float(np.sqrt(np.mean(np.square(indata))))
            volume = min(100.0, max(0.0, rms * 450.0))
            self._current_volume = volume
            if rms > 0.00001:
                self._peak_db = max(-60.0, min(0.0, 20.0 * math.log10(rms)))

            block_seconds = frames / self.sample_rate
            if volume >= 3.5:
                self._last_active_time = time.time()
                self._activity_seconds = min(3.0, self._activity_seconds + block_seconds)
                self._is_audio_active = True
            else:
                self._activity_seconds = max(0.0, self._activity_seconds - block_seconds * 0.5)
                self._is_audio_active = False

            if self._is_monitoring:
                self._preroll.append(indata.copy())
            if self._is_recording:
                self._audio_queue.put(indata.copy())
        except Exception:
            pass

    def start_recording(self, meeting_title: str = "") -> Path:
        """Starts recording audio in the background."""
        if self._is_recording:
            return self._current_file

        preroll = list(self._preroll) if self._is_monitoring else []

        config.RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in meeting_title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        if not safe_title:
            safe_title = "Meeting"
        filename = f"{safe_title}_{timestamp}.wav"
        self._current_file = config.RECORDINGS_DIR / filename

        self._is_recording = True
        self._is_monitoring = False
        self._start_time = time.time()
        self._audio_queue = queue.Queue()
        for chunk in preroll:
            self._audio_queue.put(chunk)
        self._preroll.clear()

        if self._stream is None:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                callback=self._audio_callback,
            )
            try:
                self._stream.start()
            except Exception:
                self._is_recording = False
                self._stream = None
                raise

        # Start writer thread
        self._writer_thread = threading.Thread(target=self._write_loop, daemon=True)
        self._writer_thread.start()

        return self._current_file

    def _write_loop(self):
        """Continuously writes recorded audio frames to disk."""
        with sf.SoundFile(
            str(self._current_file),
            mode="x",
            samplerate=self.sample_rate,
            channels=self.channels,
            subtype="PCM_16",
        ) as f:
            while self._is_recording or not self._audio_queue.empty():
                try:
                    data = self._audio_queue.get(timeout=0.2)
                    f.write(data)
                except queue.Empty:
                    continue

    def stop_recording(self) -> Optional[Path]:
        """Stops recording and returns the path to the completed audio file."""
        if not self._is_recording:
            return self._current_file

        self._is_recording = False
        self._is_monitoring = False
        self._current_volume = 0.0
        self._is_audio_active = False

        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        if self._writer_thread is not None:
            self._writer_thread.join(timeout=3.0)
            self._writer_thread = None

        return self._current_file
