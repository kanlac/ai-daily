"""Public Reddit JSON collector for pain-point discovery."""
from __future__ import annotations
import json
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from daily_brief.config import SourceConfig
from daily_brief.memory import canonicalize_url
from daily_brief.models import CollectedItem
from .base import CollectorResult


def collect_reddit(source: SourceConfig, run_date: str, timeout: int = 20) -> CollectorResult:
    if not source.url:
        return CollectorResult(source.id, [], ["missing Reddit JSON URL"], True)
    try:
        req = Request(source.url, headers={"User-Agent": "daily-brief/0.1 read-only research"})
        with urlopen(req, timeout=timeout) as response:  # noqa: S310 - public configured source
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return CollectorResult(source.id, [], [f"Reddit fetch failed: {exc}"], True)
    fetched_at_dt = datetime.now(timezone.utc).replace(microsecond=0)
    fetched_at = fetched_at_dt.isoformat()
    cutoff = fetched_at_dt - timedelta(hours=int(source.metadata.get("lookback_hours", 48) or 48))
    section = str(source.metadata.get("section", "product_ideas"))
    tags = source.metadata.get("tags", ["Reddit", "Pain point"])
    children = data.get("data", {}).get("children", [])
    items: list[CollectedItem] = []
    for idx, child in enumerate(children, 1):
        post = child.get("data", {})
        created = post.get("created_utc")
        published_dt = datetime.fromtimestamp(float(created), tz=timezone.utc) if created else fetched_at_dt
        if published_dt < cutoff and len(items) >= min(2, source.max_items):
            continue
        title = str(post.get("title") or f"Reddit item {idx}")
        permalink = str(post.get("permalink") or "")
        url = permalink if permalink.startswith("http") else f"https://www.reddit.com{permalink}"
        excerpt = str(post.get("selftext") or post.get("url") or title).strip()[:900]
        if not excerpt:
            excerpt = title
        items.append(CollectedItem(
            id=f"{source.id}-{post.get('id', idx)}",
            source_id=source.id,
            source_type="reddit",
            title=title,
            url=url,
            canonical_url=canonicalize_url(url),
            author=str(post.get("author") or "redditor"),
            published_at=published_dt.replace(microsecond=0).isoformat(),
            fetched_at=fetched_at,
            raw_excerpt=excerpt,
            content_text=f"{title}\n\n{excerpt}",
            language="en",
            metadata={"section": section, "subreddit": post.get("subreddit"), "score": post.get("score"), "num_comments": post.get("num_comments"), "tags": tags, "collector": "reddit"},
        ))
        if len(items) >= source.max_items:
            break
    return CollectorResult(source.id, items, warnings=[] if items else ["no Reddit posts returned"], degraded=not bool(items))
