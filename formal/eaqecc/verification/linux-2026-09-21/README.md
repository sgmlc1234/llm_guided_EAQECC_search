# Fresh Linux Comparator replay — 2026-09-21

Theorem 1 and the supporting Lemma 2 both passed the exact-goal comparison and Lean kernel replay, with exit code 0 and “Your solution is okay!”. The original source manifest passed before and after the run. All ten package revisions matched the preserved lockfile.

The theorem sources and proof goals were not changed. Lean is 4.29.0-rc6; Comparator is a4f696825c583ed8a5b4060d9a0faa5b882d365b; lean4export is 048394e1afeeb52b0fa27bcf3f1ade2ff0f0ab6d. The exporter source is unchanged. Binary hashes and package revisions are in environment.json.

The unpatched run reproduced landrun 0.1.17 consuming the exporter argument separator. The attached comparator-landrun-separator.patch inserts `--` before the executable in the CLI argument construction. No comparison, axiom-policy, exporter, or kernel checking logic was edited. The failed attempt and argument probe are retained. This is a new reproducible repair, not the historical patch, which has not been recovered.

Full logs are included with private filesystem prefixes replaced by placeholders. Original unredacted bytes are retained under ignored notes/private/. The Linux host uses x86_64; the historical supplied README described a different Ubuntu/aarch64 run. These fresh results must not be relabeled as that historical execution.

The main paper should focus on Theorem 1. Lemma 2 remains a supporting codebase certificate. Optional nanoda is disabled in the preserved configurations; a Linux replay of the Lean kernel is not an independent-kernel validation.
