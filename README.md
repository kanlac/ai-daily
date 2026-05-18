# Daily Brief

面向个人 builder 的本地优先每日新闻推送项目。它每天早上（默认 `07:00`）整理科技深度文章、工具工程更新、社媒博客、视频内容和产品/业务创意，生成一份自适应 HTML 报告，并通过 Codex App webhook adapter 创建自动化复盘任务。

> 当前版本默认执行真实只读采集：RSS/Atom、GitHub Releases、Reddit public JSON、YouTube channel feed。离线 fixture 仍保留在配置中，但默认关闭，主要用于测试和回归。

## 快速开始

```bash
uv run --with pytest pytest -q
uv run python -m daily_brief.cli run --config configs/daily-brief.yaml --date 2026-05-18 --loops 7
open reports/2026-05-18-daily-brief.html
```

如果不使用 `uv`：

```bash
python3 -m pip install -e '.[dev]'
python3 -m pytest -q
python3 -m daily_brief.cli run --config configs/daily-brief.yaml --date 2026-05-18 --loops 7
```

## 生成物

- `reports/{date}-daily-brief.html`：桌面优先、手机自适应的 HTML 日报。
- `reports/evaluations/{date}-scorecard.json`：每轮评分记录，默认 7 轮。
- `reports/push-payload-{date}.json`：Codex App webhook payload；未配置 webhook 时为 dry-run。
- `data/memory.sqlite3`：跨日记忆、去重、关联和评分历史。
- `data/runs/{date}/run.json`：本次运行 manifest。

## 当前真实采集源

默认配置在 `configs/daily-brief.yaml`：

- OpenAI News / Blog RSS
- Simon Willison Atom feed
- Latent Space RSS
- Hacker News AI RSS search
- Anthropic Claude Code GitHub Releases
- OpenAI Codex GitHub Releases
- NousResearch Hermes Agent GitHub Releases
- Reddit `r/smallbusiness` / `r/startups` public JSON
- Y Combinator YouTube channel RSS

Telegram 私域频道和 Chrome 登录态浏览采集不默认启用；它们需要用户显式提供公开导出/API 或外部只读 browser-use worker。

## 内容板块

1. **科技新闻**：深度文章、AI infra、Builder 实践，必须保留原文链接。
2. **工具与工程更新**：Claude Code、Codex、OpenAI、Anthropic、Hermes 等工具链动态。
3. **社交媒体与博客**：公开社媒、博客、Telegram 可行路径，聚焦“做事的人”和独特观点。
4. **视频内容**：YouTube Builder 访谈，优先字幕摘要，保留链接。
5. **产品创意与业务创意**：Reddit/非 AI 社区痛点 → 用户场景 → AI solution → MVP/GTM/风险。

## Codex App 自动化 / 7:00 推送

`configs/daily-brief.yaml` 默认：

```yaml
schedule:
  time: "07:00"
push:
  adapter: codex_app_webhook
  codex_app_webhook_url_env: CODEX_APP_WEBHOOK_URL
```

未设置 `CODEX_APP_WEBHOOK_URL` 时，runner 不会失败，而是写入本地 dry-run payload：

```bash
uv run python -m daily_brief.cli run --date 2026-05-18 --loops 7
cat reports/push-payload-2026-05-18.json
```

设置 webhook 后会用标准库 `urllib` POST JSON：

```bash
export CODEX_APP_WEBHOOK_URL='https://your-codex-app-server.example/webhook/daily-brief'
uv run python -m daily_brief.cli run --date 2026-05-18 --loops 7
```

本仓库还提供：

- `.codex/daily-news-push.md`：给 Codex App 自动化任务使用的说明。
- `scripts/run_daily_brief.sh`：本地 runner。
- `scripts/com.daily-brief.plist`：macOS launchd 示例，7:00 执行。

## 安全边界

- 默认只读采集公开来源或用户显式提供的导出/API。
- 不绕过登录墙、验证码、paywall、rate limit。
- 不读取 Cookie、密码、session token；配置中出现 `password/cookie/session` 会被拒绝。
- Telegram 私域频道不自动抓取；只支持公开 RSS/preview、用户导出或明确授权 API。
- Browser/Chrome 采集通过 `collectors/browser_prompts.py` 生成只读任务提示，由外部 Codex/Hermes browser-use worker 执行。

## 目录结构

```text
configs/                         # daily runner 配置
src/daily_brief/                  # Python 包
  cli.py                          # collect/dedup/evaluate/render/push pipeline
  memory.py                       # SQLite 记忆、去重、跨日关联
  renderer.py                     # 自适应 HTML 报告渲染
  evaluator.py                    # 5-10 轮多维评分
  push.py                         # Codex App webhook/dry-run adapter
  collectors/                     # RSS/Reddit/YouTube/Telegram/GitHub/browser prompt adapters
reports/                          # 生成的 HTML、scorecard、push payload
data/                             # SQLite memory 和 run manifests
docs/design/                      # 子代理产出的架构/来源/UX 文档
docs/plans/                       # 实施计划
scripts/                          # launchd 和本地执行脚本
tests/                            # TDD 测试
```

## 评估循环

`--loops` 必须在 5 到 10 之间。每轮都会输出：美观、信噪比、阅读体验、时效性、证据可追溯、去重/关联、移动端。默认发布阈值：综合分 ≥ 8.0，且无阻断项。

## 后续扩展建议

1. 把 RSS/GitHub collector 接入真实源，并保留失败 source 的 degraded 状态。
2. 用 Codex/Hermes browser-use worker 执行 `browser_prompts.py` 中的只读 Chrome 采集任务。
3. 为 YouTube 增加字幕抓取与无字幕低置信 fallback。
4. 引入 LLM 翻译/摘要 provider，但保持 dry-run fixture 测试不依赖网络。
5. 将 memory 从 Jaccard 扩展到本地 embedding/向量索引，但保留可解释 reason code。
