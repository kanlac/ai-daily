# 每日新闻推送项目架构方案与任务拆分

## 1. 目标与范围

本项目是一个本地优先的每日新闻推送与 HTML 报告生成系统：每天早上 7 点触发一次自动化任务，收集过去 24 小时内的高价值信息，经过去重、关联、摘要、翻译、评分与多轮修订后，生成一份桌面阅读优先、移动端自适应的精美 HTML 报告，并将报告与结构化中间产物保存在 Git 仓库中；同时通过 Codex App push adapter 将“今日推送任务/报告入口”送达 Codex App 或本地可替代入口。

核心内容板块：

1. **科技深度 / Builder 实践**：长文、工程复盘、独立开发者实践、架构与产品构建经验。
2. **工具工程更新**：Claude Code、Codex、OpenAI、Anthropic、Hermes 等模型/Agent/开发工具生态更新。
3. **Chrome 浏览搜集**：基于可配置源，收集 24h 内社媒、博客、Telegram 等公开内容线索。
4. **YouTube Builder 采访摘要**：对 Builder / founder / engineer 访谈做结构化摘要、洞察提炼与可执行建议。
5. **产品 / 业务创意**：从 Reddit 等公开社区真实痛点出发，形成 AI product idea，并给出用户、场景、差异化与验证路径。

非目标：

- 不做自动化登录、凭证提取、反检测绕过或访问权限规避。
- 不绕过平台付费墙、访问控制、robots/ToS 限制。
- 不将 Codex App 适配逻辑与采集、渲染、记忆等核心逻辑耦合。
- 不追求全自动“真实判断”，所有自动评分都应保留可追溯输入、链接和人工复核入口。

---

## 2. 推荐技术栈

### 2.1 语言与运行时

- **Python 3.12+**：作为主流程、采集编排、记忆/去重、评分 gate 与测试的核心语言。
- **uv**：管理 Python 依赖、虚拟环境与脚本入口，保证本地运行速度与可复现性。
- **pytest + pytest-asyncio**：TDD 主测试框架，覆盖采集器、去重、评分 gate、渲染与 runner。
- **ruff + mypy**：基础代码质量、格式化与类型检查。

### 2.2 数据与持久化

- **SQLite**：保存 item、source、run、dedup fingerprint、cross-day memory、relation graph 等轻量状态。
- **本地文件系统**：保存每日 HTML、JSON 中间产物、原文摘录、评分记录、截图或渲染快照。
- **可选向量索引**：后期可引入 sqlite-vss、LanceDB 或 Chroma，用于跨日语义查重和主题关联；第一阶段先以 SimHash/MinHash + embedding adapter 接口保留扩展点。

### 2.3 采集与解析

- **httpx + selectolax / BeautifulSoup**：用于公开网页、RSS、博客、API 风格源的只读采集与解析。
- **feedparser**：RSS/Atom 订阅源解析。
- **yt-dlp / YouTube Transcript API adapter**：仅用于公开可访问的 YouTube 元信息与字幕/转录文本；若无合法字幕则保留链接并标记为“待人工处理”。
- **Playwright（可选，受限使用）**：仅在源明确允许、且普通 HTTP 无法获取公开内容时使用浏览器渲染公开页面；禁止隐身绕过、指纹伪装、验证码绕过、自动登录。
- **Chrome profile export/import adapter（可选）**：从用户主动导出的 bookmarks、history 或阅读列表中读取公开 URL；不读取 Cookie、密码、session token。

### 2.4 内容生成与翻译

- **LLM provider adapter**：统一封装 OpenAI / Anthropic / 本地模型等摘要、翻译、评分和修订能力，核心系统不绑定具体供应商。
- **Prompt templates**：以版本化模板文件管理摘要、翻译、产品创意、评分和 revision 指令。
- **Pydantic models**：约束 LLM 输出 schema，确保每条内容包含原文摘录、中文翻译、来源链接、时间、评分、去重信息与引用关系。

### 2.5 HTML 渲染

- **Jinja2**：服务端静态 HTML 渲染。
- **Tailwind CSS 或轻量 CSS tokens**：桌面优先，移动端自适应；第一阶段建议使用自维护 CSS tokens，减少构建链复杂度。
- **Playwright screenshot tests（可选）**：用于视觉回归和 responsive sanity check。
- **静态资源本地化**：CSS、图标、字体策略可配置；默认不依赖外部 CDN，以便报告长期可读。

### 2.6 调度与推送

- **macOS launchd**：本地每天 7 点触发 daily runner。
- **CLI 入口**：`daily-brief run --date YYYY-MM-DD`、`daily-brief render --run-id ...`、`daily-brief push --date ...`。
- **Codex App push adapter**：通过隔离的 adapter 对接 Codex App 能力；若暂无稳定 API，则降级为本地通知、打开报告文件、生成 Codex task spec 或调用用户配置的命令。

---

## 3. 推荐目录结构

```text
/Users/kan/Documents/daily-brief
├── README.md
├── pyproject.toml
├── uv.lock
├── config/
│   ├── sources.example.yaml          # 可配置信息源样例
│   ├── scoring.example.yaml          # 评分维度、阈值、权重
│   └── runtime.example.yaml          # 调度、输出路径、provider 配置样例
├── data/
│   ├── daily_brief.sqlite3           # 本地状态库；建议 gitignore
│   ├── raw/YYYY-MM-DD/               # 原始抓取片段、转录、响应快照；按需 gitignore
│   ├── runs/YYYY-MM-DD/              # 每日结构化中间产物
│   └── memory/                       # 跨日主题、实体、fingerprint、关联图导出
├── reports/
│   └── YYYY/MM/DD/index.html         # 每日最终 HTML 报告，建议纳入 Git
├── docs/
│   ├── design/
│   │   └── architecture.md           # 本文档
│   └── ops/
│       ├── launchd.md                # 本地 7 点调度说明
│       └── sources-policy.md         # 源与合规策略
├── scripts/
│   ├── install_launchd.py            # 安装/更新 launchd plist
│   └── smoke_run.py                  # 本地冒烟运行
├── src/daily_brief/
│   ├── __init__.py
│   ├── cli.py                        # Typer/argparse CLI
│   ├── runner/
│   │   ├── daily_runner.py           # 每日编排入口
│   │   ├── pipeline.py               # DAG/阶段执行
│   │   └── preflight.py              # Pre-flight gate
│   ├── collectors/
│   │   ├── base.py                   # Collector 协议与公共模型
│   │   ├── rss.py
│   │   ├── web.py
│   │   ├── chrome_export.py
│   │   ├── telegram_public.py
│   │   ├── reddit.py
│   │   └── youtube.py
│   ├── enrichment/
│   │   ├── extract.py                # 正文抽取、摘录定位
│   │   ├── translate.py              # 原文摘录→中文翻译
│   │   ├── summarize.py              # 摘要与洞察
│   │   └── idea_generator.py         # 痛点→AI product idea
│   ├── memory/
│   │   ├── store.py                  # SQLite repository
│   │   ├── fingerprints.py           # URL/content/entity fingerprints
│   │   ├── dedup.py                  # 跨日去重
│   │   └── relations.py              # 主题/实体/来源关联
│   ├── scoring/
│   │   ├── dimensions.py             # 评分维度定义
│   │   ├── revision_gate.py          # 5-10 轮迭代修订 gate
│   │   └── report_card.py            # 分数记录与解释
│   ├── rendering/
│   │   ├── renderer.py               # HTML renderer 边界
│   │   ├── assets/
│   │   └── templates/
│   │       ├── report.html.j2
│   │       └── components/
│   ├── push/
│   │   ├── codex_app.py              # Codex App push adapter
│   │   ├── local_notification.py     # 降级通道
│   │   └── task_spec.py              # 推送任务描述格式
│   ├── providers/
│   │   ├── llm.py                    # LLM provider interface
│   │   └── browser.py                # 受限浏览器接口
│   └── models/
│       ├── item.py
│       ├── report.py
│       ├── source.py
│       └── run.py
└── tests/
    ├── fixtures/
    ├── unit/
    ├── integration/
    └── snapshots/
```

说明：第一阶段可以不一次性创建所有目录，但代码边界应按上述结构演进。`reports/` 中的最终 HTML 建议提交到 Git；`data/raw`、SQLite、API 响应缓存等是否提交由隐私策略决定，默认不提交。

---

## 4. 组件边界

### 4.1 本地 Daily Runner

职责：

- 作为每日 7 点任务的唯一编排入口。
- 加载配置、创建 run record、执行 pre-flight gate。
- 调用 collectors 获取候选内容。
- 调用 enrichment、memory/dedup、scoring、renderer、push adapter。
- 产出结构化运行日志、可复现的 run manifest 与错误报告。

输入：

- 日期与时间窗口：默认 `now - 24h` 到 `now`。
- 配置文件：sources、scoring、runtime、provider。
- 本地 memory store。

输出：

- `data/runs/YYYY-MM-DD/run.json`：本次运行 manifest。
- `data/runs/YYYY-MM-DD/items.json`：规范化候选与入选内容。
- `data/runs/YYYY-MM-DD/scorecards.json`：评分和修订记录。
- `reports/YYYY/MM/DD/index.html`：最终报告。
- push adapter 的投递结果。

边界：

- Runner 不直接解析网页、不直接生成 HTML 字符串、不直接调用某个具体 LLM API。
- Runner 只依赖接口：`Collector`、`MemoryStore`、`Renderer`、`LLMProvider`、`PushAdapter`。
- 任何外部 I/O 都必须可被 mock，以支持 TDD 和 dry-run。

### 4.2 HTML Renderer

职责：

- 将 `Report` 结构化对象渲染为单文件或少量静态资源 HTML。
- 提供桌面优先的信息密度、导航、标签、来源、原文摘录、中文翻译与评分解释。
- 保证移动端自适应：单列布局、可折叠长摘录、可点击目录、合理字号和触控间距。
- 输出可长期保存、可离线打开、链接可追溯的报告。

输入：

- `Report` model：包含 section、item、source、excerpt、translation、score、relations、idea card 等。
- 渲染配置：主题、密度、是否嵌入 CSS、是否生成目录。

输出：

- HTML 文件。
- 可选渲染元数据：字数、条目数、section 分布、截图路径。

边界：

- Renderer 不负责采集、摘要、翻译或评分。
- Renderer 不修改 memory store。
- Renderer 只接受已完成 gate 的 report 对象；若输入不完整，应失败并返回可测试错误。

### 4.3 Memory / Dedup

职责：

- 跨日保存来源、URL、canonical URL、标题、作者、发布时间、正文指纹、摘要指纹、实体、主题、评分历史。
- 去重：同 URL、相似 URL、转载/镜像、相似标题、相似正文、同一事件多来源。
- 关联：将今日内容与过去报道、同一产品/公司/人物/主题建立关系。
- 为报告提供“此前提到过”“与昨日/上周内容关联”“新进展/重复信息”等解释。

去重策略分层：

1. **硬去重**：canonical URL、source item id、YouTube video id、Reddit post id 等完全一致。
2. **规范化去重**：去 tracking 参数、URL fragment、大小写、尾部斜杠、移动端域名映射。
3. **文本指纹**：标题 SimHash、正文 MinHash、关键句 fingerprint。
4. **语义近似**：通过 embedding adapter 计算相似度；第一阶段可先保留接口与测试假实现。
5. **事件聚类**：实体 + 时间 + 动作词 + 来源类型聚类，识别“同一新闻多来源”。

边界：

- Memory 不调用网络。
- Dedup 不删除原始候选，只标记 `duplicate_of`、`novelty_score`、`relation_ids`。
- 所有去重决策必须可解释、可回放、可覆盖测试。

### 4.4 Source Collectors

职责：

- 从可配置公开源收集候选 item。
- 统一输出 `CollectedItem`：source、url、title、author、published_at、fetched_at、raw_excerpt、content_type、language、metadata。
- 记录抓取状态、错误、速率限制与跳过原因。

建议 collector 类型：

- `RSSCollector`：博客、公司更新、技术媒体。
- `WebCollector`：公开网页列表页、文章页。
- `ChromeExportCollector`：用户主动导出的 Chrome bookmarks/history/reading list 中的 URL。
- `TelegramPublicCollector`：公开频道网页或用户提供的公开导出，不读取私有会话或凭证。
- `RedditCollector`：公开 subreddit 搜索/列表，聚焦 pain point、complaint、workflow hack。
- `YouTubeCollector`：公开视频元信息、字幕/转录、章节与评论摘要（评论需遵守平台规则）。

边界：

- Collector 只做“发现与基础抽取”，不负责最终摘要、翻译、评分、渲染。
- Collector 必须遵守 per-source 配置：启用/禁用、频率、时间窗口、最大条数、允许字段。
- Collector 默认只读、低频、尊重 robots/ToS；遇到登录、验证码、付费墙、访问限制时应停止并标记原因。

### 4.5 Codex App Push Adapter

职责：

- 将每日报告入口和任务说明投递给 Codex App 或本地等价入口。
- 隔离 Codex App 相关能力差异，避免核心 pipeline 依赖具体 UI 或 API。
- 支持 dry-run，便于测试和本地开发。

建议抽象：

```python
class PushAdapter(Protocol):
    def push(self, task: PushTask) -> PushResult: ...
```

`PushTask` 至少包含：

- `title`：如“每日新闻简报 - 2026-05-18”。
- `summary`：今日重点与报告路径。
- `report_path`：本地 HTML 路径。
- `run_manifest_path`：结构化运行记录。
- `suggested_actions`：建议在 Codex App 中执行的复盘或 follow-up task。

适配策略：

1. **官方能力优先**：若 Codex App 提供稳定 URL scheme、CLI、API 或 inbox 目录，则 adapter 实现对应通道。
2. **本地通知降级**：通过 macOS notification 展示标题与报告路径。
3. **文件任务降级**：生成 `data/runs/YYYY-MM-DD/codex_task.md`，用户从 Codex App 打开或引用。
4. **命令钩子降级**：允许用户配置 `push.command`，由 adapter 传入安全的 JSON payload。

边界：

- Adapter 不读取 Codex App 凭证、数据库或私有状态。
- Adapter 不负责生成报告内容。
- Adapter 失败不应导致报告生成失败；runner 应记录 push 失败并保留重试命令。

---

## 5. 数据模型建议

### 5.1 CollectedItem

- `id`：本地稳定 ID。
- `source_id` / `source_type`。
- `url` / `canonical_url`。
- `title`。
- `author`。
- `published_at` / `fetched_at`。
- `raw_excerpt`：原始摘录，保留原语言。
- `content_text`：可选正文片段。
- `language`。
- `metadata`：平台字段，如 video id、subreddit、channel、tags。

### 5.2 BriefItem

- `collected_item_id`。
- `section`：报告板块。
- `original_excerpt`：可引用的原文摘录。
- `zh_translation`：中文翻译。
- `summary_zh`：中文摘要。
- `why_it_matters`：重要性解释。
- `builder_takeaway`：对 builder 的启发。
- `dedup_status`：new / duplicate / related / follow_up。
- `relations`：关联历史 item 或主题。
- `scores`：各维度评分。
- `source_links`：保留全部来源链接。

### 5.3 ProductIdea

- `pain_point_evidence`：来自 Reddit/社区的原文痛点摘录与中文翻译。
- `target_user`。
- `current_workaround`。
- `ai_solution`。
- `mvp_scope`。
- `distribution`。
- `risk`。
- `validation_plan`。
- `score`：痛点强度、付费意愿、可实现性、差异化、时机。

### 5.4 Report

- `date` / `window_start` / `window_end`。
- `sections`。
- `top_highlights`。
- `cross_day_memory`：今日与历史关联摘要。
- `source_coverage`：源覆盖、失败源、跳过原因。
- `revision_history`：gate 迭代记录。
- `render_metadata`。

---

## 6. Daily Pipeline

```text
launchd 07:00
  -> daily-brief run --date today
    -> load config
    -> Pre-flight gate
    -> collect candidates from sources
    -> normalize + canonicalize
    -> extract excerpts + translate
    -> memory lookup + dedup + relation linking
    -> classify into sections
    -> summarize / synthesize / idea generation
    -> Revision gate: score, critique, revise, repeat 5-10 rounds or until pass
    -> render HTML
    -> validate output
    -> save artifacts
    -> push to Codex App adapter
```

失败策略：

- 单个 source 失败：记录为 degraded，不中断全局任务。
- 核心 gate 失败：不推送“正式报告”，生成 failure report 或 draft report，提示失败原因。
- LLM provider 失败：使用缓存或降级模板；无法生成摘要时保留原始摘录与链接。
- Push 失败：报告仍保存，输出重试命令。

---

## 7. 安全与合规边界

必须遵守以下原则：

1. **只读抓取**：仅访问公开、允许访问的页面/API/RSS/导出文件；不做写入、点赞、评论、关注、私信等交互。
2. **保留链接与出处**：每条报告内容必须保留原始 URL、来源名称、发布时间或抓取时间；不得生成无法追溯的“无源新闻”。
3. **可配置源**：所有 source 必须来自配置文件，支持启用/禁用、频率限制、最大条数、时间窗口与字段白名单。
4. **无反检测**：禁止使用指纹伪装、代理池轮换、验证码绕过、自动重试规避风控、模拟人类行为绕过限制。
5. **无凭证提取**：禁止读取浏览器 Cookie、密码、session、localStorage token、私有数据库或 App 内部凭证。
6. **尊重访问控制**：遇到登录墙、付费墙、403/401、验证码、robots/ToS 明确限制时停止并记录跳过原因。
7. **最小化保存**：默认只保存必要摘录、链接、摘要、翻译和评分；敏感原始响应不进入 Git。
8. **隐私隔离**：Chrome/Telegram 等个人数据只能来自用户主动导出或明确配置的公开源；不得扫描私人聊天、邮箱或未授权目录。
9. **可审计**：每次运行保存 source coverage、抓取时间、跳过原因、去重决策、LLM prompt 版本与评分记录。
10. **人工可控**：提供 dry-run、source allowlist、禁用 Playwright、禁用外部 LLM、禁用 push 等开关。

---

## 8. 5-10 轮迭代评分 Gate 设计

评分 gate 分为 **Pre-flight gate** 和 **Revision gate**。Pre-flight gate 决定“是否可以开始”；Revision gate 决定“是否可以发布”。

### 8.1 Pre-flight Gate

运行在采集与生成之前，用于避免低质量或不可控运行。

检查项：

- 配置有效：sources/scoring/runtime/provider schema 校验通过。
- 输出路径可写：`data/runs` 与 `reports` 可创建或写入。
- 时间窗口有效：默认 24h，允许手动覆盖。
- 源合规：所有启用源有 type、URL、rate limit、policy 标记。
- 凭证边界：未配置读取 Cookie/password/session 等禁止字段。
- Provider 可用：LLM provider、翻译、摘要能力通过轻量 health check；不可用则进入降级模式。
- 历史库可读写：SQLite migration 可执行，memory store 可访问。
- Push adapter 可 dry-run：即使正式 push 不可用，也能生成本地 task spec。

输出：

- `preflight_passed: true/false`
- `warnings[]`
- `blocking_errors[]`
- `degraded_capabilities[]`

规则：

- 有 blocking error：停止 pipeline，生成 failure manifest。
- 只有 warning/degraded：继续运行，但报告中显示 source coverage 和降级说明。

### 8.2 Revision Gate 总体流程

目标是在发布前进行 5-10 轮多维评估与修订，提升信噪比、时效性、美观和阅读体验。

```text
Draft Report v0
  -> Round 1 score + critique
  -> revise
  -> Round 2 score + critique
  -> revise
  -> ...
  -> min_rounds reached and pass thresholds
  -> final validation
```

建议参数：

- `min_rounds = 5`
- `max_rounds = 10`
- `pass_threshold_overall = 8.0 / 10`
- `hard_floor_per_dimension = 6.5 / 10`
- `must_have_sections = 5`
- `min_original_excerpt_ratio = 0.9`：入选 item 中至少 90% 有原文摘录。
- `min_translation_ratio = 0.9`：入选 item 中至少 90% 有中文翻译。
- `max_duplicate_ratio = 0.15`：重复或低新意 item 不超过 15%。

### 8.3 评分维度

每轮输出结构化 scorecard，包含分数、证据、问题、修订建议。

| 维度 | 说明 | 建议权重 |
| --- | --- | ---: |
| 时效性 | 是否覆盖过去 24h 内新信息，是否标注旧闻/延展 | 15% |
| 信噪比 | 是否去除重复、营销稿、空泛观点，信息密度是否足够 | 18% |
| Builder 价值 | 是否提供可执行工程/产品/增长启发 | 15% |
| 来源可信与可追溯 | 是否保留链接、摘录、发布时间，多源是否互证 | 12% |
| 跨日记忆与关联 | 是否说明与历史主题的关系、新进展与重复点 | 10% |
| 中文表达与翻译质量 | 翻译准确、摘要自然、不夸大、不丢失限定条件 | 10% |
| 阅读体验 | 结构、标题、导航、长短节奏、重点突出 | 8% |
| 视觉美观 | HTML 布局、层级、色彩、卡片、移动端适配 | 7% |
| 产品创意质量 | 痛点证据真实，idea 清晰、可验证、差异化 | 5% |

### 8.4 每轮修订策略

每一轮不应简单重写全文，而应有明确目标：

1. **Round 1：覆盖与合规**  
   检查五大板块是否齐全、来源链接是否完整、是否存在不合规采集内容。
2. **Round 2：去重与新意**  
   删除重复 item，合并同一事件多来源，补充“新进展”说明。
3. **Round 3：摘要与翻译**  
   修正原文摘录/中文翻译，确保摘要不脱离来源。
4. **Round 4：Builder 价值**  
   增加工程实践、可执行 takeaway、产品机会与风险。
5. **Round 5：结构与阅读体验**  
   优化标题、排序、目录、重点摘要、长文节奏。
6. **Round 6：视觉与响应式**  
   检查 HTML 卡片、标签、暗色/浅色、移动端断点。
7. **Round 7：事实与引用回查**  
   对高影响 claim 做 source back-check，无法确认则降级表述。
8. **Round 8：产品创意打磨**  
   强化 pain point evidence、MVP、distribution、validation plan。
9. **Round 9：压缩与信噪比**  
   删除低价值段落，保留关键证据与行动项。
10. **Round 10：发布前一致性**  
    检查 schema、链接、日期、路径、coverage、scorecard 完整性。

第一阶段可以固定执行 5 轮；当任一硬性指标未达标时继续到最多 10 轮。每轮必须保存 diff 或 revision note，避免不可解释的“黑盒改稿”。

### 8.5 发布判定

可发布条件：

- 至少完成 `min_rounds`。
- overall score 达到阈值。
- 无 hard floor 维度低于阈值。
- 五大板块齐全；若某板块无可靠来源，必须在报告中说明“今日未发现足够可信更新”。
- 所有入选 item 均有来源链接；绝不发布无来源 claim。
- HTML validation 通过：文件存在、非空、包含标题、日期、目录、section anchor、source links。

不可发布时：

- 保存 draft HTML 与 failure manifest。
- Push adapter 只推送“生成失败/需人工复核”的任务，不推送正式报告。

---

## 9. HTML 报告信息架构

建议页面结构：

1. **Hero 摘要**
   - 日期、时间窗口、运行状态。
   - 今日 3-5 条最高价值 highlights。
   - Source coverage：成功/失败/降级源数量。
2. **今日脉络**
   - 与过去几天/几周主题的关系。
   - 新进展、重复信息、值得继续追踪的问题。
3. **五大内容板块**
   - 每个 item 用卡片呈现：标题、标签、来源、时间、评分、为什么重要。
   - 展开区展示原文摘录与中文翻译。
   - 显示 dedup/related 状态。
4. **产品/业务创意卡片**
   - 痛点证据、目标用户、AI 方案、MVP、验证路径、风险。
5. **评分与修订记录**
   - overall score、各维度雷达/条形分、轮次摘要。
6. **附录**
   - 全部来源链接。
   - 跳过/失败源说明。
   - 运行 manifest 链接。

桌面优先建议：

- 最大内容宽度约 1180-1320px。
- 左侧 sticky 目录 + 主内容双栏；移动端折叠为顶部目录。
- 卡片密度高但留足行距；长摘录默认折叠。
- 每条内容显示“阅读价值标签”：`新进展`、`工程可用`、`产品机会`、`需验证`、`重复合并`。

移动端适配：

- 断点小于 768px 时单列。
- 来源链接、展开按钮、目录 anchor 触控区域不小于 44px。
- 表格转为卡片或横向滚动。
- Hero highlights 控制长度，避免首屏过长。

---

## 10. 实现任务拆分（适合 TDD 与子代理执行）

### Phase 0：项目骨架与质量基线

1. **初始化 Python 项目**
   - 产出：`pyproject.toml`、`src/daily_brief`、`tests`。
   - 测试：`daily-brief --help` 可运行；ruff/mypy/pytest 基线通过。
2. **定义 Pydantic 数据模型**
   - 产出：`CollectedItem`、`BriefItem`、`Report`、`RunManifest`、`ScoreCard`。
   - 测试：schema round-trip、必填字段校验、非法 URL/日期失败。
3. **配置加载器**
   - 产出：sources/scoring/runtime YAML loader。
   - 测试：示例配置加载成功；缺少 rate limit、非法 source type 失败。

### Phase 1：Pre-flight 与 Runner 框架

4. **实现 Pre-flight gate**
   - 产出：配置校验、路径校验、provider dry check、合规字段检查。
   - 测试：blocking error/warning/degraded 三类结果快照。
5. **实现 Daily Runner pipeline skeleton**
   - 产出：阶段编排、run manifest、错误收集、dry-run。
   - 测试：使用 fake collector/renderer/push adapter 完成端到端 dry-run。
6. **实现 launchd 安装脚本设计**
   - 产出：生成 plist，不自动覆盖已有配置。
   - 测试：plist 内容包含 7:00、正确工作目录、日志路径。

### Phase 2：采集器

7. **Collector base protocol 与 normalize 工具**
   - 产出：统一 `collect(window) -> list[CollectedItem]`。
   - 测试：URL canonicalization、时间窗口过滤、source metadata。
8. **RSSCollector**
   - 测试：fixture feed 解析、旧条目过滤、重复 guid 合并。
9. **WebCollector**
   - 测试：fixture HTML 抽取标题、正文摘录、发布时间；403/登录墙跳过。
10. **RedditCollector**
    - 测试：fixture JSON/HTML 中提取 pain point；保留 subreddit/permalink。
11. **YouTubeCollector**
    - 测试：fixture metadata/transcript；无字幕时返回可解释 skipped reason。
12. **ChromeExportCollector**
    - 测试：仅读取用户指定导出文件；不访问 Cookie/password/session 路径。
13. **TelegramPublicCollector**
    - 测试：公开频道 fixture；私有/登录要求页面跳过。

### Phase 3：Memory、Dedup 与关联

14. **SQLite schema 与 repository**
    - 产出：runs、sources、items、fingerprints、relations、scorecards 表。
    - 测试：migration 幂等、insert/update/query。
15. **URL 与标题硬去重**
    - 测试：tracking 参数、尾斜杠、大小写、YouTube/Reddit id 去重。
16. **文本指纹去重**
    - 测试：相似标题/正文识别；不同事件不误杀。
17. **跨日 relation linking**
    - 测试：同实体/主题与历史 item 建立关系，输出解释。
18. **Dedup report**
    - 测试：每个 duplicate/related 决策都有 reason code。

### Phase 4：摘要、翻译与产品创意

19. **LLM provider interface 与 fake provider**
    - 测试：schema 输出、重试、超时、降级。
20. **原文摘录与中文翻译模块**
    - 测试：保留原文、翻译字段完整；空摘录失败。
21. **分板块分类器**
    - 测试：五大板块分类；低置信度进入 review bucket。
22. **YouTube Builder 采访摘要器**
    - 测试：长 transcript 分块、要点合并、引用时间戳。
23. **Product idea generator**
    - 测试：必须包含 pain point evidence、目标用户、MVP、验证路径；无证据则不生成 idea。

### Phase 5：Revision Gate

24. **评分维度与权重实现**
    - 测试：overall score 计算、hard floor、权重和为 100%。
25. **Revision loop controller**
    - 测试：至少 5 轮；达标提前在第 5 轮后停止；不达标最多 10 轮。
26. **Critique + revise prompt templates**
    - 测试：fake provider 返回 revision note；schema 不合格会重试或失败。
27. **事实与来源 back-check**
    - 测试：无来源 claim 被标记；缺链接 item 阻断发布。
28. **Scorecard 持久化与报告展示数据**
    - 测试：每轮 scorecard 可回放；HTML 输入包含 revision history。

### Phase 6：HTML Renderer

29. **基础 Jinja2 renderer**
    - 测试：给定 Report fixture 生成 HTML，包含五大 section anchor。
30. **报告组件化**
    - 测试：item card、excerpt/translation、idea card、scorecard 组件 snapshot。
31. **响应式 CSS**
    - 测试：CSS 包含移动端断点；关键 class/变量存在。
32. **HTML validation**
    - 测试：标题、日期、链接、目录、source coverage、revision history 必须存在。
33. **视觉回归 smoke test（可选）**
    - 测试：Playwright 渲染桌面/移动截图不报错。

### Phase 7：Codex App Push Adapter 与调度闭环

34. **PushTask / PushResult 模型**
    - 测试：序列化、本地路径校验、缺报告路径失败。
35. **Codex App adapter skeleton**
    - 测试：dry-run 生成 payload；无官方通道时走降级策略。
36. **Local notification adapter**
    - 测试：命令构造安全，不拼接未转义 shell 字符串。
37. **Task spec file adapter**
    - 测试：生成 `codex_task.md`，包含报告路径、summary、建议 follow-up。
38. **端到端 smoke run**
    - 测试：fake sources -> dedup -> revision gate -> render -> push dry-run，全链路通过。

### Phase 8：运维、文档与验收

39. **示例源配置与合规文档**
    - 测试：example config 能被 loader 读取。
40. **运行手册**
    - 内容：首次安装、手动运行、launchd 安装、失败重试、禁用某源。
41. **报告样例生成**
    - 测试：固定 fixture 生成 deterministic sample report。
42. **验收清单**
    - 7 点调度可触发。
    - 过去 24h 时间窗口生效。
    - 五大板块齐全或有明确缺失说明。
    - 每条内容有链接、原文摘录、中文翻译。
    - 跨日去重与关联可解释。
    - Revision gate 至少 5 轮并保存 scorecard。
    - HTML 桌面优先、移动端可读。
    - Push adapter 成功或提供可重试降级产物。

---

## 11. 子代理并行建议

后续可拆给多个子代理并行执行：

- **Collector 子代理**：实现 RSS/Web/Reddit/YouTube/Telegram/Chrome export，交付 fixture 与单元测试。
- **Memory 子代理**：实现 SQLite schema、fingerprint、dedup、relation linking。
- **Renderer 子代理**：实现 Jinja2 模板、CSS、HTML validation、快照测试。
- **Gate 子代理**：实现 Pre-flight、Revision loop、scorecard schema、prompt templates。
- **Push/Ops 子代理**：实现 Codex App adapter、local notification、launchd plist、运行手册。
- **E2E 子代理**：搭建 fake provider/fake sources，全链路 smoke test 与样例报告。

为避免冲突，每个子代理应只修改自己负责的目录，并以测试先行：先提交 failing test，再实现功能，再补充文档或 fixture。

---

## 12. 关键建议

1. **先做可复现闭环，再扩大源**：第一版用 fixture + 少量 RSS/公开网页跑通 collect -> dedup -> gate -> render -> push dry-run。
2. **把 Codex App 适配隔离为薄层**：不要让核心 pipeline 依赖某个尚不稳定的 App API；始终保留本地通知和 task spec 降级。
3. **记忆系统先解释性，后语义化**：先实现 URL/标题/文本指纹与 reason code，再引入 embedding/向量库。
4. **评分 gate 必须结构化持久化**：每轮分数、批评、修订建议和是否通过都要保存，便于回放与质量调参。
5. **报告要保留证据链**：原文摘录 + 中文翻译 + 链接是核心质量底线，不能只输出二手摘要。
6. **合规默认保守**：遇到访问限制即跳过，不做反检测，不读取凭证，不自动登录。
7. **TDD 优先使用 fake provider 与 fixture**：避免早期测试依赖真实网络、真实 LLM 或 Codex App 状态。
