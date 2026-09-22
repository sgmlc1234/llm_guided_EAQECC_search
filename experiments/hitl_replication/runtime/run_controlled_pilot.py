"""Budgeted Vertex pilot: independent proposals versus feedback-guided evolution."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import time

from controlled_execution import evaluate_program
from pilot_budget import BudgetExceeded, Ledger, atomic_json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODEL = "gemini-3.5-flash"

TASK = """Improve a Python search program for binary entanglement-assisted
quantum stabilizer codes. This is a retrospective construction benchmark,
not a request to claim new mathematical discoveries. The target list below
is frozen. Targets used later for testing are not provided.

Each target has n,k,c,d. Return generators of S as Python integers with
bit 2*i=X and bit 2*i+1=Z. Required rank(S)=n-k+c; the trusted evaluator
checks the symplectic signature and the minimum non-radical logical weight.
Human-proposed directions available equally to both arms: constructive
warm starts from hyperbolic/isotropic generators; classical GF(4) ideas;
structure shared across targets; coupled generator moves; cyclic qubit
shifts. No code-family formula or successful generators are supplied.

Execution contract: define search(), returning up to 16 (target_index, gens)
pairs. E, TARGETS, np, rng, TIME_BUDGET_S are provided. TARGETS is an
immutable sequence of read-only dictionaries. Use rng for randomness.
time.time() is a virtual clock advanced by calls to E.evaluate; respect
TIME_BUDGET_S with while-loop checks. There is also a real CPU limit.
E.evaluate(n,gens,d_target) returns n,s,c,iso,k,d,offending,logical_count,
or an error. A valid target requires matching k,c and offending=0.
Available helper functions: E.gf2_basis(gens), E.nullspace(rows,nbits),
E._J(v,n), E.sform(a,b,n), E.random_stabilizer(n,s,rng),
E.span_array(basis), E.symplectic_weights(vectors,n). E.nullspace gives
binary vectors orthogonal to the integer-bit rows; E._J swaps X/Z bits.
Thus a basis for a small dual space L can be converted to S using
E.nullspace([E._J(v,n) for v in L],2*n).

Selection uses mean number of distinct valid targets returned over two
fixed training seeds, with a small normalized offending-progress tiebreaker.
Produce a general program that reads TARGETS, not a stored answer list.
Allowed imports: math, itertools, time, numpy. Files, network, processes,
reflection, classes, global declarations and module attribute mutation are
unavailable. Keep source under 20,000 bytes and preferably under 150 lines.
Return one JSON object with a string field code containing the complete
Python program. Do not include markdown fences or external dependencies.
"""


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def summarize_feedback(evaluation):
    feedback = {k: evaluation.get(k) for k in ("mean_closed", "mean_progress", "score", "error")}
    feedback["seeds"] = [{"seed": r["seed"], "error": r.get("error"),
                           "n_evals": r.get("n_evals"),
                           "targets": [{k: t.get(k) for k in ("id", "closed", "progress", "offending")}
                                       for t in r.get("per_target", [])]}
                          for r in evaluation.get("runs", [])]
    return feedback


def prepare(directory, project, price_file):
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / "protocol.json").exists():
        raise RuntimeError("protocol already frozen; use --run")
    original = json.loads((HERE / "targets_original68.json").read_text())
    selector = random.Random(20260912)
    family = [t for t in original if t["k"] == 1 and t["d"] == t["n"] - 1 and t["n"] in (7, 9, 11)]
    other_train = [t for t in original if t["k"] >= 2 and t["n"] <= 11
                   and t["n"] + t["k"] - t["c"] <= 10]
    sampled_train = selector.sample(other_train, 5)
    other_test = [t for t in other_train if t not in sampled_train]
    train = sorted(family + sampled_train, key=lambda t: (t["n"], t["k"], t["c"], t["d"]))
    test = sorted([{"n": 13, "k": 1, "c": 10, "d": 12, "kind": "family-transfer"},
                   {"n": 15, "k": 1, "c": 12, "d": 14, "kind": "family-transfer"}]
                  + selector.sample(other_test, 6), key=lambda t: (t["n"], t["k"], t["c"], t["d"]))
    assert len(train) == len(test) == 8
    atomic_json(directory / "train_targets.json", train)
    atomic_json(directory / "test_targets.json", test)
    seed = (HERE / "seed_naive_sa.py").read_text()
    seed = seed[seed.index("import math"):]
    (directory / "initial_program.py").write_text(seed)
    (directory / "task.txt").write_text(TASK)
    runtime = directory / "runtime"
    runtime.mkdir()
    runtime_names = ("controlled_driver.py", "controlled_helpers.py", "controlled_execution.py",
                     "pilot_budget.py", "run_controlled_pilot.py")
    for name in runtime_names:
        shutil.copyfile(HERE / name, runtime / name)
    prices = json.loads(price_file.read_text())["skus"]
    selected = {}
    for label, description in (("input", "Gemini 3.5 Flash Global Text Input - Predictions"),
                               ("output", "Gemini 3.5 Flash Global Text Output - Predictions")):
        sku = next(x for x in prices if x["description"] == description)
        rate = sku["pricingInfo"][-1]["pricingExpression"]["tieredRates"][0]["unitPrice"]
        assert rate["currencyCode"] == "KRW"
        selected[label] = {"sku_id": sku["skuId"], "description": description,
                           "krw_per_token": int(rate["units"]) + rate["nanos"] / 1e9}
    atomic_json(directory / "prices.json", selected)
    protocol = {"title": "Controlled EAQECC evolution pilot", "created_unix": time.time(),
                "backend": "Vertex generateContent; controlled local evolutionary loop, not managed AlphaEvolve",
                "project": project, "location": "global", "model": MODEL,
                "replicates": 4, "generations_per_arm": 12, "arms": ["independent", "evolution"],
                "train_evaluations": 8000, "test_evaluations": 16000,
                "train_seeds": [2026091201, 2026091202],
                "test_seeds": [2026091301, 2026091302, 2026091303, 2026091304],
                "max_output_tokens": 8192, "thinking_level": "LOW", "max_input_tokens": 20000,
                "model_seed_base": 2026091200, "user_budget_krw": 30000,
                "service_cap_with_safety_krw": 24000, "safety_multiplier": 1.25,
                "reserved_generated_tokens_per_call": 131072,
                "primary_endpoint": "paired difference in selected-program mean held-out target count",
                "secondary_endpoints": ["family-transfer count", "other-target count", "training trajectory",
                                        "invalid/failed candidates", "actual token cost"],
                "test_rule": "test only final selected programs after all generation; never feed test results to models",
                "target_selection": "Training: n=7,9,11 family plus five parameter-filtered original68 cases; test: n=13,15 family transfer plus six disjoint cases from the same non-family pool; selector seed 20260912",
                "max_wall_seconds": 7200,
                "seed_provenance": "archived reconstruction of the pre-evolution annealing heuristic",
                "scope": "retrospective, small-budget pilot; four pairs do not establish broad domain superiority"}
    files = ["initial_program.py", "train_targets.json", "test_targets.json", "task.txt", "prices.json",
             *["runtime/" + name for name in runtime_names]]
    protocol["input_hashes"] = {name: digest(directory / name) for name in files}
    atomic_json(directory / "protocol.json", protocol)
    (directory / ".env").write_text(f"GOOGLE_CLOUD_PROJECT={project}\nGOOGLE_CLOUD_LOCATION=global\n"
                                     f"PILOT_MODEL={MODEL}\nPILOT_USER_BUDGET_KRW=30000\n")
    print(json.dumps({"prepared": str(directory), "replicates": 4, "generations_per_arm": 12,
                      "planned_generation_requests": 96, "service_cap_krw": 24000}), flush=True)


def generate(session, endpoint, payload, location, ledger, call_id):
    location.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False).encode()
    atomic_json(location / "request.json", payload)
    reservation = ledger.reserve(call_id, ledger.bound(len(encoded)))
    started = time.time()
    try:
        response = session.post(endpoint + ":generateContent", json=payload, timeout=180)
    except Exception:
        reservation["status"] = "uncertain"
        ledger.save()
        raise RuntimeError("generation response uncertain; reservation retained, no automatic retry") from None
    try:
        data = response.json()
    except ValueError:
        raise RuntimeError("generation response unreadable; reservation retained") from None
    atomic_json(location / "response.json", data)
    if response.status_code != 200:
        ledger.fail_http(reservation, response.status_code)
        raise RuntimeError(f"generation HTTP {response.status_code}: "
                           f"{data.get('error', {}).get('message', '')[:300]}")
    ledger.settle(reservation, data.get("usageMetadata", {}))
    usage = data["usageMetadata"]
    if usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0) > payload["generationConfig"]["maxOutputTokens"]:
        raise RuntimeError("provider output cap mismatch; usage settled and experiment stopped")
    atomic_json(location / "receipt.json", {"id": call_id, "elapsed_s": time.time() - started,
                                            "model_version": data.get("modelVersion"),
                                            "response_id": data.get("responseId"),
                                            "usage": data.get("usageMetadata")})
    try:
        candidate = data["candidates"][0]
        text = "".join(p.get("text", "") for p in candidate["content"]["parts"] if not p.get("thought"))
        code = json.loads(text)["code"]
        if not isinstance(code, str):
            raise ValueError("code is not a string")
        return code
    except (KeyError, IndexError, ValueError, TypeError):
        return "# Invalid or truncated model response; candidate receives a failure score.\n"


def run(directory):
    import google.auth
    from google.auth.transport.requests import AuthorizedSession

    lock = (directory / "runner.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    protocol = json.loads((directory / "protocol.json").read_text())
    if protocol["model"] != MODEL or protocol["user_budget_krw"] != 30000 or protocol["service_cap_with_safety_krw"] > 24000:
        raise RuntimeError("protocol exceeds the authorized pilot model/budget bounds")
    for name, expected in protocol["input_hashes"].items():
        if digest(directory / name) != expected:
            raise RuntimeError(f"frozen input changed: {name}")
    if (directory / "budget_ledger.json").exists():
        raise RuntimeError("run already has a ledger; automatic restart is disabled")
    configured_project = os.environ.get("GOOGLE_CLOUD_PROJECT", protocol["project"])
    if configured_project != protocol["project"]:
        raise RuntimeError("environment and frozen billing project disagree")
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials = credentials.with_quota_project(protocol["project"])
    session = AuthorizedSession(credentials)
    endpoint = (f"https://aiplatform.googleapis.com/v1/projects/{protocol['project']}/locations/global/"
                f"publishers/google/models/{protocol['model']}")
    prices = json.loads((directory / "prices.json").read_text())
    ledger = Ledger(directory / "budget_ledger.json", protocol["service_cap_with_safety_krw"],
                    prices["input"]["krw_per_token"], prices["output"]["krw_per_token"],
                    protocol["safety_multiplier"])
    status = {"state": "BASELINE", "protocol_sha256": digest(directory / "protocol.json"),
              "started_unix": time.time(), "completed_candidates": 0, "planned_candidates": 96}
    atomic_json(directory / "status.json", status)
    seed_code = (directory / "initial_program.py").read_text()
    runtime = directory / "runtime"
    train_manifest = directory / "train_targets.json"
    baseline = evaluate_program(seed_code, train_manifest, protocol["train_seeds"],
                                protocol["train_evaluations"], runtime)
    if not baseline.get("runs") or any(r.get("error") for r in baseline["runs"]):
        status.update(state="STOPPED", reason="baseline execution failed before paid inference")
        atomic_json(directory / "status.json", status)
        raise RuntimeError("baseline execution failed; inference not started: " + str(summarize_feedback(baseline)))
    atomic_json(directory / "baseline_train.json", baseline)
    print("Baseline ready: " + json.dumps(summarize_feedback(baseline)), flush=True)
    task = (directory / "task.txt").read_text()
    task += "\nFrozen training targets:\n" + train_manifest.read_text()
    selected = {}
    try:
        for replicate in range(protocol["replicates"]):
            best = {arm: {"code": seed_code, "evaluation": baseline, "generation": -1}
                    for arm in protocol["arms"]}
            last = {}
            for generation in range(protocol["generations_per_arm"]):
                if (directory / "STOP").exists() or time.time() - status["started_unix"] > protocol["max_wall_seconds"]:
                    raise RuntimeError("local stop condition reached before next paired generation")
                payloads = {}
                for arm in protocol["arms"]:
                    parent = best[arm] if arm == "evolution" else {"code": seed_code, "evaluation": baseline}
                    prompt = task + "\nStarting program for this proposal:\n" + parent["code"]
                    prompt += "\nIts training feedback:\n" + json.dumps(summarize_feedback(parent["evaluation"]))
                    if arm == "evolution" and generation and arm in last:
                        prompt += "\nMost recent attempted child (possibly rejected):\n" + last[arm]["code"]
                        prompt += "\nIts feedback:\n" + json.dumps(summarize_feedback(last[arm]["evaluation"]))
                    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                               "generationConfig": {"maxOutputTokens": protocol["max_output_tokens"],
                                                    "candidateCount": 1,
                                                    "thinkingConfig": {"thinkingLevel": protocol["thinking_level"]},
                                                    "seed": protocol["model_seed_base"] + replicate * 100 + generation,
                                                    "responseMimeType": "application/json",
                                                    "responseSchema": {"type": "OBJECT", "properties": {
                                                        "code": {"type": "STRING"}}, "required": ["code"]}},
                               "labels": {"experiment": "eaqecc-evolution-pilot", "arm": arm}}
                    counted = session.post(endpoint + ":countTokens", json={"contents": payload["contents"]}, timeout=30)
                    counted.raise_for_status()
                    tokens = counted.json()["totalTokens"]
                    if tokens > protocol["max_input_tokens"]:
                        raise RuntimeError("prompt exceeds frozen input-token limit")
                    payloads[arm] = payload
                ledger.ensure(sum(ledger.bound(len(json.dumps(p, ensure_ascii=False).encode())) for p in payloads.values()))
                order = protocol["arms"] if (replicate + generation) % 2 == 0 else list(reversed(protocol["arms"]))
                for arm in order:
                    call_id = f"r{replicate:02d}_{arm}_g{generation:02d}"
                    location = directory / "candidates" / call_id
                    status.update(state="GENERATING", replicate=replicate, generation=generation, arm=arm)
                    atomic_json(directory / "status.json", status)
                    code = generate(session, endpoint, payloads[arm], location, ledger, call_id)
                    (location / "program.py").write_text(code)
                    status["state"] = "EVALUATING"
                    atomic_json(directory / "status.json", status)
                    evaluation = evaluate_program(code, train_manifest, protocol["train_seeds"],
                                                  protocol["train_evaluations"], runtime)
                    atomic_json(location / "train_evaluation.json", evaluation)
                    last[arm] = {"code": code, "evaluation": evaluation}
                    if evaluation["score"] > best[arm]["evaluation"]["score"]:
                        best[arm] = {"code": code, "evaluation": evaluation, "generation": generation}
                    status["completed_candidates"] += 1
                    status["committed_krw"] = ledger.data["committed_krw"]
                    atomic_json(directory / "status.json", status)
                    print(json.dumps({"candidate": call_id, "mean_closed": evaluation["mean_closed"],
                                      "progress": evaluation["mean_progress"],
                                      "best_score": best[arm]["evaluation"]["score"],
                                      "committed_krw": round(ledger.data["committed_krw"], 2)}), flush=True)
                atomic_json(directory / f"replicate_{replicate:02d}_state.json", best)
            selected[str(replicate)] = best
            atomic_json(directory / "selected_programs.json", selected)
        status["state"] = "HELDOUT_EVALUATION"
        atomic_json(directory / "status.json", status)
        heldout = {"baseline": evaluate_program(seed_code, directory / "test_targets.json", protocol["test_seeds"],
                                                 protocol["test_evaluations"], runtime), "replicates": {}}
        for replicate, pair in selected.items():
            heldout["replicates"][replicate] = {}
            for arm, program in pair.items():
                heldout["replicates"][replicate][arm] = evaluate_program(
                    program["code"], directory / "test_targets.json", protocol["test_seeds"],
                    protocol["test_evaluations"], runtime)
                atomic_json(directory / "heldout_results.json", heldout)
        status.update(state="COMPLETED", finished_unix=time.time(), committed_krw=ledger.data["committed_krw"])
    except (BudgetExceeded, Exception) as exc:
        status.update(state="STOPPED", reason=f"{type(exc).__name__}: {str(exc)[:600]}",
                      stopped_unix=time.time(), committed_krw=ledger.data["committed_krw"])
        atomic_json(directory / "status.json", status)
        raise
    atomic_json(directory / "status.json", status)
    if status["state"] == "COMPLETED":
        lines = ["# Controlled evolution pilot results", "", "Completed all planned candidates.", "",
                 "| Replicate | Independent held-out mean | Evolution held-out mean | Difference |",
                 "|---|---:|---:|---:|"]
        differences = []
        for replicate, arms in heldout["replicates"].items():
            independent = arms["independent"]["mean_closed"]
            evolved = arms["evolution"]["mean_closed"]
            differences.append(evolved - independent)
            lines.append(f"| {int(replicate)+1} | {independent:.3f} | {evolved:.3f} | {evolved-independent:+.3f} |")
        lines += ["", f"Mean paired difference: {sum(differences)/len(differences):+.3f} targets.",
                  f"Baseline held-out mean: {heldout['baseline']['mean_closed']:.3f} targets.",
                  f"Estimated model charges: KRW {ledger.data['estimated_model_krw']:.2f} before safety markup.",
                  f"Conservative ledger total: KRW {ledger.data['committed_krw']:.2f}.", "",
                  "This four-pair retrospective pilot uses a controlled Vertex loop, not managed AlphaEvolve. "
                  "It does not establish cross-domain superiority or confirm final invoiced charges."]
        (directory / "RESULTS.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(status), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--project")
    parser.add_argument("--prices", type=Path)
    args = parser.parse_args()
    if args.prepare == args.run:
        parser.error("select exactly one of --prepare and --run")
    if args.prepare:
        if not args.project or not args.prices:
            parser.error("--prepare needs --project and --prices")
        prepare(args.out.resolve(), args.project, args.prices)
    else:
        run(args.out.resolve())


if __name__ == "__main__":
    main()
