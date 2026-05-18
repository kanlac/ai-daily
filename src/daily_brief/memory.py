"""SQLite-backed memory, URL canonicalization and conservative dedup logic."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .models import CollectedItem, DedupDecision

_TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "dclid",
    "gbraid",
    "wbraid",
    "mc_cid",
    "mc_eid",
    "igshid",
    "ref",
    "ref_src",
    "spm",
}
_STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "is",
    "are",
    "了",
    "的",
    "和",
    "与",
}


def canonicalize_url(url: str) -> str:
    """Return a stable canonical URL for dedup.

    Rules: lower-case scheme/host, drop fragments and common tracking params,
    sort remaining query params, normalize youtu.be links, strip trailing slash.
    """

    raw = url.strip()
    parts = urlsplit(raw)
    scheme = (parts.scheme or "https").lower()
    host = (parts.hostname or "").lower()
    if host.startswith("m.") and host not in {"m.youtube.com"}:
        host = host[2:]
    if host == "youtu.be":
        video_id = parts.path.strip("/")
        return f"https://www.youtube.com/watch?v={video_id}"
    if host in {"youtube.com", "m.youtube.com"}:
        host = "www.youtube.com"
    port = ""
    if parts.port and not ((scheme == "https" and parts.port == 443) or (scheme == "http" and parts.port == 80)):
        port = f":{parts.port}"
    netloc = f"{host}{port}"
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    query_pairs: list[tuple[str, str]] = []
    for key, value in parse_qsl(parts.query, keep_blank_values=False):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in _TRACKING_PARAMS:
            continue
        if host == "www.youtube.com" and path == "/watch" and lowered != "v":
            continue
        query_pairs.append((key, value))
    query = urlencode(sorted(query_pairs))
    if path == "/" and not query:
        path = ""
    return urlunsplit((scheme, netloc, path, query, ""))


def normalize_title(title: str) -> str:
    lowered = title.casefold().strip()
    lowered = re.sub(r"[\u2018\u2019\u201c\u201d'\"]", "", lowered)
    lowered = re.sub(r"[^\w\s\-\u4e00-\u9fff]", " ", lowered, flags=re.UNICODE)
    lowered = lowered.replace("-", " ")
    return re.sub(r"\s+", " ", lowered).strip()


def _tokens(text: str) -> set[str]:
    normalized = normalize_title(text)
    result: set[str] = set()
    for token in normalized.split():
        if token in _STOPWORDS or len(token) <= 1:
            continue
        if token.endswith("ies") and len(token) > 4:
            token = f"{token[:-3]}y"
        elif token.endswith("s") and len(token) > 3:
            token = token[:-1]
        result.add(token)
    return result


def fingerprint_text(text: str) -> str:
    normalized = normalize_title(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def jaccard_similarity(a: str, b: str) -> float:
    left = _tokens(a)
    right = _tokens(b)
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


@dataclass(slots=True)
class StoredItem:
    id: str
    title: str
    normalized_title: str
    canonical_url: str
    text_hash: str
    content_text: str
    run_date: str


class MemoryStore:
    """Small SQLite repository used for dedup and cross-day relations."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id TEXT PRIMARY KEY,
                    run_date TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    normalized_title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    canonical_url TEXT NOT NULL,
                    text_hash TEXT NOT NULL,
                    content_text TEXT NOT NULL,
                    published_at TEXT,
                    fetched_at TEXT,
                    metadata_json TEXT,
                    dedup_status TEXT DEFAULT 'new',
                    duplicate_of TEXT,
                    related_ids_json TEXT DEFAULT '[]',
                    relation_reason TEXT DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS idx_items_canonical_url ON items(canonical_url);
                CREATE INDEX IF NOT EXISTS idx_items_text_hash ON items(text_hash);
                CREATE TABLE IF NOT EXISTS relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT NOT NULL,
                    related_item_id TEXT NOT NULL,
                    reason_code TEXT NOT NULL,
                    similarity_score REAL NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS runs (
                    date TEXT PRIMARY KEY,
                    manifest_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS scorecards (
                    run_date TEXT NOT NULL,
                    round INTEGER NOT NULL,
                    scorecard_json TEXT NOT NULL,
                    PRIMARY KEY(run_date, round)
                );
                """
            )

    def record_collected_item(
        self,
        item: CollectedItem,
        run_date: str,
        decision: DedupDecision | None = None,
    ) -> None:
        canonical_url = canonicalize_url(item.canonical_url or item.url)
        normalized_title = normalize_title(item.title)
        text_hash = fingerprint_text(item.content_text or item.raw_excerpt or item.title)
        related_ids = decision.related_ids if decision else []
        with self.connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO items (
                    id, run_date, source_id, source_type, title, normalized_title, url,
                    canonical_url, text_hash, content_text, published_at, fetched_at,
                    metadata_json, dedup_status, duplicate_of, related_ids_json, relation_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.id,
                    run_date,
                    item.source_id,
                    item.source_type,
                    item.title,
                    normalized_title,
                    item.url,
                    canonical_url,
                    text_hash,
                    item.content_text,
                    item.published_at,
                    item.fetched_at,
                    json.dumps(item.metadata, ensure_ascii=False, sort_keys=True),
                    decision.status if decision else "new",
                    decision.duplicate_of if decision else None,
                    json.dumps(related_ids, ensure_ascii=False),
                    decision.reason_code if decision else "seed",
                ),
            )
            if decision:
                for related_id in decision.related_ids:
                    connection.execute(
                        """
                        INSERT INTO relations (item_id, related_item_id, reason_code, similarity_score)
                        VALUES (?, ?, ?, ?)
                        """,
                        (item.id, related_id, decision.reason_code, decision.similarity_score),
                    )

    def dedup_item(self, item: CollectedItem) -> DedupDecision:
        canonical_url = canonicalize_url(item.canonical_url or item.url)
        text_hash = fingerprint_text(item.content_text or item.raw_excerpt or item.title)
        normalized_title = normalize_title(item.title)

        with self.connect() as connection:
            canonical_match = connection.execute(
                "SELECT * FROM items WHERE canonical_url = ? AND id != ? ORDER BY run_date DESC LIMIT 1",
                (canonical_url, item.id),
            ).fetchone()
            if canonical_match:
                return DedupDecision(
                    item_id=item.id,
                    status="duplicate",
                    reason_code="canonical_url",
                    duplicate_of=str(canonical_match["id"]),
                    related_ids=[str(canonical_match["id"])],
                    novelty_score=0.0,
                    similarity_score=1.0,
                    explanation="规范化 URL 与历史条目完全一致。",
                )

            text_match = connection.execute(
                "SELECT * FROM items WHERE text_hash = ? AND id != ? ORDER BY run_date DESC LIMIT 1",
                (text_hash, item.id),
            ).fetchone()
            if text_match:
                return DedupDecision(
                    item_id=item.id,
                    status="duplicate",
                    reason_code="text_fingerprint",
                    duplicate_of=str(text_match["id"]),
                    related_ids=[str(text_match["id"])],
                    novelty_score=0.05,
                    similarity_score=1.0,
                    explanation="清洗后的正文 SHA-256 指纹相同。",
                )

            related: list[tuple[str, float, str]] = []
            duplicate_candidate: tuple[str, float] | None = None
            for stored in self._iter_items(connection):
                if stored.id == item.id:
                    continue
                title_similarity = jaccard_similarity(normalized_title, stored.normalized_title)
                body_similarity = jaccard_similarity(item.content_text or item.raw_excerpt, stored.content_text)
                similarity = max(title_similarity, body_similarity)
                if similarity >= 0.78:
                    duplicate_candidate = (stored.id, similarity)
                    break
                if similarity >= 0.30:
                    reason = "jaccard_similarity" if similarity >= 0.40 else "shared_terms"
                    related.append((stored.id, similarity, reason))

            if duplicate_candidate:
                duplicate_id, similarity = duplicate_candidate
                return DedupDecision(
                    item_id=item.id,
                    status="duplicate",
                    reason_code="title_similarity",
                    duplicate_of=duplicate_id,
                    related_ids=[duplicate_id],
                    novelty_score=max(0.0, round(1.0 - similarity, 3)),
                    similarity_score=round(similarity, 3),
                    explanation="标题/正文 Jaccard 相似度达到重复阈值。",
                )

            if related:
                related.sort(key=lambda entry: entry[1], reverse=True)
                related_ids = [entry[0] for entry in related[:3]]
                top_similarity = related[0][1]
                reason = related[0][2]
                return DedupDecision(
                    item_id=item.id,
                    status="related",
                    reason_code=reason,
                    related_ids=related_ids,
                    novelty_score=round(max(0.2, 1.0 - top_similarity), 3),
                    similarity_score=round(top_similarity, 3),
                    explanation="与历史主题共享关键实体/术语，作为跨日关联而非删除。",
                )

        return DedupDecision(
            item_id=item.id,
            status="new",
            reason_code="no_match",
            novelty_score=1.0,
            similarity_score=0.0,
            explanation="未命中 URL、文本指纹或近似标题重复。",
        )

    def _iter_items(self, connection: sqlite3.Connection) -> Iterable[StoredItem]:
        rows = connection.execute(
            "SELECT id, title, normalized_title, canonical_url, text_hash, content_text, run_date FROM items"
        ).fetchall()
        for row in rows:
            yield StoredItem(
                id=str(row["id"]),
                title=str(row["title"]),
                normalized_title=str(row["normalized_title"]),
                canonical_url=str(row["canonical_url"]),
                text_hash=str(row["text_hash"]),
                content_text=str(row["content_text"]),
                run_date=str(row["run_date"]),
            )

    def record_run_manifest(self, date: str, manifest: dict[str, object]) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO runs (date, manifest_json) VALUES (?, ?)",
                (date, json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)),
            )

    def record_scorecards(self, date: str, scorecards: list[dict[str, object]]) -> None:
        with self.connect() as connection:
            for card in scorecards:
                connection.execute(
                    "INSERT OR REPLACE INTO scorecards (run_date, round, scorecard_json) VALUES (?, ?, ?)",
                    (date, int(card["round"]), json.dumps(card, ensure_ascii=False, sort_keys=True)),
                )

    def seed_previous_item(self, item: CollectedItem, run_date: str) -> None:
        self.record_collected_item(item, run_date=run_date)
