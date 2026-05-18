"""YouTube channel/feed collector.

MVP strategy: use public channel RSS. If transcripts are needed later, route the
video URL to the youtube-content skill/script or a dedicated transcript adapter.
"""
from __future__ import annotations
from daily_brief.config import SourceConfig
from .base import CollectorResult
from .rss import collect_rss


def collect_youtube_feed(source: SourceConfig, run_date: str) -> CollectorResult:
    result = collect_rss(source, run_date)
    for item in result.items:
        item.source_type = "youtube"
        item.metadata["section"] = source.metadata.get("section", "video")
        item.metadata.setdefault("tags", source.metadata.get("tags", ["YouTube", "Builder"] ))
        item.metadata["summary_strategy"] = "RSS title/description now; transcript extraction is the next adapter."
    return result
