# MMU Reproduction Guide

Audience: a researcher who has this branch and wants to rebuild the simulator,
re-run the eight MMU fault models, and verify the frozen campaign.

Nothing in this guide depends on the original `/home/sdc/gem5-fi-mmu-impl-v2`
workspace. The only external inputs are the two runtime assets described in
section 2.4.

---

## 1. Environment

The frozen campaign was executed on the 0202 server with:

| Item | Value |
|---|---|
| OS | openEuler 22.03 LTS |
| Architecture | aarch64 (native, no cross toolchain) |
| Compiler | gcc (GCC) 10.3.1 |
| Python | 3.8.18 |
| SCons | 4.11.1 |
| CPU / RAM | 96 cores / 313 GB |
| gem5 base | upstream `62c7bf284864b83f7308f5e14ca9c80812621c29` (vendored) |
| Python packages | `openpyxl`, `PyYAML`, `pytest` (`reproduction/requirements.txt`) |

Guest requirements: AArch64 Linux full-system image, the boot checkpoint
`mmu_bootF1/cpt.244799013609`, and the matching disk template. The checkpoint
enables `FEAT_EPAN` (`ID_AA64MMFR1_EL1.PAN=3`), which M07-R03 needs.

Build memory: use **`-j16`** on a 29 GB host. `-j126` OOM-kills the build.
The 0202 server is larger, but `-j16` is the safe documented default.

---

## 2. Download and build

### 2.1 Clone

```bash
git clone https://github.com/wangxumarshall/gem5-fi.git
cd gem5-fi
git checkout mmu-final-reproducible
git rev-parse HEAD          # record this SHA
```

Repository: `https://github.com/wangxumarshall/gem5-fi`
Branch: `mmu-final-reproducible`

### 2.2 Python dependencies

```bash
python3 -m pip install -r MMU_FINAL/reproduction/requirements.txt
```

### 2.3 Build gem5

```bash
MMU_FINAL/reproduction/build_mmu.sh
```

This runs `scons -j16 build/ARM/gem5.opt` inside `CHAOS/gem5` and checks that
all eight model hook identifiers are present in `CHAOS/gem5/src`. The first
configure can take minutes per Python conftest; it is not hung.

The output path is `CHAOS/gem5/build/ARM/gem5.opt` (inside the vendored tree,
not a second copy at the repository root).

### 2.4 Runtime assets

Place the assets in this layout (they are copied, never symlinked):

```
<ASSET_ROOT>/gem5-fs/vmlinux
<ASSET_ROOT>/gem5-fs/boot.arm64
<ASSET_ROOT>/runs/disks/mmu_template.img
<ASSET_ROOT>/runs/mmu_bootF1/cpt.244799013609/
```

Then:

```bash
MMU_FINAL/reproduction/prepare_runtime_assets.sh <ASSET_ROOT>
```

`boot.arm64` and the checkpoint are bundled in
`MMU_FINAL/runtime_assets/`. `vmlinux` and `mmu_template.img` are
`EXTERNAL_ASSET_NOT_YET_DISTRIBUTED` — see
`External_Artifacts_Manifest.json`. **Without them the full-system samples
cannot run**, even though the code builds and the archive verifies.

Verify the assets:

```bash
sha256sum gem5-fs/vmlinux          # 9b9b9ce70bc6fb831461b527ccf36f124f1af8f3dc717d7ef13e62060aecfa7e
sha256sum runs/disks/mmu_template.img
                                   # bb872707d6bae3885688556908536d4f92e07da68aae0401d27ff03216425759
```

### 2.5 Preflight

```bash
MMU_FINAL/reproduction/preflight_mmu.sh
```

This is read-only. It checks dependencies, frozen authority, workloads,
runtime assets, all archive hashes, and generates the 40 `--describe` plans.

---

## 3. The eight models

Common trigger: F0 deterministic event selection, `--mmu_fault_enable true`,
seed `N/A_DETERMINISTIC`. Every sample runs one gem5 process, with a fresh
disk copy and a private output directory.

### M01 — L2/Unified TLB invalidation suppression

- Fault site: `retain_l2_complete_invalidation`
- Workload: W9, read contexts R01-R05
- Semantics: a matching TLBI is suppressed, the stale L2 entry survives, and a
  later lookup consumes the old PA.
- Expected activation: `mmu_fault_arm` → `tlbi_suppressed` →
  `tlb_lookup_hit` → old PA → LSU → oracle.
- Frozen terminal: 5 SDC (stale marker `0xAA` instead of `0x55`).

### M02 — PTW refill PFN corruption

- Fault site: `refill_pfn_corrupt`, `refill_pfn_xor_bit0`
- Workload: W10, R01-R05
- Parameters: per-context `--mmu_m02_old_pfn` resolved from an independent
  no-fault W10 control; `--mmu_m02_xor_mask 1`; DRAM range
  `0x80000000..0x100000000`.
- Frozen terminal: 5 SDC (PFN `0x834b2 → 0x834b3` in R02).

### M03 — ASID tag-match false positive

- Fault site: `tlb_lookup_miss_false_hit`
- Workload: W11, R01-R05
- Semantics: on a TLB miss, a foreign-ASID entry is selected
  (`candidate_asid != request ASID`).
- Frozen terminal: R01-R04 SQUASHED (PARTIAL propagation by design), R05 SDC
  (execute consumer).

### M04 — Resident TLB entry PFN corruption

- Fault site: `tlb_lookup_hit_pfn_subst`
- Workload: W12, R01-R05
- Semantics: entry_id/generation remains valid; the PFN is substituted with a
  different mapped page of the same size.
- Frozen terminal: 5 SDC.

### M05 — Partial walk-cache pointer corruption

- Fault site: `ptw_insertPartialTableEntry`
- Workload: W13, R01-R05
- Parameters: `--mmu_target_n 21` (2 MiB), `--mmu_target_walk_level 2`,
  `--mmu_m05_decoy_table_base 0`, `--mmu_m05_decoy_va 0x4010200000`.
- Semantics: the partial entry's `next_table_pa` changes and a later partial
  hit resumes at the decoy L3 table.
- Frozen terminal: 5 SDC.

### M06 — Leaf descriptor validity corruption

- Fault site: `ptw_doLongDescriptor_valid_clear`
- Workload: W10 / W10S, R01-R05 (R02 is the W10S cold store)
- Semantics: descriptor bits `[1:0]` go `0b11 → 0b10` on the fetched leaf; PTE
  memory is **not** written. The translation fault is detected and delivered.
- Frozen terminal: 5 DETECTED_CONTAINED (`fault_state_consumed=1`,
  `fault_result_propagated=1`, `exception_delivery=1`, guest sees the correct
  sentinel).

### M07 — Permission grant decision inversion

- Fault site: `mmu_checkPermissions64`
- Workload: W14, R01-R05
- Semantics: same VA/PA/PFN; `permission_before=false → permission_after=true`.
- Frozen parameters: R03 = PAGE_EXECONLY + EL0 load; R04 target
  `0x400d400100`; R05 target `0x400d600180`.
- Frozen terminal: 5 SDC. Manifestation is **permission bypass**
  (UNAUTHORIZED_WRITE / UNAUTHORIZED_READ / UNAUTHORIZED_EXECUTION /
  WRONG_CODE_PAGE_EXECUTION), not a numeric miscalculation.

### M08 — Final PA materialization corruption

- Fault site: `mmu_translate_set_paddr`
- Workload: W10, R01-R05
- Parameters: `--mmu_m08_pa_xor_mask 0x1000`
- Semantics: TLB entry/PFN unchanged; the Request PA changes by XOR 0x1000.
- Frozen terminal: 5 SDC.

---

## 4. Build-equivalence policy

A rebuilt binary hashes differently if the compiler, flags, paths, or build
timestamps differ. A hash mismatch is **neither automatic success nor
automatic failure**:

1. Confirm the source closure: `git diff 60f1a876..HEAD -- CHAOS/gem5/src`
   must be empty for the frozen design.
2. Record compiler (`gcc --version`), SCons version, Python version, build
   flags and the checkout path.
3. Confirm the build was clean (no warnings/errors introduced).
4. Run the eight representative samples (section 5.4) and compare semantics:
   activation kind/fault site, entry identity relation, VA→PA change,
   downstream consumer, oracle result, terminal state.
5. Only then report semantic reproducibility. Never replace fault semantics
   with "the build succeeded".

When the rebuilt binary differs, enable the explicit waiver for an
independent replication:

```bash
export MMU_ALLOW_REBUILT_BINARY=1
MMU_FINAL/reproduction/preflight_mmu.sh
MMU_FINAL/reproduction/run_mmu_sample.sh M01-F0-W9-S01-R01 /data/rebuilt-smoke
```

The waiver is recorded in the plan/manifest as
`global.gem5_sha256_waived` with both hashes. It is **not** a silent pass:
source hashes and workload hashes must still match the frozen values, and the
original 40/10 campaign was produced without any waiver.

The frozen artifact remains the authority for the original 40/10 results.

---

## 5. Running experiments

### 5.1 One sample

```bash
MMU_FINAL/reproduction/run_mmu_sample.sh M01-F0-W9-S01-R01
# output: runs/MMU_FINAL_VALIDATION/M01-F0-W9-S01-R01/
```

The runner refuses to overwrite an existing non-empty directory and refuses
any output under the frozen campaign.

### 5.2 The 40 formal contexts

```bash
# command generation only (default)
MMU_FINAL/reproduction/run_mmu_formal_40.sh --dry-run

# actual replication into a fresh root
MMU_FINAL/reproduction/run_mmu_formal_40.sh --execute /data/mmu-replica-40
```

This is an independent replication. The original campaign is never touched.

### 5.3 The 10 repeat runs

```bash
MMU_FINAL/reproduction/run_mmu_repeat_10.sh --dry-run
MMU_FINAL/reproduction/run_mmu_repeat_10.sh --execute /data/mmu-replica-repeat10
```

The archived `command.sh` is reused; only repository root, output directory and
the fresh disk copy are rewritten. Fault parameters and run IDs are unchanged.

### 5.4 Eight-model representative smoke test

Use these frozen samples (one per model, all legal members of the 40-sample
matrix):

| Model | SampleRunID |
|---|---|
| M01 | `M01-F0-W9-S01-R01` |
| M02 | `M02-F0-W10-S01-R02` |
| M03 | `M03-F0-W11-S01-R05` |
| M04 | `M04-F0-W12-S01-R05` |
| M05 | `M05-F0-W13-S01-R05` |
| M06 | `M06-F0-W10-S01-R02` |
| M07 | `M07-F0-W14-S01-R05` |
| M08 | `M08-F0-W10-S01-R01` |

```bash
for s in M01-F0-W9-S01-R01 M02-F0-W10-S01-R02 M03-F0-W11-S01-R05 \
         M04-F0-W12-S01-R05 M05-F0-W13-S01-R05 M06-F0-W10-S01-R02 \
         M07-F0-W14-S01-R05 M08-F0-W10-S01-R01; do
  MMU_FINAL/reproduction/run_mmu_sample.sh "$s" /data/mmu-smoke
done
```

Each run writes `Trace/prop_evt.txt.gz`, `Run_Log/board.terminal`,
`Run_Log/golden_output.txt`, `Validation/verdict.json`, `sample_manifest.json`
and `SHA256/SHA256SUMS.txt`.

### 5.5 Viewing traces and chains

```bash
zcat runs/.../Trace/prop_evt.txt.gz | grep '^PROP-EVT:' | head
python3 tools/mmu_causal_slice.py --help
python3 tools/mmu_chain_slice.py --help
```

Frozen causal slices and per-sample propagation chains are already archived in
`MMU_FINAL/results/formal/campaign_package/propagation_chains/`.

### 5.6 Diagnostic features

`MMU_FINAL/results/diagnostic/feature_library/` contains the CSV/JSON/XLSX
feature library and `Model_Propagation_Signatures.md` (model signatures, key
discriminators, confusable paths, ranked root-cause features).

Blinded views, simulation-assisted views and the leakage audit are in
`results/diagnostic/views/` and `results/diagnostic/leakage/`. Their
observability constraints are retained verbatim; do not remove them.

---

## 6. Result semantics

| Field | Meaning |
|---|---|
| `ACTIVATED` | The fault hook fired at the selected event. |
| `CONSUMED` / `FaultStateConsumed` | The corrupted state was actually used downstream. |
| `PropagationStatus=FULL` | The fault reached a software-visible consumer. |
| `PropagationStatus=PARTIAL` | Propagation legally stopped before a data-side consumer (e.g. squash). |
| `TraceCompleteness=COMPLETE` | The raw trace covers the required path; independent of propagation depth. |
| `SDC` | Wrong architectural outcome: wrong value **or permission bypass**. |
| `DETECTED_CONTAINED` | The fault was consumed and detected; the guest recovered (M06). |
| `SQUASHED` | The faulted operation was squashed before architectural update (M03 R01-R04). |
| `OracleResult=FAIL` | Guest oracle differs from the no-fault control. |
| `PASS_EXPECTED_DETECTION` | Fault detected and contained; the guest sees the correct sentinel. |

Do not describe M07 as an ordinary value error. It is an authorization
bypass.

---

## 7. Research limitations

These limitations are part of the result, not cleanup noise:

1. **Simulator-only observation signals.** Some diagnostic features exist only
   in the simulator's `prop_evt` stream; they are not claims of hardware
   observability.
2. **Blinded diagnostic inputs.** The blinded feature set was generated under
   its recorded observable/target conditions. Those restrictions must be
   preserved.
3. **IFU coverage.** The frozen binary does not emit per-instruction IFU
   fetch-response, decode or IFU-specific commit events. Instruction-side
   samples join MMU translation/permission → Execute Request → guest oracle and
   mark unobserved nodes `NOT_EMITTED_BY_FROZEN_BINARY`.
4. **Synthetic execute requests.** Execute-side consumption is evidenced within
   that join; it is not a full instruction-fetch trace.
5. **Repeatability scope.** Ten independent repeats establish determinism for
   the selected contexts. They are not a distribution over all possible
   microarchitectural timings.
6. **Model equivalence.** M01-M08 are simulator abstractions of MMU failure
   modes; they are not claimed to be bit-exact models of every physical ARM
   implementation.
7. **External assets.** `vmlinux` and the disk template are not publicly
   distributed yet. This blocks independent full-system execution outside the
   0202 server, although the archive and code are complete.

---

## 8. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `gem5 binary missing` | Run `reproduction/build_mmu.sh`. |
| `kernel missing` / `disk template missing` | Run `reproduction/prepare_runtime_assets.sh`. |
| `BKPT`/`HANG` at restore | Checkpoint/disk mismatch or missing EPAN-capable kernel. |
| `refusing to overwrite` | Choose a new output root; never reuse a formal directory. |
| describe fails for one sample | Run preflight; inspect `/tmp/mmu_describe_<SampleRunID>.txt`. |
| build OOM | Lower `MMU_BUILD_JOBS` (default 16). |
