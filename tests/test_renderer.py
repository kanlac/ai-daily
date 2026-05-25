from daily_brief.evaluator import run_evaluation_loops
from daily_brief.renderer import render_report_html, validate_report_html
from daily_brief.sample_data import build_sample_report


def test_renderer_contains_required_daily_brief_blocks():
    report = build_sample_report("2026-05-18")
    report.revision_history = run_evaluation_loops(report, loops=5)

    html = render_report_html(report)
    validation = validate_report_html(html, report)

    assert validation.ok, validation.missing
    assert "<header" in html
    assert "<nav" in html
    assert "id=\"tech_news\"" in html
    assert "id=\"tool_engineering\"" in html
    assert "id=\"social_blogs\"" in html
    assert "id=\"video\"" in html
    assert "id=\"product_ideas\"" in html
    assert "原文摘录" in html
    assert "中文翻译" in html
    assert "跨日关联" in html
    assert "评分摘要" in html
    assert "@media (max-width: 768px)" in html
    assert "@media print" in html
    assert "Product Idea Canvas" in html
    assert "需 LLM 精修" not in html
    assert "中文翻译草稿" not in html
