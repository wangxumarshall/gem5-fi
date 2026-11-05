# R6-P diagnostic audit — P07-c / P09-a / P09-c (2026-11-05)

Scope: the non-B0 diagnostic evidence cited by the P-unit closeout. These are
**not RunIDs** and are **not counted** in the 14 RunIDs / 42 seeds. The audit
checks (a) the exact command and gem5 build in `run.out`, (b) binary SHA
against a frozen artifact, (c) a no-fault control with the golden hash,
(d) raw events in `prop_evt.txt.gz`, (e) guest output and oracle, and
(f) lineage from the real fault event to a real `errant_commit`.

All three diagnostics use `--l2_size 16KiB` (non-B0 by construction). The
authoritative B0 `P09-F0-W6/W8` and `P07-F0-W6/W8` coverage blocks are
unchanged.

## Verdict table

| diagnostic | RunID? | binary (frozen) | SHA verified | control output | fault output | raw origin event | chain | oracle | status |
|---|---|---|---|---|---|---|---|---|---|
| P09-a writeback loss | no | `binaries/gem5.opt-c6953bba` | yes (frozen copy; STATE pin) | `062e5124df3667f9` | `8e64d8d4427c2169` | `pf_wb` ×1 + `cache_evict` ×3 | full / L5 | n/a | PASS |
| P09-c dirty clear (v2) | no | `binaries/gem5.opt-5b26240c` | yes (frozen copy) | `062e5124df3667f9` | `8e64d8d4427c2169` | `pf_dirty` ×1 + `cache_evict` ×3 | full / L5 | n/a | PASS |
| P07-c stale tag | no | `binaries/gem5.opt-5b26240c` | yes (frozen copy) | `062e5124df3667f9` | `fcecec2dd089d871` | `pf_stale_tag` ×1 | full / L5 | n/a | PASS |
| P09-b done early | no | — | — | — | — | — | — | — | MODEL_NOT_EXPRESSIBLE_AT_SITE |

## Per-diagnostic detail

### P09-a — dirty writeback request suppressed

- Evidence: `p09_diag_l2small_fault_20261104/P09-DIAG-W6-L2_16KiB/seed1`,
  control `p09_diag_l2small_20261104b/16KiB`.
- Command (from `run.out`): `--prefetch_mode p09_wb_loss`, F0, warm-up 1,
  span 378, max-faults 1, seed 1, `--l2_size 16KiB`.
- Binary: frozen `c6953bba…` (STATE-pinned; the original build path was
  later overwritten by later P work, the frozen copy is the identity
  artifact). Compiled Nov 4 2026 19:00:58.
- Raw events: 1 `pf_wb` origin, 3 `cache_evict`, 4 `taint_reg`, 1 real
  `errant_commit`; checker per-fault terminal `full`, `provable_to=L5`
  (L0→L1→L2→L3→L4→L5 all proven).
- Output: fault `8e64d8d4427c2169`, control golden `062e5124df3667f9`;
  oracle `n/a` (direct diagnostic).

### P09-c — dirty state cleared before the eviction decision

- Original evidence: `p09c_diag_l2small_fault_20261105` and
  `p09c_diag_l2small_nofault_20261105`. Its binary was the worktree build
  `c8b0e25f…`, which was **overwritten** by the later P07-c build and is
  not on disk — a provenance gap in the original directory.
- Correction (v2, authoritative identity): re-ran the exact command with the
  frozen `binaries/gem5.opt-5b26240c` (same P09-c source plus P07-c, which
  is mode-gated) into
  `p09c_diag_l2small_v2_fault_20261105` and
  `p09c_diag_l2small_v2_nofault_20261105`.
- Result: fault output `8e64d8d4427c2169`, control golden
  `062e5124df3667f9` — byte-identical to the original. Raw events: 1
  `pf_dirty` (`dirty→clean`), 3 `cache_evict`, 4 `taint_reg`, 1 real
  `errant_commit`; checker per-fault `full`/L5. Oracle `n/a`.
- The original directory is retained and labelled
  `BINARY NOT FROZEN — v2 is authoritative`.

### P07-c — old tag/valid reused

- Evidence: `p07c_diag_l2small_fault_20261105/P07C-DIAG-W6-L2_16KiB/seed1`,
  control/census `p07c_diag_l2small_20261105/16KiB`,
  `census_p07c_20261105`.
- Command: `--prefetch_mode p07_stale_tag`, F0, warm-up 1, span 595,
  max-faults 1, seed 1, `--l2_size 16KiB`.
- Binary: `5b26240c…` (original build; frozen copy exists).
- Raw events: 1 `pf_stale_tag` (new line 0x81080 keeps victim tag 0x77480),
  24 `taint_reg`, 1 real `errant_commit`; checker per-fault `full`/L5.
- Output: fault `fcecec2dd089d871`, control golden `062e5124df3667f9`;
  oracle `n/a`.
- B0 coverage: `census_p07c_20261105` W6/W8 show `victim_valid=0` at 1 MiB
  L2; no authoritative eligible event.

### P09-b — done early

Not a run: the classic gem5 L1D writeback is fire-and-forget
(`writebackBlk` clears dirty at creation and invalidates the line); there is
no completion ack at the dropped-writeback site. Recorded as
`MODEL_NOT_EXPRESSIBLE_AT_SITE`, not relabelled as P09-c.

## Honest boundaries

- Non-B0 diagnostics prove the model path end-to-end; they do **not** turn
  the authoritative B0 RunIDs into certified coverage.
- The P09-c original directory has a binary-identity gap; the v2 re-run
  restores a hash-verifiable identity and reproduces the same outputs.
- None of these entries adds a RunID, a seed, or a CATALOG row.
