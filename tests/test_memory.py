from datetime import datetime, timezone

from daily_brief.memory import (
    MemoryStore,
    canonicalize_url,
    fingerprint_text,
    jaccard_similarity,
    normalize_title,
)
from daily_brief.models import CollectedItem


def make_item(item_id: str, title: str, url: str, text: str) -> CollectedItem:
    now = datetime(2026, 5, 18, 7, 0, tzinfo=timezone.utc).isoformat()
    return CollectedItem(
        id=item_id,
        source_id="fixture",
        source_type="fixture",
        title=title,
        url=url,
        canonical_url=canonicalize_url(url),
        author="Daily Brief Test",
        published_at=now,
        fetched_at=now,
        raw_excerpt=text[:180],
        content_text=text,
        language="en",
        metadata={},
    )


def test_url_title_fingerprint_helpers():
    assert (
        canonicalize_url("HTTPS://Example.com/Path/?utm_source=x&b=2&a=1#frag")
        == "https://example.com/Path?a=1&b=2"
    )
    assert canonicalize_url("https://youtu.be/abc123?t=10&utm_campaign=x") == "https://www.youtube.com/watch?v=abc123"
    assert normalize_title("  OpenAI   ships Agents SDK!!! ") == "openai ships agents sdk"
    assert len(fingerprint_text("OpenAI ships Agents SDK")) == 64
    assert jaccard_similarity("agent workflows for code review", "code review agent workflow") >= 0.5


def test_memory_store_dedup_and_related_ids(tmp_path):
    db_path = tmp_path / "memory.sqlite3"
    store = MemoryStore(db_path)
    store.initialize()

    historical = make_item(
        "old-1",
        "OpenAI ships agents SDK for production workflows",
        "https://openai.com/blog/agents-sdk?utm_source=newsletter",
        "OpenAI ships an Agents SDK for production workflows and tool orchestration.",
    )
    store.record_collected_item(historical, run_date="2026-05-17")

    duplicate = make_item(
        "new-dup",
        "OpenAI ships agents SDK for production workflows",
        "https://openai.com/blog/agents-sdk/",
        "OpenAI ships an Agents SDK for production workflows and tool orchestration.",
    )
    related = make_item(
        "new-related",
        "OpenAI Agents SDK adds tracing for production debugging",
        "https://openai.com/blog/agents-sdk-tracing",
        "The Agents SDK now adds tracing, production debugging and evaluations for developers.",
    )

    duplicate_decision = store.dedup_item(duplicate)
    related_decision = store.dedup_item(related)

    assert duplicate_decision.status == "duplicate"
    assert duplicate_decision.duplicate_of == "old-1"
    assert duplicate_decision.reason_code in {"canonical_url", "text_fingerprint", "title_similarity"}
    assert related_decision.status in {"related", "new"}
    assert related_decision.status == "related"
    assert "old-1" in related_decision.related_ids
    assert related_decision.reason_code in {"jaccard_similarity", "shared_terms"}
