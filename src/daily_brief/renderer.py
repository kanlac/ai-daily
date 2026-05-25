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
    nav = ''.join(f'<a href="#{escape(sid)}">{escape(title)}</a>' for sid, title in report.section_titles.items())
    nav += '<a href="#memory">跨日关联</a><a href="#ideas">产品创意</a><a href="#scores">评分摘要</a>'
    sections = ''.join(_render_section(sid, title, report.sections.get(sid, [])) for sid, title in report.section_titles.items())
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{escape(report.date)} Daily Builder Brief</title>
<style>
:root {{ --ink:#17130f; --muted:#6d665b; --paper:#f7f1e7; --panel:#fffaf2; --line:rgba(23,19,15,.14); --accent:#bb4526; --blue:#164e63; --soft:#efe4d2; --radius:18px; --serif:Charter,Georgia,'Songti SC',serif; --sans:Inter,-apple-system,BlinkMacSystemFont,'SF Pro Text','PingFang SC','Noto Sans CJK SC','Segoe UI',sans-serif; --mono:ui-monospace,SFMono-Regular,Menlo,monospace; }}
* {{ box-sizing:border-box; }} html {{ scroll-behavior:smooth; }} body {{ margin:0; background:var(--paper); color:var(--ink); font-family:var(--sans); line-height:1.68; }}
a {{ color:var(--blue); text-underline-offset:.18em; }} .shell {{ max-width:1480px; margin:auto; padding:18px 24px 56px; }}
.topbar {{ display:flex; align-items:baseline; justify-content:space-between; gap:18px; padding:8px 2px 12px; border-bottom:1px solid var(--line); }} .date-title {{ font-family:var(--serif); font-size:clamp(24px,3vw,40px); line-height:1; letter-spacing:-.02em; }} .top-meta {{ color:var(--muted); font-size:13px; }}
nav.topnav {{ position:sticky; top:0; z-index:10; display:flex; flex-wrap:wrap; gap:8px; margin:12px 0 18px; padding:10px; border:1px solid var(--line); border-radius:16px; background:rgba(247,241,231,.92); backdrop-filter:blur(12px); }} nav.topnav a {{ min-height:38px; display:inline-flex; align-items:center; padding:7px 11px; border-radius:12px; background:rgba(255,250,242,.78); text-decoration:none; font-weight:720; font-size:14px; }}
.search {{ margin-left:auto; min-width:270px; min-height:38px; border:1px solid var(--line); border-radius:12px; padding:0 12px; background:var(--panel); font:inherit; }} .layout {{ display:grid; grid-template-columns:minmax(0,1fr) 360px; gap:24px; align-items:start; }} main {{ display:grid; gap:22px; min-width:0; }} aside {{ position:sticky; top:82px; display:grid; gap:14px; max-height:calc(100vh - 96px); overflow:auto; padding-right:4px; }}
.panel,.report-section,.idea,.memory-card,.toc-card {{ border:1px solid var(--line); border-radius:var(--radius); background:rgba(255,250,242,.9); box-shadow:0 8px 26px rgba(40,29,11,.045); }} .panel {{ padding:20px; }} .report-section {{ overflow:hidden; scroll-margin-top:88px; }} .section-head {{ display:flex; justify-content:space-between; gap:18px; align-items:end; padding:22px 22px 8px; border-bottom:1px solid rgba(23,19,15,.08); }}
h1,h2,h3 {{ margin:0; text-wrap:pretty; }} h1 {{ font-family:var(--serif); }} h2 {{ font-family:var(--serif); font-size:clamp(28px,3vw,42px); line-height:1.08; }} h3 {{ font-size:21px; line-height:1.32; letter-spacing:-.01em; }} .muted {{ color:var(--muted); }} .kicker {{ font-family:var(--mono); font-size:11px; letter-spacing:.12em; text-transform:uppercase; color:var(--accent); font-weight:850; }}
.items {{ display:grid; gap:12px; padding:14px; }} .item {{ padding:18px; border:1px solid var(--line); border-radius:16px; background:rgba(255,255,255,.56); scroll-margin-top:90px; }} .item-top {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:14px; align-items:start; }} .sid {{ font-family:var(--mono); color:var(--accent); font-weight:850; font-size:12px; }} .status,.tag {{ font-family:var(--mono); font-size:11px; padding:4px 7px; border:1px solid var(--line); border-radius:999px; color:var(--muted); background:rgba(255,255,255,.62); }} .status.related {{ color:var(--blue); }} .one-line {{ margin:8px 0 12px; font-weight:760; color:#30261d; }} .summary {{ margin:0 0 12px; }} .explain {{ display:grid; gap:8px; margin:12px 0; padding:12px 13px; border-radius:12px; background:rgba(239,228,210,.58); }} .explain strong {{ color:#38251b; }}
.original-title {{ margin-top:6px; font-size:13px; color:var(--muted); }} .evidence-note {{ margin:10px 0; padding:10px 12px; border:1px dashed rgba(20,79,100,.35); border-radius:12px; background:rgba(20,79,100,.06); color:var(--blue); font-size:13px; }} details.quote {{ margin-top:12px; border:1px solid rgba(23,19,15,.1); border-radius:13px; padding:12px 13px; background:rgba(247,241,231,.74); }} details summary {{ cursor:pointer; font-weight:780; }} blockquote {{ margin:12px 0 8px; padding-left:14px; border-left:3px solid rgba(23,19,15,.22); color:#352a21; }} .tags {{ display:flex; flex-wrap:wrap; gap:7px; margin-top:12px; }} .item-meta {{ font-size:13px; color:var(--muted); }}
.toc-card {{ padding:16px; }} .toc-section {{ margin:12px 0 16px; }} .toc-section>a {{ display:block; font-weight:860; text-decoration:none; margin-bottom:8px; }} .toc-item {{ display:block; padding:8px 9px; border-radius:10px; text-decoration:none; color:var(--ink); border:1px solid transparent; }} .toc-item:hover,.toc-item:focus {{ background:var(--soft); border-color:var(--line); }} .toc-item small {{ display:block; color:var(--muted); line-height:1.38; margin-top:2px; }}
.idea {{ padding:18px; margin-top:12px; }} .idea-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin-top:12px; }} .idea-grid div {{ border:1px solid var(--line); border-radius:12px; padding:12px; background:rgba(255,255,255,.48); }} .label {{ display:block; font-family:var(--mono); font-size:11px; color:var(--muted); letter-spacing:.08em; text-transform:uppercase; margin-bottom:4px; }}
.score-table {{ width:100%; border-collapse:collapse; font-size:13px; }} .score-table th,.score-table td {{ padding:9px 6px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }} .bar {{ height:8px; background:rgba(23,19,15,.1); border-radius:999px; overflow:hidden; }} .bar i {{ display:block; height:100%; background:linear-gradient(90deg,var(--accent),var(--blue)); }} pre {{ white-space:pre-wrap; word-break:break-word; background:#171411; color:#f7ead7; padding:16px; border-radius:14px; overflow:auto; }} .empty {{ padding:18px; color:var(--muted); }}
@media (max-width: 1120px) {{ .layout {{ grid-template-columns:1fr; }} aside {{ position:static; max-height:none; order:-1; }} }}
@media (max-width: 768px) {{ .shell {{ padding:14px 12px 40px; }} .topbar {{ align-items:flex-start; flex-direction:column; }} nav.topnav {{ border-radius:14px; }} nav.topnav a,.search {{ width:100%; min-height:44px; }} .search {{ margin-left:0; }} .item-top,.idea-grid {{ grid-template-columns:1fr; }} }}
@media print {{ body {{ background:white; }} nav.topnav,.search,aside {{ display:none; }} .shell {{ max-width:none; padding:0; }} .panel,.report-section,.idea,.memory-card {{ box-shadow:none; break-inside:avoid; }} details.quote>* {{ display:block; }} }}
</style>
</head>
<body><div class="shell">
<header class="topbar"><h1 class="date-title">{escape(report.date)} 每日简报</h1><div class="top-meta">{len(report.all_items())} 条核心消息 · {len(report.revision_history)} 轮评估 · 只读公开来源</div></header>
<nav class="topnav" aria-label="报告导航">{nav}<input class="search" id="searchBox" type="search" placeholder="搜索标题 / 一句话 / 摘录…" /></nav>
<div class="layout"><main>{sections}{_render_memory(report)}{_render_product_ideas(report.product_ideas)}{_render_scorecards(report.revision_history)}{_render_appendix(report)}</main><aside>{_render_toc(report)}{_render_sidebar(report)}</aside></div>
</div><script>const box=document.getElementById('searchBox');box&&box.addEventListener('input',()=>{{const q=box.value.trim().toLowerCase();document.querySelectorAll('article.item,.idea,.memory-card').forEach(n=>{{n.style.display=(!q||n.textContent.toLowerCase().includes(q))?'':'none';}});}});</script></body></html>'''


def validate_report_html(html: str, report: Report) -> HtmlValidationResult:
    required = ['<html', '</html>', '<header', '<nav', '原文摘录', '中文翻译', '跨日关联', '评分摘要', '@media (max-width: 768px)', '@media print', 'Product Idea Canvas', 'id="toc"']
    required.extend(f'id="{sid}"' for sid in report.section_titles)
    missing = [token for token in required if token not in html]
    return HtmlValidationResult(ok=not missing, missing=missing)


def _render_section(section_id: str, title: str, items: list[BriefItem]) -> str:
    body = ''.join(_render_item(item) for item in items) if items else '<div class="empty">本轮没有新条目；保留板块结构稳定。</div>'
    return f'<section id="{escape(section_id)}" class="report-section"><div class="section-head"><div><div class="kicker">Section</div><h2>{escape(title)}</h2></div><span class="muted">{len(items)} 条</span></div><div class="items">{body}</div></section>'


def _render_item(item: BriefItem) -> str:
    tags = ''.join(f'<span class="tag">{escape(tag)}</span>' for tag in item.tags)
    links = ' · '.join(f'<a href="{escape(link)}" target="_blank" rel="noopener noreferrer">原文链接 {idx}</a>' for idx, link in enumerate(item.source_links, 1))
    relation = f'<p class="muted">关联历史：{escape(", ".join(item.relation_ids))} · {escape(item.relation_reason)}</p>' if item.relation_ids else ''
    evidence = _render_evidence_note(item)
    original_title = item.original_title or item.title
    original_title_html = f'<p class="original-title">英文原标题：{escape(original_title)}</p>' if original_title and original_title != item.title else ''
    one_sentence = f'<p class="one-line">{escape(item.one_sentence or item.summary_zh)}</p>'
    return f'''<article id="{escape(item.id)}" class="item"><div class="item-top"><div><span class="sid">{escape(item.source_id or item.id)}</span><h3>{escape(item.title)}</h3>{original_title_html}</div><span class="status {escape(item.dedup_status)}">{escape(item.dedup_status)}</span></div>{one_sentence}<p class="summary">{escape(item.summary_zh)}</p><div class="explain"><div><strong>为什么值得看：</strong>{escape(item.why_it_matters)}</div><div><strong>可执行启发：</strong>{escape(item.builder_takeaway)}</div></div>{evidence}<details class="quote"><summary>原文摘录和中文翻译</summary><blockquote>{escape(item.original_excerpt)}</blockquote><p><strong>中文翻译：</strong>{escape(item.zh_translation)}</p></details>{relation}<p class="item-meta">{escape(item.source_title)} · {escape(item.published_at)} · {links}</p><div class="tags">{tags}</div></article>'''


def _render_evidence_note(item: BriefItem) -> str:
    status = str(item.evidence_metadata.get('transcript_status', '')).strip()
    if not status:
        return ''
    language = str(item.evidence_metadata.get('transcript_language', '')).strip() or 'n/a'
    provider = str(item.evidence_metadata.get('transcript_provider', '')).strip() or 'n/a'
    note = str(item.evidence_metadata.get('transcript_note', f'transcript_status={status}')).strip()
    label = '字幕证据' if status == 'fetched' else '字幕降级说明'
    return f'<div class="evidence-note"><span class="label">{escape(label)}</span>{escape(note)} · language={escape(language)} · provider={escape(provider)}</div>'


def _render_toc(report: Report) -> str:
    blocks: list[str] = []
    for sid, title in report.section_titles.items():
        items = report.sections.get(sid, [])
        links = ''.join(
            f'<a class="toc-item" href="#{escape(item.id)}">{escape(item.title)}<small>{escape(item.one_sentence or item.summary_zh)}</small></a>'
            for item in items
        )
        blocks.append(f'<div class="toc-section"><a href="#{escape(sid)}">{escape(title)} · {len(items)} 条</a>{links}</div>')
    return f'<section id="toc" class="toc-card"><div class="kicker">目录</div><h2>快速跳转</h2>{"".join(blocks)}</section>'


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
    suggestions = ''.join(f'<li>{escape(_sanitize_score_text(s))}</li>' for s in latest.improvement_suggestions)
    return f'<section id="scores" class="panel"><div class="kicker">Evaluation</div><h2>评分摘要</h2><p>已完成 {len(cards)} 轮 Revision gate。最新总分 <strong>{latest.overall_score:.2f}/10</strong>。</p><table class="score-table"><tbody>{rows}</tbody></table><details><summary>下一步改进建议</summary><ul>{suggestions}</ul></details></section>'


def _sanitize_score_text(value: str) -> str:
    return value.replace('Hero、今日判断、', '').replace('今日判断', '开头导读').replace('Builder takeaway', '可执行启发')


def _render_appendix(report: Report) -> str:
    import json
    payload_dict = report.to_dict()
    payload_dict['revision_history'] = [{'round': c.round, 'overall_score': c.overall_score, 'passed': c.passed} for c in report.revision_history]
    payload = json.dumps(payload_dict, ensure_ascii=False, indent=2)
    return f'<section id="appendix" class="panel"><div class="kicker">Appendix</div><h2>原始结构化数据 Appendix</h2><details><summary>展开 JSON 摘要</summary><pre>{escape(payload)}</pre></details></section>'


def _render_sidebar(report: Report) -> str:
    policy = escape(str(report.source_coverage.get('policy', '只读公开来源与 fixture。')))
    return f'<section class="panel"><div class="kicker">Source Coverage</div><h2>来源覆盖</h2><p class="muted">{policy}</p><table class="score-table"><tr><th>配置源</th><td>{escape(str(report.source_coverage.get("configured_sources","—")))}</td></tr><tr><th>成功源</th><td>{escape(str(report.source_coverage.get("successful_sources","—")))}</td></tr><tr><th>去重后条目</th><td>{escape(str(report.source_coverage.get("deduplicated_events","—")))}</td></tr></table></section>'
