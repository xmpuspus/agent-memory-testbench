"""Cross-judge validation: re-grade existing answers with a second judge LLM.

Reads the per-seed `recall_records` from `results/longmemeval-s_<strategy>_seed*.json`
for the top-K strategies, re-grades each (answer, reference) pair through a
second judge model (default `gpt-4o`), and writes a rank-correlation report
to `results/cross_judge_report.json`.

Why: the headline accuracy numbers in the README are graded by Opus 4.7.
"Anthropic-on-Anthropic" is a fair criticism. Spearman rank correlation with
GPT-4o tells the reader whether the leaderboard order is stable across
judges or driven by Opus's preferences.

Cost: ~$2 across the top-5 strategies × 16 questions × 3 seeds = 240 grades.

Usage:
    OPENAI_API_KEY=sk-... python scripts/cross_judge.py
    OPENAI_API_KEY=sk-... python scripts/cross_judge.py --top-k 8 --judge gpt-4o
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results"
QUESTIONS_FILE = REPO_ROOT / "datasets" / "longmemeval-s" / "processed" / "questions.jsonl"
REPORT = RESULTS_DIR / "cross_judge_report.json"


def _load_questions() -> dict[str, dict]:
    """question_id -> {question, reference_answer}"""
    out: dict[str, dict] = {}
    with open(QUESTIONS_FILE) as f:
        for line in f:
            d = json.loads(line)
            out[d["id"]] = {
                "question": d["question"],
                "reference_answer": d.get("ground_truth", {}).get("answer", ""),
            }
    return out


JUDGE_PROMPT = """You are grading an AI assistant's answer to a question about a
long-running chat conversation. Compare the candidate answer against the
reference answer. Output a single integer 0..100, no other text.

100 = factually equivalent to reference; 80 = mostly right with minor omission;
50 = partially right but missing a key fact; 20 = wrong but related; 0 = wrong.

Question: {question}

Reference answer: {reference}

Candidate answer: {candidate}

Score (0-100):"""


async def _grade_one(client, model: str, question: str, reference: str, candidate: str) -> int:
    prompt = JUDGE_PROMPT.format(question=question, reference=reference, candidate=candidate)
    resp = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8,
        temperature=0,
    )
    raw = resp.choices[0].message.content.strip()
    digits = "".join(c for c in raw if c.isdigit())[:3]
    if not digits:
        return 0
    return max(0, min(100, int(digits)))


def _load_top_strategies(top_k: int) -> list[str]:
    summaries = []
    for p in RESULTS_DIR.glob("longmemeval-s_*_summary.json"):
        d = json.loads(p.read_text())
        summaries.append((d["strategy"], d.get("accuracy", 0.0)))
    summaries.sort(key=lambda t: -t[1])
    return [s for s, _ in summaries[:top_k]]


def _load_seed_records(strategy: str) -> list[dict]:
    out = []
    for p in sorted(RESULTS_DIR.glob(f"longmemeval-s_{strategy}_seed*.json")):
        d = json.loads(p.read_text())
        seed = (d.get("metadata") or {}).get("seed")
        for rec in d.get("recall_records", []):
            out.append({**rec, "seed": rec.get("seed", seed)})
    return out


def _primary_raw_score(record: dict) -> float | None:
    score = record.get("score") or {}
    value = score.get("judge_score") if isinstance(score, dict) else None
    if value is None:
        return None
    return max(0.0, min(100.0, float(value)))


def _ungraded_identity(record: dict, strategy: str, reason: str) -> dict:
    return {
        "question_id": record.get("question_id", ""),
        "strategy": strategy,
        "seed": record.get("seed"),
        "status": "ungraded",
        "reason": reason,
    }


def _spearman(opus_rank: list[int], gpt_rank: list[int]) -> float:
    if len(opus_rank) != len(gpt_rank) or len(opus_rank) < 2:
        return 0.0
    n = len(opus_rank)
    diffs_sq = sum((o - g) ** 2 for o, g in zip(opus_rank, gpt_rank, strict=True))
    return 1 - (6 * diffs_sq) / (n * (n**2 - 1))


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-k", type=int, default=5, help="Top-N strategies to re-grade")
    ap.add_argument("--judge", default="gpt-4o", help="Cross-judge model")
    args = ap.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required for cross-judge.")

    try:
        from openai import AsyncOpenAI
    except ImportError as e:
        raise SystemExit("pip install openai>=2.0") from e
    client = AsyncOpenAI()

    strategies = _load_top_strategies(args.top_k)
    print(f"Cross-judging top {args.top_k}: {', '.join(strategies)}")

    questions = _load_questions()
    per_strategy: dict[str, dict] = {}
    per_question: list[dict] = []
    grade_counts = {"graded": 0, "ungraded": 0}
    for strategy in strategies:
        recs = _load_seed_records(strategy)
        if not recs:
            print(f"  [skip] {strategy}: no recall_records")
            continue
        opus_scores: list[float] = []
        gpt_scores: list[float] = []
        ungraded_count = 0
        for rec in recs:

            def record_ungraded(reason: str) -> None:
                nonlocal ungraded_count
                ungraded_count += 1
                grade_counts["ungraded"] += 1
                per_question.append(_ungraded_identity(rec, strategy, reason))

            opus = _primary_raw_score(rec)
            if opus is None:
                record_ungraded("missing_primary_raw_score")
                continue
            qid = rec.get("question_id", "")
            qmeta = questions.get(qid)
            if not qmeta:
                record_ungraded("missing_question_metadata")
                continue
            q = qmeta.get("question") or ""
            ref = qmeta.get("reference_answer") or ""
            cand = rec.get("answer") or ""
            if not q.strip():
                record_ungraded("blank_question")
                continue
            if not ref.strip():
                record_ungraded("blank_reference_answer")
                continue
            if not cand.strip():
                record_ungraded("blank_candidate_answer")
                continue
            try:
                gpt = await _grade_one(client, args.judge, q, ref, cand)
            except Exception as exc:
                print(f"  [warn] {strategy}: skipped record ({exc})")
                record_ungraded("secondary_judge_exception")
                continue
            opus_scores.append(opus)
            gpt_scores.append(float(gpt))
            grade_counts["graded"] += 1
            per_question.append(
                {
                    "question_id": qid,
                    "strategy": strategy,
                    "seed": rec.get("seed"),
                    "primary_raw_score": opus,
                    "second_raw_score": float(gpt),
                    "disagreement": abs(opus - float(gpt)),
                }
            )
        if not opus_scores:
            per_strategy[strategy] = {
                "n_grades": 0,
                "graded_count": 0,
                "ungraded_count": ungraded_count,
            }
            print(f"  [skip] {strategy}: no completed grades")
            continue
        per_strategy[strategy] = {
            "opus_mean": mean(opus_scores),
            "gpt4o_mean": mean(gpt_scores),
            "n_grades": len(opus_scores),
            "graded_count": len(opus_scores),
            "ungraded_count": ungraded_count,
        }
        print(
            f"  [done] {strategy}: opus={mean(opus_scores):.1f} "
            f"{args.judge}={mean(gpt_scores):.1f} (n={len(opus_scores)})"
        )

    # Spearman rank-correlation across the top strategies.
    ranked_strategies = {
        strategy: result for strategy, result in per_strategy.items() if result["graded_count"]
    }
    opus_rank = sorted(ranked_strategies, key=lambda s: -ranked_strategies[s]["opus_mean"])
    gpt_rank = sorted(ranked_strategies, key=lambda s: -ranked_strategies[s]["gpt4o_mean"])
    name_to_opus_rank = {s: i for i, s in enumerate(opus_rank)}
    name_to_gpt_rank = {s: i for i, s in enumerate(gpt_rank)}
    rho = _spearman(
        [name_to_opus_rank[s] for s in opus_rank],
        [name_to_gpt_rank[s] for s in opus_rank],
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(
            {
                "judges": ["claude-opus-4-7", args.judge],
                "score_semantics": {
                    "primary": "raw_judge_score_0_100",
                    "secondary": "raw_judge_score_0_100",
                },
                "grade_counts": grade_counts,
                "spearman_rank_correlation": rho,
                "opus_rank": opus_rank,
                f"{args.judge}_rank": gpt_rank,
                "per_strategy": per_strategy,
                "per_question": per_question,
            },
            indent=2,
        )
    )
    print(f"\nWrote {REPORT}")
    print(f"Spearman rank correlation (opus vs {args.judge}): {rho:+.3f}")


if __name__ == "__main__":
    asyncio.run(main())
