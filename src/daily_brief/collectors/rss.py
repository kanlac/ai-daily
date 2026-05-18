"""Minimal RSS/Atom collector using only the Python standard library."""
from __future__ import annotations

import html
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from daily_brief.config import SourceConfig
from daily_brief.memory import canonicalize_url, fingerprint_text
from daily_brief.models import CollectedItem
from .base import CollectorResult

ATOM = "{http://www.w3.org/2005/Atom}"
MEDIA = "{http://search.yahoo.com/mrss/}"
DC = "{http://purl.org/dc/elements/1.1/}"
CONTENT = "{http://purl.org/rss/1.0/modules/content/}"


def collect_rss(source: SourceConfig, run_date: str, timeout: int = 20) -> CollectorResult:
    if not source.url:
        return CollectorResult(source.id, [], ["missing RSS URL"], True)
    try:
        request = Request(source.url, headers={"User-Agent": "daily-brief/0.1 read-only RSS collector"})
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - user-configured public source
            xml = response.read()
        root = ET.fromstring(xml)
    except Exception as exc:  # noqa: BLE001
        return CollectorResult(source.id, [], [f"RSS fetch failed: {exc}"], True)

    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    warnings: list[str] = []
    entries = _entries(root)
    lookback_hours = int(source.metadata.get("lookback_hours", 72) or 72)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    max_items = max(1, source.max_items)
    items: list[CollectedItem] = []
    for idx, node in enumerate(entries, start=1):
        parsed = _parse_node(node, source, idx, fetched_at)
        if parsed is None:
            continue
        published_dt = _parse_datetime(parsed["published_at"])
        if published_dt and published_dt < cutoff:
            # Keep a few high-signal evergreen feed entries if the feed is quiet.
            if len(items) >= min(2, max_items):
                continue
        items.append(_to_item(parsed, source, fetched_at))
        if len(items) >= max_items:
            break
    if not items:
        warnings.append(f"no entries within roughly {lookback_hours}h; feed may be quiet or dated")
    return CollectorResult(source.id, items, warnings=warnings, degraded=bool(warnings))


def _entries(root: ET.Element) -> list[ET.Element]:
    rss_items = root.findall(".//item")
    if rss_items:
        return rss_items
    return root.findall(f".//{ATOM}entry")


def _parse_node(node: ET.Element, source: SourceConfig, idx: int, fetched_at: str) -> dict[str, str] | None:
    is_atom = node.tag.endswith("entry")
    if is_atom:
        title = _text(node, f"{ATOM}title") or f"Untitled Atom item {idx}"
        link = _atom_link(node) or source.url
        desc = _text(node, f"{ATOM}summary") or _text(node, f"{ATOM}content") or title
        author = _text(node, f"{ATOM}author/{ATOM}name") or source.name
        published = _text(node, f"{ATOM}published") or _text(node, f"{ATOM}updated") or fetched_at
    else:
        title = _text(node, "title") or f"Untitled RSS item {idx}"
        link = _text(node, "link") or _text(node, "guid") or source.url
        desc = _text(node, f"{CONTENT}encoded") or _text(node, "description") or _text(node, f"{MEDIA}description") or title
        author = _text(node, f"{DC}creator") or _text(node, "author") or source.name
        published = _text(node, "pubDate") or _text(node, f"{DC}date") or fetched_at
    title = _clean_text(title)
    desc = _clean_text(desc)
    if not title or not link:
        return None
    return {"title": title, "url": link, "raw_excerpt": desc[:900] or title, "author": _clean_text(author) or source.name, "published_at": published or fetched_at}


def _to_item(parsed: dict[str, str], source: SourceConfig, fetched_at: str) -> CollectedItem:
    canonical = canonicalize_url(parsed["url"])
    item_id = f"{source.id}-{fingerprint_text(canonical)[:12]}"
    tags = source.metadata.get("tags", [])
    if isinstance(tags, str):
        tags = [part.strip() for part in tags.split(",") if part.strip()]
    metadata = {
        "section": source.metadata.get("section", "tech_news"),
        "tags": tags,
        "source_name": source.name,
        "collector": "rss",
    }
    return CollectedItem(
        id=item_id,
        source_id=source.id,
        source_type=source.type,
        title=parsed["title"],
        url=parsed["url"],
        canonical_url=canonical,
        author=parsed["author"],
        published_at=_normalize_datetime(parsed["published_at"], fallback=fetched_at),
        fetched_at=fetched_at,
        raw_excerpt=parsed["raw_excerpt"],
        content_text=f"{parsed['title']}\n\n{parsed['raw_excerpt']}",
        language=str(source.metadata.get("language", "en")),
        metadata=metadata,
    )


def _text(node: ET.Element, tag: str) -> str:
    child = node.find(tag)
    if child is None:
        return ""
    return "".join(child.itertext()).strip()


def _atom_link(node: ET.Element) -> str:
    for link in node.findall(f"{ATOM}link"):
        href = link.attrib.get("href", "").strip()
        rel = link.attrib.get("rel", "alternate")
        if href and rel in {"alternate", ""}:
            return href
    link = node.find(f"{ATOM}link")
    return link.attrib.get("href", "").strip() if link is not None else ""


def _clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _parse_datetime(value: str) -> datetime | None:
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    try:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _normalize_datetime(value: str, fallback: str) -> str:
    dt = _parse_datetime(value)
    return dt.replace(microsecond=0).isoformat() if dt else fallback
