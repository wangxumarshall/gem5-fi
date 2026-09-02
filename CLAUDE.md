# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is


## Build & run


## Architecture

## Writing fi

## Patch discipline (feature/porting/bug/adapter)

This repository enforces a strict one-patch-per-unit workflow. Apply it to **every** change, including ARM64 porting points, feature development, bug fixes, and architecture adapters.

### One patch per unit

Each feature, functionality point, bug, or adaptation point is its own commit. Never bundle unrelated changes into one commit. A "unit" means a single coherent item from a work list (e.g. "#13 uncore frequency exit bug" is one patch; "#12 thermal monitor" is the next). When a task spans several numbered points, solve them **one at a time, sequentially** — finish one (verify → commit → push) before starting the next. Do not parallelize or batch.

### Self-verification before commit (mandatory, 100% real)

After writing code and before committing, the AI **must verify itself** with real commands — no claims based on "it should work" or reading the diff. Specifically:

1. **Build clean**: any warning/error introduced by the change is a failure.
2. **Functional verification**: run the actual affected behavior with real commands and capture real output. Quote the real observed output as proof, not a prediction.
3. **Regression check**: run at least one unaffected test and confirm `exit: pass`, zero SIGSEGV, to prove no collateral breakage.

Do **not** commit if any of these fail. If a verification step fails, fix and re-verify until it passes. Skipping verification or fabricating results ("assumed to pass") is strictly forbidden — every claim in the commit message must correspond to a command the AI actually ran.

### Auto-push to a non-main branch after verification

Once a patch is committed and verified, **push it automatically to the remote** — do not wait to be asked, and do not push to `main`. Work on a feature branch (e.g. `fix/mce-check-arm64-null-test-run`) and `git push` after each commit. If on `main` when starting work, create/switch to a feature branch first (`git checkout -b <branch>`) before committing.

Commit message must not end with:
```
Co-Authored-By: Claude <noreply@anthropic.com>
```
### Plan-driven workflow (mandatory for every non-trivial change)

All non-trivial work — feature development, porting, refactors, multi-step fixes, anything beyond a single obvious line — **must** be executed via a written plan using the `superpowers:writing-plans` skill, not ad-hoc. "Trivial" means a typo or a one-line obvious fix the change itself describes completely.

1. **Plan first**: before writing any code, invoke `superpowers:writing-plans` and save the plan to `docs/superpowers/plans/YYYY-MM-DD-<feature>.md`. The plan defines one-patch-per-unit decomposition, exact files, real test commands, and per-step checkboxes (`- [ ]`).
2. **Plan == the work list**: each plan task maps to exactly one commit, satisfying "One patch per unit" above. Do not bundle multiple plan tasks into one commit, and do not commit work not in the plan.
3. **Track progress visibly**: implement via `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans`. Check off each `- [ ]` as it completes; the live plan file is the single source of truth for what is done vs pending. If the scope changes mid-execution, edit the plan file first, then proceed.
4. **Verify against the plan, not the diff**: the self-verification above applies per task; a task is not "done" until its plan-specified verification command's real output is quoted and its checkbox is checked.
5. **Provenance**: keep plan files in the repo under `docs/superpowers/plans/` (they document *why* a change was made one unit at a time, complementing git history).

If a request would produce more than one commit, write the plan first. No plan, no code.

### Placeholder-test honesty

When porting a feature that cannot be fully implemented yet (e.g. SMI counting on ARM, IST backend), the test must report a clean skip with reason `"to be implemented (placeholder): <what's missing>"` (return `EXIT_SKIP` from `test_init`, **not** `EXIT_SUCCESS`). A no-op test that returns success is a bug — it falsely reports `pass`. The `mce_check` test, by contrast, is a *real* EDAC-backed test on ARM64 and should `pass`.
### 必须诚实、不能说谎、必须100%服从事实、所有工作和结果必须基于事实并且经过严格的逻辑推理或实证，永远尊重事实、永远真诚。
