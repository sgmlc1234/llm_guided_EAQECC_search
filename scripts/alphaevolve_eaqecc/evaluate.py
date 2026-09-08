"""Evaluator for the AlphaEvolve EAQECC multi-target campaign.

Each candidate program proposes (target_index, stabilizer generators)
pairs; every proposal is exactly re-verified. Closing any target (matching
(n, k, c) with zero offending logicals) is a new best-known EAQECC —
archived as SOLUTION_n{n}_k{k}_c{c}.json and scored +1e6.
"""

import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from alpha_evolve.models import (
    AlphaEvolveEvaluationInsight,
    AlphaEvolveEvaluationInsights,
    AlphaEvolveEvaluationScore,
    AlphaEvolveEvaluationScores,
    AlphaEvolveProgramEvaluation,
)

logger = logging.getLogger(__name__)

HERE = Path(__file__).resolve().parent
SOL_EVOLVE = HERE.parents[1]  # repository root
sys.path.insert(0, str(HERE))
import helpers_eaqecc as E  # noqa: E402

MAIN_METRIC = "eaqecc_score"
TIME_BUDGET_S = float(os.getenv("SEARCH_BUDGET_S", "240"))
OUT_DIR = Path(os.getenv(
    "HARVEST_DIR", SOL_EVOLVE / "artifacts" / "witnesses" / "q2"))
OUT_DIR.mkdir(parents=True, exist_ok=True)
RNG_SEED = int(os.getenv("EVAL_RNG_SEED", "20260713"))
PYTHON = sys.executable


def _load_initial_program():
    return (HERE / "program.py").read_text()


INITIAL_PROGRAM_CODE = _load_initial_program()

_closed = set()  # target indices closed in this run


def eaqecc_evaluation(program_candidate) -> dict:
    code = program_candidate["content"]["files"][0]["content"]
    score_value = -1e9
    n_closed_new = 0
    best_offending = None
    insights = []

    with tempfile.TemporaryDirectory() as tmp:
        code_f = Path(tmp) / "candidate.py"
        out_f = Path(tmp) / "result.json"
        code_f.write_text(code)
        env = dict(os.environ,
                   TIME_BUDGET_S=str(TIME_BUDGET_S),
                   EVAL_RNG_SEED=str(RNG_SEED))
        try:
            subprocess.run(
                [PYTHON, str(HERE / "driver.py"), str(code_f), str(out_f)],
                env=env, timeout=TIME_BUDGET_S * 1.5 + 60, check=False,
                capture_output=True)
        except subprocess.TimeoutExpired:
            insights.append(AlphaEvolveEvaluationInsight(
                label="Timeout",
                text="search() exceeded the hard limit; respect "
                     "TIME_BUDGET_S inside your loops."))
            out_f = None
        result = json.loads(out_f.read_text()) if out_f and out_f.exists() else None

    if result is None:
        pass
    elif result["error"]:
        insights.append(AlphaEvolveEvaluationInsight(
            label="Runtime Error",
            text=f"The program failed during execution: {result['error']}"))
    elif not result["candidates"]:
        insights.append(AlphaEvolveEvaluationInsight(
            label="No candidates",
            text=f"search() returned nothing in {result['elapsed']:.0f}s."))
    else:
        insights.append(AlphaEvolveEvaluationInsight(
            label="Search",
            text=f"{len(result['candidates'])} proposals in "
                 f"{result['elapsed']:.0f}s (budget {TIME_BUDGET_S:.0f}s)."))
        for tid, gens in result["candidates"]:
            t = E.TARGETS[tid]
            r = E.evaluate(t["n"], gens, t["d"])
            if "error" in r:
                insights.append(AlphaEvolveEvaluationInsight(
                    label="Invalid",
                    text=f"target {tid} [[{t['n']},{t['k']};{t['c']}]]: "
                         f"{r['error']}"))
                continue
            sig_ok = (r["c"] == t["c"] and r["k"] == t["k"])
            if not sig_ok:
                cand_score = -5000.0 * abs(r["c"] - t["c"]) - 1000.0
                insights.append(AlphaEvolveEvaluationInsight(
                    label="Signature mismatch",
                    text=f"target {tid} needs (k={t['k']}, c={t['c']}), got "
                         f"(k={r['k']}, c={r['c']})."))
            else:
                off = r["offending"]
                best_offending = off if best_offending is None else min(
                    best_offending, off)
                cand_score = 1000.0 - off
                if off == 0:
                    path = OUT_DIR / (
                        f"SOLUTION_n{t['n']}_k{t['k']}_c{t['c']}_d{t['d']}.json")
                    is_new = tid not in _closed and not path.exists()
                    if is_new:
                        path.write_text(json.dumps(
                            {"target": t,
                             "generators": [int(g) for g in gens],
                             "verified": r}))
                        n_closed_new += 1
                        cand_score += 1e6
                        logger.critical(
                            "SOLUTION FOUND: [[%d,%d,%d;%d]] closes a "
                            "codetables gap! %s",
                            t["n"], t["k"], t["d"], t["c"], path)
                    _closed.add(tid)
                    insights.append(AlphaEvolveEvaluationInsight(
                        label="TARGET CLOSED" + ("" if is_new else " (already closed earlier — no jackpot; hunt the remaining open targets)"),
                        text=f"[[{t['n']},{t['k']},{t['d']};{t['c']}]] "
                             f"achieved — new best-known EAQECC."))
                else:
                    insights.append(AlphaEvolveEvaluationInsight(
                        label="Progress",
                        text=f"target {tid} [[{t['n']},{t['k']},{t['d']};"
                             f"{t['c']}]]: signature OK, d={r['d']}, "
                             f"{off} logical operators below d={t['d']} "
                             f"remain (0 closes it)."))
            score_value = max(score_value, cand_score)

    scores = [
        AlphaEvolveEvaluationScore(metric=MAIN_METRIC, score=float(score_value)),
        AlphaEvolveEvaluationScore(metric="targets_closed",
                                   score=float(len(_closed))),
        AlphaEvolveEvaluationScore(
            metric="best_offending",
            score=float(best_offending if best_offending is not None else 1e9)),
    ]
    return AlphaEvolveProgramEvaluation(
        scores=AlphaEvolveEvaluationScores(scores=scores),
        insights=AlphaEvolveEvaluationInsights(insights=insights),
    ).model_dump()
