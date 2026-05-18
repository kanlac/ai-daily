'''Command-line runner for Daily Brief.'''
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from .config import BriefConfig, ConfigError, load_config
from .evaluator import run_evaluation_loops
from .memory import MemoryStore
from .collectors.runner import collect_sources
from .models import PushTask, RunManifest
from .push import send_codex_app_push
from .renderer import render_report_html, validate_report_html
from .sample_data import build_report_from_items, build_sample_report


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == 'run':
            return _cmd_run(args)
        if args.command == 'render-sample':
            return _cmd_render_sample(args)
    except ConfigError as exc:
        parser.exit(2, f'Config error: {exc}\n')
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='daily-brief', description='Generate a local-first HTML daily builder briefing.')
    sub = parser.add_subparsers(dest='command', required=True)
    run = sub.add_parser('run', help='Run collect/dedup/evaluate/render/push pipeline.')
    run.add_argument('--config', default='configs/daily-brief.yaml')
    run.add_argument('--date', default=None)
    run.add_argument('--loops', type=int, default=None)
    run.add_argument('--no-push', action='store_true')
    sample = sub.add_parser('render-sample', help='Render sample HTML without touching memory.')
    sample.add_argument('--config', default='configs/daily-brief.yaml')
    sample.add_argument('--date', default=None)
    sample.add_argument('--output', default=None)
    return parser


def _cmd_run(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    run_date = args.date or datetime.now(timezone.utc).date().isoformat()
    loops = _resolve_loops(args.loops, cfg)
    store = MemoryStore(_format_path(cfg.paths.memory, run_date))
    store.initialize()
    items, coverage = collect_sources(cfg.sources, run_date)
    decisions = {}
    for item in items:
        decision = store.dedup_item(item)
        decisions[item.id] = decision
        store.record_collected_item(item, run_date=run_date, decision=decision)
    report = build_report_from_items(run_date, items, decisions, cfg.sections, source_coverage=coverage)
    scorecards = run_evaluation_loops(report, loops=loops)
    report.revision_history = scorecards
    html = render_report_html(report)
    validation = validate_report_html(html, report)
    if not validation.ok:
        raise RuntimeError(f'HTML validation failed, missing: {validation.missing}')
    report_path = Path(_format_path(cfg.paths.report, run_date))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(html, encoding='utf-8')
    scorecard_path = Path('reports') / 'evaluations' / f'{run_date}-scorecard.json'
    scorecard_path.parent.mkdir(parents=True, exist_ok=True)
    score_payload = {'date': run_date, 'loop_count': loops, 'pass_score': cfg.thresholds.pass_score, 'latest_score': scorecards[-1].overall_score, 'passed': bool(scorecards[-1].overall_score >= cfg.thresholds.pass_score and not scorecards[-1].blocking_issues), 'scorecards': [c.to_dict() for c in scorecards]}
    scorecard_path.write_text(json.dumps(score_payload, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
    store.record_scorecards(run_date, [c.to_dict() for c in scorecards])
    run_dir = Path(_format_path(cfg.paths.run_dir, run_date)); run_dir.mkdir(parents=True, exist_ok=True)
    push_result = None
    if not args.no_push:
        task = PushTask(title=f'{run_date} Daily Builder Brief', summary=f'HTML 日报已生成：{report.title}；最新评分 {scorecards[-1].overall_score:.2f}/10。', report_path=str(report_path), scorecard_path=str(scorecard_path), run_manifest_path=str(run_dir / 'run.json'), suggested_actions=['打开 HTML 报告阅读今日判断', '检查评分摘要里的弱项', '从产品创意板块选择一个 idea 做 spike'], date=run_date)
        push_result = send_codex_app_push(task, payload_path=_format_path(cfg.paths.push_payload, run_date), webhook_url_env=cfg.push.codex_app_webhook_url_env, dry_run_without_webhook=cfg.push.dry_run_without_webhook)
    manifest = RunManifest(date=run_date, status='ok', config_path=str(Path(args.config)), report_path=str(report_path), scorecard_path=str(scorecard_path), memory_path=str(store.path), item_count=len(report.all_items()), scorecard_count=len(scorecards), push=push_result.to_dict() if push_result else {'skipped': True}, source_coverage=report.source_coverage, warnings=[w for c in scorecards for w in c.warnings])
    manifest_path = run_dir / 'run.json'
    manifest_path.write_text(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
    store.record_run_manifest(run_date, manifest.to_dict())
    print(json.dumps({'status': 'ok', 'report': str(report_path), 'scorecard': str(scorecard_path), 'manifest': str(manifest_path), 'push': manifest.push}, ensure_ascii=False, indent=2))
    return 0


def _cmd_render_sample(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    run_date = args.date or datetime.now(timezone.utc).date().isoformat()
    report = build_sample_report(run_date, sections=cfg.sections)
    report.revision_history = run_evaluation_loops(report, loops=cfg.thresholds.default_loops)
    output = Path(args.output or _format_path(cfg.paths.report, run_date))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report_html(report), encoding='utf-8')
    print(str(output))
    return 0


def _resolve_loops(requested: int | None, cfg: BriefConfig) -> int:
    loops = requested if requested is not None else cfg.thresholds.default_loops
    if not (cfg.thresholds.min_loops <= loops <= cfg.thresholds.max_loops):
        raise ConfigError(f'--loops must be between {cfg.thresholds.min_loops} and {cfg.thresholds.max_loops}')
    return loops


def _format_path(template: str, date: str) -> str:
    return template.format(date=date)


if __name__ == '__main__':
    raise SystemExit(main())
