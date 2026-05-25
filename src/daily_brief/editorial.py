"""Agent-authored editorial overrides for personal brief runs.

The collectors stay deterministic and evidence-preserving. When the scheduled
Codex/Hermes task has already translated and edited items, it can write a small
JSON file under ``data/editorial/{date}.json``. The pipeline then applies those
fields before report construction without adding an in-repo LLM provider.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import CollectedItem

_ALLOWED_FIELDS = {
    "title_zh",
    "original_title",
    "one_sentence",
    "summary_zh",
    "zh_translation",
    "why_it_matters",
    "builder_takeaway",
}


def editorial_overrides_path(run_date: str, base_dir: str | Path = "data/editorial") -> Path:
    return Path(base_dir) / f"{run_date}.json"


def apply_editorial_overrides(items: list[CollectedItem], path: str | Path) -> int:
    """Apply agent-authored Chinese title/summary/translation overrides.

    Missing files are fine: the deterministic fallback path remains usable.
    Unknown item IDs and unknown fields are ignored to keep the overlay safe.
    """

    override_path = Path(path)
    if not override_path.exists():
        return 0
    payload = json.loads(override_path.read_text(encoding="utf-8"))
    raw_items = payload.get("items", {}) if isinstance(payload, dict) else {}
    if not isinstance(raw_items, dict):
        return 0

    by_id = {item.id: item for item in items}
    applied = 0
    for item_id, fields in raw_items.items():
        item = by_id.get(str(item_id))
        if item is None or not isinstance(fields, dict):
            continue
        item.metadata.setdefault("original_title", item.title)
        for key, value in fields.items():
            if key in _ALLOWED_FIELDS and _valid_text(value):
                item.metadata[key] = str(value).strip()
        applied += 1
    return applied


def _valid_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
