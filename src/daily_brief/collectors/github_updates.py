"""GitHub releases update collector."""
from __future__ import annotations
import json
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from daily_brief.config import SourceConfig
from daily_brief.memory import canonicalize_url
from daily_brief.models import CollectedItem
from .base import CollectorResult
from .rss import _clean_text, _parse_datetime


def collect_github_releases(source: SourceConfig, run_date: str, timeout: int = 20) -> CollectorResult:
    if not source.url:
        return CollectorResult(source.id, [], ["missing GitHub API URL"], True)
    try:
        req = Request(source.url, headers={"Accept": "application/vnd.github+json", "User-Agent": "daily-brief/0.1"})
        with urlopen(req, timeout=timeout) as response:  # noqa: S310 - configured public source
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return CollectorResult(source.id, [], [f"GitHub fetch failed: {exc}"], True)
    releases = data if isinstance(data, list) else [data]
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=int(source.metadata.get("lookback_hours", 168) or 168))
    items: list[CollectedItem] = []
    for idx, release in enumerate(releases, 1):
        published = str(release.get("published_at") or release.get("created_at") or fetched_at)
        dt = _parse_datetime(published)
        if dt and dt < cutoff and len(items) >= 1:
            continue
        title = str(release.get("name") or release.get("tag_name") or f"GitHub update {idx}")
        url = str(release.get("html_url") or source.url)
        body = _clean_text(str(release.get("body") or title))[:1000]
        canonical = canonicalize_url(url)
        items.append(CollectedItem(
            id=f"{source.id}-{release.get('id', idx)}",
            source_id=source.id,
            source_type="github_updates",
            title=title,
            url=url,
            canonical_url=canonical,
            author=source.name,
            published_at=dt.replace(microsecond=0).isoformat() if dt else fetched_at,
            fetched_at=fetched_at,
            raw_excerpt=body or title,
            content_text=f"{title}\n\n{body}",
            language="en",
            metadata={"section": source.metadata.get("section", "tool_engineering"), "tags": source.metadata.get("tags", ["GitHub", "release"]), "collector": "github_updates"},
        ))
        if len(items) >= source.max_items:
            break
    return CollectorResult(source.id, items, warnings=[] if items else ["no GitHub releases returned"], degraded=not bool(items))
