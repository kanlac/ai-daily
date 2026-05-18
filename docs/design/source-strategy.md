# 数据源与采集策略

本文档定义每日新闻推送项目的数据源、采集方式与下游加工策略，覆盖新闻/深度文章、Builder 实践、AI 工具更新、社媒/博客/Telegram、YouTube Builder 访谈，以及 Reddit/非 AI 社区中的产品创意挖掘。

## 1. 目标与边界

### 目标
- 每日抓取最近 24 小时内的高信号内容，保留原始链接、关键原文摘录，并生成可信的中文摘要/翻译。
- 将“事实更新”和“创意线索”分开处理：新闻侧强调准确、可追溯；创意侧强调痛点证据、场景、可行方案和个人 builder 可执行性。
- 建立跨日记忆，避免重复推送，同时能把同一主题的连续更新串起来。

### 边界与合规原则
- 优先使用 RSS、官方 API、公开网页和用户手工配置的数据源。
- Chrome 人类登录态仅用于用户自己有权限访问、且网站条款允许个人自动化辅助阅读的场景；不绕过付费墙、验证码、反爬限制或私域权限。
- Telegram 不假设可以直接抓取私域/私密频道；仅处理公开 channel、用户授权 API、用户导出或用户主动转发的数据。
- 对视频、音频和字幕的处理需遵守平台条款与版权约束；无字幕时只在合法可用的前提下做转写 fallback。

## 2. 采集方式分层

| 层级 | 方式 | 适用场景 | 优点 | 风险/限制 |
| --- | --- | --- | --- | --- |
| L0 手工配置 | `sources.yaml` / 管理后台维护来源、频道、关键词、权重、白/黑名单 | 高质量固定来源、人工精选 feed、Telegram/YouTube channel 列表 | 可控、低噪声、便于解释 | 需要维护；冷启动覆盖有限 |
| L1 RSS/Atom | 官方博客、媒体、YouTube channel RSS、部分社区/Newsletter | 新闻、博客、视频发布检测 | 稳定、轻量、易做 24h 过滤 | 可能缺正文；发布时间质量不一 |
| L2 官方 API | Reddit API、YouTube Data API、GitHub API、OpenAI/Anthropic status/changelog API（若提供）、论坛 API | 评论/评分/互动数据、精确时间戳、分页回溯 | 结构化、可限速、可增量 | 配额、鉴权、字段不完整 |
| L3 公开浏览器抓取 | 非登录公开网页、博客正文、文档 changelog 页面 | RSS 只有摘要，需要补正文/摘录 | 可补齐正文和元数据 | 易受页面结构变化影响；需尊重 robots/条款 |
| L4 Chrome 人类登录态 | 用户授权登录后的个人阅读列表、Newsletter Web 版、自己加入的公开/半公开社区 | API/RSS 不覆盖但用户有合法访问权限 | 覆盖面广 | 需本机授权、不可集中化；避免批量抓取和绕过限制 |
| L5 手工导入/标注 | Telegram 导出、手动粘贴链接、人工精选爆款帖、用户反馈 | 私域内容、低频高价值材料 | 合规、信号强 | 自动化程度低 |

## 3. 板块级数据源与采集策略

### 3.1 深度科技文章 / 研究型内容

**推荐来源类型**
- 官方研究博客：OpenAI、Anthropic、Google DeepMind、Meta AI、Microsoft Research、Apple ML Research 等。
- 工程/基础设施博客：Cloudflare、Vercel、Stripe、Uber、Netflix、Datadog、Supabase、PlanetScale 等。
- 高质量技术媒体与独立博客：The Pragmatic Engineer、Simon Willison、Latent Space、Lenny's Newsletter、Hacker News 高分外链等。
- 论文/报告源：arXiv RSS、Papers with Code、公司技术报告页。

**采集方式**
- 首选 RSS/Atom；对没有 RSS 的 changelog/文章列表用公开浏览器抓取。
- 对需要完整正文的文章，先保存 canonical URL、标题、作者、发布时间、站点名，再抓取正文 HTML 并抽取正文段落。
- Hacker News 可通过官方 Firebase API 或 Algolia API 获取近 24 小时高分外链，并只把 HN 作为发现入口，最终内容仍以原文为准。
- 对 Newsletter：优先 RSS/公开 Web 归档；用户已订阅但无公开归档时，可用 L4 Chrome 人类登录态或手工转发/导入。

**筛选重点**
- 新模型/新工具能力、工程实践、架构复盘、成本优化、安全事故、数据/评测方法。
- 排除纯营销、重复转载、无实质信息的列表文章。

### 3.2 Builder 实践 / 独立开发经验

**推荐来源类型**
- 独立开发者博客、build-in-public 帖子、产品复盘、收入/增长报告。
- Indie Hackers、Hacker News `Show HN`、Product Hunt、X/Twitter 长帖、Substack/Medium 个人博客。
- GitHub trending/release notes、开源项目 issue/discussion 中的真实使用反馈。

**采集方式**
- RSS/API：博客、Substack、GitHub releases/issues、Product Hunt（如可用 API）。
- 浏览器：无 RSS 的个人站、公开帖子详情页。
- Chrome 人类登录态：仅用于用户个人账号已可见的 X/Twitter、Indie Hackers 等页面，保存链接和公开可引用片段，不批量抓取私信/私有群组。
- 手工配置：维护 builder 名单、产品名、关键词（MRR、launch、pricing、churn、retention、distribution、SEO、cold email、demo video 等）。

**筛选重点**
- 有具体数字或过程证据：收入、成本、转化率、流量、时间线、失败原因。
- 可复用方法：选题、获客、定价、冷启动、自动化、客服、增长实验。
- 对每日 brief 输出“实践启发”，而不是只复述成功故事。

### 3.3 Claude Code / Codex / OpenAI / Anthropic / Hermes 更新

**推荐来源类型**
- 官方 changelog、release notes、docs 更新页、status page。
- 官方博客、开发者论坛、GitHub 仓库 release/commit、SDK package release（npm/PyPI/GitHub）。
- 官方社媒账号、员工技术博客/演讲、可信社区讨论。
- Hermes 相关：官方文档、release notes、仓库 changelog、社区公告（以实际项目配置为准）。

**采集方式**
- RSS/API 优先：官方博客 RSS、GitHub Releases API、npm/PyPI 版本元数据、status page feed。
- 公开浏览器抓取：docs/changelog 没有 RSS 时，采集页面 diff，只保存新增段落和 anchor 链接。
- 手工配置：维护产品/关键词映射，例如 `claude-code`、`codex`、`agents sdk`、`computer use`、`tool use`、`pricing`、`rate limit`、`model deprecation`。
- Chrome 人类登录态：仅用于用户有权限访问的控制台公告或论坛内容；默认不作为稳定自动源。

**筛选重点**
- 影响开发者日常使用的变化：模型、价格、上下文长度、速率限制、CLI/API 行为、权限、安全、废弃计划。
- 对同一产品的多个来源做交叉确认；官方公告权重高于社媒爆料。

### 3.4 社媒 / 博客 / Telegram

**推荐来源类型**
- X/Twitter、Bluesky、Mastodon、Threads 等公开社媒账号。
- 个人博客、Substack、Medium、Mirror、Dev.to。
- Telegram 公开频道、用户提供的导出文件或授权 API 数据。
- Discord/Slack/微信群等私域内容仅接受用户手工导入或明确授权导出，不默认自动抓取。

**采集方式**
- RSS：个人博客、Substack、Mastodon、部分公开社媒桥接 feed。
- API：Mastodon/Bluesky 官方 API；X/Twitter 若使用则需用户自有 API/账号与合规配额。
- 浏览器：公开帖子详情页、公开博客正文。
- Chrome 人类登录态：适合用户个人已登录且允许自动辅助阅读的社媒页面；只抓取公开/可引用内容，不抓取私信、闭群、付费墙。
- 手工配置：维护账号列表、频道列表、关键词列表、语言/地区过滤、来源权重。

#### Telegram 的现实可行实现

Telegram 采集按可行性与合规性排序：
1. **公开 channel 的 RSS/镜像 feed**：若 channel 有公开 RSS、公开归档或用户自建 RSSHub/桥接服务，可按普通 RSS 处理；需要保留原始 `t.me/<channel>/<message_id>` 链接。
2. **公开 Web 页面**：对 `t.me/s/<channel>` 这类公开预览页可做低频、限速抓取；页面可用性不稳定，且无法覆盖私密频道。
3. **用户提供 Telegram API 授权**：用户使用自己的 Telegram 账号/API ID/API Hash 授权后，可读取自己有权限访问的 channel；必须本地保存 session、支持撤权、遵守 Telegram 限速，不上传账号凭据。
4. **用户导出/转发**：用户从 Telegram Desktop 导出 HTML/JSON，或把消息转发到项目提供的 bot/收集入口；这是处理私域/半私域内容的推荐方式。

明确不做：假设能直接抓取私密 channel、绕过登录或邀请限制、采集私人聊天、批量复制付费内容。

**筛选重点**
- 社媒内容需要证据链：原帖链接、作者身份、发布时间、引用/截图仅作辅助。
- 优先保留观点原文句子；中文输出需标注“原文摘录/中文转述”。
- 对爆料类内容标注置信度，不与官方事实混淆。

### 3.5 YouTube Builder 采访 / 视频内容

**推荐来源类型**
- Builder/创业访谈频道：独立开发者访谈、AI 工具开发者访谈、产品增长复盘、技术播客视频版。
- 官方发布会/开发者大会/产品 demo 视频。
- 个人 builder 的 launch/demo/build log 视频。

**采集方式**
- YouTube channel RSS：`https://www.youtube.com/feeds/videos.xml?channel_id=<CHANNEL_ID>` 用于发现新视频。
- YouTube Data API：补充标题、描述、发布时间、频道、时长、播放量、评论数、缩略图、playlist 归属。
- 字幕优先：优先读取官方字幕/自动字幕（若平台与权限允许），按时间戳切分并生成摘要。
- 手工配置：维护频道 ID、playlist、关键词和排除项；为高价值长访谈设置人工优先级。

**摘要策略**
1. 元数据过滤：只处理最近 24 小时发布或被手工标记的重要视频；短视频/纯宣传片默认降权。
2. 字幕摘要：按 3–8 分钟片段切块，抽取“问题—回答—具体案例—数字/工具/流程”，保留时间戳链接。
3. 无字幕 fallback：
   - 先用标题、描述、章节、置顶评论、公开视频页面文本生成低置信摘要，并标注“未基于完整字幕”。
   - 若版权/平台条款和用户授权允许，再下载音频做语音转写；转写失败则进入人工队列，不输出强结论。
4. 输出应包含：视频链接、频道、发布时间、关键时间戳、原文/字幕摘录、中文总结、对 builder 的启发。

### 3.6 Reddit / 非 AI 社区痛点挖掘

**推荐来源类型**
- Reddit 非 AI 社区：smallbusiness、freelance、consulting、accounting、teachers、nursing、realestate、law、ecommerce、etsy、shopify、webdev、sysadmin、dataengineering、parenting、homeowners 等。
- 行业论坛/社区：Stack Exchange、专业论坛、App Store/Chrome Web Store/Shopify App Store 评论、G2/Capterra/Trustpilot、GitHub issues、Discourse 论坛。
- 交易与服务平台：Fiverr/Upwork 项目需求、公开 job board、模板/插件市场评论。

**采集方式**
- Reddit API：按 subreddit、关键词、时间窗口抓取 posts/comments，保留 score、comment count、created_utc、permalink、作者匿名 ID hash。
- 浏览器/API：公开评论站、应用市场、论坛帖子；优先结构化 API 或公开页面。
- 手工配置：维护行业、角色、关键词词典，例如 `manual`, `spreadsheet`, `invoice`, `follow up`, `compliance`, `scheduling`, `reporting`, `client onboarding`, `I hate`, `how do you manage`, `any tool for`。
- Chrome 人类登录态：仅用于用户自己可访问且允许的社区阅读，不抓私信/闭群/付费区。

**筛选重点**
- 目标不是“AI 新闻”，而是非 AI 用户在真实工作/生活中的重复痛点。
- 优先选择有上下文、多人共鸣、已有笨办法/替代方案、存在付费意愿的帖子。
- 避免只因“抱怨强烈”就判定为机会；需要验证频率、预算、可达渠道和实施复杂度。

## 4. 最近 24 小时过滤策略

### 时间字段优先级
1. `published_at` / `created_at`：源站发布或帖子创建时间。
2. `updated_at`：文档/changelog 更新时使用；需保存变更 diff，避免旧页面因更新时间变化重复入选。
3. `fetched_at`：仅用于缺少发布时间的页面；这类内容标记低时间置信度。

### 过滤规则
- 默认窗口：`now - 24h <= event_time <= now`，其中 `event_time = published_at || created_at || meaningful_updated_at || fetched_at`。
- 每个 item 保存 `source_timezone`、原始时间字符串和标准化 UTC 时间；展示时可转换为用户本地时间。
- 对跨时区/日期不准的 RSS，允许 `24h + grace_period(2–6h)` 的候选池，但输出前按置信度和去重结果裁剪。
- 对文档页、软件包版本、GitHub release：以“实际版本发布时间/页面新增段落时间”为准，而非每次抓取时间。
- 对热门旧内容被重新讨论：不作为“新新闻”，但可以作为“跨日关联/背景链接”出现在相关条目下。

## 5. 链接保留、原文摘录与中文翻译策略

### 链接保留
- 每条内容必须保存：`canonical_url`、`original_url`、`source_url`、`archive_url(optional)`、`referrer/discovery_url(optional)`。
- 社媒/Reddit/YouTube 必须保留可点击 permalink；视频摘要保留时间戳链接。
- URL 规范化：去除常见追踪参数（`utm_*`, `fbclid`, `gclid`），保留影响内容的参数（如 YouTube `v`、`t`、playlist 必要参数）。
- 对多源转载，以原始发布源为 canonical，转载/讨论作为 discovery 或 evidence。

### 原文摘录
- 每条最终入选内容保留 1–3 段短摘录，优先选择：事实声明、数字、限制条件、用户原话、关键步骤。
- 摘录字段保存原语言，不做改写；每段记录来源位置：段落序号、字幕时间戳、评论 ID 或页面 anchor。
- 对付费/版权内容只保存合理短摘录和摘要，不复制大段全文。

### 中文翻译/摘要
- 采用“两段式”：先做忠实中文翻译/转述，再做面向读者的解释与影响分析。
- 专有名词保持英文原名，首次出现可加中文解释；版本号、价格、限制、时间不得意译。
- 不确定信息显式标注：`官方确认`、`社区反馈`、`传闻/未证实`、`基于无字幕元数据`。
- 引用性内容避免把作者观点写成事实；输出格式建议为“原文摘录 → 中文要点 → 为什么重要 → 适合谁关注”。

## 6. 去重、指纹、近似相似度与跨日 memory store

### 去重 key 设计

按来源类型生成多层 key，命中任一强 key 即认为同一 item：

| 类型 | 强去重 key | 辅助 key |
| --- | --- | --- |
| 普通文章 | `hash(canonical_url)` | `hash(normalized_title + source_domain)` |
| RSS item | `source_id + guid` | `canonical_url` |
| 社媒帖 | `platform + post_id` | `author_id + created_at + normalized_text_hash` |
| Reddit | `reddit + thing_id` | `subreddit + title_hash + created_utc` |
| Telegram | `telegram + channel_id + message_id` | `channel_username + message_link` |
| YouTube | `youtube + video_id` | `channel_id + title_hash + published_at` |
| GitHub release/issue | `github + repo + object_type + object_id/tag` | `repo + title_hash + created_at` |
| 文档 diff | `source_id + page_url + content_block_hash` | `page_url + heading_path + text_hash` |

### 内容指纹
- `text_hash`: 对清洗后的正文/帖子文本做 SHA-256，用于完全重复检测。
- `simhash`: 对标题 + 摘要 + 正文前若干段生成 64-bit/128-bit SimHash，用于近重复文章和转载检测。
- `minhash`: 对句子/段落 shingles 生成 MinHash，用于长文转载、摘要改写检测。
- `embedding_vector`: 对标题 + 摘要 + 关键摘录生成向量，用于主题聚类和跨日关联。
- `entity_fingerprint`: 提取产品、公司、模型、版本、人物、项目名，用于事件线索串联。

### 近似相似度规则
- 标题相似度高且 canonical domain 不同：进入“转载/同源报道”候选。
- `simhash` 汉明距离小于阈值：近重复，默认只保留最高权重来源。
- `minhash_jaccard >= 0.8`：视为大段转载或轻微改写。
- `embedding_cosine >= 0.88` 且实体重合度高：视为同一事件的不同报道，合并为一个 cluster。
- `embedding_cosine 0.75–0.88`：视为相关背景，作为“延伸阅读/跨日关联”，不强合并。

阈值应按语料回放调参；对短帖和标题党内容降低自动合并权重，避免误杀。

### Memory store 设计

建议使用 SQLite/Postgres 起步，后续可拆分向量库。核心表/集合：

```text
sources
- source_id, type, name, url, collection_method, language, weight, enabled, config, last_checked_at

raw_items
- item_id, source_id, raw_payload, fetched_at, fetch_status, original_url, canonical_url

content_items
- item_id, source_id, type, title, author, published_at, updated_at, event_time,
  canonical_url, language, cleaned_text, excerpts, summary_zh, translation_zh,
  text_hash, simhash, minhash, embedding_id, quality_score, time_confidence

clusters
- cluster_id, topic_title, representative_item_id, entities, first_seen_at, last_seen_at,
  status(active/resolved/background), cluster_embedding_id

cluster_items
- cluster_id, item_id, relation(primary/duplicate/source/background/reaction), similarity_score

memory_events
- event_id, event_key, entities, event_type, first_seen_at, last_seen_at,
  summary, open_questions, latest_cluster_id, importance_score

source_runs
- run_id, source_id, started_at, finished_at, status, item_count, error_count, cursor

brief_history
- brief_id, date, item_id/cluster_id, section, rank, rendered_title, rendered_at

idea_evidence
- evidence_id, item_id, community, user_role, pain_quote, pain_type, frequency_signal,
  workaround, willingness_to_pay_signal, created_at

idea_candidates
- idea_id, title, target_user, scenario, ai_solution, evidence_ids,
  feasibility_score, distribution_score, risk_notes, status
```

### 跨日关联
- `event_key = normalized_entities + event_type + semantic_topic`，例如 `anthropic|claude-code|release|permissions`。
- 新 item 先与最近 7 天 active cluster 匹配，再与 30–90 天 memory_events 匹配；命中后输出“此前进展/今天新增”。
- brief 已推送过的 item 不重复推送；若同一 cluster 有高价值新增事实，则以“更新”形式出现。
- 对长期主题（价格调整、模型能力、开源项目路线图）保留时间线，便于生成背景段落。

## 7. 产品创意挖掘策略

产品创意挖掘使用“痛点证据 → 用户场景 → AI 可行解 → 个人 builder 可执行性”的流水线。

### 7.1 痛点证据

从 Reddit/论坛/评论/工单/应用市场中抽取：
- 用户身份：职业、行业、团队规模、技术水平。
- 触发场景：什么时候遇到问题、频率、输入/输出材料。
- 原话证据：抱怨、求助、替代方案、预算暗示。
- 现有 workaround：Excel、手工复制粘贴、Zapier 拼接、请 VA、外包、内部脚本。
- 强度信号：点赞/评论数、多人附和、重复出现、负面情绪、明确成本/时间损失。

### 7.2 用户场景

将零散帖子归纳为可执行场景卡：
- `As a <role>, when <situation>, I need <job>, so I can <outcome>.`
- 明确输入、输出、频率、约束、失败后果。
- 区分购买者、使用者、受影响者；B2B 场景需识别预算归属。

### 7.3 AI 可行解

评估 AI 是否真正适合：
- 是否涉及非结构化文本/语音/图片/网页/文档理解。
- 是否需要分类、抽取、总结、生成、匹配、监控、工作流编排。
- 是否有可获得的数据输入与可验证输出。
- 幻觉容忍度：低容忍场景需 human-in-the-loop、引用来源、审计日志。
- 与传统自动化比较：AI 必须明显降低配置成本或处理长尾变化。

### 7.4 个人 builder 可执行性

评分维度（1–5 分）：
- 痛点强度：是否高频、刚需、有明确损失。
- 付费意愿：是否已有付费替代品、外包/人力成本、预算主体清晰。
- 数据可得性：是否能通过用户授权接入 Gmail/Drive/Slack/Notion/CSV/网页等。
- 技术复杂度：MVP 是否可由个人在 2–6 周完成。
- 分发可行性：是否能通过 SEO、社区、插件市场、模板市场、冷邮件触达。
- 竞争压力：是否被大平台轻易覆盖；是否有垂直工作流/数据壁垒。
- 合规风险：隐私、医疗、法律、金融、儿童数据等。

### 7.5 输出格式

每个候选创意建议输出：
```text
标题：
目标用户：
痛点证据：原帖/评论链接 + 1–3 条原文摘录
用户场景：
AI 可行解：
MVP 范围：
个人 builder 可执行性评分：
分发入口：
主要风险：
下一步验证问题：
```

## 8. 排序与质量控制

### 内容评分
- 来源可信度：官方/一手来源 > 可信专家 > 社区讨论 > 二手转载。
- 新鲜度：24 小时内优先；高价值深度文章可放宽但需标注。
- 影响面：开发者、AI builder、独立开发者、目标行业用户的受影响程度。
- 信息密度：是否包含具体事实、数字、方法、代码、案例。
- 可行动性：读者看完能否做出决策、尝试工具、调整路线或产生产品想法。

### 人工审核点
- 官方更新、价格/限制、模型能力等高影响内容需二次核对链接。
- 社媒爆料和 Telegram 消息需标注置信度，不得改写成官方结论。
- 翻译后的数字、日期、否定词、限制条件必须回看原文。
- 创意挖掘不能输出可识别个人隐私；Reddit 用户名等可哈希或不展示。

## 9. 推荐落地流程

1. 手工配置第一批高质量 sources：官方博客/changelog、核心 builder 博客、YouTube 频道、Reddit 社区、Telegram 公开频道。
2. 每小时运行增量采集：RSS/API → browser 补正文 → 存 raw_items/content_items。
3. 对候选内容做 24h 过滤、去重、近似聚类、跨日 memory 匹配。
4. 生成候选池：新闻更新、深度文章、Builder 实践、视频访谈、产品创意。
5. LLM 加工：原文摘录校验 → 中文摘要/翻译 → 影响分析 → 创意评分。
6. 人工或规则审核高风险条目，最终生成每日 brief。
7. 写回 brief_history、clusters、memory_events、idea_candidates，供次日去重和关联。

## 10. 重点风险

- **平台权限风险**：X/Twitter、Telegram、YouTube 字幕/音频、付费 Newsletter 都可能受条款、登录态、配额限制；应优先官方 API/RSS/用户授权。
- **时间戳风险**：RSS 更新时间、页面修改时间、抓取时间可能不等于发布时间；需要保存原始时间和置信度。
- **重复与转载风险**：同一事件会在官方博客、社媒、HN、Reddit 多处出现；必须按 cluster 输出，避免刷屏。
- **翻译失真风险**：价格、限制、模型名称、否定条件最容易出错；关键事实保留原文摘录。
- **私域合规风险**：Telegram/Discord/Slack/微信群等不应默认抓取；只接受公开、授权或用户导入。
- **视频摘要风险**：无字幕时摘要置信度低；不得仅凭标题/描述推断具体观点。
- **创意误判风险**：强烈抱怨不等于商业机会；必须验证频率、预算、可达渠道和 MVP 可行性。
