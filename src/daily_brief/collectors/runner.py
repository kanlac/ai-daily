"""Source collection dispatcher."""
from __future__ import annotations

from daily_brief.config import SourceConfig
from daily_brief.models import CollectedItem
from daily_brief.sample_data import build_sample_collected_items
from .base import CollectorResult
from .browser_prompts import collect_browser_prompt
from .github_updates import collect_github_releases
from .reddit import collect_reddit
from .rss import collect_rss
from .telegram import collect_telegram
from .youtube import collect_youtube_feed


def collect_sources(sources: list[SourceConfig], run_date: str) -> tuple[list[CollectedItem], dict[str, object]]:
    all_items: list[CollectedItem] = []
    results: list[CollectorResult] = []
    configured = len([source for source in sources if source.enabled])
    for source in sources:
        if not source.enabled:
            continue
        if source.type == "fixture":
            items = build_sample_collected_items(run_date)[: source.max_items]
            result = CollectorResult(source.id, items, warnings=["fixture source enabled; not real-time news"], degraded=True)
        elif source.type == "rss":
            result = collect_rss(source, run_date)
        elif source.type == "reddit":
            result = collect_reddit(source, run_date)
        elif source.type == "youtube":
            result = collect_youtube_feed(source, run_date)
        elif source.type == "github_updates":
            result = collect_github_releases(source, run_date)
        elif source.type == "browser_prompts":
            result = collect_browser_prompt(source, run_date)
        elif source.type == "telegram":
            result = collect_telegram(source, run_date)
        else:
            result = CollectorResult(source.id, [], [f"unsupported source type: {source.type}"], True)
        results.append(result)
        all_items.extend(result.items)
    coverage = {
        "configured_sources": configured,
        "successful_sources": sum(1 for result in results if result.items),
        "failed_sources": sum(1 for result in results if not result.items and result.degraded),
        "degraded_sources": [result.source_id for result in results if result.degraded],
        "source_warnings": {result.source_id: result.warnings for result in results if result.warnings},
        "collected_events": len(all_items),
        "policy": "真实采集：只读公开 RSS/API/JSON/YouTube feed；不读取 Cookie、密码、session，不绕过登录墙或验证码。",
    }
    return all_items, coverage
