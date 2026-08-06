"""Tests for the historical cross-judge report."""

from __future__ import annotations

import json
import sys
from types import ModuleType, SimpleNamespace

import pytest

from scripts import cross_judge


def test_primary_raw_score_uses_judge_score_not_adjusted_accuracy():
    rec = {"score": {"judge_score": 80.0, "accuracy": 0.4}}
    assert cross_judge._primary_raw_score(rec) == pytest.approx(80.0)


def test_primary_raw_score_returns_none_when_missing():
    assert cross_judge._primary_raw_score({"score": {"accuracy": 0.4}}) is None


@pytest.mark.parametrize(
    ("judge_score", "expected"),
    [
        (0, 0.0),
        (100, 100.0),
        ("80", 80.0),
        (79.5, 79.5),
        (None, None),
        ("NaN", None),
        (float("nan"), None),
        (float("inf"), None),
        (float("-inf"), None),
        ("abc", None),
        ("", None),
        (-1, None),
        (101, None),
        ([80], None),
        ({"value": 80}, None),
    ],
)
def test_primary_raw_score_rejects_a_value_outside_the_grading_range(judge_score, expected):
    """A stored grade that is not a finite number from 0 through 100 is not a grade."""

    assert cross_judge._primary_raw_score({"score": {"judge_score": judge_score}}) == expected


def test_primary_failure_reason_separates_an_absent_grade_from_a_broken_one():
    assert cross_judge._primary_failure_reason({"score": {}}) == "missing_primary_raw_score"
    assert (
        cross_judge._primary_failure_reason({"score": {"judge_score": "NaN"}})
        == "invalid_primary_raw_score"
    )


def test_spearman_reports_no_correlation_when_evidence_is_too_thin():
    """Fewer than two ranked strategies give an undefined correlation, not zero."""

    assert cross_judge._spearman([], []) is None
    assert cross_judge._spearman([0], [0]) is None
    assert cross_judge._spearman([0, 1], [0, 1]) == pytest.approx(1.0)


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


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("85", 85),
        ("  85  ", 85),
        ("0", 0),
        ("100", 100),
        ("085", 85),
        ("", None),
        ("   ", None),
        (None, None),
        ("N/A", None),
        ("I would say 85 out of 100", None),
        ("85/100", None),
        ("Score: 85", None),
        ("85.5", None),
        ("-5", None),
        ("101", None),
        ("150", None),
        ("1e2", None),
    ],
)
def test_parse_secondary_score_accepts_only_a_bare_integer_0_to_100(raw, expected):
    """Only a bare integer inside the grading range counts as a grade."""

    assert cross_judge._parse_secondary_score(raw) == expected


class _FakeCompletions:
    def __init__(self, content):
        self._content = content
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        message = SimpleNamespace(content=self._content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class _FakeClient:
    def __init__(self, content):
        self.completions = _FakeCompletions(content)
        self.chat = SimpleNamespace(completions=self.completions)


@pytest.mark.asyncio
@pytest.mark.parametrize("content", ["", "N/A", "I would say 85 out of 100", "150", None])
async def test_grade_one_returns_none_for_an_unusable_response(content):
    """An unusable judge response never becomes a numeric grade."""

    client = _FakeClient(content)

    assert await cross_judge._grade_one(client, "gpt-4o", "q", "ref", "cand") is None


@pytest.mark.asyncio
async def test_grade_one_returns_the_integer_for_a_valid_response():
    client = _FakeClient(" 72 ")

    assert await cross_judge._grade_one(client, "gpt-4o", "q", "ref", "cand") == 72
    assert client.completions.calls[0]["model"] == "gpt-4o"


@pytest.mark.asyncio
async def test_report_counts_an_unparseable_secondary_response_as_ungraded(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    """An unparseable secondary response is ungraded, never a zero grade."""

    record = {
        "question_id": "unparseable-secondary",
        "seed": 17,
        "answer": "candidate",
        "score": {"judge_score": 80.0},
    }

    async def return_unparseable(client, model, question, reference, candidate):
        return None

    report = await _run_report(
        monkeypatch,
        tmp_path,
        records=[record],
        questions={
            "unparseable-secondary": {"question": "question", "reference_answer": "reference"}
        },
        grade_one=return_unparseable,
    )

    assert report["grade_counts"] == {"graded": 0, "ungraded": 1}
    assert report["per_strategy"]["test_strategy"] == {
        "n_grades": 0,
        "graded_count": 0,
        "ungraded_count": 1,
    }
    assert report["per_question"] == [
        {
            "question_id": "unparseable-secondary",
            "strategy": "test_strategy",
            "seed": 17,
            "status": "ungraded",
            "reason": "unparseable_secondary_judge_response",
        }
    ]
    assert report["opus_rank"] == []
    assert report["spearman_rank_correlation"] is None


@pytest.mark.asyncio
async def test_report_keeps_a_valid_zero_grade(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """A judge that really answers zero still produces a graded record."""

    record = {
        "question_id": "real-zero",
        "seed": 19,
        "answer": "candidate",
        "score": {"judge_score": 80.0},
    }

    async def return_zero(client, model, question, reference, candidate):
        return 0

    report = await _run_report(
        monkeypatch,
        tmp_path,
        records=[record],
        questions={"real-zero": {"question": "question", "reference_answer": "reference"}},
        grade_one=return_zero,
    )

    assert report["grade_counts"] == {"graded": 1, "ungraded": 0}
    assert report["per_question"] == [
        {
            "question_id": "real-zero",
            "strategy": "test_strategy",
            "seed": 19,
            "primary_raw_score": 80.0,
            "second_raw_score": 0.0,
            "disagreement": 80.0,
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
    assert report["spearman_rank_correlation"] is None
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
