from daily_brief.config import SectionConfig
from daily_brief.evaluator import run_evaluation_loops
from daily_brief.models import CollectedItem, DedupDecision
from daily_brief.renderer import render_report_html
from daily_brief.sample_data import build_report_from_items, build_sample_report


def test_report_opens_with_content_not_hero_or_judgement():
    report = build_sample_report("2026-05-19")
    report.revision_history = run_evaluation_loops(report, loops=5)

    html = render_report_html(report)

    assert 'class="hero"' not in html
    assert "今日判断" not in html
    assert "JUDGEMENT" not in html
    assert "Builder takeaway" not in html
    assert html.index("<main>") < html.index('id="tech_news"')
    assert html.index('id="tech_news"') < html.index('id="tool_engineering"')
    assert html.index('id="tech_news"') < html.index('id="memory"')


def test_renderer_uses_chinese_title_original_title_and_one_sentence_toc():
    item = CollectedItem(
        id="rss-1",
        source_id="real_feed",
        source_type="rss",
        title="Builder teams are adding audit logs to agent workflows",
        url="https://example.com/agent-audit-logs",
        canonical_url="https://example.com/agent-audit-logs",
        author="Example Feed",
        published_at="2026-05-19T00:00:00+00:00",
        fetched_at="2026-05-19T00:01:00+00:00",
        raw_excerpt="Teams are adding audit logs, evals, and human approval steps before automating customer-facing AI workflows.",
        content_text="Builder teams are adding audit logs to agent workflows\n\nTeams are adding audit logs, evals, and human approval steps before automating customer-facing AI workflows.",
        language="en",
        metadata={
            "section": "tech_news",
            "tags": ["AI infra"],
            "title_zh": "团队在 Agent 工作流里补上审计日志",
            "one_sentence": "Agent 从 demo 走向业务前，团队正在先补审计、评估和人工确认。",
            "summary_zh": "这篇文章讨论团队如何在客户可见的 AI workflow 自动化之前，增加审计日志、回归评估和人工审批，让系统更可追溯。",
            "zh_translation": "团队正在加入审计日志、评估和人工审批步骤，然后才自动化面向客户的 AI 工作流。",
        },
    )
    report = build_report_from_items(
        "2026-05-19",
        [item],
        {item.id: DedupDecision(item_id=item.id, status="new", reason_code="no_match")},
        [SectionConfig("tech_news", "科技新闻")],
    )

    html = render_report_html(report)

    assert "团队在 Agent 工作流里补上审计日志" in html
    assert "英文原标题：Builder teams are adding audit logs to agent workflows" in html
    assert "这篇文章讨论团队如何" in html
    assert 'id="toc"' in html
    assert 'href="#B-001"' in html
    assert "Agent 从 demo 走向业务前" in html
