"""Tests for the historical cross-judge report."""

from __future__ import annotations

import json
import sys
from types import ModuleType

import pytest

from scripts import cross_judge


def test_primary_raw_score_uses_judge_score_not_adjusted_accuracy():
    rec = {"score": {"judge_score": 80.0, "accuracy": 0.4}}
    assert cross_judge._primary_raw_score(rec) == 80.0


def test_primary_raw_score_returns_none_when_missing():
    assert cross_judge._primary_raw_score({"score": {"accuracy": 0.4}}) is None


@pytest.mark.asyncio
async def test_report_counts_missing_primary_scores_without_grading_or_appending_them(
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

    async def grade_once(client, model, question, reference, candidate):
        return 60

    monkeypatch.setattr(cross_judge, "_grade_one", grade_once)

    await cross_judge.main()

    report = json.loads(report_path.read_text())
    strategy = report["per_strategy"]["test_strategy"]
    assert report["score_semantics"]["primary"] == "raw_judge_score_0_100"
    assert strategy["ungraded_count"] == 1
    assert strategy["graded_count"] == 1
    assert strategy["opus_mean"] == 80.0
    assert report["per_question"] == [
        {
            "question_id": "graded",
            "strategy": "test_strategy",
            "seed": 7,
            "primary_raw_score": 80.0,
            "second_raw_score": 60.0,
            "disagreement": 20.0,
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
    assert report["per_question"] == []
