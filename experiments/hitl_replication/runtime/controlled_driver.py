"""Run one candidate against an immutable manifest inside the OS sandbox."""

import argparse
import ast
import builtins
import contextlib
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import resource
import time
from types import MappingProxyType

import numpy as np

import controlled_helpers as H

IMPORTS = {"math": math, "itertools": itertools, "numpy": np}
FORBIDDEN_NAMES = {"eval", "exec", "compile", "open", "input", "getattr", "setattr",
                   "delattr", "globals", "locals", "vars", "dir", "type", "object",
                   "help", "breakpoint", "memoryview"}
FORBIDDEN_ATTRS = {"ctypes", "ctypeslib", "load", "save", "savez", "loadtxt", "savetxt",
                   "genfromtxt", "fromfile", "tofile", "memmap", "f2py", "distutils",
                   "testing", "load_library", "dump", "dumps", "lib", "core"}


def inspect_code(code):
    tree = ast.parse(code)
    if len(code.encode()) > 20000:
        raise ValueError("candidate exceeds 20 KB source limit")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Global, ast.ClassDef)):
            raise ValueError("global declarations and classes are unavailable")
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [x.name for x in node.names] if isinstance(node, ast.Import) else [node.module]
            if any(name not in {*IMPORTS, "time"} for name in names):
                raise ValueError("unsupported import")
        if isinstance(node, ast.Name) and (node.id in FORBIDDEN_NAMES or node.id.startswith("__")):
            raise ValueError("unsupported builtin or reflection")
        if isinstance(node, ast.Attribute):
            if (node.attr.startswith("_") and node.attr != "_J") or node.attr in FORBIDDEN_ATTRS:
                raise ValueError("unsupported attribute")
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                raise ValueError("module/evaluator attributes are read-only")
    return tree


class Clock:
    def __init__(self, limit):
        self.calls = 0
        self.limit = limit

    def time(self):
        return self.calls / self.limit

    perf_counter = time
    monotonic = time


class Evaluator:
    def __init__(self, clock):
        self.clock = clock

    def evaluate(self, *args, **kwargs):
        if self.clock.calls >= self.clock.limit + 2:
            raise RuntimeError("evaluation budget exhausted")
        self.clock.calls += 1
        return H.evaluate(*args, **kwargs)

    gf2_basis = staticmethod(H.gf2_basis)
    nullspace = staticmethod(H.nullspace)
    _J = staticmethod(H._J)
    sform = staticmethod(H.sform)
    span_array = staticmethod(H.span_array)
    symplectic_weights = staticmethod(H.symplectic_weights)
    random_stabilizer = staticmethod(H.random_stabilizer)


def run(code, targets, seed, max_evals):
    clock = Clock(max_evals)
    evaluator = Evaluator(clock)
    allowed = {name: getattr(builtins, name) for name in (
        "abs", "all", "any", "bool", "dict", "enumerate", "Exception", "filter",
        "float", "frozenset", "int", "isinstance", "len", "list", "map", "max",
        "min", "next", "pow", "print", "range", "reversed", "round", "RuntimeError",
        "set", "slice", "sorted", "StopIteration", "str", "sum", "tuple", "ValueError", "zip")}

    def controlled_import(name, *args, **kwargs):
        if name == "time":
            return clock
        if name in IMPORTS:
            return IMPORTS[name]
        raise ImportError("unsupported import")

    allowed["__import__"] = controlled_import
    ns = {"__builtins__": allowed, "E": evaluator, "np": np,
          "rng": np.random.default_rng(seed), "TIME_BUDGET_S": 1.0,
          "TARGETS": tuple(MappingProxyType(t) for t in targets)}
    per_target = [{"id": i, "key": [t[k] for k in ("n", "k", "c", "d")],
                   "closed": False, "progress": 0.0, "offending": None}
                  for i, t in enumerate(targets)]
    error = None
    invalid = 0
    started = time.perf_counter()
    try:
        inspect_code(code)
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(code, "candidate.py", "exec"), ns)
            proposals = ns["search"]()
            proposals = list(itertools.islice(proposals or (), 16))
        for proposal in proposals:
            try:
                tid, generators = proposal
                tid = int(tid)
                if not 0 <= tid < len(targets):
                    raise ValueError("target index outside frozen manifest")
                target = targets[tid]
                generators = list(itertools.islice(generators, 2 * target["n"] + 1))
                if (len(generators) > 2 * target["n"]
                        or any(not isinstance(g, (int, np.integer)) or not 0 <= int(g) < 1 << (2 * target["n"])
                               for g in generators)):
                    raise ValueError("invalid generators")
                checked = H.evaluate(target["n"], generators, target["d"])
                if checked.get("k") != target["k"] or checked.get("c") != target["c"]:
                    invalid += 1
                    continue
                off = checked["offending"]
                progress = 1 - off / max(1, checked["logical_count"])
                if per_target[tid]["offending"] is None or off < per_target[tid]["offending"]:
                    per_target[tid].update(closed=off == 0, progress=progress, offending=off,
                                          parameters=checked)
                    if off == 0:
                        per_target[tid]["generators"] = [int(g) for g in generators]
            except (ValueError, TypeError, IndexError, KeyError):
                invalid += 1
    except BaseException as exc:
        error = f"{type(exc).__name__}: {str(exc)[:300]}"
    closed = sum(x["closed"] for x in per_target)
    progress = sum(x["progress"] for x in per_target) / len(targets)
    return {"seed": seed, "n_evals": clock.calls, "error": error, "invalid": invalid,
            "closed": closed, "progress": progress, "score": closed + .001 * progress,
            "per_target": per_target, "elapsed_s": time.perf_counter() - started}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("code", type=Path)
    parser.add_argument("targets", type=Path)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--max-evals", type=int, required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (35, 40))
    code = args.code.read_text()
    raw = args.targets.read_bytes()
    result = run(code, json.loads(raw), args.seed, args.max_evals)
    result["manifest_sha256"] = hashlib.sha256(raw).hexdigest()
    result["code_sha256"] = hashlib.sha256(code.encode()).hexdigest()
    print(json.dumps(result))


if __name__ == "__main__":
    main()
