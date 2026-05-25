"""YouTube channel/feed collector with transcript enrichment.

The collector first uses public channel RSS, then attempts public transcript
retrieval for each retained video. Transcript failures are stored per item and
surfaced in the HTML instead of failing the whole daily run.
"""
from __future__ import annotations

from collections.abc import Sequence

from daily_brief.config import SourceConfig
from .base import CollectorResult
from .rss import collect_rss
from .youtube_transcripts import DEFAULT_TRANSCRIPT_LANGUAGES, TranscriptFetcher, fetch_youtube_transcript


def collect_youtube_feed(
    source: SourceConfig,
    run_date: str,
    transcript_fetcher: TranscriptFetcher | None = None,
) -> CollectorResult:
    result = collect_rss(source, run_date)
    warnings = list(result.warnings)
    transcript_languages = _transcript_languages(source)
    non_fetched = 0
    for item in result.items:
        item.source_type = "youtube"
        item.metadata["section"] = source.metadata.get("section", "video")
        item.metadata.setdefault("tags", source.metadata.get("tags", ["YouTube", "Builder"]))
        transcript = fetch_youtube_transcript(item.url, languages=transcript_languages, fetcher=transcript_fetcher)
        item.metadata.update(transcript.to_metadata())
        tags = item.metadata.get("tags", [])
        if isinstance(tags, list):
            tags.append(f"transcript:{transcript.status}")
            if transcript.language:
                tags.append(f"lang:{transcript.language}")
        if transcript.status == "fetched" and transcript.excerpt:
            item.raw_excerpt = transcript.excerpt
            item.content_text = f"{item.title}\n\n{transcript.excerpt}"
            item.metadata["summary_strategy"] = "YouTube transcript excerpt is primary video evidence."
        else:
            non_fetched += 1
            note = str(item.metadata.get("transcript_note", f"transcript_status={transcript.status}; transcript unavailable"))
            if "transcript_status=" not in item.raw_excerpt:
                item.raw_excerpt = f"{note}. Feed fallback: {item.raw_excerpt}"
            item.content_text = f"{item.title}\n\n{item.raw_excerpt}"
            item.metadata["summary_strategy"] = "Transcript attempted; RSS/feed text is low-confidence fallback."
            warnings.append(f"{item.id}: {note}")
    return CollectorResult(result.source_id, result.items, warnings=warnings, degraded=bool(result.degraded or non_fetched))


def _transcript_languages(source: SourceConfig) -> tuple[str, ...]:
    raw = source.metadata.get("transcript_languages", DEFAULT_TRANSCRIPT_LANGUAGES)
    if isinstance(raw, str):
        values: Sequence[str] = [part.strip() for part in raw.split(",")]
    elif isinstance(raw, Sequence):
        values = [str(part).strip() for part in raw]
    else:
        values = DEFAULT_TRANSCRIPT_LANGUAGES
    cleaned = tuple(value for value in values if value)
    return cleaned or DEFAULT_TRANSCRIPT_LANGUAGES
