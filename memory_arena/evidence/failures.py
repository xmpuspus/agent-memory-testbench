"""Classify why one question failed, and join it to its question evidence.

The benchmark page says which architecture scored higher. It does not say why an
answer was wrong, so a reader cannot tell a retrieval problem from a reasoning
problem. That difference is the point of the testbench, and the stored records
already carry it: retrieval hits sit in `ir`, the grade sits in `score`, and the
question text and expected answer sit in the corpus question file.

Every field here comes from a stored record. Nothing is estimated.
"""

from __future__ import annotations

import math

# A judge score at or under this counts as a wrong answer. The judge prompt
# treats 50 as "partially right but missing a key fact", so 50 is a failure and
# anything above it is not. The number is named here, reported in the API
# response, and pinned by a test, so a reader can check the cut we used.
JUDGE_FAIL_THRESHOLD = 50.0

FAILURE_CLASSES = (
    "answer_ok",
    "correct_session_wrong_answer",
    "retrieval_miss",
    "retrieval_unmeasured",
    "ungraded",
    "error",
)


def _judge_score(record: dict) -> float | None:
    """The stored grade, or None when the record holds no usable grade."""
    score = record.get("score")
    if not isinstance(score, dict):
        return None
    value = score.get("judge_score")
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0.0 or number > 100.0:
        return None
    return number


def _hit(record: dict, key: str) -> bool | None:
    ir = record.get("ir")
    if not isinstance(ir, dict):
        return None
    value = ir.get(key)
    if value is None:
        return None
    try:
        return float(value) > 0.0
    except (TypeError, ValueError):
        return None


def classify_failure(record: dict) -> str:
    """Name the failure this record shows, using only what the record stores."""
    if record.get("error"):
        return "error"
    judge = _judge_score(record)
    if judge is None:
        return "ungraded"
    session_hit = _hit(record, "session_hit_at_k")
    if session_hit is None:
        return "retrieval_unmeasured"
    if not session_hit:
        # The strategy never retrieved a labelled supporting session. Whether
        # the model then guessed correctly says nothing about its memory.
        return "retrieval_miss"
    if judge <= JUDGE_FAIL_THRESHOLD:
        return "correct_session_wrong_answer"
    return "answer_ok"


def join_question_evidence(records: list[dict], questions: dict[str, dict]) -> list[dict]:
    """Attach question text, expected answer, gold sessions, and failure class.

    A question the corpus does not hold gets explicit nulls. The Failure Lab
    must never show an expected answer that no question file states.
    """
    joined: list[dict] = []
    for record in records:
        meta = questions.get(record.get("question_id", "")) or {}
        joined.append(
            {
                **record,
                "question": meta.get("question"),
                "expected_answer": meta.get("answer"),
                "gold_session_ids": list(meta.get("supporting_session_ids") or []),
                "failure_class": classify_failure(record),
                "judge_score": _judge_score(record),
                "session_hit": _hit(record, "session_hit_at_k"),
                "turn_hit": _hit(record, "turn_hit_at_k"),
            }
        )
    return joined


__all__ = [
    "FAILURE_CLASSES",
    "JUDGE_FAIL_THRESHOLD",
    "classify_failure",
    "join_question_evidence",
]
