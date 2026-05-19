# Daily Brief Acceptance Criteria

> Last updated: 2026-05-19
>
> Scope: this is a personal daily briefing system for the user, not a customer-facing SaaS/product. The final briefing can be produced by the agent itself during the scheduled Codex/Hermes task. The repo should provide reliable collection, evidence storage, HTML rendering, memory/dedup, and automation hooks; it does **not** need an embedded LLM-provider abstraction.

## Definitions

- **P0** — must pass before this is considered a usable daily briefing workflow.
- **P1** — important quality upgrades after P0 works reliably for several days.
- **P2** — nice-to-have / optional expansion.
- **Agent-generated report** — the scheduled Codex/Hermes task can use the agent to synthesize, translate, rank, and polish the report from collected evidence. This is not a productized LLM integration and does not require a provider abstraction in the repo.
- **Evidence item** — a structured record with source, URL, title, author/channel, published time, fetched time, original excerpt/transcript segment, Chinese explanation/translation, and section assignment.

---

## P0 — daily workflow must-haves

### P0.1 Real read-only collection, no fake news in production runs

**Requirement**

- Production/default config must collect from real public sources, not fixture-only sample content.
- Fixture source may exist for tests but must be disabled by default.
- Every report must expose source coverage: configured sources, successful sources, failed/degraded sources, collected item count, and deduplicated item count.

**Acceptance check**

```bash
uv run python -m daily_brief.cli run --config configs/daily-brief.yaml --date YYYY-MM-DD --loops 7
```

Pass if:

- `data/runs/YYYY-MM-DD/run.json` exists.
- `source_coverage.successful_sources >= 1`.
- `source_coverage.collected_events > 0`.
- `reports/YYYY-MM-DD-daily-brief.html` contains no known fixture-only titles.

**Current status**

- PASS for 2026-05-19 run: 11/11 configured real sources succeeded, 32 collected events, 26 report items.

### P0.2 YouTube subtitles/transcripts are automatically fetched

**Requirement**

- For each YouTube video retained in the report, the system must attempt automatic transcript/subtitle retrieval.
- Preferred languages: `zh`, `zh-Hans`, `en` fallback.
- If transcript exists, report must include transcript-derived excerpt with timestamp or transcript source metadata.
- If transcript is unavailable/disabled, report must explicitly mark `transcript_status=unavailable` or `disabled`; it must not pretend the RSS description is a transcript.
- Transcript fetch failures must degrade per item, not fail the whole daily run.

**Acceptance check**

Run a daily report with at least one YouTube item. Pass if each retained YouTube item in the structured evidence has one of:

- `transcript_status=fetched` and a non-empty transcript excerpt; or
- `transcript_status=unavailable|disabled|error` plus a visible low-confidence note in the HTML.

**Current status**

- NOT PASS yet. Current implementation uses YouTube channel RSS title/description only. This is the next P0 implementation task.

### P0.3 Report is agent-generated, not productized LLM integration

**Requirement**

- The project should not add a customer-facing LLM provider layer just for translation/summarization.
- The scheduled Codex/Hermes task can ask the agent to synthesize the final brief from structured evidence and write the HTML/report artifacts.
- Repo code should keep deterministic fallback rendering so tests and automation still work without network/model access.

**Acceptance check**

Pass if:

- No required `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / model config is needed to run tests or collection.
- Report generation can run in deterministic fallback mode.
- Codex/Hermes automation prompt describes that the agent is responsible for final editorial synthesis.

**Current status**

- PARTIAL PASS. Code has deterministic fallback and no LLM dependency. Codex automation prompt still needs to explicitly describe final agent synthesis.

### P0.4 HTML report is the primary artifact

**Requirement**

- The report must be a polished, readable HTML file saved under `reports/`.
- Desktop reading is primary; mobile responsive layout must exist.
- Must include: hero, daily judgement, five sections, source links, original excerpts, Chinese translation/explanation, cross-day memory, score summary, and product idea canvas.

**Acceptance check**

Pass if generated HTML contains:

- `id="tech_news"`, `id="tool_engineering"`, `id="social_blogs"`, `id="video"`, `id="product_ideas"`
- `原文摘录`, `中文翻译`, `跨日关联`, `评分摘要`, `Product Idea Canvas`
- `@media (max-width: 768px)` and `@media print`
- Browser console has no JS errors.

**Current status**

- PASS for 2026-05-19 run.

### P0.5 Source links and evidence traceability

**Requirement**

- Every core item must have at least one source URL.
- Every major claim must be traceable to original source text, feed description, transcript excerpt, or structured collector metadata.
- The report should avoid unsupported claims; weak/low-confidence items must be labeled.

**Acceptance check**

Pass if every `BriefItem` has:

- non-empty `source_links`
- non-empty `original_excerpt`
- non-empty `zh_translation` or Chinese explanation
- `source_id` visible in HTML

**Current status**

- PASS for RSS/GitHub/Reddit evidence. YouTube transcript-specific traceability is not P0.2-complete yet.

### P0.6 Memory, dedup, and cross-day association

**Requirement**

- Daily runs must update SQLite memory.
- URL canonicalization, title normalization, content fingerprinting, duplicate detection, and related-item association must run before rendering.
- Duplicate items should not crowd the main report.

**Acceptance check**

Pass if:

- `data/memory.sqlite3` is updated.
- duplicate/related statuses are persisted.
- HTML includes cross-day memory summary.
- Duplicate items are either removed from main sections or clearly downgraded.

**Current status**

- PASS basic implementation. Further quality tuning is P1.

### P0.7 Daily automation and Codex App push contract

**Requirement**

- A daily 07:00 automation path must exist.
- If `CODEX_APP_WEBHOOK_URL` is set, runner POSTs a JSON task payload.
- If not set, runner writes local dry-run payload and does not fail.
- The pushed task should point to HTML report, scorecard, and run manifest.

**Acceptance check**

Pass if:

- `scripts/run_daily_brief.sh` runs successfully.
- `scripts/com.daily-brief.plist` exists as macOS launchd example.
- `.codex/daily-news-push.md` documents the task contract.
- dry-run payload exists when webhook env var is absent.

**Current status**

- PASS.

### P0.8 Safety boundary

**Requirement**

- Only read public sources or user-provided exports/API.
- No credential/cookie/session extraction.
- No login-wall, CAPTCHA, paywall, rate-limit bypass.
- No anti-detection/evasion behavior.
- Telegram is not required for P0 if it requires login/private channel access.

**Acceptance check**

Pass if:

- Config and docs state these boundaries.
- Secret scan of generated HTML and JSON reports finds no obvious tokens.
- Telegram collectors are disabled or restricted to public/export/API paths.

**Current status**

- PASS. Telegram deferred.

### P0.9 Evaluation loop with real gates

**Requirement**

- Each run must perform 5–10 evaluation loops.
- Dimensions: visual quality, signal-to-noise, reading experience, timeliness, evidence traceability, dedup/association, mobile experience.
- Scorecard JSON must record every round and latest pass/fail.
- P0 pass threshold: latest score >= 8.0, min dimension >= 7.0, no blocking issues.

**Acceptance check**

Pass if:

- `reports/evaluations/YYYY-MM-DD-scorecard.json` exists.
- `loop_count` is 5–10.
- latest score and dimensions meet thresholds.

**Current status**

- PASS for 2026-05-19 run: 7 loops, latest score 8.39, min latest dimension 8.21.

---

## P1 — next quality bar after P0

### P1.1 Better editorial ranking and pruning

- Rank by builder relevance, novelty, source quality, and actionability.
- Limit each section to the highest-signal items.
- Move weak/duplicate/low-confidence items to appendix instead of main body.

### P1.2 Stronger person/context cards

- For non-obvious people/authors, include one-sentence background.
- Show why this person is worth listening to.
- Do not over-explain universally known figures.

### P1.3 Product idea quality gates

- Separate raw community pain from actual product opportunity.
- Score each idea by pain intensity, frequency, willingness to pay, feasibility, distribution, and regulatory/privacy risk.
- Require each product idea to cite the source item(s) that triggered it.

### P1.4 Real browser/social collection without unsafe login handling

- Add optional Chrome/browser-use workers for public pages and user-approved read-only sessions.
- If a source requires private login state, skip it unless user explicitly provides a safe export/API route.
- Keep Telegram optional: public RSS/export/API only.

### P1.5 YouTube transcript summarization quality

- After P0 transcript fetch works, summarize with timestamped chapters.
- Include 1–2 paragraphs per retained video: topic, guest/founder context, contrarian insight, builder takeaway.
- Mark transcript language and confidence.

### P1.6 Source configuration hygiene

- Move personal source lists into config profiles.
- Add per-source quotas and category-specific freshness windows.
- Add retries/backoff and clearer degraded-source diagnostics.

### P1.7 Visual polish

- Tighten typography, spacing, and section rhythm.
- Add better appendix collapse/search.
- Add print/PDF export check.

---

## P2 — optional expansion

- Public Telegram channel ingestion via RSS/export/API.
- Local semantic similarity / embeddings for dedup, if useful.
- OPML import for blogs/RSS.
- Multi-day trend pages and weekly synthesis.
- Manual thumbs-up/down feedback that tunes source weighting.

---

## Immediate next P0 task

Implement **P0.2 automatic YouTube transcript fetch**.

Suggested implementation path:

1. Add optional dependency path for `youtube-transcript-api` or vendor a tiny adapter that shells out to the existing `youtube-content` helper script when available.
2. Add `src/daily_brief/collectors/youtube_transcripts.py`.
3. Extend YouTube collector to attach transcript metadata to `CollectedItem.metadata`:
   - `transcript_status`
   - `transcript_language`
   - `transcript_excerpt`
   - `transcript_segments_sample`
4. Update renderer/report builder to display transcript-derived excerpt and low-confidence fallback notes.
5. Add tests with a fake transcript provider; no network dependency in unit tests.
6. Run a real YouTube report and verify each YouTube item has a transcript status.
