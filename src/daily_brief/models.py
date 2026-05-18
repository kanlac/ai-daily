"""Core dataclass models for the daily briefing pipeline.

The first project iteration intentionally uses only the Python standard library.
Dataclasses keep the schema explicit while avoiding a hard dependency on
Pydantic or other validation packages.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _require_non_empty(value: str | list[Any], field_name: str) -> None:
    if isinstance(value, str) and not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if isinstance(value, list) and not value:
        raise ValueError(f"{field_name} must not be empty")


def _validate_url(url: str, field_name: str = "url") -> None:
    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("file://")):
        raise ValueError(f"{field_name} must be an http(s) or file URL: {url!r}")


@dataclass(slots=True)
class CollectedItem:
    id: str
    source_id: str
    source_type: str
    title: str
    url: str
    canonical_url: str
    author: str
    published_at: str
    fetched_at: str
    raw_excerpt: str
    content_text: str
    language: str = "en"
    metadata: JsonDict = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name in ("id", "source_id", "source_type", "title", "url", "canonical_url"):
            _require_non_empty(getattr(self, field_name), field_name)
        _validate_url(self.url)
        _validate_url(self.canonical_url, "canonical_url")

    def to_dict(self) -> JsonDict:
        return to_jsonable(self)


@dataclass(slots=True)
class DedupDecision:
    item_id: str
    status: str
    reason_code: str
    duplicate_of: str | None = None
    related_ids: list[str] = field(default_factory=list)
    novelty_score: float = 1.0
    similarity_score: float = 0.0
    explanation: str = ""

    def to_dict(self) -> JsonDict:
        return to_jsonable(self)


@dataclass(slots=True)
class BriefItem:
    id: str
    collected_item_id: str
    section: str
    title: str
    original_excerpt: str
    zh_translation: str
    summary_zh: str
    why_it_matters: str
    builder_takeaway: str
    source_links: list[str]
    dedup_status: str = "new"
    duplicate_of: str | None = None
    relation_ids: list[str] = field(default_factory=list)
    relation_reason: str = ""
    scores: dict[str, float] = field(default_factory=dict)
    source_id: str = ""
    source_title: str = ""
    published_at: str = ""
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for field_name in (
            "id",
            "collected_item_id",
            "section",
            "title",
            "original_excerpt",
            "zh_translation",
            "summary_zh",
            "why_it_matters",
        ):
            _require_non_empty(getattr(self, field_name), field_name)
        _require_non_empty(self.source_links, "source_links")
        for link in self.source_links:
            _validate_url(link, "source_links[]")

    def to_dict(self) -> JsonDict:
        return to_jsonable(self)


@dataclass(slots=True)
class ProductIdea:
    id: str
    title: str
    trigger_source_ids: list[str]
    pain_point_evidence: str
    pain_point_translation: str
    target_user: str
    current_workaround: str
    ai_solution: str
    mvp_scope: str
    distribution: str
    risks: str
    validation_plan: str
    score: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name in (
            "id",
            "title",
            "pain_point_evidence",
            "pain_point_translation",
            "target_user",
            "ai_solution",
            "mvp_scope",
            "validation_plan",
        ):
            _require_non_empty(getattr(self, field_name), field_name)
        _require_non_empty(self.trigger_source_ids, "trigger_source_ids")

    def to_dict(self) -> JsonDict:
        return to_jsonable(self)


@dataclass(slots=True)
class ScoreCard:
    round: int
    overall_score: float
    dimension_scores: dict[str, float]
    dimension_labels: dict[str, str]
    blocking_issues: list[str]
    warnings: list[str]
    critique: str
    revision_notes: list[str]
    improvement_suggestions: list[str]
    passed: bool
    created_at: str = field(default_factory=utc_now_iso)
    non_decrease_reason: str = ""

    def __post_init__(self) -> None:
        if self.round < 1:
            raise ValueError("round must be >= 1")
        if not (0 <= self.overall_score <= 10):
            raise ValueError("overall_score must be between 0 and 10")
        _require_non_empty(self.dimension_scores, "dimension_scores")
        _require_non_empty(self.dimension_labels, "dimension_labels")
        _require_non_empty(self.critique, "critique")

    def to_dict(self) -> JsonDict:
        return to_jsonable(self)


@dataclass(slots=True)
class Report:
    date: str
    window_start: str
    window_end: str
    title: str
    top_highlights: list[str]
    sections: dict[str, list[BriefItem]]
    section_titles: dict[str, str]
    product_ideas: list[ProductIdea]
    cross_day_memory: list[JsonDict]
    source_coverage: JsonDict
    revision_history: list[ScoreCard] = field(default_factory=list)
    render_metadata: JsonDict = field(default_factory=dict)
    generated_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        for field_name in ("date", "window_start", "window_end", "title"):
            _require_non_empty(getattr(self, field_name), field_name)
        _require_non_empty(self.top_highlights, "top_highlights")
        _require_non_empty(self.sections, "sections")
        _require_non_empty(self.section_titles, "section_titles")

    def all_items(self) -> list[BriefItem]:
        items: list[BriefItem] = []
        for section_items in self.sections.values():
            items.extend(section_items)
        return items

    def to_dict(self) -> JsonDict:
        return to_jsonable(self)


@dataclass(slots=True)
class PushTask:
    title: str
    summary: str
    report_path: str
    run_manifest_path: str
    suggested_actions: list[str]
    date: str
    scorecard_path: str = ""

    def __post_init__(self) -> None:
        for field_name in ("title", "summary", "report_path", "run_manifest_path", "date"):
            _require_non_empty(getattr(self, field_name), field_name)
        _require_non_empty(self.suggested_actions, "suggested_actions")

    def to_dict(self) -> JsonDict:
        return to_jsonable(self)


@dataclass(slots=True)
class PushResult:
    success: bool
    dry_run: bool
    message: str
    payload_path: str | None = None
    status_code: int | None = None
    error: str | None = None

    def to_dict(self) -> JsonDict:
        return to_jsonable(self)


@dataclass(slots=True)
class RunManifest:
    date: str
    status: str
    config_path: str
    report_path: str
    scorecard_path: str
    memory_path: str
    item_count: int
    scorecard_count: int
    push: JsonDict
    source_coverage: JsonDict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> JsonDict:
        return to_jsonable(self)


def to_jsonable(value: Any) -> Any:
    """Convert dataclasses and common runtime values to JSON-friendly objects."""

    if is_dataclass(value):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value
