"""YouTube transcript/subtitle adapter.

The daily brief collector uses public YouTube metadata and optional public
transcripts only. This module never reads cookies/session state and treats every
failure as per-video degradation so a daily run can still complete.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

DEFAULT_TRANSCRIPT_LANGUAGES = ("zh-Hans", "zh", "en")
_TRANSCRIPT_PROVIDER = "youtube-transcript-api"

TranscriptFetcher = Callable[[str, tuple[str, ...]], Any]


@dataclass(slots=True)
class TranscriptResult:
    """Normalized transcript fetch result stored on collected item metadata."""

    status: str
    video_id: str
    language: str = ""
    excerpt: str = ""
    segments_sample: list[dict[str, object]] = field(default_factory=list)
    provider: str = _TRANSCRIPT_PROVIDER
    is_generated: bool | None = None
    error: str = ""
    error_type: str = ""

    def to_metadata(self) -> dict[str, object]:
        note = _status_note(self.status)
        metadata: dict[str, object] = {
            "transcript_status": self.status,
            "transcript_video_id": self.video_id,
            "transcript_language": self.language,
            "transcript_excerpt": self.excerpt,
            "transcript_segments_sample": self.segments_sample,
            "transcript_provider": self.provider,
            "transcript_note": f"transcript_status={self.status}; {note}",
        }
        if self.is_generated is not None:
            metadata["transcript_is_generated"] = self.is_generated
        if self.error:
            metadata["transcript_error"] = self.error
        if self.error_type:
            metadata["transcript_error_type"] = self.error_type
        return metadata


def extract_video_id(url_or_id: str) -> str:
    """Extract the 11-character video id from common YouTube URL shapes."""

    value = (url_or_id or "").strip()
    patterns = [
        r"(?:v=|youtu\.be/|shorts/|embed/|live/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)
    return value


def fetch_youtube_transcript(
    url_or_id: str,
    languages: Sequence[str] = DEFAULT_TRANSCRIPT_LANGUAGES,
    fetcher: TranscriptFetcher | None = None,
    max_segments: int = 8,
    max_excerpt_chars: int = 1400,
) -> TranscriptResult:
    """Attempt to fetch public YouTube transcript metadata for one video.

    Unit tests pass a fake ``fetcher``; production uses ``youtube-transcript-api``
    when installed. Any exception is converted into a structured status rather
    than escaping and failing the whole collector.
    """

    video_id = extract_video_id(url_or_id)
    language_tuple = tuple(languages or DEFAULT_TRANSCRIPT_LANGUAGES)
    try:
        fetched = fetcher(video_id, language_tuple) if fetcher else _fetch_with_youtube_transcript_api(video_id, language_tuple)
        language = _extract_language(fetched)
        is_generated = _extract_is_generated(fetched)
        segments = _normalize_segments(_extract_segments(fetched))
        if not segments:
            return TranscriptResult(
                status="unavailable",
                video_id=video_id,
                language=language,
                error="transcript provider returned zero segments",
                error_type="empty_transcript",
            )
        sample = segments[: max(1, max_segments)]
        excerpt = _build_excerpt(sample, max_chars=max_excerpt_chars)
        return TranscriptResult(
            status="fetched",
            video_id=video_id,
            language=language,
            excerpt=excerpt,
            segments_sample=sample,
            is_generated=is_generated,
        )
    except Exception as exc:  # noqa: BLE001 - degrade per item, do not fail the run
        status, error_type = _classify_exception(exc)
        return TranscriptResult(
            status=status,
            video_id=video_id,
            error=str(exc).strip()[:500],
            error_type=error_type,
        )


def _fetch_with_youtube_transcript_api(video_id: str, languages: tuple[str, ...]) -> Any:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError("youtube-transcript-api is not installed") from exc

    language_list = list(languages)
    api = YouTubeTranscriptApi()
    fetch = getattr(api, "fetch", None)
    if callable(fetch):
        return fetch(video_id, languages=language_list)

    legacy_fetch = getattr(YouTubeTranscriptApi, "get_transcript", None)
    if callable(legacy_fetch):  # pragma: no cover - legacy package compatibility
        return legacy_fetch(video_id, languages=language_list)
    raise RuntimeError("youtube-transcript-api has no supported fetch method")


def _extract_segments(fetched: Any) -> Iterable[Any]:
    if isinstance(fetched, dict):
        return fetched.get("segments") or fetched.get("snippets") or []
    return fetched


def _extract_language(fetched: Any) -> str:
    if isinstance(fetched, dict):
        return str(fetched.get("language_code") or fetched.get("language") or "")
    return str(getattr(fetched, "language_code", "") or getattr(fetched, "language", ""))


def _extract_is_generated(fetched: Any) -> bool | None:
    if isinstance(fetched, dict):
        raw = fetched.get("is_generated")
    else:
        raw = getattr(fetched, "is_generated", None)
    return raw if isinstance(raw, bool) else None


def _normalize_segments(segments: Iterable[Any]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for raw in segments:
        if isinstance(raw, dict):
            text = str(raw.get("text", "")).strip()
            start = _float(raw.get("start", 0.0))
            duration = _float(raw.get("duration", 0.0))
        else:
            text = str(getattr(raw, "text", "")).strip()
            start = _float(getattr(raw, "start", 0.0))
            duration = _float(getattr(raw, "duration", 0.0))
        if not text:
            continue
        normalized.append(
            {
                "timestamp": format_timestamp(start),
                "start": round(start, 3),
                "duration": round(duration, 3),
                "text": _compact_text(text),
            }
        )
    return normalized


def _build_excerpt(segments: list[dict[str, object]], max_chars: int) -> str:
    lines = [f"[{segment['timestamp']}] {segment['text']}" for segment in segments]
    excerpt = "\n".join(lines).strip()
    if len(excerpt) <= max_chars:
        return excerpt
    return excerpt[: max(0, max_chars - 1)].rstrip() + "…"


def format_timestamp(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _classify_exception(exc: Exception) -> tuple[str, str]:
    name = exc.__class__.__name__.lower()
    message = str(exc).lower()
    combined = f"{name} {message}"
    if "disabled" in combined:
        return "disabled", exc.__class__.__name__
    if "no transcript" in combined or "notranscript" in combined or "unavailable" in combined or "not found" in combined:
        return "unavailable", exc.__class__.__name__
    return "error", exc.__class__.__name__


def _status_note(status: str) -> str:
    if status == "fetched":
        return "public YouTube transcript fetched and used as primary evidence"
    if status == "disabled":
        return "transcripts are disabled for this video; feed text is low-confidence fallback"
    if status == "unavailable":
        return "no matching public transcript was available; feed text is low-confidence fallback"
    return "transcript fetch errored; feed text is low-confidence fallback"
