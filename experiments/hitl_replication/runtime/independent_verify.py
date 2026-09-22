"""Recheck two witnesses without importing the search evaluator."""

from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rref(rows, width):
    matrix = [row[:] for row in rows]
    pivots = []
    for col in range(width):
        pivot = next((i for i in range(len(pivots), len(matrix)) if matrix[i][col]), None)
        if pivot is None:
            continue
        pos = len(pivots)
        matrix[pos], matrix[pivot] = matrix[pivot], matrix[pos]
        for i in range(len(matrix)):
            if i != pos and matrix[i][col]:
                matrix[i] = [a ^ b for a, b in zip(matrix[i], matrix[pos])]
        pivots.append(col)
    return matrix[:len(pivots)], pivots


def symplectic(a, b):
    return sum(a[i] * b[i + 1] + a[i + 1] * b[i] for i in range(0, len(a), 2)) % 2


def verify(path, expected):
    data = json.loads(path.read_text())
    target = data["target"]
    declared = [target["n"], target["k"], target["d"], target["c"]]
    if declared != expected:
        raise ValueError("witness metadata disagrees with the refinement claim")
    n = target["n"]
    if any(type(g) is not int or not 0 <= g < (1 << (2 * n)) for g in data["generators"]):
        raise ValueError("generator is outside the declared binary space")
    generators = [[(g >> i) & 1 for i in range(2 * n)] for g in data["generators"]]
    _, spivots = rref(generators, 2 * n)
    if len(spivots) != n - expected[1] + expected[3]:
        raise ValueError("generator rank disagrees with the claimed signature")
    constraints = [[row[i ^ 1] for i in range(2 * n)] for row in generators]
    reduced, pivots = rref(constraints, 2 * n)
    dual = []
    for free in sorted(set(range(2 * n)) - set(pivots)):
        vector = [0] * (2 * n)
        vector[free] = 1
        for row, pivot in zip(reduced, pivots):
            vector[pivot] = row[free]
        dual.append(vector)
    assert all(symplectic(v, g) == 0 for v in dual for g in generators)
    radical_count, weights = 0, Counter()
    for coefficients in itertools.product((0, 1), repeat=len(dual)):
        vector = [sum(a * row[i] for a, row in zip(coefficients, dual)) % 2
                  for i in range(2 * n)]
        if all(symplectic(vector, row) == 0 for row in dual):
            radical_count += 1
        else:
            weights[sum(bool(vector[i] or vector[i + 1]) for i in range(0, 2 * n, 2))] += 1
    iso = radical_count.bit_length() - 1
    assert radical_count == 2 ** iso
    s = len(spivots)
    assert (s - iso) % 2 == 0
    c = (s - iso) // 2
    observed = [n, n - s + c, min(weights), c]
    assert observed == expected, (observed, expected)
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "parameters_n_k_d_c": observed, "rank_S": s, "dim_dual": len(dual),
            "radical_dimension": iso, "logical_weight_distribution": dict(weights),
            "status": "PASS"}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args()
    claims = json.loads((args.root / "artifacts/solver_refinement/claims.json").read_text())
    results = [verify(args.root / "artifacts" / c["witness"],
                      [c["n"], c["k"], c["d"], c["c"]]) for c in claims]
    print(json.dumps(results, indent=2))
