'''Codex App webhook/dry-run push adapter.'''
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from .models import PushResult, PushTask


def send_codex_app_push(task: PushTask, *, payload_path: str | Path, webhook_url_env: str, dry_run_without_webhook: bool = True, timeout_seconds: int = 20) -> PushResult:
    payload_file = Path(payload_path)
    payload_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {'target': 'codex_app', 'type': 'daily_news_push_task', 'task': task.to_dict(), 'dry_run_hint': f'Set {webhook_url_env} to deliver this payload.'}
    payload_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
    webhook_url = os.getenv(webhook_url_env, '').strip()
    if not webhook_url:
        if dry_run_without_webhook:
            return PushResult(True, True, f'dry-run: {webhook_url_env} is not set; payload written locally', str(payload_file))
        return PushResult(False, False, f'missing required webhook env var {webhook_url_env}', str(payload_file), error='missing_webhook_url')
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    request = Request(webhook_url, data=body, method='POST', headers={'Content-Type': 'application/json; charset=utf-8', 'User-Agent': 'daily-brief/0.1'})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - user configured webhook
            status = int(response.status)
        ok = 200 <= status < 300
        return PushResult(ok, False, f'webhook POST returned HTTP {status}', str(payload_file), status, None if ok else 'non_2xx_status')
    except (URLError, TimeoutError, OSError) as exc:
        return PushResult(False, False, 'webhook POST failed; local payload preserved', str(payload_file), error=str(exc))
