'''Telegram public-channel ingestion boundary.'''
from __future__ import annotations
from daily_brief.config import SourceConfig
from .base import CollectorResult

def collect_telegram(source: SourceConfig, run_date: str) -> CollectorResult:
    return CollectorResult(source.id, [], ['Telegram collector supports public RSS/export/API only; no private scraping is attempted.'], True)
