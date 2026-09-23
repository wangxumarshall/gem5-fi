# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

gem5-fi is an AArch64 microarchitecture **fault-injection (FI) research platform** built on a vendored gem5 v25.1.0.1 tree (`CHAOS/gem5/`, upstream commit `62c7bf2` recorded in `CHAOS/gem5_base_version.md`). 

Two experiment tracks share the toolchain but have **different scopes — never mix their numbers**:

The host is native aarch64 (openEuler24.03): workload ELFs build with host `gcc -O2 -static` — no cross toolchain.

## Build & run

### Build gem5 (only for C++ changes under `CHAOS/gem5/src/`)

```bash
cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt    # clean build: MUST be -j16 (-j126 OOM-kills on 29 GB host)
cd CHAOS/gem5 && scons -j126 build/ARM/gem5.opt   # incremental rebuilds only
```

- First configure is slow (~2 min per `Checking Python version...` conftest) — it is **not hung**; do not abort.
- Every tool invokes the **repo-root** `build/ARM/gem5.opt`. A stale duplicate under `CHAOS/gem5/build/ARM` once caused fake segfaults — always reference the repo-root path in commands.
- Python-only changes (`configs/**`, `tools/**`, workloads) need **no** rebuild.

### Run one workload (SE)

```bash
build/ARM/gem5.opt --outdir=/tmp/out configs/se/arm_chaos.py --cmd workloads/directed/reg_chain --cpu O3
# OoO north-star platform: configs/se/ooo_proxy.py --cmd workloads/ooo/<name>/<name> --cpu O3
```

### Canonical regression (the "unaffected test" for patch discipline)


### Workloads

### Experiments

### Standalone unit test (trigger semantics, outside the gem5 build)


### Full-system (FS)

Needs `gem5-fs/` (kernel + disk images; a ~3 GB git submodule, contents not in this repo). Boot via checkpoint; the restore-tick baseline **is the checkpoint directory name** — ROI windows must be computed from that baseline. Hard cap **4 concurrent gem5 processes** (more OOM-kills the whole batch).

## Architecture

### Vendored gem5 + injectors

`CHAOS/gem5/` is a plain-file vendored gem5 (nested `.git` deleted). All C++ that actually builds lives under `CHAOS/gem5/src/`:

- `src/CHAOSReg/` — architectural GPR injector (commit-map abstraction; the committed mapping lags in-flight reads on O3 — for O3 PRF work use CHAOSPhysReg).
- `src/mem/CHAOSMem/`, `src/mem/cache/CHAOSCache/` — DRAM injector (`protectionModel` none/sed/secded_poison/secded) and cache-line injector.
- `src/cpu/o3/CHAOS*` — OoO-family injectors: **PhysReg** (physical PRF cells; modes `phys` / `arch_frontend` / `arch_commit` — only `phys` matches the ITC'23 abstraction, `arch_commit` fails on O3), **RenameMap** (RAT), **FreeList**, **ROB**, **IQ**, **Exec**, **FPU**, **LSQFwd**, **L1DForward**, **BPU**, **AddrPath**, **Decode**, **ExMon**, **RAS**, **Probe** (occupancy/threshold sampler), plus shared headers `chaos_trigger.hh` / `chaos_event_sample.hh`.
- Arm **TLB / SysReg / PTW** injectors — FS-only (SE-inert by construction).

The top-level `CHAOS/<Name>/` dirs are the **original standalone plugin copies** (some stale vs the vendored tree) — editing them changes nothing; edit `CHAOS/gem5/src/...`.

Many injectors **self-attach** in their constructor (e.g. `cpu->lsqFwd = this`); the .py config only instantiates the SimObject. The O3 accessors/hooks (`cpu.hh`, `free_list.hh`, `regfile.hh`) ship pre-patched in the vendored tree.

### Config families (`runner.py` `CONFIG_FAMILY`)

C0 `arm_chaos.py` · C2 `kp920_proxy.py` (V110) · C3 `ooo_proxy.py` (north star) · C0-CACHE `arm_chaos_cache.py` · C0-FS `arm_chaos_fs.py` · C2-FS `configs/fs/kp920_proxy_fs.py`. All are gem5-stdlib SimpleBoard + classic caches; attaching extra SimObjects to stdlib boards is done by monkey-patching `hierarchy._pre_instantiate` before `sim.run()`.

### Experiment pipeline


### gem5 v25 gotchas (empirically hit)


### Repo discipline

- Multiple Claude sessions may work this repo concurrently — **never `git add -A`**; stage explicit paths (scratch files, `m5out/`, `runs/`, campaign outputs appear and disappear constantly).
- `.entire/` is an external agent-framework workspace that has force-reset the worktree before — commit finished work promptly.

## Writing fi

- **New injector = four-piece SimObject** (`.hh` / `.cc` / `.py` / `SConscript`). Copy the `CHAOSFreeList` skeleton: self-attach in ctor/`startup()`, periodic work via `EventFunctionWrapper` + `cpu->schedule(cpu->clockEdge(...))`, end-of-sim summary via an exit callback (see `CHAOSPhysReg.cc` `ReadTraceFinal`).
- **Trigger semantics**: use `src/cpu/o3/chaos_trigger.hh` (modes F0–F5) — never hand-roll probability checks. `lastClock` **0 means unrestricted** (a small nonzero "window" silently yields zero injections); use `maxFaults` for count control and a nonzero `rngSeed` for reproducibility.
- **ARM64 targets**: integer reg index ≥ 32 is banked (31 = XZR/Zero, excluded); fault masks on NEON/vector regs must be 64-bit — 32-bit masks under-cover 128-bit regs.
- **Wire new components end-to-end**: injector → config-family mount flags → `runner.py` dispatch → `schemas/manifest.schema.json` enum → `tools/manifest_validate.py`. A component not wired everywhere must be rejected loudly, not half-routed.
- **One classifier, no drift**: runner and campaign both import `tools/classify.py`; keep the fixed classification order and the oracle-specific Masked/SDC split there.
- **Honesty conventions**: report `n/a`, never silent zeros (e.g. `event_density.py` probe columns); unimplemented capabilities return `EXIT_SKIP`; directed controls are determinism replications, not independent samples.

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
