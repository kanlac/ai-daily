from daily_brief.config import SectionConfig
from daily_brief.models import CollectedItem, DedupDecision
from daily_brief.sample_data import build_report_from_items
from daily_brief.renderer import render_report_html


def test_fallback_translation_is_final_chinese_explanation_not_llm_draft():
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
        metadata={"section": "tech_news", "tags": ["AI infra"]},
    )
    report = build_report_from_items(
        "2026-05-19",
        [item],
        {item.id: DedupDecision(item_id=item.id, status="new", reason_code="no_match")},
        [SectionConfig("tech_news", "科技新闻")],
    )

    html = render_report_html(report)

    assert "中文解释" in html
    assert "需 LLM 精修" not in html
    assert "中文翻译草稿" not in html
