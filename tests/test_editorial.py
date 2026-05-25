import json

from daily_brief.editorial import apply_editorial_overrides
from daily_brief.models import CollectedItem


def test_apply_editorial_overrides_updates_item_metadata(tmp_path):
    item = CollectedItem(
        id="item-1",
        source_id="feed",
        source_type="rss",
        title="Original English Title",
        url="https://example.com/a",
        canonical_url="https://example.com/a",
        author="Feed",
        published_at="2026-05-19T00:00:00+00:00",
        fetched_at="2026-05-19T00:01:00+00:00",
        raw_excerpt="Original excerpt.",
        content_text="Original English Title\n\nOriginal excerpt.",
    )
    overrides_path = tmp_path / "editorial.json"
    overrides_path.write_text(
        json.dumps(
            {
                "items": {
                    "item-1": {
                        "title_zh": "中文标题",
                        "one_sentence": "一句话概括。",
                        "summary_zh": "整理后的中文摘要。",
                        "zh_translation": "真正的中文翻译。",
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    applied = apply_editorial_overrides([item], overrides_path)

    assert applied == 1
    assert item.metadata["title_zh"] == "中文标题"
    assert item.metadata["original_title"] == "Original English Title"
    assert item.metadata["summary_zh"] == "整理后的中文摘要。"
    assert item.metadata["zh_translation"] == "真正的中文翻译。"
