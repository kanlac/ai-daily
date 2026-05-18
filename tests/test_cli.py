import json
from pathlib import Path

from daily_brief.cli import main


def test_cli_run_generates_artifacts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    config_path = config_dir / "daily-brief.yaml"
    config_path.write_text(
        """
project:
  name: daily-brief
  timezone: Asia/Shanghai
schedule:
  time: "07:00"
paths:
  report: reports/{date}-daily-brief.html
  memory: data/memory.sqlite3
  run_dir: data/runs/{date}
  push_payload: reports/push-payload-{date}.json
sections:
  - id: tech_news
    title: 科技新闻
  - id: tool_engineering
    title: 工具工程更新
  - id: social_blogs
    title: 社媒博客
  - id: video
    title: 视频
  - id: product_ideas
    title: 产品/业务创意
sources:
  - id: sample
    type: fixture
    name: Sample fixture
    enabled: true
thresholds:
  min_loops: 5
  max_loops: 10
  pass_score: 8.0
push:
  codex_app_webhook_url_env: CODEX_APP_WEBHOOK_URL
""",
        encoding="utf-8",
    )
    monkeypatch.delenv("CODEX_APP_WEBHOOK_URL", raising=False)

    exit_code = main(["run", "--config", str(config_path), "--date", "2026-05-18", "--loops", "7"])

    assert exit_code == 0
    report_path = tmp_path / "reports" / "2026-05-18-daily-brief.html"
    scorecard_path = tmp_path / "reports" / "evaluations" / "2026-05-18-scorecard.json"
    memory_path = tmp_path / "data" / "memory.sqlite3"
    push_payload_path = tmp_path / "reports" / "push-payload-2026-05-18.json"
    run_manifest = tmp_path / "data" / "runs" / "2026-05-18" / "run.json"

    assert report_path.exists()
    assert scorecard_path.exists()
    assert memory_path.exists()
    assert push_payload_path.exists()
    assert run_manifest.exists()

    scorecards = json.loads(scorecard_path.read_text(encoding="utf-8"))
    manifest = json.loads(run_manifest.read_text(encoding="utf-8"))
    assert len(scorecards["scorecards"]) == 7
    assert manifest["status"] == "ok"
    assert manifest["push"]["dry_run"] is True
    html = report_path.read_text(encoding="utf-8")
    assert "2026-05-18" in html
    assert "科技新闻" in html
    assert "原文摘录" in html
    assert "中文翻译" in html
