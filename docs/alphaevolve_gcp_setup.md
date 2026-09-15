# Connecting the search stage to AlphaEvolve on Google Cloud

The search stage calls AlphaEvolve through Google Cloud. This document is
what a reader needs in order to run it, and — just as important — what
they can run *without* it.

## What needs no Cloud access

Everything except the evolutionary run. The reproduction command
re-derives every archived result locally:

```bash
python3 scripts/reproduce_eaqecc.py
```

That covers witness re-derivation, the closed-form families, the table
correction, openness against the dated snapshots, the archived
refutations, and the *seeded search itself* — the last one replays the
archived programs under a deterministic driver, which needs no network.
Cloud access is required only to evolve **new** programs.

## What the client actually talks to

`AlphaEvolveClient` (from Google's `alpha_evolve` package, pinned in `requirements-search.txt`) posts to

```
https://discoveryengine.googleapis.com/.../
  projects/$PROJECT_ID/locations/$LOCATION/
  collections/default_collection/engines/$GE_APP_ID
```

so AlphaEvolve is reached as a **Discovery Engine engine** ("app") that
you create in the Cloud console. Authentication is Application Default
Credentials — `google.auth.default()` — not an API key.

## Prerequisites

1. **Access.** Verify current project access and IAM permissions using the
   [official AlphaEvolve guide](https://docs.cloud.google.com/gemini/enterprise/docs/alphaevolve/reference-guide/api-reference?hl=en).
   The archived campaigns used an early-access configuration; Google
   subsequently [opened AlphaEvolve access](https://cloud.google.com/blog/products/ai-machine-learning/alphaevolve-is-available-for-everyone).
2. **A project with the API enabled.**
   ```bash
   gcloud services enable discoveryengine.googleapis.com --project $PROJECT_ID
   ```
3. **An AlphaEvolve app** created in that project. Its id is what
   `GE_APP_ID` must be set to. Ours was named for an earlier campaign;
   the name carries no meaning to the service.
4. **Credentials, once per machine.**
   ```bash
   gcloud auth application-default login
   gcloud auth application-default set-quota-project $PROJECT_ID
   ```
   The second line matters: without a quota project the client warns and
   attributes usage elsewhere, which surfaces later as confusing
   "API not enabled" errors.

## Running a campaign

```bash
export PROJECT_ID=my-project
export GE_APP_ID=my-alphaevolve-app
export MAX_PROGRAMS_GENERATED=120   # candidates to evolve
export SEARCH_BUDGET_S=240          # wall-clock per candidate
python3 scripts/alphaevolve_eaqecc/run_evolution.py
```

`PROJECT_ID` and `GE_APP_ID` have **no defaults**. Both are required, and
the script exits with the commands above if either is unset — a default
here would silently call a project that is not yours.

The launcher reads exported environment variables; it does not load `.env`
automatically. The managed campaign launcher has no KRW spending cap.
Its candidate count is not a monetary budget, and AlphaEvolve has an agent
charge in addition to Gemini model charges. Check the current
[Google price list](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing).

## Latest controlled comparison

The active reviewer bundle is `experiments/hitl_ablation/`. It preserves the
latest Vertex generateContent comparison, its request bodies, received sources,
usage ledger, unavailable-response records and pre-test protocol amendments.
The controlled local feedback loop is distinct from managed AlphaEvolve.

Use `python3 scripts/eaqecc_ablation/audit.py` for an offline audit and
`python3 scripts/eaqecc_ablation/replay.py --program b02_evolution_g02 --split transfer --out /tmp/eaqecc_replay`
for fixed-program reconstruction. Neither command calls a cloud model.
Historical launch sources under `provenance/` record the original operation;
they may refer to archived local ledgers and are not the portable entry points.
Account configuration is excluded from the reviewer bundle. No command in the
portable audit/replay path can consume the remaining model authorization.
