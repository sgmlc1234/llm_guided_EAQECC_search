# Start here: checking and reproducing the paper

Run commands from the extracted repository root. No account, network request or
LLM call is needed for the checks below. The current paper is in
[paper/iclr2027/paper/main.pdf](../paper/iclr2027/paper/main.pdf).
The [result-to-evidence map](RESULTS_AND_EVIDENCE.md) links each reported result.

## 1. Inspect the supplied evidence

Use Python 3.12 for the recorded study environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-ablation.txt
python scripts/make_manifest.py --check
python scripts/eaqecc_ablation/audit.py
python scripts/paper_results.py --out ../table-evidence.json
```

The ablation audit recomputes selection, prompt/parent relationships, metrics and
235 witness checks. Expected held-out counts are 21/64 (independent) and 38/64
(iterative); at longer lengths they are 0/32 and 6/32. All six longer-length
successes come from the selected `b02_evolution_g02`: 3/4 at n=13 and 3/4 at n=15.
This audit uses archived records; it does not execute fresh model sampling.
`paper_results.py` locates every Table 1/2 matrix and its checksum, and verifies
all displayed historical intervals. It checks links, not distances by itself.

The release ZIP includes a full-file `RELEASE_MANIFEST.sha256`. Before creating
a virtual environment or other files inside the release, check it with:

```bash
python3 scripts/release/audit.py .
```

The audit uses Poppler (`pdftotext`, `pdfinfo`) for PDF content/metadata inspection;
without it the PDF inspection is reported as PARTIAL. A new local environment or
rerun output is intentionally not in the immutable release manifest. Keep an
untouched extracted copy for subsequent integrity checks.

## 2. Recompute mathematical results

```bash
python scripts/reproduce_eaqecc.py --tier deterministic --out ../checks/deterministic
python scripts/reproduce_eaqecc.py --claim search-determinism --out ../checks/historical-search
```

The first command recomputes all 115 core witnesses, the 54 family gap closures,
398 upper-bound corrections, snapshot comparisons, refinement links and prompt
provenance. The second re-executes historical fixed programs against their seeded
fingerprints. These checks work without cloud services. Family verification can
be the longest deterministic step; it enumerates exact finite-field objects.

The 115 core matrices and 235 study witness files are different collections.
The latter include repeated outcomes across runs; neither file count is a count
of distinct new bounds. The n=15 Table 1 witness is in the study archive, and its
parameters were already covered by the family theorem.

## 3. Re-execute Algorithm 1 and the policy comparison

The recorded OS-sandbox backend requires macOS with `/usr/bin/sandbox-exec`.
Python 3.12.12 and NumPy 2.5.1 were used for the archived executions. The offline
record and witness audits above are not macOS-specific. A Linux/Windows process
backend is not supplied or claimed to reproduce the original sandbox protocol.

```bash
python scripts/eaqecc_ablation/replay.py --program b02_evolution_g02 --split test --out ../checks/algorithm1-test
python scripts/eaqecc_ablation/replay.py --program b02_evolution_g02 --split transfer --out ../checks/algorithm1-longer-codes
```

Expected: 16/16 at n=9,11; 6/8 at n=13,15. `transfer` is the frozen machine-readable
split name; the paper calls it **Generalization to longer codes**. Replay compares
success, evaluation count, parameters and generators against the archived record.
Wall time is measured again and is not expected to match across machines.

To replay all eight selected programs on both splits and the initial test baseline:

```bash
python scripts/eaqecc_ablation/replay_selected.py --out ../checks/all-selected
```

For individual programs, use their IDs in
[selection records](../experiments/hitl_ablation/selected_programs.json), with
`--split test` and `--split transfer` for each. `--program initial --split test`
runs the initial program on the same seeds. Output directories must be new and
outside the archived dataset. Every successful output is independently checked.
No paid generation or cloud client is used by this entry point.

## 4. Check nonexistence and the independent implementation

Follow the separate [external-tool installation guide](EXTERNAL_VERIFICATION.md) for CaDiCaL, DRAT-trim, Magma and the on-demand proof cache.

Install CaDiCaL, drat-trim and optionally Magma, then run:

```bash
python scripts/reproduce_eaqecc.py --claim refutations --out ../checks/refutations
python scripts/reproduce_eaqecc.py --claim magma-crosscheck --out ../checks/magma
```

Nine CNF/DRAT pairs are shipped; the tenth proof is regenerated on demand
(approximately 0.6 GB). Commands and environment variables are in the root README.
Magma independently checked 148 objects in the archived run. Without a local
installation, its saved log is evidence of that run, not a fresh cross-check.
A missing solver/checker is reported as missing; exit zero with overall PARTIAL
must not be interpreted as complete verification. The qutrit encoding also relies
on the mathematical normalization lemma; see [its documentation](qutrit_certificate.md).

## 5. Figures, paper and tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
python scripts/eaqecc_ablation/make_figure.py
cd paper/iclr2027/paper
tectonic -X compile main.tex
```

Figure generation and manuscript compilation require Tectonic and Poppler; the
first Tectonic build may download its TeX bundle. See [figure sources](paper_figures.md)
for the other figures. These dependencies are separate from numerical verification.

## Archived discovery versus a new campaign

The supplied requests, responses, source code and parentage document what happened.
Original cloud orchestration sources in `experiments/hitl_ablation/provenance/`
are historical evidence and depend on retired operational helpers; they are not
runnable reviewer entry points. The complete numerical protocol and every received
program remain inspectable through the portable audit/replay tools.
For a new historical-style AlphaEvolve campaign, use
[the optional cloud setup](alphaevolve_gcp_setup.md). It requires the reader's own
account and budget; fresh model sampling is not an exact replay of this paper.
