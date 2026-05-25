from __future__ import annotations

from daily_brief.config import SectionConfig, SourceConfig
from daily_brief.models import CollectedItem, DedupDecision
from daily_brief.sample_data import build_report_from_items
from daily_brief.renderer import render_report_html
from daily_brief.collectors import youtube
from daily_brief.collectors.base import CollectorResult
from daily_brief.collectors.youtube_transcripts import fetch_youtube_transcript, extract_video_id


class FakeTranscript(list):
    language_code = "en"
    is_generated = True


def _youtube_item() -> CollectedItem:
    return CollectedItem(
        id="yt-abc",
        source_id="youtube_yc",
        source_type="youtube",
        title="Founder explains eval-driven building",
        url="https://www.youtube.com/watch?v=abcdefghijk",
        canonical_url="https://www.youtube.com/watch?v=abcdefghijk",
        author="Y Combinator",
        published_at="2026-05-19T00:00:00+00:00",
        fetched_at="2026-05-19T00:01:00+00:00",
        raw_excerpt="Feed description only; this must not be treated as transcript evidence.",
        content_text="Founder explains eval-driven building\n\nFeed description only.",
        metadata={"section": "video", "tags": ["YouTube", "Builder"]},
    )


def test_extract_video_id_supports_common_youtube_urls():
    assert extract_video_id("https://www.youtube.com/watch?v=abcdefghijk&t=42s") == "abcdefghijk"
    assert extract_video_id("https://youtu.be/abcdefghijk") == "abcdefghijk"
    assert extract_video_id("https://youtube.com/shorts/abcdefghijk") == "abcdefghijk"
    assert extract_video_id("abcdefghijk") == "abcdefghijk"


def test_fetch_youtube_transcript_normalizes_segments_from_provider():
    def fake_fetcher(video_id: str, languages: tuple[str, ...]):
        assert video_id == "abcdefghijk"
        assert languages[:2] == ("zh-Hans", "zh")
        return FakeTranscript(
            [
                {"text": "We stopped debating prompts.", "start": 12.2, "duration": 2.0},
                {"text": "Every workflow now gets a regression eval.", "start": 15.8, "duration": 2.5},
            ]
        )

    result = fetch_youtube_transcript("https://www.youtube.com/watch?v=abcdefghijk", fetcher=fake_fetcher)

    assert result.status == "fetched"
    assert result.video_id == "abcdefghijk"
    assert result.language == "en"
    assert "[00:12] We stopped debating prompts." in result.excerpt
    assert result.segments_sample[1]["timestamp"] == "00:15"
    metadata = result.to_metadata()
    assert metadata["transcript_status"] == "fetched"
    assert metadata["transcript_excerpt"] == result.excerpt


def test_collect_youtube_feed_attempts_transcript_and_replaces_excerpt(monkeypatch):
    def fake_collect_rss(source: SourceConfig, run_date: str) -> CollectorResult:
        return CollectorResult(source.id, [_youtube_item()])

    def fake_fetcher(video_id: str, languages: tuple[str, ...]):
        return FakeTranscript([{"text": "Transcript evidence from the interview.", "start": 3.0, "duration": 4.0}])

    monkeypatch.setattr(youtube, "collect_rss", fake_collect_rss)
    source = SourceConfig(
        id="youtube_yc",
        type="youtube",
        name="YC",
        url="https://www.youtube.com/feeds/videos.xml?channel_id=UCexample",
        metadata={"section": "video", "tags": ["YouTube"]},
    )

    result = youtube.collect_youtube_feed(source, "2026-05-19", transcript_fetcher=fake_fetcher)

    item = result.items[0]
    assert item.metadata["transcript_status"] == "fetched"
    assert item.metadata["transcript_language"] == "en"
    assert item.raw_excerpt.startswith("[00:03] Transcript evidence from the interview.")
    assert "Transcript evidence from the interview." in item.content_text
    assert not result.degraded


def test_report_renders_visible_transcript_status_for_unavailable_video():
    item = _youtube_item()
    item.metadata.update(
        {
            "transcript_status": "unavailable",
            "transcript_language": "",
            "transcript_excerpt": "",
            "transcript_note": "transcript_status=unavailable; low-confidence feed fallback",
        }
    )
    report = build_report_from_items(
        "2026-05-19",
        [item],
        {item.id: DedupDecision(item_id=item.id, status="new", reason_code="no_match")},
        [SectionConfig("video", "视频")],
    )

    html = render_report_html(report)

    assert "transcript_status=unavailable" in html
    assert "low-confidence feed fallback" in html
