# Installing external tools and performing fresh verification

These steps are separate from the Python-only checks. The release validation
record does **not** claim that SAT/DRAT or Magma was freshly rerun in an environment
without those tools. Original certificates and the 148-object Magma log are
included; follow this guide to obtain fresh evidence. Run the verification commands
from the repository root and keep new outputs outside the archive.

## 1. CaDiCaL and DRAT-trim

CaDiCaL decides whether a CNF is satisfiable; DRAT-trim independently checks an
UNSAT proof. A solver's UNSAT answer alone is not a completed certificate check.
The recorded qutrit run used CaDiCaL 3.0.0 and these exact source revisions:

| Tool | Source revision |
|---|---|
| CaDiCaL | `7b99c07f0bcab5824a5a3ce62c7066554017f641` |
| DRAT-trim | `2e3b2dc0ecf938addbd779d42877b6ed69d9a985` |

Prerequisites: Git, Make and a C/C++ compiler. On macOS, install the Xcode Command
Line Tools if those build tools are unavailable. On Linux, use your distribution's
compiler/build-tool packages. Put the tool sources outside this repository:

```bash
export EAQECC_TOOL_DIR="$HOME/.local/share/eaqecc-tools"
mkdir -p "$EAQECC_TOOL_DIR"
git clone https://github.com/arminbiere/cadical.git "$EAQECC_TOOL_DIR/cadical"
git -C "$EAQECC_TOOL_DIR/cadical" checkout --detach 7b99c07f0bcab5824a5a3ce62c7066554017f641
(cd "$EAQECC_TOOL_DIR/cadical" && ./configure && make -j4)

git clone https://github.com/marijnheule/drat-trim.git "$EAQECC_TOOL_DIR/drat-trim"
git -C "$EAQECC_TOOL_DIR/drat-trim" checkout --detach 2e3b2dc0ecf938addbd779d42877b6ed69d9a985
make -C "$EAQECC_TOOL_DIR/drat-trim" drat-trim

export CADICAL_PATH="$EAQECC_TOOL_DIR/cadical/build/cadical"
export DRAT_TRIM_PATH="$EAQECC_TOOL_DIR/drat-trim/drat-trim"
"$CADICAL_PATH" --version
```

Use new directories if these clones already exist. The build commands follow the
[CaDiCaL instructions](https://github.com/arminbiere/cadical/tree/7b99c07f0bcab5824a5a3ce62c7066554017f641)
and the [DRAT-trim build target](https://github.com/marijnheule/drat-trim/blob/2e3b2dc0ecf938addbd779d42877b6ed69d9a985/Makefile).

Install the Python dependencies into your active environment and check the
shipped certificates:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/reproduce_eaqecc.py --claim refutations --out ../verification/refutations
```

Nine CNF/proof pairs are included. Without the tenth on-demand proof, the report
can remain PARTIAL even after the nine available proofs pass. To include it:

```bash
export EAQECC_PROOF_CACHE="$(pwd)/../verification/proofs"
mkdir -p "$EAQECC_PROOF_CACHE"
python3 scripts/refutations/sat_normal_form_q2.py --only 10,1,5,9 --proof --timeout 180 --out "$EAQECC_PROOF_CACHE"
sat_exit=$?
test "$sat_exit" -eq 20
python3 scripts/reproduce_eaqecc.py --claim refutations --out ../verification/refutations-complete
```

Exit code 20 from the encoder means UNSAT, following the SAT solver convention.
Reserve at least 1 GB for the approximately 0.6 GB uncompressed on-demand proof
and temporary outputs. The 180-second timeout is a starting allowance, not a
cross-machine runtime guarantee; inspect logs before increasing it. Full success
requires all ten decisions and all ten proof checks to succeed. The report gives
separate statuses per entry. Retain both its JSON and Markdown outputs.

To regenerate the qutrit proof or run its known-code positive control, use
[the qutrit certificate instructions](qutrit_certificate.md). The mathematical
coordinate-normalization lemma remains part of the justification; a DRAT check
does not mechanically establish that lemma.

## 2. Magma

The archived cross-check used Magma V2.28-20 on 148 objects: 115 core codes
and 33 family instances. Use that version when available to match the recorded
software environment, and record the version if using a different release.

Obtain a distribution for your platform through the
[official Magma downloads](https://magma.maths.usyd.edu.au/magma/download) and follow
[the official installation instructions](https://magma.maths.usyd.edu.au/magma/faq/install).
Magma requires a machine-specific `magmapassfile`; obtain and install your own
through [the documented license-file process](https://magma.maths.usyd.edu.au/magma/faq/magmapassfile).
The executable, common files and license file are not bundled with this artifact.

After installation, launch Magma once to confirm that its license and common
files are available. Set `MAGMA_PATH` to the installed **magma launcher**, which
initializes the package paths, rather than directly to `magma.exe`. For example,
replace the placeholder with your actual path:

```bash
export MAGMA_PATH="/path/to/your/magma/launcher"
python3 scripts/reproduce_eaqecc.py --claim magma-crosscheck --out ../verification/magma
```

Expected: a fresh 148/148 verification with zero mismatches. Without a runnable
Magma installation, the saved log remains archived evidence, and the command
must not be interpreted as a fresh cross-check.

Alternatively, use a licensed host you control:

```bash
export MAGMA_SSH_HOST="your-magma-host"
unset MAGMA_PATH
python3 scripts/reproduce_eaqecc.py --claim magma-crosscheck --out ../verification/magma-remote
```

The remote host needs `magma` and `timeout` on PATH; the client needs `ssh` and
`scp`. The script uses a temporary remote directory and cleans it up. If a local
Magma is already on PATH, the auditor prefers it; use the local installation or
an environment without that local executable to select SSH. No remote execution
is attempted unless the host is explicitly configured.

## 3. Keep installation state outside the anonymous release

Do not add binaries, tool clones, `magmapassfile`, credentials, host configuration
or machine-local reports to Git. The environment variables above are execution
settings, not manuscript inputs. The anonymous ZIP contains the original evidence
and generic instructions, while your fresh verification outputs stay separate.
