from pathlib import Path

import pytest

from daily_brief.config import ConfigError, load_config


def test_load_default_config_contract():
    cfg = load_config(Path("configs/daily-brief.yaml"))

    assert cfg.project.name == "daily-brief"
    assert cfg.schedule.time == "07:00"
    assert cfg.push.codex_app_webhook_url_env == "CODEX_APP_WEBHOOK_URL"
    assert len(cfg.sections) >= 5
    assert {section.id for section in cfg.sections} >= {
        "tech_news",
        "tool_engineering",
        "social_blogs",
        "video",
        "product_ideas",
    }
    assert cfg.thresholds.min_loops == 5
    assert cfg.thresholds.max_loops == 10


def test_load_json_fallback_config(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
        {
          "project": {"name": "daily-brief", "timezone": "Asia/Shanghai"},
          "schedule": {"time": "07:00"},
          "paths": {
            "report": "out/{date}.html",
            "memory": "data/memory.sqlite3",
            "run_dir": "data/runs/{date}",
            "push_payload": "out/push-payload-{date}.json"
          },
          "sections": [
            {"id": "tech_news", "title": "科技新闻"},
            {"id": "tool_engineering", "title": "工具工程更新"},
            {"id": "social_blogs", "title": "社媒博客"},
            {"id": "video", "title": "视频"},
            {"id": "product_ideas", "title": "产品/业务创意"}
          ],
          "sources": [{"id": "fixture", "type": "fixture", "name": "Fixture", "enabled": true}],
          "thresholds": {"min_loops": 5, "max_loops": 10, "pass_score": 8.0},
          "push": {"codex_app_webhook_url_env": "CODEX_APP_WEBHOOK_URL"}
        }
        """,
        encoding="utf-8",
    )

    cfg = load_config(config_path)

    assert cfg.paths.report == "out/{date}.html"
    assert cfg.sources[0].type == "fixture"


def test_config_missing_required_sections_fails(tmp_path):
    config_path = tmp_path / "bad.yaml"
    config_path.write_text(
        """
project:
  name: daily-brief
  timezone: Asia/Shanghai
schedule:
  time: "07:00"
paths:
  report: reports/{date}.html
  memory: data/memory.sqlite3
  run_dir: data/runs/{date}
  push_payload: reports/push-payload-{date}.json
sections: []
sources: []
thresholds:
  min_loops: 5
  max_loops: 10
  pass_score: 8.0
push:
  codex_app_webhook_url_env: CODEX_APP_WEBHOOK_URL
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load_config(config_path)
