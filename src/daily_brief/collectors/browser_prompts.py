'''Prompt templates for Chrome/browser-use collection workers.'''
from __future__ import annotations
from daily_brief.config import SourceConfig
from .base import CollectorResult

BROWSER_COLLECTION_PROMPT = '''Use a read-only Chrome/browser session to inspect the last 24 hours of public posts. Do not bypass logins, CAPTCHAs, paywalls, or rate limits. Do not extract cookies or credentials. Return JSONL with title, url, author, published_at, original_excerpt, why_builder_should_care, and a Chinese translation.'''

def build_browser_prompt(source: SourceConfig, run_date: str) -> str:
    return f'{BROWSER_COLLECTION_PROMPT}\n\nrun_date={run_date}\nsource_id={source.id}\nsource_name={source.name}\nurl={source.url or source.path}'

def collect_browser_prompt(source: SourceConfig, run_date: str) -> CollectorResult:
    return CollectorResult(source.id, [], ['browser collection requires an external Chrome/Codex browser-use worker', build_browser_prompt(source, run_date)], True)
