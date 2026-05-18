'''Responsive HTML renderer for Daily Brief.'''
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from statistics import mean

from .models import BriefItem, ProductIdea, Report, ScoreCard


@dataclass(slots=True)
class HtmlValidationResult:
    ok: bool
    missing: list[str]


def render_report_html(report: Report) -> str:
    latest = report.revision_history[-1] if report.revision_history else None
    latest_score = latest.overall_score if latest else 0.0
    nav = ''.join(f'<a href="#{escape(sid)}">{escape(title)}</a>' for sid, title in report.section_titles.items())
    nav += '<a href="#memory">跨日关联</a><a href="#ideas">产品创意</a><a href="#scores">评分摘要</a>'
    highlights = ''.join(f'<li>{escape(h)}</li>' for h in report.top_highlights)
    sections = ''.join(_render_section(sid, title, report.sections.get(sid, [])) for sid, title in report.section_titles.items())
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{escape(report.date)} Daily Builder Brief</title>
<style>
:root {{ --ink:#12100d; --muted:#68635b; --paper:#f5efe5; --panel:#fffaf1; --line:rgba(18,16,13,.14); --accent:#d24a26; --blue:#144f64; --radius:22px; --serif:Charter,Georgia,serif; --sans:Inter,-apple-system,BlinkMacSystemFont,'SF Pro Text','Segoe UI',sans-serif; --mono:ui-monospace,SFMono-Regular,Menlo,monospace; }}
* {{ box-sizing:border-box; }} html {{ scroll-behavior:smooth; }} body {{ margin:0; background:radial-gradient(circle at 15% -10%, rgba(210,74,38,.18), transparent 34%), var(--paper); color:var(--ink); font-family:var(--sans); line-height:1.62; }}
a {{ color:var(--blue); text-underline-offset:.18em; }} .shell {{ max-width:1440px; margin:auto; padding:34px 28px 64px; }}
.hero {{ display:grid; grid-template-columns:minmax(0,1.5fr) 360px; gap:28px; padding:34px; border:1px solid var(--line); border-radius:30px; background:linear-gradient(135deg, rgba(255,250,241,.96), rgba(247,236,216,.92)); box-shadow:0 20px 70px rgba(40,29,11,.12); }}
.kicker {{ font-family:var(--mono); font-size:12px; letter-spacing:.16em; text-transform:uppercase; color:var(--accent); font-weight:850; }}
h1 {{ font-family:var(--serif); font-size:clamp(42px,6vw,82px); line-height:.95; letter-spacing:-.045em; margin:14px 0 18px; text-wrap:balance; }} h2 {{ font-family:var(--serif); font-size:clamp(28px,3vw,44px); line-height:1.06; margin:0; }} h3 {{ font-size:19px; line-height:1.25; margin:0; }}
.hero p,.muted {{ color:var(--muted); }} .metrics {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }} .metric {{ border:1px solid var(--line); border-radius:18px; padding:14px; background:rgba(255,255,255,.55); }} .metric strong {{ display:block; font-family:var(--serif); font-size:32px; line-height:1; }}
nav {{ position:sticky; top:0; z-index:5; display:flex; flex-wrap:wrap; gap:9px; margin:22px 0; padding:12px; border:1px solid var(--line); border-radius:999px; background:rgba(245,239,229,.84); backdrop-filter:blur(14px); }} nav a {{ min-height:42px; display:inline-flex; align-items:center; padding:8px 13px; border-radius:999px; background:rgba(255,250,241,.75); text-decoration:none; font-weight:760; }}
.search {{ margin-left:auto; min-width:250px; min-height:42px; border:1px solid var(--line); border-radius:999px; padding:0 14px; background:var(--panel); font:inherit; }} .layout {{ display:grid; grid-template-columns:minmax(0,1fr) 340px; gap:28px; align-items:start; }} main {{ display:grid; gap:24px; }} aside {{ position:sticky; top:96px; display:grid; gap:18px; }}
.panel,.report-section,.idea,.memory-card {{ border:1px solid var(--line); border-radius:var(--radius); background:rgba(255,250,241,.82); box-shadow:0 10px 30px rgba(40,29,11,.06); }} .panel {{ padding:22px; }} .report-section {{ overflow:hidden; scroll-margin-top:96px; }} .section-head {{ display:flex; justify-content:space-between; gap:18px; padding:24px 24px 0; }} .items {{ display:grid; gap:14px; padding:18px; }}
.item {{ padding:20px; border:1px solid var(--line); border-radius:18px; background:rgba(255,255,255,.48); }} .item-top {{ display:flex; justify-content:space-between; gap:14px; align-items:flex-start; }} .sid {{ font-family:var(--mono); color:var(--accent); font-weight:850; }} .status,.tag {{ font-family:var(--mono); font-size:11px; padding:5px 8px; border:1px solid var(--line); border-radius:999px; color:var(--muted); background:rgba(255,255,255,.54); }} .status.related {{ color:var(--blue); }} .status.duplicate {{ color:#8d351e; }}
.why {{ margin-top:12px; padding:12px 14px; border-left:3px solid var(--accent); background:rgba(210,74,38,.06); border-radius:0 12px 12px 0; }} details.quote {{ margin-top:12px; border:1px solid rgba(18,16,13,.1); border-radius:14px; padding:12px 14px; background:rgba(245,239,229,.58); }} details summary {{ cursor:pointer; font-weight:760; }} blockquote {{ margin:12px 0 8px; padding-left:16px; border-left:3px solid rgba(18,16,13,.2); }} .tags {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }}
.idea {{ padding:22px; margin-top:14px; }} .idea-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; margin-top:14px; }} .idea-grid div {{ border:1px solid var(--line); border-radius:14px; padding:13px; background:rgba(255,255,255,.44); }} .label {{ display:block; font-family:var(--mono); font-size:11px; color:var(--muted); letter-spacing:.08em; text-transform:uppercase; margin-bottom:4px; }}
.score-table {{ width:100%; border-collapse:collapse; font-size:13px; }} .score-table th,.score-table td {{ padding:10px 6px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }} .bar {{ height:8px; background:rgba(18,16,13,.1); border-radius:999px; overflow:hidden; }} .bar i {{ display:block; height:100%; background:linear-gradient(90deg,var(--accent),var(--blue)); }} pre {{ white-space:pre-wrap; word-break:break-word; background:#171411; color:#f7ead7; padding:16px; border-radius:14px; overflow:auto; }}
.empty {{ padding:20px; color:var(--muted); }}
@media (max-width: 1100px) {{ .hero,.layout {{ grid-template-columns:1fr; }} aside {{ position:static; grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
@media (max-width: 768px) {{ .shell {{ padding:18px 14px 40px; }} .hero {{ padding:22px; border-radius:22px; }} .metrics,aside,.idea-grid {{ grid-template-columns:1fr; }} nav {{ border-radius:20px; }} nav a,.search {{ width:100%; min-height:44px; }} .search {{ margin-left:0; }} .item-top {{ flex-direction:column; }} }}
@media print {{ body {{ background:white; }} nav,.search {{ display:none; }} .shell {{ max-width:none; padding:0; }} .hero,.panel,.report-section,.idea,.memory-card {{ box-shadow:none; break-inside:avoid; }} details.quote>* {{ display:block; }} }}
</style>
</head>
<body><div class="shell">
<header class="hero"><div><div class="kicker">Daily Builder Brief · {escape(report.date)}</div><h1>{escape(report.title)}</h1><p>面向个人 builder 的高信噪日报：每条核心信息保留原文摘录、中文翻译、来源链接和跨日记忆。默认只读采集，不做反检测，不提取凭证。</p><ul>{highlights}</ul></div><div class="metrics"><div class="metric"><strong>{latest_score:.2f}</strong><span>最新综合评分 / 10</span></div><div class="metric"><strong>{len(report.revision_history)}</strong><span>评分轮数</span></div><div class="metric"><strong>{len(report.all_items())}</strong><span>核心条目</span></div><div class="metric"><strong>{len(report.cross_day_memory)}</strong><span>跨日 thread</span></div></div></header>
<nav aria-label="报告导航">{nav}<input class="search" id="searchBox" type="search" placeholder="搜索标题 / 标签 / 摘录…" /></nav>
<div class="layout"><main><section class="panel"><div class="kicker">Judgement</div><h2>今日判断</h2><p>今天最值得关注的主线不是又一个 AI demo，而是 Agent workflow 正在补齐 tracing、eval、审计日志、webhook 自动化和人工确认边界。</p></section>{sections}{_render_memory(report)}{_render_product_ideas(report.product_ideas)}{_render_scorecards(report.revision_history)}{_render_appendix(report)}</main><aside>{_render_sidebar(report)}</aside></div>
</div><script>const box=document.getElementById('searchBox');box&&box.addEventListener('input',()=>{{const q=box.value.trim().toLowerCase();document.querySelectorAll('article.item,.idea,.memory-card').forEach(n=>{{n.style.display=(!q||n.textContent.toLowerCase().includes(q))?'':'none';}});}});</script></body></html>'''


def validate_report_html(html: str, report: Report) -> HtmlValidationResult:
    required = ['<html', '</html>', '<header', '<nav', '原文摘录', '中文翻译', '跨日关联', '评分摘要', '@media (max-width: 768px)', '@media print', 'Product Idea Canvas']
    required.extend(f'id="{sid}"' for sid in report.section_titles)
    missing = [token for token in required if token not in html]
    return HtmlValidationResult(ok=not missing, missing=missing)


def _render_section(section_id: str, title: str, items: list[BriefItem]) -> str:
    body = ''.join(_render_item(item) for item in items) if items else '<div class="empty">本轮没有新条目；保留板块结构稳定。</div>'
    return f'<section id="{escape(section_id)}" class="report-section"><div class="section-head"><h2>{escape(title)}</h2><span class="muted">{len(items)} items</span></div><div class="items">{body}</div></section>'


def _render_item(item: BriefItem) -> str:
    tags = ''.join(f'<span class="tag">{escape(tag)}</span>' for tag in item.tags)
    links = ' · '.join(f'<a href="{escape(link)}" target="_blank" rel="noopener noreferrer">原文链接 {idx}</a>' for idx, link in enumerate(item.source_links, 1))
    relation = f'<p class="muted">关联历史：{escape(", ".join(item.relation_ids))} · {escape(item.relation_reason)}</p>' if item.relation_ids else ''
    return f'''<article class="item"><div class="item-top"><div><span class="sid">{escape(item.source_id or item.id)}</span><h3>{escape(item.title)}</h3></div><span class="status {escape(item.dedup_status)}">{escape(item.dedup_status)}</span></div><p>{escape(item.summary_zh)}</p><div class="why"><strong>Builder takeaway：</strong>{escape(item.builder_takeaway)}<br><strong>Why it matters：</strong>{escape(item.why_it_matters)}</div><details class="quote"><summary>原文摘录 / 中文翻译</summary><blockquote>{escape(item.original_excerpt)}</blockquote><p><strong>中文翻译：</strong>{escape(item.zh_translation)}</p></details>{relation}<p class="muted">{escape(item.source_title)} · {escape(item.published_at)} · {links}</p><div class="tags">{tags}</div></article>'''


def _render_memory(report: Report) -> str:
    cards = []
    for t in report.cross_day_memory:
        related = ', '.join(str(x) for x in t.get('related_ids', []))
        cards.append(f'''<div class="memory-card"><span class="label">{escape(str(t.get('thread_id','thread')))}</span><h3>{escape(str(t.get('title','跨日主题')))}</h3><p>{escape(str(t.get('today_new_evidence','')))}</p><p class="muted">first seen {escape(str(t.get('first_seen','')))} · latest {escape(str(t.get('latest_update','')))} · related {escape(related)}</p><p><strong>Next watch：</strong>{escape(str(t.get('next_watch','')))}</p></div>''')
    body = ''.join(cards) or '<p class="empty">暂无跨日关联。</p>'
    return f'<section id="memory" class="panel"><div class="kicker">Memory</div><h2>跨日关联</h2>{body}</section>'


def _render_product_ideas(ideas: list[ProductIdea]) -> str:
    body = ''.join(_render_idea(i) for i in ideas) or '<p class="empty">本轮没有产品创意。</p>'
    return f'<section id="ideas" class="panel"><div class="kicker">Product Idea Canvas</div><h2>产品创意与业务创意</h2>{body}</section>'


def _render_idea(idea: ProductIdea) -> str:
    avg = mean(idea.score.values()) if idea.score else 0
    cells = {'痛点证据': idea.pain_point_evidence, '中文翻译': idea.pain_point_translation, '目标用户': idea.target_user, '当前 workaround': idea.current_workaround, 'AI 解法': idea.ai_solution, 'MVP 范围': idea.mvp_scope, '分发': idea.distribution, '风险': idea.risks, '验证计划': idea.validation_plan}
    grid = ''.join(f'<div><span class="label">{escape(k)}</span>{escape(v)}</div>' for k, v in cells.items())
    return f'<article class="idea"><h3>{escape(idea.title)} <span class="tag">机会均分 {avg:.1f}/5</span></h3><p class="muted">触发来源：{escape(", ".join(idea.trigger_source_ids))}</p><div class="idea-grid">{grid}</div></article>'


def _render_scorecards(cards: list[ScoreCard]) -> str:
    if not cards:
        return '<section id="scores" class="panel"><h2>评分摘要</h2><p class="empty">尚未评分。</p></section>'
    latest = cards[-1]
    rows = ''.join(f'<tr><th>{escape(latest.dimension_labels.get(k,k))}</th><td>{v:.2f}</td><td><div class="bar"><i style="width:{max(0,min(100,v*10)):.0f}%"></i></div></td></tr>' for k, v in latest.dimension_scores.items())
    rounds = ''.join(f'<li>Round {c.round}: {c.overall_score:.2f}/10 — {escape(c.critique)}</li>' for c in cards)
    suggestions = ''.join(f'<li>{escape(s)}</li>' for s in latest.improvement_suggestions)
    return f'<section id="scores" class="panel"><div class="kicker">Evaluation</div><h2>评分摘要</h2><p>已完成 {len(cards)} 轮 Revision gate。最新总分 <strong>{latest.overall_score:.2f}/10</strong>。</p><table class="score-table"><tbody>{rows}</tbody></table><details open><summary>每轮评分</summary><ol>{rounds}</ol></details><details><summary>下一步改进建议</summary><ul>{suggestions}</ul></details></section>'


def _render_appendix(report: Report) -> str:
    import json
    payload = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    return f'<section id="appendix" class="panel"><div class="kicker">Appendix</div><h2>原始结构化数据 Appendix</h2><details><summary>展开 JSON 摘要</summary><pre>{escape(payload)}</pre></details></section>'


def _render_sidebar(report: Report) -> str:
    policy = escape(str(report.source_coverage.get('policy', '只读公开来源与 fixture。')))
    return f'<section class="panel"><div class="kicker">Source Coverage</div><h2>来源覆盖</h2><p class="muted">{policy}</p><table class="score-table"><tr><th>配置源</th><td>{escape(str(report.source_coverage.get("configured_sources","—")))}</td></tr><tr><th>成功源</th><td>{escape(str(report.source_coverage.get("successful_sources","—")))}</td></tr><tr><th>去重后条目</th><td>{escape(str(report.source_coverage.get("deduplicated_events","—")))}</td></tr></table></section><section class="panel"><div class="kicker">Reading Map</div><h2>阅读路径</h2><p>先看 Hero 和今日判断，再读 Builder takeaway。原文摘录默认折叠，适合桌面深读；手机端保持单列和 44px 触控目标。</p></section>'
