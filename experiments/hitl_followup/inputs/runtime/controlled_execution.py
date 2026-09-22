"""Sandboxed local evaluation shared by both arms of the controlled pilot."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

from controlled_driver import inspect_code


def supervised_run(command, directory, environment, timeout):
    import psutil
    process = subprocess.Popen(command, cwd=directory, env=environment, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, start_new_session=True)
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                stdout, stderr = process.communicate(timeout=.1)
                return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
            except subprocess.TimeoutExpired:
                if time.monotonic() >= deadline:
                    raise RuntimeError("candidate wall-time limit reached") from None
                try:
                    if psutil.Process(process.pid).memory_info().rss > 1024**3:
                        raise RuntimeError("candidate resident-memory limit reached")
                except psutil.NoSuchProcess:
                    pass
    finally:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()


def sandbox_profile(directory):
    directory = Path(directory).resolve()
    readable = [str(directory), sys.base_prefix, str(Path(sys.executable).parent.parent.resolve()),
                "/System/Library", "/usr/lib", "/usr/share", "/Library/Apple"]
    paths = "\n".join(f"  (subpath {json.dumps(p)})" for p in readable)
    executables = {str(Path(sys.executable)), str(Path(sys.executable).resolve())}
    execs = " ".join(f"(literal {json.dumps(p)})" for p in executables)
    return f"""(version 1)
(deny default)
(allow process-fork)
(allow process-exec {execs})
(allow sysctl-read)
(allow mach-lookup)
(allow file-read-metadata)
(allow file-read-data
{paths}
  (literal "/")
  (literal "/dev/null") (literal "/dev/urandom") (literal "/dev/random")
  (literal "/private/etc/localtime") (literal "/etc/localtime"))
(allow file-write* (literal "/dev/null"))
"""


def evaluate_program(code, manifest, seeds, max_evals, runtime, timeout=45):
    targets = json.loads(Path(manifest).read_text())
    manifest_hash = hashlib.sha256(Path(manifest).read_bytes()).hexdigest()
    try:
        inspect_code(code)
    except (SyntaxError, ValueError) as exc:
        return {"mean_closed": 0.0, "mean_progress": 0.0, "score": -1.0,
                "error": f"{type(exc).__name__}: {str(exc)[:250]}", "runs": []}
    if not Path("/usr/bin/sandbox-exec").exists():
        raise RuntimeError("this pilot requires the macOS OS sandbox")
    results = []
    with tempfile.TemporaryDirectory(prefix="eaqecc_controlled_") as temp:
        temp = Path(temp)
        (temp / "candidate.py").write_text(code)
        shutil.copyfile(manifest, temp / "targets.json")
        for name in ("controlled_driver.py", "controlled_helpers.py"):
            shutil.copyfile(Path(runtime) / name, temp / name)
        (temp / "sandbox.sb").write_text(sandbox_profile(temp))
        environment = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1",
                       "PYTHONHASHSEED": "0", "OPENBLAS_NUM_THREADS": "1",
                       "OMP_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1",
                       "LANG": "en_US.UTF-8"}
        for seed in seeds:
            command = ["/usr/bin/sandbox-exec", "-f", str(temp / "sandbox.sb"),
                       sys.executable, str(temp / "controlled_driver.py"),
                       str(temp / "candidate.py"), str(temp / "targets.json"),
                       "--seed", str(seed), "--max-evals", str(max_evals)]
            try:
                process = supervised_run(command, temp, environment, timeout)
                if process.returncode:
                    raise RuntimeError(f"driver exit {process.returncode}: {process.stderr[-400:]}")
                result = json.loads(process.stdout)
                if result["manifest_sha256"] != manifest_hash:
                    raise RuntimeError("driver/parent target manifest mismatch")
                results.append(result)
            except (subprocess.TimeoutExpired, RuntimeError, json.JSONDecodeError) as exc:
                results.append({"seed": seed, "closed": 0, "progress": 0.0,
                                "error": f"{type(exc).__name__}: {str(exc)[:350]}",
                                "per_target": [{"id": i, "closed": False, "progress": 0.0}
                                               for i in range(len(targets))]})
    closed = sum(x["closed"] for x in results) / len(results)
    progress = sum(x["progress"] for x in results) / len(results)
    return {"mean_closed": closed, "mean_progress": progress,
            "score": closed + .001 * progress, "runs": results}
