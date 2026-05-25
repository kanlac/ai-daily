"""Deterministic offline data used by tests and the MVP runner."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .config import SectionConfig
from .memory import canonicalize_url
from .models import BriefItem, CollectedItem, DedupDecision, ProductIdea, Report


DEFAULT_SECTIONS: list[SectionConfig] = [
    SectionConfig("tech_news", "科技新闻", "科技深度、AI infra 与 Builder 实践。"),
    SectionConfig("tool_engineering", "工具工程更新", "开发工具、Agent 与工程链路更新。"),
    SectionConfig("social_blogs", "社媒博客", "公开社媒、博客与 Telegram 线索。"),
    SectionConfig("video", "视频", "YouTube Builder 采访与 demo。"),
    SectionConfig("product_ideas", "产品/业务创意", "社区痛点驱动的产品机会。"),
]


def _iso(date: str, hour: int, minute: int = 0) -> str:
    year, month, day = (int(part) for part in date.split("-"))
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc).isoformat()


def build_sample_collected_items(date: str) -> list[CollectedItem]:
    fetched_at = _iso(date, 23, 0)
    raw_items = [
        {
            "id": "sample-tech-agent-tracing",
            "section": "tech_news",
            "source_id": "openai_blog",
            "source_type": "rss",
            "title": "OpenAI Agents SDK adds tracing and eval hooks for production workflows",
            "url": "https://openai.com/blog/agents-sdk-tracing?utm_source=daily",
            "author": "OpenAI Developer Platform",
            "published_at": _iso(date, 6, 20),
            "raw_excerpt": "The Agents SDK now includes tracing hooks, evaluation callbacks, and a production debugging workflow for tool-using agents.",
            "zh_translation": "Agents SDK 现在包含 tracing hooks、评估回调，以及面向工具型 Agent 的生产调试工作流。",
            "summary_zh": "OpenAI 把 Agent 工具链从 demo 推向可观测、可评估的生产工作流。",
            "why_it_matters": "可观测性和评估接口是 Agent 进入真实业务流程前最缺的一层。",
            "builder_takeaway": "如果你在做 Agent 产品，应优先设计 trace、eval 和权限审计，而不是只堆模型调用。",
            "tags": ["AI infra", "Agent", "Observability"],
        },
        {
            "id": "sample-tool-codex-webhook",
            "section": "tool_engineering",
            "source_id": "codex_changelog",
            "source_type": "rss",
            "title": "Codex App webhook automation adapter reaches public preview",
            "url": "https://developers.openai.com/codex/changelog/webhook-automation",
            "author": "Codex App Team",
            "published_at": _iso(date, 7, 0),
            "raw_excerpt": "Webhook automation lets external schedulers submit JSON tasks with report links, suggested actions, and run metadata.",
            "zh_translation": "Webhook 自动化允许外部调度器提交包含报告链接、建议动作和运行元数据的 JSON 任务。",
            "summary_zh": "Codex App 的 webhook 入口让本地日报可以用标准 JSON payload 投递任务。",
            "why_it_matters": "这把定时任务、报告生成与 Codex App 的复盘动作解耦。",
            "builder_takeaway": "先用 webhook + dry-run 文件做薄适配，避免核心 pipeline 绑定不稳定 UI。",
            "tags": ["Codex", "Webhook", "Automation"],
        },
        {
            "id": "sample-social-local-first-agents",
            "section": "social_blogs",
            "source_id": "simon_blog",
            "source_type": "rss",
            "title": "Local-first agent workflows need boring audit logs",
            "url": "https://simonwillison.net/2026/May/18/local-first-agent-audit-logs/",
            "author": "Simon Willison",
            "published_at": _iso(date, 9, 30),
            "raw_excerpt": "The useful pattern is not a smarter agent; it is a boring local-first workflow where every tool call leaves an audit trail.",
            "zh_translation": "真正有用的模式不是更聪明的 Agent，而是一个本地优先、每次工具调用都留下审计轨迹的朴素工作流。",
            "summary_zh": "社媒与博客讨论从“模型更强”转向“本地可控、可审计的 Agent 工作流”。",
            "why_it_matters": "这与昨日关于 Agent runtime 的主题形成延续，说明市场正在重视信任层。",
            "builder_takeaway": "把日志、撤销、重放和人工确认作为默认产品体验，而不是高级功能。",
            "tags": ["Local-first", "Audit", "Blog"],
        },
        {
            "id": "sample-video-builder-evals",
            "section": "video",
            "source_id": "youtube_builder_interviews",
            "source_type": "youtube",
            "title": "Solo founder interview: using evals to ship reliable AI workflows",
            "url": "https://www.youtube.com/watch?v=builder123&utm_campaign=brief",
            "author": "Builder Systems Podcast",
            "published_at": _iso(date, 11, 15),
            "raw_excerpt": "At 18:42 the founder says: we stopped arguing about prompts and started writing regression evals for every customer workflow.",
            "zh_translation": "在 18:42，创始人说：我们不再争论 prompt，而是为每个客户工作流编写回归评估。",
            "summary_zh": "视频强调：小团队要交付可靠 AI workflow，关键是把 eval 当作产品交付的一部分。",
            "why_it_matters": "这提供了从原型走向付费客户的实践路径。",
            "builder_takeaway": "把 demo、客户验收和持续评估连接成一个最小闭环。",
            "tags": ["YouTube", "Founder", "Evals"],
        },
        {
            "id": "sample-reddit-invoice-followup",
            "section": "product_ideas",
            "source_id": "reddit_smallbusiness",
            "source_type": "reddit",
            "title": "Small business owners need invoice follow-up without awkward manual chasing",
            "url": "https://www.reddit.com/r/smallbusiness/comments/1abcxyz/invoice_follow_up_is_taking_over_my_fridays/",
            "author": "anonymous redditor",
            "published_at": _iso(date, 13, 5),
            "raw_excerpt": "I spend every Friday copying invoice statuses into a spreadsheet, then writing awkward follow-up emails to clients who are only a few days late.",
            "zh_translation": "我每周五都要把发票状态复制到表格里，然后给只晚了几天的客户写尴尬的催款邮件。",
            "summary_zh": "非 AI 社区暴露出小企业账款跟进的重复、低价值但高频痛点。",
            "why_it_matters": "这是可授权接入邮箱/会计软件、可引用状态、可人工确认的垂直 Agent 场景。",
            "builder_takeaway": "从 Gmail/QuickBooks/Xero 只读接入和人工确认发信做 MVP，先卖节省时间。",
            "tags": ["Reddit", "Pain point", "SMB"],
        },
        {
            "id": "sample-github-hermes-docs",
            "section": "tool_engineering",
            "source_id": "github_updates",
            "source_type": "github_updates",
            "title": "Hermes Agent docs clarify tool-use enforcement and automation safety",
            "url": "https://github.com/NousResearch/hermes-agent/releases/tag/docs-2026-05-18",
            "author": "Nous Research",
            "published_at": _iso(date, 15, 45),
            "raw_excerpt": "The documentation now separates tool-use enforcement, dry-run behavior, and webhook automation boundaries for local agents.",
            "zh_translation": "文档现在区分了工具使用强制、dry-run 行为，以及本地 Agent 的 webhook 自动化边界。",
            "summary_zh": "Hermes Agent 文档把自动化边界写得更明确，便于本地日报任务安全执行。",
            "why_it_matters": "对本项目而言，边界清晰比功能激进更重要。",
            "builder_takeaway": "把安全边界写进 README、配置和 adapter，而不是只靠口头约定。",
            "tags": ["Hermes", "Docs", "Safety"],
        },
    ]

    items: list[CollectedItem] = []
    for raw in raw_items:
        metadata = {
            "section": raw["section"],
            "zh_translation": raw["zh_translation"],
            "summary_zh": raw["summary_zh"],
            "why_it_matters": raw["why_it_matters"],
            "builder_takeaway": raw["builder_takeaway"],
            "tags": raw["tags"],
        }
        url = raw["url"]
        items.append(
            CollectedItem(
                id=raw["id"],
                source_id=raw["source_id"],
                source_type=raw["source_type"],
                title=raw["title"],
                url=url,
                canonical_url=canonicalize_url(url),
                author=raw["author"],
                published_at=raw["published_at"],
                fetched_at=fetched_at,
                raw_excerpt=raw["raw_excerpt"],
                content_text=f"{raw['title']}\n\n{raw['raw_excerpt']}\n\n{raw['summary_zh']}",
                language="en",
                metadata=metadata,
            )
        )
    return items


def build_sample_previous_item(date: str) -> CollectedItem:
    current = datetime.fromisoformat(f"{date}T00:00:00+00:00")
    previous = (current - timedelta(days=1)).date().isoformat()
    url = "https://openai.com/blog/agents-sdk-production-workflows"
    return CollectedItem(
        id="hist-agent-sdk-production",
        source_id="historical_memory",
        source_type="fixture",
        title="OpenAI ships Agents SDK for production workflows",
        url=url,
        canonical_url=canonicalize_url(url),
        author="Daily Brief Memory",
        published_at=_iso(previous, 8, 0),
        fetched_at=_iso(previous, 8, 5),
        raw_excerpt="OpenAI ships an Agents SDK for production workflows and tool orchestration.",
        content_text="OpenAI ships Agents SDK production workflows tool orchestration tracing evals agents.",
        language="en",
        metadata={"thread_id": "T-2026-05-agent-infra-001", "section": "tech_news"},
    )


def build_sample_report(
    date: str,
    items: list[CollectedItem] | None = None,
    decisions: dict[str, DedupDecision] | None = None,
    sections: list[SectionConfig] | None = None,
) -> Report:
    items = items or build_sample_collected_items(date)
    sections = sections or DEFAULT_SECTIONS
    decisions = decisions or _default_decisions(items)
    return build_report_from_items(date=date, items=items, decisions=decisions, sections=sections)


def build_report_from_items(
    date: str,
    items: list[CollectedItem],
    decisions: dict[str, DedupDecision],
    sections: list[SectionConfig],
    source_coverage: dict[str, object] | None = None,
) -> Report:
    section_titles = {section.id: section.title for section in sections}
    grouped: dict[str, list[BriefItem]] = {section.id: [] for section in sections}

    for index, item in enumerate(items, start=1):
        section_id = str(item.metadata.get("section", "tech_news"))
        decision = decisions.get(item.id) or DedupDecision(item_id=item.id, status="new", reason_code="no_match")
        if decision.status == "duplicate":
            continue
        source_id = f"S-{index:03d}"
        grouped.setdefault(section_id, []).append(
            BriefItem(
                id=f"B-{index:03d}",
                collected_item_id=item.id,
                section=section_id,
                title=_brief_title(item),
                original_excerpt=_original_excerpt(item),
                zh_translation=str(item.metadata.get("zh_translation", _fallback_translation(item))),
                summary_zh=str(item.metadata.get("summary_zh", _fallback_summary(item, section_id))),
                why_it_matters=str(item.metadata.get("why_it_matters", _fallback_why_it_matters(item, section_id))),
                builder_takeaway=str(item.metadata.get("builder_takeaway", _fallback_builder_takeaway(item, section_id))),
                source_links=[item.canonical_url],
                original_title=str(item.metadata.get("original_title", item.title)),
                one_sentence=str(item.metadata.get("one_sentence", _fallback_one_sentence(item, section_id))),
                dedup_status=decision.status,
                duplicate_of=decision.duplicate_of,
                relation_ids=decision.related_ids,
                relation_reason=decision.reason_code,
                scores={"signal": _signal_score(item, section_id), "freshness": 8.2, "builder_value": _builder_score(section_id)},
                source_id=source_id,
                source_title=f"{source_id} · {item.author}",
                published_at=item.published_at,
                tags=_coerce_tags(item.metadata.get("tags", [])),
                evidence_metadata=_evidence_metadata(item),
            )
        )

    # Make missing sections explicit rather than silently dropping required blocks.
    for section in sections:
        grouped.setdefault(section.id, [])

    product_ideas = _build_product_ideas_from_items(grouped.get("product_ideas", []))
    related_item_ids = sorted({rid for decision in decisions.values() for rid in decision.related_ids})
    total_items = sum(len(value) for value in grouped.values())
    cross_day_memory = [_build_cross_day_memory(date, related_item_ids, total_items, decisions)]
    coverage = dict(source_coverage or {})
    coverage.setdefault("configured_sources", len({item.source_id for item in items}) or 1)
    coverage.setdefault("successful_sources", len({item.source_id for item in items}) or 1)
    coverage.setdefault("failed_sources", 0)
    coverage.setdefault("degraded_sources", [])
    coverage["deduplicated_events"] = total_items
    coverage["related_threads"] = len(cross_day_memory)
    coverage.setdefault("policy", "真实/fixture 采集均只使用公开或用户显式配置来源；不读取 Cookie、密码、session 或私有数据。")

    title = _build_report_title(items)
    return Report(
        date=date,
        window_start=f"{date} 00:00 UTC",
        window_end=f"{date} 23:59 UTC",
        title=title,
        top_highlights=_build_highlights(grouped),
        sections=grouped,
        section_titles=section_titles,
        product_ideas=product_ideas,
        cross_day_memory=cross_day_memory,
        source_coverage=coverage,
        render_metadata={
            "layout": "desktop-first responsive",
            "css": "inline",
            "reading_time_minutes": max(4, min(18, total_items + 3)),
            "source_count": total_items,
        },
    )


def _brief_title(item: CollectedItem) -> str:
    title_zh = str(item.metadata.get("title_zh", "")).strip()
    return title_zh or _fallback_title_zh(item)


def _fallback_title_zh(item: CollectedItem) -> str:
    if item.language.lower().startswith("zh"):
        return item.title
    source_hint = str(item.metadata.get("source_name", item.source_id))
    return f"{source_hint}：{item.title}"


def _fallback_one_sentence(item: CollectedItem, section_id: str) -> str:
    summary = str(item.metadata.get("summary_zh", "")).strip()
    if summary:
        return summary[:90]
    prefix = {
        "tech_news": "科技新闻",
        "tool_engineering": "工具更新",
        "social_blogs": "博客/社媒",
        "video": "视频",
        "product_ideas": "产品线索",
    }.get(section_id, "线索")
    return f"{prefix}：{_fallback_title_zh(item)[:72]}"


def _original_excerpt(item: CollectedItem) -> str:
    status = str(item.metadata.get("transcript_status", "")).strip()
    transcript_excerpt = str(item.metadata.get("transcript_excerpt", "")).strip()
    if item.source_type == "youtube" and status == "fetched" and transcript_excerpt:
        return transcript_excerpt
    if item.source_type == "youtube" and status and "transcript_status=" not in item.raw_excerpt:
        note = str(item.metadata.get("transcript_note", f"transcript_status={status}; low-confidence feed fallback"))
        return f"{note}. Feed fallback: {item.raw_excerpt}"
    return item.raw_excerpt


def _evidence_metadata(item: CollectedItem) -> dict[str, object]:
    evidence_keys = {
        "transcript_status",
        "transcript_video_id",
        "transcript_language",
        "transcript_excerpt",
        "transcript_segments_sample",
        "transcript_provider",
        "transcript_note",
        "transcript_error",
        "transcript_error_type",
        "transcript_is_generated",
    }
    evidence = {key: value for key, value in item.metadata.items() if key in evidence_keys}
    if item.source_type == "youtube" and "transcript_status" not in evidence:
        evidence["transcript_status"] = "not_attempted"
        evidence["transcript_note"] = "transcript_status=not_attempted; this YouTube item has not passed P0.2 enrichment"
    return evidence


def _coerce_tags(raw: object) -> list[str]:
    if isinstance(raw, list):
        return [str(item) for item in raw if str(item).strip()]
    if isinstance(raw, str):
        return [part.strip() for part in raw.split(",") if part.strip()]
    return []


def _fallback_translation(item: CollectedItem) -> str:
    excerpt = item.raw_excerpt.strip() or item.title
    if item.language.lower().startswith("zh"):
        return excerpt
    return f"中文解释：{excerpt[:300]}"


def _fallback_summary(item: CollectedItem, section_id: str) -> str:
    section_prefix = {
        "tech_news": "科技/AI 深度来源显示",
        "tool_engineering": "工具链更新来源显示",
        "social_blogs": "社媒/博客线索显示",
        "video": "视频 feed 显示",
        "product_ideas": "社区痛点线索显示",
    }.get(section_id, "公开来源显示")
    return f"{section_prefix}：{item.title}。"


def _fallback_why_it_matters(item: CollectedItem, section_id: str) -> str:
    if section_id == "product_ideas":
        return "这是来自真实社区/公开帖子的问题表述，可作为产品假设和访谈问题的证据入口。"
    if section_id == "tool_engineering":
        return "工具链变化会直接影响个人 builder 的开发、调试、自动化和发布流程。"
    if section_id == "video":
        status = str(item.metadata.get("transcript_status", ""))
        if status == "fetched":
            return "该视频已自动抓取公开字幕，正文摘录来自 transcript，因此比 RSS 描述更适合做观点/实践提炼。"
        if status:
            return "系统已尝试自动抓取字幕但未成功；本条显式标记为低置信 feed fallback，避免把 RSS 描述伪装成 transcript。"
        return "视频访谈通常包含实践细节；当前先保留 feed 摘要，后续应接字幕提取。"
    if section_id == "social_blogs":
        return "独立 builder/工程师的博客与社媒往往比官方发布更早暴露真实用法和反直觉观点。"
    return "该条目来自可追溯公开来源，可能影响 AI infra、产品路线或 builder 实践。"


def _fallback_builder_takeaway(item: CollectedItem, section_id: str) -> str:
    if section_id == "product_ideas":
        return "把原帖当作 pain point 证据：先访谈同类用户，再设计只读、人工确认、可回滚的窄 MVP。"
    if section_id == "tool_engineering":
        return "检查它是否能进入你的 agent/dev workflow；优先关注可观测性、权限、安全边界和自动化接口。"
    if section_id == "video":
        return "如果主题匹配，下一步抓字幕并提炼 founder 如何做分发、定价、验证和工程落地。"
    if section_id == "social_blogs":
        return "记录作者、背景、独特观点与可复用实践；不要只收藏链接，要转成可试验动作。"
    return "先判断它是否改变今天的构建优先级：新能力、降成本、提可靠性或新分发机会。"


def _signal_score(item: CollectedItem, section_id: str) -> float:
    base = {"tech_news": 8.0, "tool_engineering": 8.3, "social_blogs": 7.8, "video": 7.5, "product_ideas": 8.1}.get(section_id, 7.5)
    if len(item.raw_excerpt) > 240:
        base += 0.2
    if item.source_type in {"github_updates", "reddit", "youtube"}:
        base += 0.1
    return round(min(9.2, base), 2)


def _builder_score(section_id: str) -> float:
    return {"tool_engineering": 8.7, "product_ideas": 8.6, "social_blogs": 8.2, "video": 8.0, "tech_news": 8.1}.get(section_id, 7.8)


def _build_report_title(items: list[CollectedItem]) -> str:
    if not items:
        return "今日真实来源未返回足够新内容"
    tool_count = sum(1 for item in items if item.metadata.get("section") == "tool_engineering")
    product_count = sum(1 for item in items if item.metadata.get("section") == "product_ideas")
    if tool_count >= product_count and tool_count:
        return "工具链与 Agent 实践更新主导今日 Builder Brief"
    if product_count:
        return "社区痛点与真实产品机会主导今日 Builder Brief"
    return f"{items[0].title[:42]}：今日 Builder Brief"


def _build_highlights(grouped: dict[str, list[BriefItem]]) -> list[str]:
    highlights: list[str] = []
    priority = ["tool_engineering", "tech_news", "product_ideas", "social_blogs", "video"]
    for section_id in priority:
        for item in grouped.get(section_id, [])[:2]:
            highlights.append(f"{item.source_id} · {item.title}")
            break
    while len(highlights) < 3:
        highlights.append("真实采集源较少：保留缺口与 degraded source，避免用示例内容伪装新闻。")
    return highlights[:4]


def _build_cross_day_memory(
    date: str,
    related_item_ids: list[str],
    total_items: int,
    decisions: dict[str, DedupDecision],
) -> dict[str, object]:
    duplicate_count = sum(1 for decision in decisions.values() if decision.status == "duplicate")
    related_count = sum(1 for decision in decisions.values() if decision.status == "related")
    return {
        "thread_id": f"T-{date}-real-collection",
        "title": "真实来源采集与跨日去重线程",
        "first_seen": date,
        "latest_update": date,
        "trend_status": "初始化" if not related_item_ids else "延续",
        "related_ids": related_item_ids,
        "today_new_evidence": f"本次从公开源保留 {total_items} 条正文 item；检测到 {duplicate_count} 条重复、{related_count} 条跨日相关。",
        "next_watch": "后续每日运行时，memory.sqlite3 会积累 URL、文本指纹和相似标题，用来合并重复报道并建立主题延续。",
    }


def _build_product_ideas_from_items(items: list[BriefItem]) -> list[ProductIdea]:
    if not items:
        return []
    ideas: list[ProductIdea] = []
    for idx, item in enumerate(items[:3], start=1):
        ideas.append(
            ProductIdea(
                id=f"PI-{idx:03d}",
                title=f"Pain-point Copilot: {item.title[:56]}",
                trigger_source_ids=[item.source_id],
                pain_point_evidence=item.original_excerpt,
                pain_point_translation=item.zh_translation,
                target_user="发帖/讨论中暴露该痛点的具体用户群；需要下一步人工访谈确认细分画像。",
                current_workaround="从原帖摘录推断：用户正在用手工流程、通用工具或临时脚本解决问题。",
                ai_solution="构建一个只读采集上下文、生成建议/草稿、由人确认执行的窄场景 AI workflow。",
                mvp_scope="Landing page + 10 个访谈 + CSV/邮箱/浏览器只读导入 + 草稿生成 + 审计日志。",
                distribution="回到同类 subreddit/社区分享问题复盘、模板或计算器，用内容换访谈。",
                risks="不要替用户自动执行高风险动作；隐私数据只读、最小权限、可删除。",
                validation_plan="先验证痛点频率、现有替代方案、节省时间和愿付价格，再写代码。",
                score={"pain_strength": 3.8, "willingness_to_pay": 3.3, "mvp_feasibility": 4.0, "distribution": 3.4},
            )
        )
    return ideas


def _default_decisions(items: list[CollectedItem]) -> dict[str, DedupDecision]:
    decisions: dict[str, DedupDecision] = {}
    for item in items:
        if item.id == "sample-tech-agent-tracing":
            decisions[item.id] = DedupDecision(
                item_id=item.id,
                status="related",
                reason_code="jaccard_similarity",
                related_ids=["hist-agent-sdk-production"],
                novelty_score=0.62,
                similarity_score=0.46,
                explanation="与昨日 Agent SDK 生产工作流主题共享实体和工作流语义，但今天新增 tracing/eval。",
            )
        else:
            decisions[item.id] = DedupDecision(
                item_id=item.id,
                status="new",
                reason_code="no_match",
                novelty_score=1.0,
                similarity_score=0.0,
                explanation="样例数据中未发现重复。",
            )
    return decisions


def _build_invoice_product_idea() -> ProductIdea:
    return ProductIdea(
        id="PI-001",
        title="Invoice Follow-up Copilot for Small Teams",
        trigger_source_ids=["S-005"],
        pain_point_evidence=(
            "I spend every Friday copying invoice statuses into a spreadsheet, then writing awkward follow-up emails "
            "to clients who are only a few days late."
        ),
        pain_point_translation="我每周五都要把发票状态复制到表格里，然后给只晚了几天的客户写尴尬的催款邮件。",
        target_user="10 人以下的小企业 owner、自由职业者工作室、轻量 B2B 服务商。",
        current_workaround="手工导出会计系统、表格标记状态、复制粘贴邮件模板、人工判断语气。",
        ai_solution="只读连接邮箱/会计软件，识别逾期状态，生成带引用的友好跟进草稿，并要求人工确认后发送。",
        mvp_scope="Gmail + CSV/QuickBooks 导入、逾期检测、三档语气模板、人工审批、发送后状态日志。",
        distribution="通过 smallbusiness/freelance 社区内容、会计模板 SEO、QuickBooks/Xero 顾问渠道冷启动。",
        risks="账务隐私和误发风险；MVP 必须只读默认、人工确认、保留审计日志和撤销路径。",
        validation_plan="用 10 个小企业访谈验证每周耗时、愿付价格和现有工具；先做 no-code concierge 测试。",
        score={"pain_strength": 4.3, "willingness_to_pay": 3.8, "mvp_feasibility": 4.1, "distribution": 3.6},
    )
