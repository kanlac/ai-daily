# AI 日报｜2026-06-05

## 一句话总览

过去 24 小时的 AI 主线是：大模型产品继续向“更长记忆、更强代理、更深企业数据入口”推进；同时，围绕自我改进、合成生物、州/联邦监管、AI 芯片出口的治理议题明显升温；中国侧则出现 DeepSeek 融资、Qwen 代理生态、豆包商业化的密集进展。

## 最重要的 5 条

### 1. OpenAI 发布 ChatGPT 新记忆系统 “Dreaming”

- **发生了什么**：OpenAI 在官方新闻源发布 “Dreaming: Better memory for a more helpful ChatGPT”，称 ChatGPT 引入新的记忆系统，用于更好地记住用户偏好，并让跨对话上下文保持更新和相关。
- **为什么重要**：长期记忆是通用 AI 助手从“单次问答工具”走向“个人工作环境/代理入口”的关键能力。记忆越稳定，模型越能承担连续任务、个性化建议、长期项目管理。
- **影响判断**：短期看，用户体验会更像“持续协作伙伴”；中期看，记忆、隐私控制、企业合规会成为 AI 助手差异化竞争的核心。产品团队要同时关注可用性和可解释的记忆管理。
- **来源**：[OpenAI 官方](https://openai.com/index/chatgpt-memory-dreaming)

### 2. Anthropic 联合创始人警告 AI 需要“刹车踏板”

- **发生了什么**：据 BBC 报道，Anthropic 联合创始人 Jack Clark 表示 AI 行业目前像“只有油门、没有刹车”，需要通过政府政策和监管保持人类对 AI 系统的控制。他还称 Claude 的代码已有约 80% 由 Claude 自己编写，未来两年内达到 100% 并非不可能。
- **为什么重要**：这把“AI 自我改进/AI 开发 AI”的问题从抽象安全讨论拉到现实工程流程中。当前 AI 编程代理正在进入 CI/CD、代码审查、自动修复等高权限环节，风险不再只是模型回答错误。
- **影响判断**：安全和治理叙事会继续影响前沿模型发布节奏、企业采购审查和资本市场估值。对开发者而言，AI 生成代码比例上升后，权限隔离、审计、回滚和人类批准链会变得更重要。
- **来源**：[BBC](https://www.bbc.com/news/articles/cx2124z7g45o)

### 3. 据报道 DeepSeek 接近完成约 74 亿美元首轮融资

- **发生了什么**：据 Semafor 报道，DeepSeek 正接近完成约 74 亿美元融资，估值约 520 亿美元；腾讯、宁德时代以及国家支持的 AI 投资基金被报道在潜在投资方之列。报道还提到，DeepSeek 将旗舰模型 75% 折扣常态化，并看到更多美国企业直接向其付款。
- **为什么重要**：如果落地，这会是中国 AI 初创公司的一次标志性大规模融资，也说明“低成本模型 + 开源/开放生态 + 价格攻势”仍在冲击硅谷前沿实验室的高资本开支模式。
- **影响判断**：DeepSeek 的资本补给会加剧全球模型价格战，也可能推动更多企业在成本压力下采用多模型/跨地区供应商策略。但地缘、合规和数据安全风险会同步上升。
- **来源**：[Semafor](https://www.semafor.com/article/06/04/2026/deepseek-nears-7-billion-haul-in-first-raise)

### 4. 美国国会出现新的联邦 AI 框架草案，拟三年内预先排除州级 AI 法

- **发生了什么**：据 Roll Call 报道，美国众议员 Jay Obernolte 与 Lori Trahan 发布一份跨党派 AI 讨论草案，重点包括模型安全、劳动力影响，并提出对 AI 开发相关州级法律进行三年预先排除。
- **为什么重要**：美国 AI 监管正在从行政命令、州法碎片化，走向联邦统一框架的博弈。预先排除州法会影响模型发布、平台责任、儿童/隐私/安全规则等多个方向。
- **影响判断**：草案短期未必直接通过，但它会成为产业游说和监管谈判的新基准。AI 公司希望减少州级合规碎片化，安全组织和州政府则担心联邦框架变成监管上限。
- **来源**：[Roll Call](https://rollcall.com/2026/06/04/bipartisan-ai-draft-proposes-three-year-preemption-of-state-laws/)；[Reuters](https://www.reuters.com/business/us-house-lawmakers-release-draft-bill-regulate-ai-2026-06-04/)

### 5. OpenAI 模型在 Snowflake Cortex AI 中正式面向企业可用

- **发生了什么**：Snowflake 官方宣布，OpenAI 前沿模型已在 Snowflake Cortex AI 中正式可用，覆盖 AWS、Google Cloud、Microsoft Azure 上的 Snowflake 客户。Snowflake 称这延续了双方此前 2 亿美元战略合作，目标是在企业数据、治理和合规框架内直接使用前沿模型。
- **为什么重要**：这代表前沿模型竞争不只发生在聊天应用，也在企业数据云、语义层、BI/分析工作流里展开。谁能成为“企业数据上的 AI 执行层”，谁就可能掌握高价值 B2B 入口。
- **影响判断**：企业 AI 落地会更偏向“模型 + 数据治理 + 语义层 + 权限控制”的组合，而不是单独采购模型 API。数据平台、云厂商和模型公司的边界会继续重叠。
- **来源**：[Snowflake 官方](https://www.snowflake.com/en/blog/openai-snowflake-business-native-ai/)

## 其他值得关注

- **OpenAI 发布生物防御行动方案**：OpenAI 官方发布 “Biodefense in the Intelligence Age”，定位为面向 AI 驱动生物韧性的行动计划；同日 CNET 报道称 OpenAI、Anthropic、Google DeepMind 等负责人签署公开信，呼吁加强合成 DNA 规则以降低生物武器风险。来源：[OpenAI](https://openai.com/index/biodefense-in-the-intelligence-age)、[CNET](https://www.cnet.com/tech/services-and-software/ai-industry-national-security-biological-weapons-synthetic-dna/)
- **GitHub Copilot 支持 100 万 token 上下文与可配置推理强度**：GitHub 官方称，Copilot 在 VS Code、Copilot CLI 和 GitHub Copilot App 中支持更大上下文窗口和可调推理级别，但更大上下文或更高推理会消耗更多 AI credits。来源：[GitHub Changelog](https://github.blog/changelog/2026-06-04-larger-context-windows-and-configurable-reasoning-levels-for-github-copilot)
- **Meta 推出 Facebook 创作者 AI 助手**：Meta 官方发布 Creator Assistant，可基于创作者自己的受众、互动趋势和表现数据回答问题、解释内容表现并给出创意建议；先在美国、加拿大、印度推出。来源：[Meta 官方](https://about.fb.com/news/2026/06/creator-assistant-more-languages-for-ai-translations-on-facebook/)
- **xAI 发布 Grok Imagine Video 1.5 预览**：xAI 官方链接显示 Grok Imagine 1.5 已发布；The Decoder 报道称该预览版支持把静态图片生成最高 720p 的短视频，并可通过 xAI API 使用。来源：[xAI](https://x.ai/news/grok-imagine-1-5)、[The Decoder](https://the-decoder.com/xai-updates-grok-imagine-to-1-5-with-image-to-video-generation-at-720p-resolution/)
- **Qwen 向第三方 Agent/Skills 开放平台**：TechNode 报道称，阿里系 Qwen App 向第三方 Agent 和 Skills 开放，KFC、瑞幸、蜜雪冰城、中国东航等成为首批测试方，用户可用自然语言完成点餐、出行等任务。来源：[TechNode](https://technode.com/2026/06/04/qwen-opens-platform-to-third-party-ai-agents-onboards-kfc-luckin-coffee-mixue-and-more/)
- **豆包推出付费 Pro 档，商业化压力显现**：Pandaily 报道称，字节 Doubao 推出 68-500 元人民币/月的 Pro 版本；报道引用第三方数据称其 5 月月活减少 607 万至约 3.3 亿。来源：[Pandaily](https://pandaily.com/bytedance-s-doubao-introduces-paid-pro-tier-as-user-base-dip-jun2026)
- **Claude Code GitHub Action 漏洞披露**：The Hacker News 报道称，Claude Code GitHub Action 曾存在漏洞，恶意 GitHub issue 可触发工作流并获得仓库写权限；Anthropic 已修复，修复版本为 `claude-code-action v1.0.94`，CVSS v4.0 评分 7.8。来源：[The Hacker News](https://thehackernews.com/2026/06/claude-code-github-action-flaw-let-one.html)
- **英伟达 CEO 被邀请就中国 AI 芯片销售出席参议院听证**：CNBC 报道称，美国参议员 Elizabeth Warren 邀请 Jensen Huang 于 6 月 11 日出席参议院银行委员会听证，议题涉及中国销售、出口管制与数据中心政策。来源：[CNBC](https://www.cnbc.com/2026/06/04/nvidia-ceo-jensen-huang-warren-senate-hearing-china-ai-chips.html)
- **据报道 Meta 新 AI 模型 API 再次延迟**：Reuters 转述 WSJ 称，Meta 面向开发者的新 AI 模型发布被多次推迟；这会影响其开放模型生态与开发者信心。来源：[Reuters](https://www.reuters.com/technology/meta-repeatedly-pushes-back-new-ai-model-release-developers-wsj-says-2026-06-04/)
- **Google/Kaggle 推进基准创建工具化**：Google 发布文章称 Kaggle 正让 AI benchmark 创建更轻量，目标是降低构建和本地测试评测集的门槛。来源：[Google Blog](https://blog.google/innovation-and-ai/technology/developers-tools/build-kaggle--benchmarks-locally/)
- **AI 数据中心供给压力继续外溢**：The Verge 报道称，TSMC 面对美国客户 AI 需求仍承压；这再次提示先进制程、封装与晶圆产能仍是 AI 扩张瓶颈。来源：[The Verge](https://www.theverge.com/tech/943066/tsmc-ai-demand-struggles)

## 趋势判断

- **AI 助手正从“聊天窗口”走向“长期记忆 + 业务上下文 + 执行动作”**：OpenAI 记忆、Snowflake 企业数据、Qwen 第三方 Agent、Meta Creator Assistant 指向同一方向——AI 产品的核心价值越来越来自持续上下文和可执行工作流。
- **监管从“模型安全”扩展到“基础设施、合成生物、州法预先排除”**：今天的监管新闻横跨生物安全、美国联邦/州权力、AI 芯片出口，说明 AI 已被纳入国家安全、产业政策和公共安全的综合框架。
- **AI 编程工具进入高权限阶段，安全边界必须重做**：GitHub Copilot 变强、Claude Code Action 漏洞披露同时出现，说明编码代理越能做事，越需要最小权限、沙箱、审批和可观测性。
- **模型价格战和融资战会并行**：DeepSeek 融资与折扣、豆包付费、Copilot credit 消耗提示一个现实：用户期待 AI 更便宜，但模型/算力公司仍需要找到可持续商业化路径。
- **视频生成继续成为多模态竞争焦点**：xAI Grok Imagine Video 1.5 加入 API 预览，意味着短视频/广告/创意资产生成会成为各家多模态模型的重要展示场。

## 我建议重点跟进

- **产品/开发者**：优先研究“记忆 + 权限 + 可回滚”的产品设计。长期记忆和代理能力会带来粘性，也会带来隐私、误操作和合规风险。
- **创业者**：关注企业数据云与业务系统里的 AI 入口。Snowflake/OpenAI 这类合作说明，围绕语义层、权限、审计、行业工作流的垂直 AI 仍有空间。
- **AI 工具使用者**：对编码代理和 Copilot 类工具建立成本与权限预算：大上下文、高推理强度、自动 CI/CD 都要单独设限、记录和审计。
