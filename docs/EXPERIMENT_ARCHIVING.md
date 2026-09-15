# Active experiment and archival boundary

Only `experiments/hitl_ablation/` is an active ablation-study dataset in this
submission. It contains every attempted request and retained outcome from the
latest follow-up, including excluded later proposals, time-limit failures,
unavailable responses and the pre-test truncation amendment. Exclusion of older
studies does not make this follow-up a first attempt: its calibration and common
research guidance were motivated by earlier exploratory work, as the paper states.

Earlier controlled studies, fixed-budget comparisons, code-reversion analyses,
replay probes and their obsolete builders/tests have been moved to a recoverable
research archive outside both Git working trees. A local archive index records
each original path and every file's SHA-256; all moved files were checked at the
destination. Original manuscript/figure copies and the latest raw, unsanitized
study are also preserved there. Copying indexed paths back restores the material.
The user-facing revision report provides the local archive location; machine-local
paths and private account files are not embedded in the submission.

Some old study data were already tracked in Git. The next tree records their
removal; existing commit history has not been rewritten. Ignore rules prevent
retired output directories from being accidentally re-added. Discovery campaign
sources, exact-verification data, certificates and deterministic search fingerprints
remain because they support the mathematical results and reproducibility checks,
not the superseded ablation comparisons.

The latest bundle has portable audit/replay entry points and its own integrity
manifest. The export index records machine-path/opaque-provider-metadata cleanup;
model-generated Python source bytes and all numerical observations are preserved.

Internal editorial reviews, submission-form working copy and obsolete export helper
are also preserved outside the source tree. Generated TeX auxiliary files are not
release inputs. Historical discovery sources, calibration controls, prompts,
failures, selected and excluded candidates, and all code/certificate records
needed by the current manuscript remain in the public artifact. A before-change
working-tree snapshot, file hashes and Git bundle are kept privately for recovery.
