# Codex App Automation: Daily News Push

Goal: every morning at 07:00, run the local daily-brief pipeline and create a Codex App task pointing to the generated HTML report.

Command:

```bash
cd /Users/kan/Documents/daily-brief
./scripts/run_daily_brief.sh "$(date +%F)"
```

Expected artifacts:

- `reports/YYYY-MM-DD-daily-brief.html`
- `reports/evaluations/YYYY-MM-DD-scorecard.json`
- `reports/push-payload-YYYY-MM-DD.json`
- `data/runs/YYYY-MM-DD/run.json`

Webhook contract:

- Set `CODEX_APP_WEBHOOK_URL` to the Codex App Server webhook endpoint.
- The payload is JSON with `target=codex_app`, `type=daily_news_push_task`, and a `task` object containing title, summary, report path, scorecard path, run manifest path, and suggested actions.
- If the env var is absent, the runner performs a dry-run and writes the payload locally instead of failing.

Safety:

- Read-only public collection only.
- No credential/cookie/session extraction.
- No anti-detection/evasion behavior.
- Browser collection, when enabled, must use a user-authorized read-only Chrome session and skip login walls/CAPTCHA/paywalls.
