"""Subprocess driver: executes one candidate EAQECC program in isolation.

Usage: driver.py <code_file> <out_file>
Env: TIME_BUDGET_S, EVAL_RNG_SEED
Writes JSON {"candidates": [[tid, [gens...]], ...], "error": ..., "elapsed": ...}
"""

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import helpers_eaqecc as E  # noqa: E402


def main():
    code_file, out_file = sys.argv[1], sys.argv[2]
    code = Path(code_file).read_text()
    budget = float(os.environ.get("TIME_BUDGET_S", "240"))
    seed = int(os.environ.get("EVAL_RNG_SEED", "20260713"))

    result = {"candidates": [], "error": None, "elapsed": 0.0}
    t0 = time.time()
    try:
        ns = {
            "E": E,
            "TARGETS": E.TARGETS,
            "np": np,
            "rng": np.random.default_rng(seed),
            "TIME_BUDGET_S": budget,
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
    result["elapsed"] = time.time() - t0
    Path(out_file).write_text(json.dumps(result))


if __name__ == "__main__":
    main()
