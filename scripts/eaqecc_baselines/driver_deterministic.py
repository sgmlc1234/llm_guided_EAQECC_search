"""Reproducible variant of the campaign driver: an evaluation budget.

The campaign driver gives each candidate program a wall-clock budget, and
the programs spend it in `while time.time() - t0 < TIME_BUDGET_S` loops. A
seeded RNG inside a wall-clock loop is not reproducible: a faster machine
completes more iterations, draws more random numbers, and returns a
different answer for the same seed. Nothing downstream can fix that.

This driver removes the machine from the loop by replacing the `time`
module the candidate program sees with a virtual clock that advances only
when the exact evaluator runs. With `MAX_EVALS = N` the clock is scaled so
that the program's own budget check expires after exactly N calls to
E.evaluate, whatever the hardware does. Seed + N then determine the output
completely, and the programs themselves are untouched -- their control flow
still reads as a time budget.

Usage: driver_deterministic.py <code_file> <out_file>
Env: MAX_EVALS, TIME_BUDGET_S (virtual seconds), EVAL_RNG_SEED
Writes JSON {"candidates": [...], "error": ..., "elapsed": ..., "n_evals": ...}
"""

import json
import os
import sys
import time as _real_time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import helpers_eaqecc as E  # noqa: E402


class _VirtualTime:
    """Stands in for the `time` module inside the candidate program."""

    def __init__(self, dt: float):
        self.dt = dt
        self.now = 0.0

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    def tick(self) -> None:
        self.now += self.dt

    # perf_counter/monotonic are the other plausible clock reads
    perf_counter = time
    monotonic = time


class _CountingEvaluator:
    """Wraps the helpers module, advancing the clock once per evaluation."""

    def __init__(self, helpers, clock: _VirtualTime):
        self._helpers = helpers
        self._clock = clock
        self.n_evals = 0

    def __getattr__(self, name):
        return getattr(self._helpers, name)

    def evaluate(self, *args, **kwargs):
        self.n_evals += 1
        self._clock.tick()
        return self._helpers.evaluate(*args, **kwargs)


def main():
    code_file, out_file = sys.argv[1], sys.argv[2]
    code = Path(code_file).read_text()
    max_evals = int(os.environ.get("MAX_EVALS", "20000"))
    budget = float(os.environ.get("TIME_BUDGET_S", "240"))
    seed = int(os.environ.get("EVAL_RNG_SEED", "20260713"))

    clock = _VirtualTime(dt=budget / max_evals)
    counting = _CountingEvaluator(E, clock)

    result = {"candidates": [], "error": None, "elapsed": 0.0, "n_evals": 0}
    t0 = _real_time.time()
    # The candidate program does `import time`; give it the virtual clock.
    saved_time = sys.modules.get("time")
    sys.modules["time"] = clock
    try:
        ns = {
            "E": counting,
            "TARGETS": E.TARGETS,
            "np": np,
            "rng": np.random.default_rng(seed),
            "TIME_BUDGET_S": budget,
            "time": clock,
        }
        exec(code, ns)
        search = ns.get("search")
        if not callable(search):
            raise ValueError("program does not define a callable search()")
        cands = search() or []
        for item in list(cands)[:16]:
            tid, gens = item
            tid = int(tid)
            if 0 <= tid < len(E.TARGETS):
                result["candidates"].append(
                    [tid, [int(g) for g in list(gens)[:40]]])
    except Exception as e:  # noqa: BLE001
        result["error"] = f"{type(e).__name__}: {e}"
    finally:
        if saved_time is not None:
            sys.modules["time"] = saved_time
        else:
            del sys.modules["time"]
    result["elapsed"] = _real_time.time() - t0
    result["n_evals"] = counting.n_evals
    Path(out_file).write_text(json.dumps(result))


if __name__ == "__main__":
    main()
