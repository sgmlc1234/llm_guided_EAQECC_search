"""V4: no protected initialization; all final checks count against the quota."""

import argparse
import ast
import builtins
import contextlib
import hashlib
import io
import itertools
import json
from pathlib import Path
import resource
import time
from types import MappingProxyType

import numpy as np

from controlled_driver import IMPORTS, inspect_code
import controlled_helpers as H


PROTECTED_INITIALIZATION = False


class TargetSolved(BaseException):
    pass


class EvaluationBudgetExhausted(BaseException):
    pass


def inspect_target_code(code):
    tree = inspect_code(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(x.name == "time" for x in node.names):
            raise ValueError("use E.remaining, not a time budget")
        if isinstance(node, ast.ImportFrom) and node.module == "time":
            raise ValueError("use E.remaining, not a time budget")
    searches = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "search"]
    if len(searches) != 1 or len(searches[0].args.args) != 2:
        raise ValueError("define exactly one search(target, max_evals) function")
    for node in tree.body:
        if not isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.Expr)):
            raise ValueError("module level supports imports, functions and a docstring only")
        if isinstance(node, ast.Expr) and not (isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
            raise ValueError("move executable module-level code inside search")
    return tree


def clean_target(target):
    if set(target) != {"q", "n", "k", "c", "d"}:
        raise ValueError("target must contain only q,n,k,c,d")
    if any(type(x) is not int for x in target.values()):
        raise ValueError("target parameters must be integers")
    q, n, k, c, d = (target[x] for x in ("q", "n", "k", "c", "d"))
    if not (q == 2 and 1 <= k <= n <= 20 and 0 <= c <= n - k and 1 <= d <= n):
        raise ValueError("unsupported binary target parameters")
    if n + k - c > 20:
        raise ValueError("target exceeds exact enumeration limit")
    return {key: target[key] for key in ("q", "n", "k", "c", "d")}


class TargetEvaluator:
    def __init__(self, target, limit):
        self._target = target
        self._limit = limit
        self._calls = 0
        self._nullspace_calls = 0
        self._invalid = 0
        self._best = None
        self._best_key = None
        self._phase = "initialization"
        self._phase_calls = {"initialization": 0, "search": 0, "final_return": 0}

    @property
    def remaining(self):
        return self._limit - self._calls

    @property
    def incumbent(self):
        return list(self._best["generators"]) if self._best else None

    @property
    def incumbent_parameters(self):
        return dict(self._best["parameters"]) if self._best else None

    def _observe(self, generators):
        t = self._target
        try:
            values = list(itertools.islice(generators, 2 * t["n"] + 1))
            if len(values) > 2 * t["n"] or any(
                not isinstance(g, (int, np.integer)) or not 0 <= int(g) < 1 << (2 * t["n"])
                for g in values
            ):
                raise ValueError("invalid generator encoding")
            values = [int(g) for g in values]
            checked = H.evaluate(t["n"], values, t["d"])
        except (TypeError, ValueError, OverflowError) as exc:
            self._invalid += 1
            return {"error": str(exc)[:150]}
        if checked.get("k") != t["k"] or checked.get("c") != t["c"] or checked.get("d") is None:
            self._invalid += 1
            return {**checked, "error": "generator rank or symplectic signature does not match target"}
        key = (checked["d"], -checked["offending"])
        if self._best_key is None or key > self._best_key:
            self._best_key = key
            self._best = {"parameters": dict(checked), "generators": values,
                          "closed": checked["offending"] == 0,
                          "distance_ratio": min(1.0, checked["d"] / t["d"]),
                          "found_phase": self._phase}
        if checked["offending"] == 0:
            raise TargetSolved()
        return checked

    def evaluate(self, generators):
        if self.remaining <= 0:
            raise EvaluationBudgetExhausted()
        self._calls += 1
        self._phase_calls[self._phase] += 1
        return self._observe(generators)

    gf2_basis = staticmethod(H.gf2_basis)
    def nullspace(self, rows, nbits):
        self._nullspace_calls += 1
        return H.nullspace(rows, nbits)
    _J = staticmethod(H._J)
    sform = staticmethod(H.sform)
    span_array = staticmethod(H.span_array)
    symplectic_weights = staticmethod(H.symplectic_weights)
    random_stabilizer = staticmethod(H.random_stabilizer)


def protected_initialization(evaluator, target, rng, max_evals):
    n, s = target["n"], target["n"] - target["k"] + target["c"]
    for attempt in range(min(150, max_evals // 4)):
        if not evaluator.remaining:
            break
        orbit = []
        for base in range(1 if s <= n else 2):
            value = int(rng.integers(1, 1 << (2 * n)))
            for shift in range(n):
                shifted = 0
                for q in range(n):
                    shifted |= ((value >> (2 * q)) & 3) << (2 * ((q + shift) % n))
                orbit.append(shifted)
        basis = H.gf2_basis(orbit)
        if len(basis) >= s:
            evaluator.evaluate(list(basis[:s]))


def run_target(code, target, seed, max_evals):
    target = clean_target(target)
    if type(max_evals) is not int or max_evals <= 0:
        raise ValueError("max_evals must be a positive integer")
    evaluator = TargetEvaluator(target, max_evals)
    allowed = {name: getattr(builtins, name) for name in (
        "abs", "all", "any", "bool", "dict", "enumerate", "Exception", "filter",
        "float", "frozenset", "int", "isinstance", "KeyError", "len", "list", "map", "max",
        "min", "next", "pow", "print", "range", "reversed", "round", "RuntimeError",
        "set", "slice", "sorted", "StopIteration", "str", "sum", "tuple", "TypeError", "ValueError", "zip")}

    def controlled_import(name, *args, **kwargs):
        if name in IMPORTS:
            return IMPORTS[name]
        raise ImportError("unsupported import")

    allowed["__import__"] = controlled_import
    ns = {"__builtins__": allowed, "E": evaluator, "np": np,
          "rng": np.random.default_rng(seed)}
    error, termination, final_verifications = None, "returned", 0
    started = time.perf_counter()
    try:
        inspect_target_code(code)
        if PROTECTED_INITIALIZATION:
            protected_initialization(evaluator, target, ns["rng"], max_evals)
        evaluator._phase = "search"
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(code, "candidate.py", "exec"), ns)
            returned = ns["search"](MappingProxyType(target), max_evals)
            if returned is not None:
                # A returned candidate uses the same quota as an explicit evaluator call.
                final_verifications = 1
                evaluator._phase = "final_return"
                evaluator.evaluate(returned)
    except TargetSolved:
        termination = "solved"
    except EvaluationBudgetExhausted:
        termination = "budget_exhausted"
    except BaseException as exc:
        termination = "candidate_error"
        error = f"{type(exc).__name__}: {str(exc)[:300]}"
    best = evaluator._best or {"closed": False, "distance_ratio": 0.0}
    return {"target": target, "seed": seed, "allocated_evals": max_evals,
            "n_evals": evaluator._calls, "nullspace_calls": evaluator._nullspace_calls, "phase_evals": evaluator._phase_calls,
            "protected_initialization": PROTECTED_INITIALIZATION,
            "invalid_evaluations": evaluator._invalid,
            "final_verifications": final_verifications, "termination": termination, "error": error,
            "unused_evals": max_evals - evaluator._calls,
            "underused_without_solution": not best["closed"] and evaluator._calls < max_evals,
            **best, "elapsed_s": time.perf_counter() - started}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("code", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--max-evals", type=int, required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (120, 125))
    code, raw = args.code.read_text(), args.target.read_bytes()
    result = run_target(code, json.loads(raw), args.seed, args.max_evals)
    result["target_sha256"] = hashlib.sha256(raw).hexdigest()
    result["code_sha256"] = hashlib.sha256(code.encode()).hexdigest()
    print(json.dumps(result))


if __name__ == "__main__":
    main()
