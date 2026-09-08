"""The auditor must fail when the archive is not the one the paper describes.

Each test damages a private copy of the archive in one way that, before
these guards existed, went unnoticed -- and asserts the relevant claim
now FAILs and the process exits nonzero.
"""

import json
import os
import stat

DETERMINISTIC = ("archive-integrity", "witnesses", "families",
                 "table-correction", "openness")


def test_clean_archive_passes(archive, auditor):
    rc, rep, out = auditor(archive, "--tier", "deterministic")
    assert rc == 0, out
    for c in DETERMINISTIC:
        assert rep["claims"][c]["status"] == "PASS", (c, rep["claims"][c]["detail"])
    # one snapshot only: drift is a skip for want of data, not a tool
    assert rep["claims"]["novelty-drift"]["status"] == "SKIPPED_NO_DATA"


def test_missing_witness_fails(archive, auditor):
    victims = sorted((archive / "artifacts" / "witnesses" / "q2").glob("*.json"))
    victims[0].unlink()
    rc, rep, _ = auditor(archive, "--tier", "deterministic")
    assert rc == 1
    assert rep["claims"]["witnesses"]["status"] == "FAIL"
    assert "expected 114, found 113" in rep["claims"]["witnesses"]["detail"]
    assert rep["claims"]["archive-integrity"]["status"] == "FAIL"


def test_forged_witness_fails(archive, auditor):
    """A witness whose generators do not give the claimed parameters."""
    f = sorted((archive / "artifacts" / "witnesses" / "q2").glob("*.json"))[3]
    s = json.loads(f.read_text())
    s["generators"][0] ^= 0b11          # flip one qubit's Pauli in one generator
    f.write_text(json.dumps(s))
    rc, rep, _ = auditor(archive, "--claim", "witnesses")
    assert rc == 1
    assert rep["claims"]["witnesses"]["mismatches"], "tampered generator not caught"


def test_truncated_snapshot_looks_more_novel_and_fails(archive, auditor):
    """Dropping table records makes every closed cell look absent -- i.e.
    *more* novel. The openness guard must refuse that direction too."""
    snap = archive / "artifacts" / "codetables_snapshots" / "2026-07-17" / "qubit.json"
    cells = json.loads(snap.read_text())
    snap.write_text(json.dumps([c for c in cells if c["n"] > 40]))
    rc, rep, _ = auditor(archive, "--claim", "openness")
    assert rc == 1
    assert rep["claims"]["openness"]["status"] == "FAIL"
    assert "truncated" in rep["claims"]["openness"]["detail"]


def test_schema_break_deep_in_snapshot_fails(archive, auditor):
    snap = archive / "artifacts" / "codetables_snapshots" / "2026-07-17" / "qubit.json"
    cells = json.loads(snap.read_text())
    del cells[5000]["du"]
    snap.write_text(json.dumps(cells))
    rc, rep, _ = auditor(archive, "--claim", "table-correction")
    assert rc == 1
    assert "record 5000 lacks ['du']" in rep["claims"]["table-correction"]["detail"]


def test_altered_archive_file_fails_integrity(archive, auditor):
    f = archive / "artifacts" / "tables" / "plotkin_corrections.json"
    recs = json.loads(f.read_text())
    recs.pop()
    f.write_text(json.dumps(recs))
    rc, rep, _ = auditor(archive, "--claim", "archive-integrity")
    assert rc == 1
    assert "1 altered" in rep["claims"]["archive-integrity"]["detail"]
    rc, rep, _ = auditor(archive, "--claim", "table-correction")
    assert rc == 1, "the correction count is asserted, not merely printed"


def _fake_solver(path, exit_code):
    path.write_text(f"#!/bin/sh\nexit {exit_code}\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def test_solver_that_says_sat_fails_refutations(archive, auditor, tmp_path):
    """Tool presence must not decide status; only what the tool says may."""
    env = dict(os.environ, CADICAL_PATH=str(_fake_solver(tmp_path / "sat", 10)))
    rc, rep, _ = auditor(archive, "--claim", "refutations", env=env)
    assert rc == 1
    assert rep["claims"]["refutations"]["status"] == "FAIL"
    assert "0/" in rep["claims"]["refutations"]["detail"]


def test_solver_that_says_unsat_passes_refutations(archive, auditor, tmp_path):
    env = dict(os.environ, CADICAL_PATH=str(_fake_solver(tmp_path / "unsat", 20)))
    rc, rep, _ = auditor(archive, "--claim", "refutations", env=env)
    assert rc == 0
    assert rep["claims"]["refutations"]["status"] == "PASS"


def test_no_solver_is_a_skip_not_a_pass(archive, auditor):
    env = {k: v for k, v in os.environ.items() if k != "CADICAL_PATH"}
    env["PATH"] = "/nonexistent"
    rc, rep, _ = auditor(archive, "--claim", "refutations", env=env)
    assert rc == 0
    assert rep["claims"]["refutations"]["status"] == "SKIPPED_NO_TOOL"


def test_registry_entry_without_proof_is_a_decision_not_certified(archive, auditor, tmp_path):
    reg = archive / "artifacts" / "refutations" / "registry.json"
    entries = json.loads(reg.read_text())
    certified = [e for e in entries if e.get("drat")]
    victim = certified[0]
    (archive / "artifacts" / "refutations" / victim["drat"]).unlink()
    (archive / "artifacts" / "refutations" / victim["cnf"]).unlink()
    victim.pop("drat")
    victim.pop("cnf")
    victim["status"] = "decision"
    reg.write_text(json.dumps(entries))
    env = dict(os.environ, CADICAL_PATH=str(_fake_solver(tmp_path / "unsat", 20)))
    rc, rep, _ = auditor(archive, "--claim", "refutations", env=env)
    assert rc == 1, "fewer certified refutations than the paper states must fail"
    assert victim["tag"] in rep["claims"]["refutations"]["decisions"]
