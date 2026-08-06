"""Tests for the Failure Lab classification and its joined evidence."""

from __future__ import annotations

import pytest

from memory_arena.evidence.failures import (
    JUDGE_FAIL_THRESHOLD,
    classify_failure,
    join_question_evidence,
)


def _record(session_hit=1.0, turn_hit=1.0, judge=90.0):
    return {
        "question_id": "q1",
        "ir": {"session_hit_at_k": session_hit, "turn_hit_at_k": turn_hit},
        "score": {"judge_score": judge},
    }


class TestClassifyFailure:
    def test_a_good_answer_from_a_correct_session_is_not_a_failure(self):
        assert classify_failure(_record(judge=90.0)) == "answer_ok"

    def test_a_missed_session_is_a_retrieval_miss(self):
        assert classify_failure(_record(session_hit=0.0, judge=5.0)) == "retrieval_miss"

    def test_a_missed_session_with_a_good_answer_is_still_a_retrieval_miss(self):
        """Retrieval is measured on retrieval, not on whether the model guessed."""
        assert classify_failure(_record(session_hit=0.0, judge=95.0)) == "retrieval_miss"

    def test_a_correct_session_with_a_failing_grade_is_a_wrong_answer(self):
        assert classify_failure(_record(judge=5.0)) == "correct_session_wrong_answer"

    def test_the_threshold_is_inclusive(self):
        at = classify_failure(_record(judge=JUDGE_FAIL_THRESHOLD))
        above = classify_failure(_record(judge=JUDGE_FAIL_THRESHOLD + 0.1))
        assert at == "correct_session_wrong_answer"
        assert above == "answer_ok"

    @pytest.mark.parametrize("score", [None, {}, {"judge_score": None}, {"judge_score": "NaN"}])
    def test_a_record_with_no_usable_grade_is_ungraded(self, score):
        rec = _record()
        rec["score"] = score
        assert classify_failure(rec) == "ungraded"

    def test_a_record_with_no_ir_is_unmeasured(self):
        assert classify_failure({"score": {"judge_score": 5.0}}) == "retrieval_unmeasured"

    def test_an_errored_record_is_an_error(self):
        rec = _record(judge=0.0)
        rec["error"] = True
        assert classify_failure(rec) == "error"


class TestJoinQuestionEvidence:
    def test_the_join_adds_the_question_the_expected_answer_and_the_gold_sessions(self):
        records = [
            {
                "question_id": "q1",
                "ir": {"session_hit_at_k": 1.0, "turn_hit_at_k": 0.0},
                "score": {"judge_score": 5.0},
            }
        ]
        questions = {
            "q1": {
                "question": "How many weeks ago?",
                "answer": "4",
                "supporting_session_ids": ["s1"],
            }
        }

        joined = join_question_evidence(records, questions)

        assert joined[0]["question"] == "How many weeks ago?"
        assert joined[0]["expected_answer"] == "4"
        assert joined[0]["gold_session_ids"] == ["s1"]
        assert joined[0]["failure_class"] == "correct_session_wrong_answer"
        assert joined[0]["turn_hit"] is False

    def test_the_join_never_invents_evidence_for_an_unknown_question(self):
        records = [
            {"question_id": "ghost", "ir": {"session_hit_at_k": 1.0}, "score": {"judge_score": 5.0}}
        ]

        joined = join_question_evidence(records, {})

        assert joined[0]["question"] is None
        assert joined[0]["expected_answer"] is None
        assert joined[0]["gold_session_ids"] == []

    def test_the_join_keeps_the_original_record_fields(self):
        records = [{"question_id": "q1", "answer": "generated", "cost_usd": 0.5, "score": {}}]

        joined = join_question_evidence(records, {})

        assert joined[0]["answer"] == "generated"
        assert joined[0]["cost_usd"] == pytest.approx(0.5)
