"""Tests for the historical cross-judge report."""

from __future__ import annotations

import json
import sys
from types import ModuleType

import pytest

from scripts import cross_judge


def test_primary_raw_score_uses_judge_score_not_adjusted_accuracy():
    rec = {"score": {"judge_score": 80.0, "accuracy": 0.4}}
    assert cross_judge._primary_raw_score(rec) == pytest.approx(80.0)


def test_primary_raw_score_returns_none_when_missing():
    assert cross_judge._primary_raw_score({"score": {"accuracy": 0.4}}) is None


async def _run_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    *,
    records: list[dict],
    questions: dict[str, dict],
    grade_one,
) -> dict:
    report_path = tmp_path / "cross_judge_report.json"
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(sys, "argv", ["cross_judge.py", "--top-k", "1"])
    monkeypatch.setitem(sys.modules, "openai", ModuleType("openai"))
    sys.modules["openai"].AsyncOpenAI = lambda: object()
    monkeypatch.setattr(cross_judge, "REPORT", report_path)
    monkeypatch.setattr(cross_judge, "_load_top_strategies", lambda top_k: ["test_strategy"])
    monkeypatch.setattr(cross_judge, "_load_seed_records", lambda strategy: records)
    monkeypatch.setattr(cross_judge, "_load_questions", lambda: questions)
    monkeypatch.setattr(cross_judge, "_grade_one", grade_one)

    await cross_judge.main()

    return json.loads(report_path.read_text())


@pytest.mark.asyncio
async def test_report_counts_missing_primary_scores_and_records_identity(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    """Missing primary grades are reported, never converted to zero-valued grades."""

    report_path = tmp_path / "cross_judge_report.json"
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(sys, "argv", ["cross_judge.py", "--top-k", "1"])
    monkeypatch.setitem(sys.modules, "openai", ModuleType("openai"))
    sys.modules["openai"].AsyncOpenAI = lambda: object()
    monkeypatch.setattr(cross_judge, "REPORT", report_path)
    monkeypatch.setattr(cross_judge, "_load_top_strategies", lambda top_k: ["test_strategy"])
    monkeypatch.setattr(
        cross_judge,
        "_load_seed_records",
        lambda strategy: [
            {
                "question_id": "missing-primary",
                "seed": 7,
                "answer": "candidate",
                "score": {"accuracy": 0.4},
            },
            {
                "question_id": "graded",
                "seed": 7,
                "answer": "candidate",
                "score": {"judge_score": 80.0, "accuracy": 0.4},
            },
        ],
    )
    monkeypatch.setattr(
        cross_judge,
        "_load_questions",
        lambda: {
            "missing-primary": {"question": "question", "reference_answer": "reference"},
            "graded": {"question": "question", "reference_answer": "reference"},
        },
    )

    provider_calls = []

    async def grade_once(client, model, question, reference, candidate):
        provider_calls.append((model, question, reference, candidate))
        return 60

    monkeypatch.setattr(cross_judge, "_grade_one", grade_once)

    await cross_judge.main()

    report = json.loads(report_path.read_text())
    strategy = report["per_strategy"]["test_strategy"]
    assert report["score_semantics"]["primary"] == "raw_judge_score_0_100"
    assert report["grade_counts"] == {"graded": 1, "ungraded": 1}
    assert strategy["ungraded_count"] == 1
    assert strategy["graded_count"] == 1
    assert strategy["opus_mean"] == pytest.approx(80.0)
    assert report["per_question"] == [
        {
            "question_id": "missing-primary",
            "strategy": "test_strategy",
            "seed": 7,
            "status": "ungraded",
            "reason": "missing_primary_raw_score",
        },
        {
            "question_id": "graded",
            "strategy": "test_strategy",
            "seed": 7,
            "primary_raw_score": 80.0,
            "second_raw_score": 60.0,
            "disagreement": 20.0,
        },
    ]
    assert provider_calls == [("gpt-4o", "question", "reference", "candidate")]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("record", "questions", "reason"),
    [
        (
            {
                "question_id": "missing-question",
                "seed": 11,
                "answer": "candidate",
                "score": {"judge_score": 80.0},
            },
            {},
            "missing_question_metadata",
        ),
        (
            {
                "question_id": "blank-question",
                "seed": 11,
                "answer": "candidate",
                "score": {"judge_score": 80.0},
            },
            {"blank-question": {"question": " ", "reference_answer": "reference"}},
            "blank_question",
        ),
        (
            {
                "question_id": "blank-reference",
                "seed": 11,
                "answer": "candidate",
                "score": {"judge_score": 80.0},
            },
            {"blank-reference": {"question": "question", "reference_answer": " "}},
            "blank_reference_answer",
        ),
        (
            {
                "question_id": "blank-candidate",
                "seed": 11,
                "answer": " ",
                "score": {"judge_score": 80.0},
            },
            {"blank-candidate": {"question": "question", "reference_answer": "reference"}},
            "blank_candidate_answer",
        ),
    ],
)
async def test_report_counts_missing_local_grade_data_without_calling_provider(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    record,
    questions,
    reason,
):
    async def fail_if_called(client, model, question, reference, candidate):
        raise AssertionError("locally ungradable records must not call the provider")

    report = await _run_report(
        monkeypatch,
        tmp_path,
        records=[record],
        questions=questions,
        grade_one=fail_if_called,
    )

    assert report["grade_counts"] == {"graded": 0, "ungraded": 1}
    assert report["per_strategy"]["test_strategy"] == {
        "n_grades": 0,
        "graded_count": 0,
        "ungraded_count": 1,
    }
    assert report["per_question"] == [
        {
            "question_id": record["question_id"],
            "strategy": "test_strategy",
            "seed": 11,
            "status": "ungraded",
            "reason": reason,
        }
    ]


@pytest.mark.asyncio
async def test_report_counts_secondary_judge_exception_as_ungraded(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    record = {
        "question_id": "provider-error",
        "seed": 13,
        "answer": "candidate",
        "score": {"judge_score": 80.0},
    }

    async def raise_provider_error(client, model, question, reference, candidate):
        raise RuntimeError("provider failed")

    report = await _run_report(
        monkeypatch,
        tmp_path,
        records=[record],
        questions={"provider-error": {"question": "question", "reference_answer": "reference"}},
        grade_one=raise_provider_error,
    )

    assert report["grade_counts"] == {"graded": 0, "ungraded": 1}
    assert report["per_strategy"]["test_strategy"]["ungraded_count"] == 1
    assert report["per_question"] == [
        {
            "question_id": "provider-error",
            "strategy": "test_strategy",
            "seed": 13,
            "status": "ungraded",
            "reason": "secondary_judge_exception",
        }
    ]


@pytest.mark.asyncio
async def test_report_keeps_all_missing_strategy_out_of_means_and_ranks(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    """An all-ungraded strategy remains visible without a fabricated mean or rank."""

    report_path = tmp_path / "cross_judge_report.json"
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(sys, "argv", ["cross_judge.py", "--top-k", "1"])
    monkeypatch.setitem(sys.modules, "openai", ModuleType("openai"))
    sys.modules["openai"].AsyncOpenAI = lambda: object()
    monkeypatch.setattr(cross_judge, "REPORT", report_path)
    monkeypatch.setattr(cross_judge, "_load_top_strategies", lambda top_k: ["all_missing"])
    monkeypatch.setattr(
        cross_judge,
        "_load_seed_records",
        lambda strategy: [
            {
                "question_id": "missing-primary",
                "seed": 7,
                "answer": "candidate",
                "score": {"accuracy": 0.4},
            }
        ],
    )
    monkeypatch.setattr(cross_judge, "_load_questions", lambda: {})

    async def grade_once(client, model, question, reference, candidate):
        raise AssertionError("all-ungraded records must not call the provider")

    monkeypatch.setattr(cross_judge, "_grade_one", grade_once)

    await cross_judge.main()

    report = json.loads(report_path.read_text())
    assert report["per_strategy"]["all_missing"] == {
        "n_grades": 0,
        "graded_count": 0,
        "ungraded_count": 1,
    }
    assert report["opus_rank"] == []
    assert report["gpt-4o_rank"] == []
    assert report["grade_counts"] == {"graded": 0, "ungraded": 1}
    assert report["per_question"] == [
        {
            "question_id": "missing-primary",
            "strategy": "all_missing",
            "seed": 7,
            "status": "ungraded",
            "reason": "missing_primary_raw_score",
        }
    ]
