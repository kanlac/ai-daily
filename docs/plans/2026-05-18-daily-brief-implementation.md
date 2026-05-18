# 每日新闻推送 Python 项目实现计划（2026-05-18）

> 工作目录：`/Users/kan/Documents/daily-brief`  
> 计划文件：`/Users/kan/Documents/daily-brief/docs/plans/2026-05-18-daily-brief-implementation.md`  
> 任务总数：**42**  
> 原则：先用 fixture/sample data 跑通可复现闭环，再接入真实网络/API；所有外部能力必须可 mock、可 dry-run、可降级。

---

## 1. 目标与 MVP 验收口径

实现一个可运行的 Python Git 项目，用于每日新闻推送：

1. 通过 CLI 生成每日新闻简报：`python -m daily_brief.cli run --config configs/daily-brief.yaml --date 2026-05-18 --loops 7`。
2. 使用 fixture/sample data 完成端到端流程，不强依赖真实网络、真实 LLM、真实 Codex App API。
3. 输出精美、桌面优先、移动端自适应的 HTML 报告：`reports/2026-05-18-daily-brief.html`。
4. 支持 7:00 自动化任务配置：macOS `launchd` plist 生成、安装说明、dry-run 验证。
5. 支持 Codex App webhook/push adapter：优先 webhook/command；无官方通道时降级为本地 task spec 和 macOS 通知。
6. 支持跨日 memory/dedup：SQLite + URL/text fingerprint + relation reason code；初版可用 fixture 历史数据。
7. 每条入选内容包含原文摘录与中文翻译字段：`original_excerpt` / `zh_translation`，并保留可追溯链接。
8. 支持 5-10 轮评分记录：`--loops 7` 可生成 7 轮 scorecards；每轮包含分数、问题、修订建议与发布判定。
9. 测试优先：核心模块必须有 pytest 覆盖；collector/provider/push 默认使用 fake/stub。

最终验收命令：

```bash
cd /Users/kan/Documents/daily-brief
python -m daily_brief.cli run --config configs/daily-brief.yaml --date 2026-05-18 --loops 7
pytest
open reports/2026-05-18-daily-brief.html
```

也可按需求表述为：运行 `python -m daily_brief.cli run --config configs/daily-brief.yaml --date 2026-05-18 --loops 7`；运行 `pytest`；打开 `reports/2026-05-18-daily-brief.html`。

---

## 2. 设计依据摘要

已读取并参考以下设计文档：

- `docs/design/architecture.md`
- `docs/design/source-strategy.md`
- `docs/design/report-ux-evaluation.md`

关键落地要求：

1. **架构边界**：Runner 只编排，不直接抓网页、不拼 HTML、不绑定具体 LLM；依赖 `Collector`、`MemoryStore`、`Renderer`、`LLMProvider`、`PushAdapter` 接口。
2. **采集策略**：优先 RSS/API/公开网页/用户主动导出；Chrome/Telegram 仅处理用户授权或公开/导出数据；不绕过登录、验证码、付费墙或访问控制。
3. **报告 UX**：Hero、今日判断、关键变化、五大板块、原文摘录+中文翻译、Product Idea、跨日关联、Appendix、评分元数据；桌面高密度，移动单列可读。
4. **Memory/Dedup**：URL 规范化、强 key、text hash/simhash、跨日 relation；去重不删除原始候选，只标注 `duplicate_of`、`novelty_score`、`relation_ids` 与 reason code。
5. **评分 Gate**：Pre-flight gate + Revision gate；Revision gate 最少 5 轮，最多 10 轮，保存可回放 scorecard；发布前校验来源、摘录、翻译、HTML 结构与响应式。
6. **合规**：只读、低频、可配置源、无反检测、无凭证提取、遇限制即跳过并记录。

---

## 3. 实现顺序与 TDD 工作流

每个任务遵循：

```bash
cd /Users/kan/Documents/daily-brief
# 1. 先写/更新 pytest，确认目标行为
pytest tests/path/to/test_x.py -q
# 2. 实现最小代码
# 3. 跑相关测试
pytest tests/path/to/test_x.py -q
# 4. 跑全量测试
pytest
```

建议开发环境命令：

```bash
cd /Users/kan/Documents/daily-brief
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m daily_brief.cli --help
pytest
```

若后续选择 `uv`，保留同等命令：

```bash
cd /Users/kan/Documents/daily-brief
uv sync
uv run python -m daily_brief.cli --help
uv run pytest
```

---

## 4. 需要创建或修改的文件清单

> 本计划只列出后续实现需要创建/修改的文件；当前任务不实现代码。

### 4.1 项目根目录

- `pyproject.toml`：包元数据、依赖、`pytest`、`ruff`、`mypy` 配置。
- `README.md`：安装、配置、手动运行、7:00 调度、报告打开、测试说明。
- `.gitignore`：忽略 `.venv/`、`data/*.sqlite3`、`data/raw/`、缓存、日志；保留 sample fixtures 与 sample report。
- `configs/daily-brief.yaml`：MVP 主配置，默认使用 fixture/fake provider/fake push。
- `configs/sources.example.yaml`：RSS/Web/Reddit/YouTube/Telegram/Chrome export 示例源。
- `configs/scoring.example.yaml`：评分维度、权重、阈值、`min_rounds`/`max_rounds`。
- `configs/runtime.example.yaml`：路径、时区、输出、provider、push、launchd 示例。

### 4.2 Python 包：`src/daily_brief/`

- `src/daily_brief/__init__.py`
- `src/daily_brief/cli.py`
- `src/daily_brief/config.py`
- `src/daily_brief/paths.py`
- `src/daily_brief/logging.py`

Runner：

- `src/daily_brief/runner/daily_runner.py`
- `src/daily_brief/runner/pipeline.py`
- `src/daily_brief/runner/preflight.py`
- `src/daily_brief/runner/artifacts.py`

Models：

- `src/daily_brief/models/item.py`
- `src/daily_brief/models/source.py`
- `src/daily_brief/models/report.py`
- `src/daily_brief/models/run.py`
- `src/daily_brief/models/scoring.py`
- `src/daily_brief/models/push.py`

Collectors stubs：

- `src/daily_brief/collectors/base.py`
- `src/daily_brief/collectors/fixture.py`
- `src/daily_brief/collectors/rss.py`
- `src/daily_brief/collectors/web.py`
- `src/daily_brief/collectors/reddit.py`
- `src/daily_brief/collectors/youtube.py`
- `src/daily_brief/collectors/chrome_export.py`
- `src/daily_brief/collectors/telegram_public.py`

Enrichment：

- `src/daily_brief/enrichment/extract.py`
- `src/daily_brief/enrichment/translate.py`
- `src/daily_brief/enrichment/summarize.py`
- `src/daily_brief/enrichment/idea_generator.py`

Memory / Dedup：

- `src/daily_brief/memory/store.py`
- `src/daily_brief/memory/schema.sql`
- `src/daily_brief/memory/fingerprints.py`
- `src/daily_brief/memory/dedup.py`
- `src/daily_brief/memory/relations.py`

Scoring / Revision gate：

- `src/daily_brief/scoring/dimensions.py`
- `src/daily_brief/scoring/revision_gate.py`
- `src/daily_brief/scoring/report_card.py`

Rendering：

- `src/daily_brief/rendering/renderer.py`
- `src/daily_brief/rendering/validator.py`
- `src/daily_brief/rendering/assets/report.css`
- `src/daily_brief/rendering/templates/report.html.j2`
- `src/daily_brief/rendering/templates/components/hero.html.j2`
- `src/daily_brief/rendering/templates/components/item_card.html.j2`
- `src/daily_brief/rendering/templates/components/quote_block.html.j2`
- `src/daily_brief/rendering/templates/components/idea_canvas.html.j2`
- `src/daily_brief/rendering/templates/components/scorecard.html.j2`

Providers：

- `src/daily_brief/providers/llm.py`
- `src/daily_brief/providers/fake.py`
- `src/daily_brief/providers/browser.py`

Push：

- `src/daily_brief/push/codex_app.py`
- `src/daily_brief/push/webhook.py`
- `src/daily_brief/push/local_notification.py`
- `src/daily_brief/push/task_spec.py`

### 4.3 Tests / fixtures / snapshots

- `tests/conftest.py`
- `tests/fixtures/sample_sources.yaml`
- `tests/fixtures/sample_items.json`
- `tests/fixtures/sample_previous_memory.json`
- `tests/fixtures/rss/sample_feed.xml`
- `tests/fixtures/web/sample_article.html`
- `tests/fixtures/reddit/sample_reddit.json`
- `tests/fixtures/youtube/sample_transcript.json`
- `tests/fixtures/chrome/bookmarks_export.html`
- `tests/fixtures/telegram/public_channel.html`
- `tests/unit/test_config.py`
- `tests/unit/test_models.py`
- `tests/unit/test_preflight.py`
- `tests/unit/test_collectors_*.py`
- `tests/unit/test_fingerprints.py`
- `tests/unit/test_dedup.py`
- `tests/unit/test_relations.py`
- `tests/unit/test_enrichment.py`
- `tests/unit/test_revision_gate.py`
- `tests/unit/test_renderer.py`
- `tests/unit/test_push.py`
- `tests/integration/test_daily_runner_fixture.py`
- `tests/snapshots/sample_report.html`

### 4.4 Scripts / docs / reports

- `scripts/install_launchd.py`：生成/安装 macOS 7:00 launchd plist。
- `scripts/smoke_run.py`：fixture 端到端冒烟运行。
- `docs/ops/launchd.md`：7:00 调度安装、卸载、排错。
- `docs/ops/sources-policy.md`：源合规、Chrome/Telegram/YouTube/Reddit 边界。
- `reports/2026-05-18-daily-brief.html`：固定 fixture 生成的 sample report。
- `data/runs/2026-05-18/run.json`：运行 manifest（实现后由命令生成）。
- `data/runs/2026-05-18/items.json`：规范化内容（实现后由命令生成）。
- `data/runs/2026-05-18/scorecards.json`：7 轮评分记录（实现后由命令生成）。
- `data/runs/2026-05-18/codex_task.md`：Codex App 降级任务说明（实现后由命令生成）。

---

## 5. 配置契约

`configs/daily-brief.yaml` 初版建议包含以下逻辑字段：

```yaml
project:
  name: daily-brief
  timezone: Asia/Shanghai
  output_report: reports/{date}-daily-brief.html
  run_dir: data/runs/{date}

runtime:
  default_window_hours: 24
  offline_first: true
  use_fixtures: true
  allow_network: false
  max_items_per_source: 20

sources:
  config_file: configs/sources.example.yaml

memory:
  sqlite_path: data/daily_brief.sqlite3
  seed_fixture: tests/fixtures/sample_previous_memory.json

scoring:
  config_file: configs/scoring.example.yaml
  min_rounds: 5
  max_rounds: 10
  default_loops: 7

provider:
  type: fake
  timeout_seconds: 30

push:
  adapter: codex_app
  mode: task_file
  webhook_url_env: CODEX_APP_WEBHOOK_URL
  dry_run: true
  task_file: data/runs/{date}/codex_task.md

launchd:
  hour: 7
  minute: 0
  label: com.kan.daily-brief
```

必须避免在配置文件中写入 API key、Cookie、session、password；需要凭证时只允许环境变量引用。

---

## 6. 数据模型最低字段

### 6.1 `CollectedItem`

必须支持：

- `id`
- `source_id`
- `source_type`
- `title`
- `url`
- `canonical_url`
- `author`
- `published_at`
- `fetched_at`
- `raw_excerpt`
- `content_text`
- `language`
- `metadata`

### 6.2 `BriefItem`

必须支持：

- `id`
- `collected_item_id`
- `section`
- `title`
- `original_excerpt`
- `zh_translation`
- `summary_zh`
- `why_it_matters`
- `builder_takeaway`
- `source_links`
- `dedup_status`
- `duplicate_of`
- `relation_ids`
- `scores`

### 6.3 `Report`

必须支持：

- `date`
- `window_start`
- `window_end`
- `title`
- `top_highlights`
- `sections`
- `product_ideas`
- `cross_day_memory`
- `source_coverage`
- `revision_history`
- `render_metadata`

### 6.4 `ScoreCard`

必须支持：

- `round`
- `overall_score`
- `dimension_scores`
- `blocking_issues`
- `warnings`
- `critique`
- `revision_notes`
- `passed`
- `created_at`

---

## 7. 分阶段任务清单（42 项）

### Phase 0：项目骨架与质量基线

**任务 1：初始化 Python 包与依赖配置**

- 创建/修改：`pyproject.toml`、`src/daily_brief/__init__.py`。
- 依赖建议：`pydantic`、`pyyaml`、`jinja2`、`httpx`、`feedparser`、`beautifulsoup4` 或 `selectolax`、`typer` 或 `argparse`、`pytest`、`ruff`、`mypy`。
- TDD：先断言 `python -m daily_brief.cli --help` 可执行。
- 命令：`python -m pip install -e ".[dev]" && python -m daily_brief.cli --help`。

**任务 2：README 与开发命令基线**

- 创建/修改：`README.md`。
- 内容：安装、运行、测试、fixture 模式、报告路径、launchd、push adapter。
- 验收：README 中包含最终验收命令三件套。

**任务 3：配置目录与主配置样例**

- 创建/修改：`configs/daily-brief.yaml`、`configs/sources.example.yaml`、`configs/scoring.example.yaml`、`configs/runtime.example.yaml`。
- TDD：`tests/unit/test_config.py` 验证示例配置可加载；缺字段时失败。
- 命令：`pytest tests/unit/test_config.py -q`。

**任务 4：Pydantic 数据模型**

- 创建/修改：`src/daily_brief/models/*.py`。
- TDD：`tests/unit/test_models.py` 覆盖 `CollectedItem`、`BriefItem`、`Report`、`RunManifest`、`ScoreCard` round-trip。
- 验收：非法 URL、缺 `original_excerpt`、缺 `zh_translation` 的入选 item 校验失败。

**任务 5：固定 fixture 与 sample data**

- 创建/修改：`tests/fixtures/sample_items.json`、`tests/fixtures/sample_previous_memory.json`、各 collector fixture。
- 目标：覆盖五大板块：科技深度/Builder 实践、工具工程更新、Chrome/社媒/博客/Telegram、YouTube Builder 采访、产品/业务创意。
- 验收：fixture 不需要网络即可驱动 E2E。

### Phase 1：CLI、Pre-flight 与 Runner 框架

**任务 6：CLI 入口**

- 创建/修改：`src/daily_brief/cli.py`。
- 命令：`python -m daily_brief.cli run --config configs/daily-brief.yaml --date 2026-05-18 --loops 7 --dry-run`。
- TDD：help 文案、参数解析、非法日期、loops 范围校验。

**任务 7：路径与 artifacts 管理**

- 创建/修改：`src/daily_brief/paths.py`、`src/daily_brief/runner/artifacts.py`。
- 输出路径：`data/runs/{date}/run.json`、`items.json`、`scorecards.json`、`reports/{date}-daily-brief.html`。
- TDD：路径展开、目录创建、重复运行覆盖策略。

**任务 8：Pre-flight gate**

- 创建/修改：`src/daily_brief/runner/preflight.py`。
- 检查：配置 schema、输出可写、时间窗口、合规字段、provider fake health check、SQLite 可写、push dry-run。
- TDD：blocking error / warning / degraded 三类结果快照。

**任务 9：Pipeline stage abstraction**

- 创建/修改：`src/daily_brief/runner/pipeline.py`。
- 阶段：collect → normalize → enrich → memory/dedup → classify → score/revise → render → validate → push。
- TDD：fake stage 顺序、失败不中断策略、degraded 记录。

**任务 10：Daily Runner skeleton**

- 创建/修改：`src/daily_brief/runner/daily_runner.py`。
- TDD：使用 fake collector / fake provider / fake renderer / fake push 完成 dry-run。
- 验收：生成 `data/runs/2026-05-18/run.json` manifest。

### Phase 2：Collectors stubs 与规范化

**任务 11：Collector protocol 与公共 normalize**

- 创建/修改：`src/daily_brief/collectors/base.py`。
- 接口：`collect(window) -> list[CollectedItem]`。
- TDD：source metadata、时间窗口、错误/跳过 reason。

**任务 12：FixtureCollector**

- 创建/修改：`src/daily_brief/collectors/fixture.py`。
- 目标：MVP E2E 默认用 fixture，保证离线可跑。
- TDD：从 `tests/fixtures/sample_items.json` 生成稳定 item。

**任务 13：RSSCollector stub**

- 创建/修改：`src/daily_brief/collectors/rss.py`。
- TDD：`tests/fixtures/rss/sample_feed.xml` 解析、旧条目过滤、重复 guid 合并。
- 初版允许只实现 fixture/local file，不强制真实 HTTP。

**任务 14：WebCollector stub**

- 创建/修改：`src/daily_brief/collectors/web.py`。
- TDD：fixture HTML 抽取标题、正文摘录、发布时间；登录墙/403 fixture 返回 skipped reason。

**任务 15：RedditCollector stub**

- 创建/修改：`src/daily_brief/collectors/reddit.py`。
- TDD：fixture JSON 提取痛点原文、score、comment count、permalink、subreddit。
- 合规：不展示可识别个人隐私，用户名可 hash 或省略。

**任务 16：YouTubeCollector stub**

- 创建/修改：`src/daily_brief/collectors/youtube.py`。
- TDD：fixture metadata/transcript；无字幕时输出 `skipped_reason="no_transcript"` 或低置信摘要标记。

**任务 17：ChromeExportCollector stub**

- 创建/修改：`src/daily_brief/collectors/chrome_export.py`。
- TDD：只读取用户指定导出文件，如 `tests/fixtures/chrome/bookmarks_export.html`。
- 禁止：读取 Cookie、password、session、Chrome profile 私有数据库。

**任务 18：TelegramPublicCollector stub**

- 创建/修改：`src/daily_brief/collectors/telegram_public.py`。
- TDD：公开频道 fixture 解析；私有/需登录页面跳过并记录 reason。

### Phase 3：Memory、Dedup 与跨日关联

**任务 19：SQLite schema 与 repository**

- 创建/修改：`src/daily_brief/memory/schema.sql`、`src/daily_brief/memory/store.py`。
- 表：`runs`、`sources`、`items`、`fingerprints`、`relations`、`scorecards`。
- TDD：migration 幂等、insert/update/query。

**任务 20：Memory seed fixture 导入**

- 创建/修改：`src/daily_brief/memory/store.py`。
- 输入：`tests/fixtures/sample_previous_memory.json`。
- TDD：初始化测试库后可查到历史 thread/item。

**任务 21：URL canonicalization 与强去重**

- 创建/修改：`src/daily_brief/memory/fingerprints.py`、`src/daily_brief/memory/dedup.py`。
- 规则：去 `utm_*`、尾斜杠、fragment、大小写；YouTube video id、Reddit thing id 强 key。
- TDD：tracking 参数、移动域名、重复 guid。

**任务 22：文本指纹去重**

- 创建/修改：`src/daily_brief/memory/fingerprints.py`、`src/daily_brief/memory/dedup.py`。
- 初版：SHA-256 + 简化 simhash；embedding 仅保留接口/fake。
- TDD：近似标题识别；不同事件不误杀。

**任务 23：跨日 relation linking**

- 创建/修改：`src/daily_brief/memory/relations.py`。
- 输出：`relation_ids`、`thread_id`、`relation_reason`、`trend_status`。
- TDD：同实体/主题与历史 item 建立关系，并可解释。

**任务 24：Dedup report 与可回放解释**

- 创建/修改：`src/daily_brief/memory/dedup.py`、`data/runs/{date}/items.json` 输出逻辑。
- 验收：每个 duplicate/related 决策都有 reason code；不删除原始候选。

### Phase 4：摘录、翻译、摘要与产品创意

**任务 25：LLM provider interface 与 FakeProvider**

- 创建/修改：`src/daily_brief/providers/llm.py`、`src/daily_brief/providers/fake.py`。
- TDD：schema 输出、超时、重试、降级。
- 初版：FakeProvider 返回 deterministic 中文翻译/摘要/评分。

**任务 26：原文摘录模块**

- 创建/修改：`src/daily_brief/enrichment/extract.py`。
- TDD：每个入选 item 至少 1 条 `original_excerpt`；空摘录阻断发布或移入 appendix。

**任务 27：中文翻译模块**

- 创建/修改：`src/daily_brief/enrichment/translate.py`。
- TDD：`zh_translation` 字段完整；数字、版本号、URL 不被改写；fake provider deterministic。

**任务 28：摘要、影响分析与板块分类**

- 创建/修改：`src/daily_brief/enrichment/summarize.py`。
- TDD：五大板块分类；低置信内容进入 review/background；每条有 `why_it_matters`。

**任务 29：Product Idea generator**

- 创建/修改：`src/daily_brief/enrichment/idea_generator.py`。
- TDD：idea 必须包含 pain point evidence、目标用户、MVP、distribution/GTM、风险、验证路径；无证据不生成。

### Phase 5：5-10 轮评分 Gate

**任务 30：评分维度与权重**

- 创建/修改：`src/daily_brief/scoring/dimensions.py`、`configs/scoring.example.yaml`。
- 维度：时效性、信噪比、Builder 价值、来源可信与可追溯、跨日记忆与关联、中文表达与翻译质量、阅读体验、视觉美观、产品创意质量。
- TDD：权重和为 100%；hard floor 生效。

**任务 31：Revision loop controller**

- 创建/修改：`src/daily_brief/scoring/revision_gate.py`。
- 规则：`min_rounds=5`，`max_rounds=10`；`--loops 7` 固定执行 7 轮；无 `--loops` 时按阈值在第 5 轮后可停止。
- TDD：至少 5 轮、不超过 10 轮、loops 越界失败。

**任务 32：Scorecard 持久化**

- 创建/修改：`src/daily_brief/scoring/report_card.py`、`src/daily_brief/memory/store.py`。
- 输出：`data/runs/2026-05-18/scorecards.json`。
- TDD：每轮 scorecard 可 round-trip；HTML 输入包含 revision history。

**任务 33：事实与来源 back-check**

- 创建/修改：`src/daily_brief/scoring/revision_gate.py`。
- 规则：无来源 claim、缺链接 item、缺摘录/翻译核心 item 阻断正式发布。
- TDD：缺 `source_links` 或缺 `original_excerpt` 的核心 item 发布失败。

**任务 34：CLI `--loops` 与发布判定集成**

- 创建/修改：`src/daily_brief/cli.py`、`src/daily_brief/runner/daily_runner.py`。
- 验收：`python -m daily_brief.cli run --config configs/daily-brief.yaml --date 2026-05-18 --loops 7` 生成 7 条 scorecard。

### Phase 6：HTML Renderer 与 sample report

**任务 35：Jinja2 renderer 基础实现**

- 创建/修改：`src/daily_brief/rendering/renderer.py`、`src/daily_brief/rendering/templates/report.html.j2`。
- TDD：给定 Report fixture 生成 HTML；包含 `<header>`、`<nav>`、`<main>`、五大 section anchors、appendix。

**任务 36：报告组件化**

- 创建/修改：`src/daily_brief/rendering/templates/components/*.j2`。
- 组件：Hero、Judgement Block、Item Card、Quote Block、Thread Link、Idea Canvas、Scorecard。
- TDD：snapshot 覆盖关键组件。

**任务 37：响应式 CSS 与视觉规范**

- 创建/修改：`src/daily_brief/rendering/assets/report.css`。
- 要求：桌面 1200-1440px 高密度布局；小于 768px 单列；原文/appendix 默认折叠；触控目标不小于 44px；print CSS。
- TDD：CSS 包含断点、print media、关键 design tokens。

**任务 38：HTML validation**

- 创建/修改：`src/daily_brief/rendering/validator.py`。
- 检查：标题、日期、目录、section anchor、source links、original excerpt、zh translation、revision history、source coverage。
- TDD：缺任一关键块时 validator 失败。

**任务 39：固定 sample report 输出**

- 创建/修改：`reports/2026-05-18-daily-brief.html`（由实现后的命令生成）、`tests/snapshots/sample_report.html`。
- 验收：fixture 运行 deterministic；`open reports/2026-05-18-daily-brief.html` 可离线阅读。

### Phase 7：Codex App Push Adapter 与降级策略

**任务 40：PushTask / PushResult 与 Codex App adapter**

- 创建/修改：`src/daily_brief/models/push.py`、`src/daily_brief/push/codex_app.py`。
- 支持字段：title、summary、report_path、run_manifest_path、suggested_actions。
- TDD：dry-run 生成 payload；缺报告路径失败。

**任务 41：Webhook / local notification / task spec 降级**

- 创建/修改：`src/daily_brief/push/webhook.py`、`src/daily_brief/push/local_notification.py`、`src/daily_brief/push/task_spec.py`。
- 规则：webhook 失败不导致报告生成失败；写入 `data/runs/{date}/codex_task.md`；输出重试命令。
- TDD：不拼接未转义 shell 字符串；task spec 包含报告路径、summary、follow-up。

### Phase 8：7:00 调度、文档与端到端验收

**任务 42：launchd 脚本、运维文档与 E2E smoke**

- 创建/修改：`scripts/install_launchd.py`、`scripts/smoke_run.py`、`docs/ops/launchd.md`、`docs/ops/sources-policy.md`、`tests/integration/test_daily_runner_fixture.py`。
- launchd 命令：

```bash
cd /Users/kan/Documents/daily-brief
python scripts/install_launchd.py --config configs/daily-brief.yaml --hour 7 --minute 0 --dry-run
python scripts/install_launchd.py --config configs/daily-brief.yaml --hour 7 --minute 0 --install
launchctl list | grep daily-brief
```

- E2E 命令：

```bash
cd /Users/kan/Documents/daily-brief
python scripts/smoke_run.py --date 2026-05-18 --loops 7
python -m daily_brief.cli run --config configs/daily-brief.yaml --date 2026-05-18 --loops 7
pytest
```

---

## 8. 端到端产物契约

成功运行以下命令后：

```bash
cd /Users/kan/Documents/daily-brief
python -m daily_brief.cli run --config configs/daily-brief.yaml --date 2026-05-18 --loops 7
```

必须生成或更新：

- `reports/2026-05-18-daily-brief.html`
- `data/runs/2026-05-18/run.json`
- `data/runs/2026-05-18/items.json`
- `data/runs/2026-05-18/scorecards.json`
- `data/runs/2026-05-18/codex_task.md`（dry-run 或降级模式）

`scorecards.json` 必须包含 7 轮记录；每轮包含：

- `round`
- `overall_score`
- `dimension_scores`
- `critique`
- `revision_notes`
- `blocking_issues`
- `warnings`
- `passed`

HTML 报告必须包含：

- 日期 `2026-05-18` 与覆盖时间窗。
- Hero / 今日判断 / 关键变化。
- 五大内容板块或明确缺失说明。
- 每条核心内容的来源链接、原文摘录、中文翻译。
- Product Idea Canvas。
- 跨日关联 / Historical Threads。
- Appendix 来源列表。
- 评分与修订记录。
- 移动端断点和 print 样式。

---

## 9. 发布前检查清单

- [ ] `python -m daily_brief.cli --help` 可运行。
- [ ] `python -m daily_brief.cli run --config configs/daily-brief.yaml --date 2026-05-18 --loops 7` 成功退出。
- [ ] `pytest` 全部通过。
- [ ] `reports/2026-05-18-daily-brief.html` 存在、非空、可用浏览器打开。
- [ ] HTML 包含五大板块、原文摘录、中文翻译、来源链接、跨日关联、scorecards。
- [ ] `data/runs/2026-05-18/scorecards.json` 包含 7 轮评分。
- [ ] `data/runs/2026-05-18/items.json` 包含去重状态和 relation reason code。
- [ ] `data/runs/2026-05-18/codex_task.md` 在 dry-run 或无 webhook 时生成。
- [ ] `python scripts/install_launchd.py --config configs/daily-brief.yaml --hour 7 --minute 0 --dry-run` 输出 7:00 plist 且不覆盖现有配置。
- [ ] README 与 `docs/ops/launchd.md` 说明手动运行、自动化、失败重试、禁用 source。
- [ ] 不读取 Cookie、password、session，不绕过访问控制。

---

## 10. 风险与降级策略

1. **真实网络/API 不稳定**：MVP 默认 `use_fixtures: true`、`allow_network: false`；真实 collector 后续逐步启用。
2. **LLM 不可用**：默认 `FakeProvider`；真实 provider 只作为 adapter；失败时保留摘录与链接。
3. **Codex App 官方接口不确定**：adapter 隔离；优先 webhook/command；降级为 `codex_task.md` 与本地通知。
4. **去重误杀**：初版保守，只标记不删除；所有 dedup 决策保留 reason code。
5. **报告视觉不达标**：先保证语义结构和 CSS tokens；snapshot + validator 防止关键模块缺失。
6. **合规风险**：默认只读、公开/授权/导出；遇登录墙、403、付费墙、验证码即跳过并记录。

---

## 11. 推荐提交顺序

建议按以下 Git 提交粒度推进：

1. `chore: initialize python package and configs`
2. `test: add fixtures and model contract tests`
3. `feat: add cli preflight and runner skeleton`
4. `feat: add fixture collectors and normalization`
5. `feat: add sqlite memory and dedup reason codes`
6. `feat: add fake enrichment and product idea generation`
7. `feat: add revision gate and scorecard persistence`
8. `feat: add responsive html renderer and validation`
9. `feat: add codex push adapters and launchd docs`
10. `test: add e2e fixture smoke and sample report`

每个提交至少运行：

```bash
cd /Users/kan/Documents/daily-brief
pytest
```

关键里程碑提交额外运行：

```bash
cd /Users/kan/Documents/daily-brief
python -m daily_brief.cli run --config configs/daily-brief.yaml --date 2026-05-18 --loops 7
open reports/2026-05-18-daily-brief.html
```

---

## 12. 最终验收命令

必须在 `/Users/kan/Documents/daily-brief` 执行：

```bash
cd /Users/kan/Documents/daily-brief
python -m daily_brief.cli run --config configs/daily-brief.yaml --date 2026-05-18 --loops 7
pytest
open reports/2026-05-18-daily-brief.html
```

验收通过定义：

- 命令 1 成功生成 report、run manifest、items、scorecards、push task。
- 命令 2 全量测试通过。
- 命令 3 能打开精美自适应 HTML 报告，且报告包含来源、原文摘录、中文翻译、跨日关联与 7 轮评分记录。

---

## 13. 摘要

- 计划落盘路径：`/Users/kan/Documents/daily-brief/docs/plans/2026-05-18-daily-brief-implementation.md`
- 实现目标：可运行的 Python Git 项目，离线 fixture 可跑通每日新闻推送闭环。
- 核心验收：`python -m daily_brief.cli run --config configs/daily-brief.yaml --date 2026-05-18 --loops 7`、`pytest`、打开 `reports/2026-05-18-daily-brief.html`。
- 任务总数：**42**。
