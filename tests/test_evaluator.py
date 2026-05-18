import pytest

from daily_brief.evaluator import evaluate_report, run_evaluation_loops
from daily_brief.sample_data import build_sample_report


REQUIRED_DIMENSIONS = {
    "visual_quality",
    "signal_to_noise",
    "reading_experience",
    "timeliness",
    "evidence_traceability",
    "dedup_association",
    "mobile_experience",
}


def test_evaluator_generates_non_decreasing_scorecards():
    report = build_sample_report("2026-05-18")

    scorecards = run_evaluation_loops(report, loops=7)

    assert len(scorecards) == 7
    previous_score = 0.0
    for card in scorecards:
        assert set(card.dimension_scores) >= REQUIRED_DIMENSIONS
        assert card.improvement_suggestions
        assert card.revision_notes
        assert card.overall_score >= previous_score or card.non_decrease_reason
        previous_score = card.overall_score


def test_evaluator_loop_bounds():
    report = build_sample_report("2026-05-18")

    with pytest.raises(ValueError):
        run_evaluation_loops(report, loops=4)
    with pytest.raises(ValueError):
        run_evaluation_loops(report, loops=11)


def test_single_evaluation_has_required_labels():
    report = build_sample_report("2026-05-18")
    card = evaluate_report(report, round_number=1, previous_score=None)

    assert card.dimension_labels["visual_quality"] == "美观"
    assert card.dimension_labels["signal_to_noise"] == "信噪比"
    assert card.dimension_labels["reading_experience"] == "阅读体验"
    assert card.dimension_labels["timeliness"] == "时效性"
    assert card.dimension_labels["evidence_traceability"] == "证据可追溯"
    assert card.dimension_labels["dedup_association"] == "去重/关联"
    assert card.dimension_labels["mobile_experience"] == "移动端"
