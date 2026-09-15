"""The auditor must fail when the archive is not the one the paper describes.

Each test damages a private copy of the archive in one way that, before
these guards existed, went unnoticed -- and asserts the relevant claim
now FAILs and the process exits nonzero.
"""

import json
import os
import stat

DETERMINISTIC = ("archive-integrity", "witnesses", "families",
                 "table-correction", "openness", "solver-refinement")


def test_clean_archive_passes(archive, auditor):
    rc, rep, out = auditor(archive, "--tier", "deterministic")
    assert rc == 0, out
    for c in DETERMINISTIC:
        assert rep["claims"][c]["status"] == "PASS", (c, rep["claims"][c]["detail"])
    # Both archived snapshots are checked, with an explicit frozen paper reference.
    assert rep["snapshot"] == "2026-07-17"
    assert rep["claims"]["novelty-drift"]["status"] == "PASS"


def test_missing_witness_fails(archive, auditor):
    victims = sorted((archive / "artifacts" / "witnesses" / "q2").glob("*.json"))
    victims[0].unlink()
    rc, rep, _ = auditor(archive, "--tier", "deterministic")
    assert rc == 1
    assert rep["claims"]["witnesses"]["status"] == "FAIL"
    assert "expected 115, found 114" in rep["claims"]["witnesses"]["detail"]
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


def test_solver_unsat_does_not_claim_certificate_replay(archive, auditor, tmp_path):
    env = dict(os.environ, CADICAL_PATH=str(_fake_solver(tmp_path / "unsat", 20)))
    rc, rep, _ = auditor(archive, "--claim", "refutations", env=env)
    assert rc == 0
    assert rep["claims"]["refutations"]["status"] == "PARTIAL"
    assert rep["claims"]["refutations"]["solver_redecided"] == 10
    assert rep["claims"]["refutations"]["certificates_replayed"] == 0
    assert rep["overall"] == "PARTIAL"


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


def test_refinement_forged_new_witness_fails(archive, auditor):
    path = archive / "artifacts/witnesses/q2/SOLUTION_n12_k2_c9_d9.json"
    data = json.loads(path.read_text())
    data["generators"] = [0]
    path.write_text(json.dumps(data))
    rc, report, _ = auditor(archive, "--claim", "solver-refinement")
    assert rc == 1
    assert report["claims"]["solver-refinement"]["status"] == "FAIL"


def test_refinement_wrong_certificate_cell_fails(archive, auditor):
    path = archive / "artifacts/refutations/registry.json"
    records = json.loads(path.read_text())
    next(r for r in records if r["tag"] == "q2_n13_k1_c8_d12")["c"] = 9
    path.write_text(json.dumps(records))
    rc, report, _ = auditor(archive, "--claim", "solver-refinement")
    assert rc == 1
    assert "certificate link" in report["claims"]["solver-refinement"]["detail"]


def test_duplicate_snapshot_cell_fails(archive, auditor):
    path = archive / "artifacts/codetables_snapshots/2026-09-10/qutrit.json"
    rows = json.loads(path.read_text())
    rows.append(rows[0])
    path.write_text(json.dumps(rows))
    rc, report, _ = auditor(archive, "--claim", "novelty-drift")
    assert rc == 1
    assert "duplicate cell" in report["claims"]["novelty-drift"]["detail"]


def test_qutrit_newly_matched_is_not_independent_discovery(archive, auditor):
    path = archive / "artifacts/codetables_snapshots/2026-09-10/qutrit.json"
    rows = json.loads(path.read_text())
    cell = next(r for r in rows if (r["n"], r["k"], r["c"]) == (10, 1, 5))
    cell["dl"] = 9
    path.write_text(json.dumps(rows))
    rc, report, _ = auditor(archive, "--claim", "novelty-drift")
    assert rc == 0
    result = report["claims"]["novelty-drift"]
    assert len(result["by_q"]["3"]["newly_matched"]) == 1
    assert len(result["by_q"]["3"]["previously_matched"]) == 1
    assert "not inferred" in result["detail"]


def test_removed_snapshot_cell_does_not_become_novel(archive, auditor):
    path = archive / "artifacts/codetables_snapshots/2026-09-10/qubit.json"
    rows = json.loads(path.read_text())
    rows.pop()
    path.write_text(json.dumps(rows))
    rc, report, _ = auditor(archive, "--claim", "novelty-drift")
    assert rc == 1
    assert "omits 1" in report["claims"]["novelty-drift"]["detail"]


def test_openness_counts_files_and_unique_cells_separately(archive, auditor):
    rc, report, _ = auditor(archive, "--claim", "openness")
    result = report["claims"]["openness"]
    assert rc == 0
    assert result["unique_cells"] == 61
    assert result["unique_listed_cells"] == 8
    assert result["unique_absent_cells"] == 53
    assert result["gap_cells"] + result["record_cells"] == 65


def test_false_verified_message_does_not_pass(archive, auditor, tmp_path):
    checker = tmp_path / "checker"
    checker.write_text("#!/bin/sh\necho 'not s VERIFIED'\nexit 0\n")
    checker.chmod(checker.stat().st_mode | stat.S_IEXEC)
    env = dict(os.environ, CADICAL_PATH=str(_fake_solver(tmp_path / "unsat", 20)),
               DRAT_TRIM_PATH=str(checker))
    rc, report, _ = auditor(archive, "--claim", "refutations", env=env)
    assert rc == 1
    assert report["claims"]["refutations"]["certificates_replayed"] == 0


def test_qutrit_normalization_metadata_tamper_fails(archive, auditor):
    path = archive / "artifacts/refutations/q3_n10_k1_c4_d9.normalization.json"
    data = json.loads(path.read_text())
    data["unit_literals"][0] += 1
    path.write_text(json.dumps(data))
    rc, report, _ = auditor(archive, "--claim", "refutations", env={"PATH": "/nonexistent"})
    assert rc == 1
    assert "q3_n10_k1_c4_d9" in report["claims"]["refutations"]["malformed"]
