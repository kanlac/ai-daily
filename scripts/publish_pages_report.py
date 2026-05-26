#!/usr/bin/env python3
"""Publish a Markdown daily brief as a GitHub Pages static report.

This script intentionally has no third-party dependencies. It accepts the
LLM/editorial Markdown report, renders a mobile-friendly HTML page under
``docs/reports/YYYY-MM-DD/``, rebuilds the ``docs/index.html`` archive, and
optionally commits/pushes the generated site.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SITE_DIR = ROOT / "docs"
DEFAULT_REPO_NAME = "ai-daily"


@dataclass
class ReportMeta:
    date: str
    title: str
    summary: str
    source_path: Path
    output_dir: Path
    url_path: str


def run(cmd: list[str], *, cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=check)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def extract_title(markdown: str, date: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            if title:
                return title
    return f"AI 日报｜{date}"


def extract_summary(markdown: str) -> str:
    """Pick a short human-readable summary for index cards."""
    lines = [line.strip() for line in markdown.splitlines()]
    # Prefer explicit overview sections.
    for marker in ("一句话", "今日主线", "总览", "我的判断", "趋势判断"):
        for idx, line in enumerate(lines):
            if marker in line and line.startswith("#"):
                buf: list[str] = []
                for nxt in lines[idx + 1 :]:
                    if not nxt:
                        if buf:
                            break
                        continue
                    if nxt.startswith("#"):
                        break
                    cleaned = re.sub(r"^[\-*>\d\.、\s]+", "", nxt).strip()
                    if cleaned:
                        buf.append(cleaned)
                    if len("".join(buf)) > 180:
                        break
                if buf:
                    return trim_plain(" ".join(buf), 180)
    # Fallback: first non-heading paragraph/list item.
    for line in lines:
        if not line or line.startswith("#"):
            continue
        cleaned = re.sub(r"^[\-*>\d\.、\s]+", "", line).strip()
        if cleaned:
            return trim_plain(cleaned, 180)
    return "今日 AI 新闻完整报告。"


def trim_plain(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", strip_markdown(text)).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def strip_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    return text


def inline_md(text: str) -> str:
    """Render a conservative Markdown inline subset."""
    escaped = html.escape(text, quote=False)

    def link_repl(match: re.Match[str]) -> str:
        label = match.group(1)
        url = html.unescape(match.group(2)).strip()
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https", "mailto"}:
            return label
        return f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{label}</a>'

    escaped = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+|mailto:[^)\s]+)\)", link_repl, escaped)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return escaped


def render_markdown(markdown: str) -> str:
    """Render the small subset used by the daily reports."""
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    in_code = False
    code_lines: list[str] = []
    skipped_leading_h1 = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(line.strip() for line in paragraph).strip()
            if text:
                blocks.append(f"<p>{inline_md(text)}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            blocks.append("<ul>" + "".join(f"<li>{inline_md(item)}</li>" for item in list_items) + "</ul>")
            list_items = []

    def flush_code() -> None:
        nonlocal code_lines
        blocks.append(f"<pre><code>{html.escape(''.join(code_lines))}</code></pre>")
        code_lines = []

    for raw in markdown.splitlines():
        line = raw.rstrip("\n")
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                flush_paragraph()
                flush_list()
                in_code = True
                code_lines = []
            continue
        if in_code:
            code_lines.append(line + "\n")
            continue
        if not stripped:
            flush_paragraph()
            flush_list()
            continue
        if stripped.startswith("#"):
            flush_paragraph()
            flush_list()
            level = min(4, max(1, len(stripped) - len(stripped.lstrip("#"))))
            text = stripped.lstrip("#").strip()
            if level == 1 and not blocks and not skipped_leading_h1:
                # The page hero already renders the report title.
                skipped_leading_h1 = True
                continue
            if level == 1:
                # The page already has an H1 hero title; downgrade body H1.
                level = 2
            blocks.append(f"<h{level}>{inline_md(text)}</h{level}>")
            continue
        ordered = re.match(r"^(\d+)[\.、]\s+(.+)$", stripped)
        if ordered:
            flush_paragraph()
            flush_list()
            blocks.append(f"<h3>{ordered.group(1)}. {inline_md(ordered.group(2).strip())}</h3>")
            continue
        bullet = re.match(r"^[-*+]\s+(.+)$", stripped)
        if bullet:
            flush_paragraph()
            list_items.append(bullet.group(1).strip())
            continue
        flush_list()
        paragraph.append(stripped)

    flush_paragraph()
    flush_list()
    if in_code:
        flush_code()
    return "\n".join(blocks)


def page_html(title: str, date: str, summary: str, body_html: str, css_href: str) -> str:
    title_esc = html.escape(title)
    summary_esc = html.escape(summary)
    date_esc = html.escape(date)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{summary_esc}">
  <title>{title_esc}</title>
  <link rel="stylesheet" href="{css_href}">
</head>
<body>
  <header class="site-header">
    <a class="brand" href="../../">AI Daily</a>
    <nav><a href="../../">归档</a><a href="../">报告</a></nav>
  </header>
  <main class="report-shell">
    <section class="hero">
      <p class="eyebrow">Daily AI Brief</p>
      <h1>{title_esc}</h1>
      <p class="date">{date_esc}</p>
      <p class="summary">{summary_esc}</p>
    </section>
    <article class="report-content">
{body_html}
    </article>
  </main>
  <footer class="site-footer">
    <span>Generated for Telegram delivery · Source links belong to their publishers.</span>
  </footer>
</body>
</html>
"""


def build_index(site_dir: Path, repo_name: str, homepage_url: str | None = None) -> None:
    reports_root = site_dir / "reports"
    metas: list[dict[str, str]] = []
    if reports_root.exists():
        for report_md in sorted(reports_root.glob("*/report.md"), reverse=True):
            date = report_md.parent.name
            md = read_text(report_md)
            metas.append(
                {
                    "date": date,
                    "title": extract_title(md, date),
                    "summary": extract_summary(md),
                    "path": f"reports/{date}/",
                }
            )

    cards = []
    for meta in metas:
        cards.append(
            f"""
      <a class="report-card" href="{html.escape(meta['path'], quote=True)}">
        <span class="card-date">{html.escape(meta['date'])}</span>
        <strong>{html.escape(meta['title'])}</strong>
        <p>{html.escape(meta['summary'])}</p>
      </a>"""
        )
    cards_html = "\n".join(cards) if cards else "<p class=\"empty\">还没有日报。</p>"
    latest_href = html.escape(metas[0]["path"], quote=True) if metas else "#"
    index = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="AI 日报归档：模型、Agent、AI 编程、基础设施、融资和监管动态。">
  <title>AI Daily｜日报归档</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <header class="site-header">
    <a class="brand" href="./">AI Daily</a>
    <nav><a href="{latest_href}">最新一期</a><a href="https://github.com/kanlac/{html.escape(repo_name)}" target="_blank" rel="noopener noreferrer">GitHub</a></nav>
  </header>
  <main class="home-shell">
    <section class="hero home-hero">
      <p class="eyebrow">Telegram-native entry · Web archive</p>
      <h1>AI 日报归档</h1>
      <p class="summary">每天把完整 AI 新闻报告发布成网页，Telegram 只推送摘要和链接。适合长文阅读、回看和分享。</p>
      <a class="primary" href="{latest_href}">阅读最新一期</a>
    </section>
    <section class="archive">
      <h2>历史报告</h2>
      <div class="report-grid">
{cards_html}
      </div>
    </section>
  </main>
  <footer class="site-footer"><span>Hosted by GitHub Pages.</span></footer>
</body>
</html>
"""
    write_text(site_dir / "index.html", index)
    write_text(site_dir / ".nojekyll", "")

    if metas:
        latest = metas[0]
        latest_html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url=../{html.escape(latest['path'], quote=True)}">
  <link rel="canonical" href="../{html.escape(latest['path'], quote=True)}">
  <title>Redirecting…</title>
</head>
<body>
  <p>最新一期：<a href="../{html.escape(latest['path'], quote=True)}">{html.escape(latest['title'])}</a></p>
</body>
</html>
"""
        write_text(site_dir / "latest" / "index.html", latest_html)

    manifest = {
        "repo": repo_name,
        "homepage": homepage_url,
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "reports": metas,
    }
    write_text(site_dir / "reports.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


def git_has_changes(paths: list[str]) -> bool:
    result = run(["git", "status", "--short", *paths], check=False)
    return bool(result.stdout.strip())


def maybe_commit_and_push(message: str, push: bool) -> None:
    run(["git", "add", "docs"])
    # Include script/doc changes if caller is bootstrapping locally.
    run(["git", "add", "scripts/publish_pages_report.py"], check=False)
    if not git_has_changes(["docs", "scripts/publish_pages_report.py"]):
        print("No generated site changes to commit.")
        return
    run(["git", "commit", "-m", message])
    if push:
        run(["git", "push", "-u", "origin", "HEAD:main"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Report date, YYYY-MM-DD")
    parser.add_argument("--input", required=True, type=Path, help="Markdown report file")
    parser.add_argument("--site-dir", default=DEFAULT_SITE_DIR, type=Path)
    parser.add_argument("--repo-name", default=DEFAULT_REPO_NAME)
    parser.add_argument("--homepage-url", default=None)
    parser.add_argument("--commit", action="store_true", help="Commit generated docs")
    parser.add_argument("--push", action="store_true", help="Push commit to origin/main")
    args = parser.parse_args(argv)

    report_date = dt.date.fromisoformat(args.date).isoformat()
    source = args.input.resolve()
    markdown = read_text(source)
    title = extract_title(markdown, report_date)
    summary = extract_summary(markdown)

    site_dir = args.site_dir.resolve()
    report_dir = site_dir / "reports" / report_date
    body_html = render_markdown(markdown)
    html_doc = page_html(title, report_date, summary, body_html, "../../assets/style.css")
    write_text(report_dir / "index.html", html_doc)
    write_text(report_dir / "report.md", markdown.rstrip() + "\n")

    meta = ReportMeta(
        date=report_date,
        title=title,
        summary=summary,
        source_path=source,
        output_dir=report_dir,
        url_path=f"reports/{report_date}/",
    )
    write_text(
        report_dir / "meta.json",
        json.dumps(meta.__dict__ | {"source_path": str(meta.source_path), "output_dir": str(meta.output_dir)}, ensure_ascii=False, indent=2)
        + "\n",
    )
    build_index(site_dir, args.repo_name, args.homepage_url)

    if args.commit or args.push:
        maybe_commit_and_push(f"docs: publish AI daily {report_date}", args.push)

    print(f"Published {title} -> {report_dir / 'index.html'}")
    if args.homepage_url:
        print(args.homepage_url.rstrip("/") + f"/reports/{report_date}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
