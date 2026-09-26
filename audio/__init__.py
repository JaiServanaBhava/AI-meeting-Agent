# Audio subpackage - lazy imports only, no heavy ML at module load time
from .recorder import LiveAudioRecorder
from .transcriber import MeetingTranscriber

__all__ = [
    "LiveAudioRecorder",
    "MeetingTranscriber",
]
