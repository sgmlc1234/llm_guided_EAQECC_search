"""Allocate independent per-target processes and quotas; never pool unused work."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

from controlled_execution import sandbox_profile, supervised_run
from target_driver import clean_target

RUNTIME_FILES = ("target_driver.py", "target_execution.py", "controlled_driver.py",
                 "controlled_helpers.py", "controlled_execution.py")


def target_seed(seed, target):
    """Stable under manifest permutations and identical in paired arms."""
    data = [seed, *[target[k] for k in ("q", "n", "k", "c", "d")]]
    return int.from_bytes(hashlib.sha256(json.dumps(data).encode()).digest()[:8], "big")


def evaluate_target_program(code, manifest, seeds, max_evals_per_target, runtime, timeout=135):
    if type(max_evals_per_target) is not int or max_evals_per_target <= 0:
        raise ValueError("per-target evaluation quota must be positive")
    seeds = list(seeds)
    if not seeds or len(set(seeds)) != len(seeds) or any(type(s) is not int for s in seeds):
        raise ValueError("provide nonempty, distinct integer execution seeds")
    raw = Path(manifest).read_bytes()
    targets = [clean_target(t) for t in json.loads(raw)]
    keys = [tuple(t[k] for k in ("q", "n", "k", "c")) for t in targets]
    if not targets or len(keys) != len(set(keys)):
        raise ValueError("manifest must contain distinct parameter cells")
    if not Path("/usr/bin/sandbox-exec").exists():
        raise RuntimeError("this evaluator requires the macOS OS sandbox")
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    runs = []
    for seed in seeds:
        cases = []
        for tid, target in enumerate(targets):
            execution_seed = target_seed(seed, target)
            result = {"target": target, "seed": execution_seed, "allocated_evals": max_evals_per_target,
                      "n_evals": None, "closed": False, "distance_ratio": 0.0,
                      "underused_without_solution": None, "termination": "process_error"}
            # Only this target and candidate source enter the temporary sandbox.
            # Witness files, other targets, previous cases and campaign logs do not.
            with tempfile.TemporaryDirectory(prefix="eaqecc_target_") as scratch:
                scratch = Path(scratch)
                (scratch / "candidate.py").write_text(code)
                (scratch / "target.json").write_text(json.dumps(target))
                target_hash = hashlib.sha256((scratch / "target.json").read_bytes()).hexdigest()
                for name in ("target_driver.py", "controlled_driver.py", "controlled_helpers.py"):
                    shutil.copyfile(Path(runtime) / name, scratch / name)
                (scratch / "sandbox.sb").write_text(sandbox_profile(scratch))
                environment = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1",
                               "PYTHONHASHSEED": "0", "OPENBLAS_NUM_THREADS": "1",
                               "OMP_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1", "LANG": "en_US.UTF-8"}
                command = ["/usr/bin/sandbox-exec", "-f", str(scratch / "sandbox.sb"),
                           sys.executable, str(scratch / "target_driver.py"),
                           str(scratch / "candidate.py"), str(scratch / "target.json"),
                           "--seed", str(execution_seed), "--max-evals", str(max_evals_per_target)]
                try:
                    process = supervised_run(command, scratch, environment, timeout)
                    if process.returncode:
                        raise RuntimeError(f"driver exit {process.returncode}: {process.stderr[-300:]}")
                    observed = json.loads(process.stdout)
                    if (observed["target_sha256"] != target_hash or observed["code_sha256"] != code_hash
                            or observed["target"] != target or observed["seed"] != execution_seed
                            or observed["allocated_evals"] != max_evals_per_target
                            or not 0 <= observed["n_evals"] <= max_evals_per_target):
                        raise RuntimeError("driver result disagrees with dispatched target/code/quota")
                    result = observed
                except (RuntimeError, ValueError, KeyError) as exc:
                    result["error"] = f"{type(exc).__name__}: {str(exc)[:350]}"
            result["id"] = tid
            cases.append(result)
        runs.append({"seed": seed, "closed": sum(x["closed"] for x in cases),
                     "distance_ratio": sum(x["distance_ratio"] for x in cases) / len(cases),
                     "failed_targets": sum(bool(x.get("error")) for x in cases), "per_target": cases})
    closed = sum(x["closed"] for x in runs) / len(runs)
    ratio = sum(x["distance_ratio"] for x in runs) / len(runs)
    return {"schema": "per-target-v2", "manifest_sha256": hashlib.sha256(raw).hexdigest(),
            "code_sha256": code_hash, "mean_closed": closed, "mean_distance_ratio": ratio,
            "score": closed + .001 * ratio, "runs": runs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("code", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--evals-per-target", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output already exists; preserve prior evaluations")
    result = evaluate_target_program(args.code.read_text(), args.manifest, args.seeds,
                                     args.evals_per_target, Path(__file__).resolve().parent)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("schema", "mean_closed", "mean_distance_ratio", "score")}))


if __name__ == "__main__":
    main()
