"""Speech -> text with faster-whisper (runs offline on your laptop CPU)."""
from faster_whisper import WhisperModel

_models = {}


def _get(size):
    if size not in _models:
        _models[size] = WhisperModel(size, device="cpu", compute_type="int8")
    return _models[size]


def transcribe(path, size="base"):
    """Returns (segments, language). Each segment = {start, end, text}."""
    segs, info = _get(size).transcribe(path, beam_size=1, vad_filter=True)
    out = [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segs if s.text.strip()]
    return out, info.language


def to_text(segments):
    return " ".join(s["text"] for s in segments)


def with_timestamps(segments):
    return "\n".join(f"[{int(s['start'] // 60):02d}:{int(s['start'] % 60):02d}] {s['text']}" for s in segments)
