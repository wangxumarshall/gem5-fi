# MMU Independent Reproduction Validation Report

Date: 2026-11-15
Location: `/var/tmp/mmu-repro` (isolated from the historical workspace)

## 1. Clone

```
git clone --branch mmu-final-reproducible --depth 1 \
    git@github.com:wangxumarshall/gem5-fi.git /var/tmp/mmu-repro/gem5-fi
```

| Item | Value |
|---|---|
| Remote | `https://github.com/wangxumarshall/gem5-fi` |
| Branch | `mmu-final-reproducible` |
| Validated commit | `100f9ce3` |
| Clone independence | no path, symlink or env variable points at `/home/sdc/gem5-fi-mmu-impl-v2` |
| Archive check in clone | `MMU_ARCHIVE_INTEGRITY=PASS` (1514 files, 40 samples, 28 controls, 10 repeats) |

## 2. Runtime assets

Copied (not symlinked) into the clone with
`reproduction/prepare_runtime_assets.sh`:

| Asset | SHA256 |
|---|---|
| `gem5-fs/vmlinux` | `9b9b9ce70bc6fb831461b527ccf36f124f1af8f3dc717d7ef13e62060aecfa7e` |
| `gem5-fs/boot.arm64` | `37ca07b55da2c0843d6670bb0693d21159236e0c6b74526f531abaeeaab51bfd` |
| `runs/disks/mmu_template.img` | `bb872707d6bae3885688556908536d4f92e07da68aae0401d27ff03216425759` |
| checkpoint `cpt.244799013609` | files present; recomputed manifest digest `ab200657...` |

## 3. Independent build

```
MMU_BUILD_JOBS=16 MMU_FINAL/reproduction/build_mmu.sh
```

Real output:

```
[mmu] built binary: .../CHAOS/gem5/build/ARM/gem5.opt
[mmu] sha256:       16a954c7029dcbfa27e6f783483333980981af5b7f5f436f6fdccbddc230d2c5
[mmu] frozen:       b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185
[mmu] binary differs from the frozen artifact; this is reported, not hidden.
[mmu] hook present: M01 ... M08
BUILD_EXIT=0
```

The rebuilt binary differs from the frozen artifact because the build path,
build date and embedded paths differ. Source closure was checked with
`git diff 60f1a876..872953c2 -- CHAOS/gem5/src` (empty). The source and
workload hashes are still checked exactly by the runner; the binary mismatch
uses the explicit `MMU_ALLOW_REBUILT_BINARY=1` waiver, recorded per run as
`global.gem5_sha256_waived`.

Compiler: gcc 10.3.1; SCons 4.11.1; Python 3.8.18; openEuler 22.03 LTS
aarch64; `-j16`.

## 4. Preflight in the independent clone

Real output:

```
PASS  workload W9 ... W14
PASS  gem5 16a954c7...
PASS  kernel / checkpoint / disk template
MMU_ARCHIVE_INTEGRITY=PASS
PASS  describe plans: 40/40
MMU_PREFLIGHT=PASS
```

The control oracles resolved from
`MMU_FINAL/results/formal/controls/` because `runs/TEST-F1-CTRL-*` does not
exist in a fresh clone. This required a real code fix (commit `6a5dd8ca`) and
is not hidden.

## 5. Eight-model smoke test

Representative samples (one per model, all members of the frozen matrix):

| Model | SampleRunID | Runtime | Activation / site | Terminal | Status |
|---|---|---|---|---|---|
| M01 | M01-F0-W9-S01-R01 | 236 s | `mmu_fault_arm` / L2 invalidation suppression | SDC (orig SDC) | PASS |
| M02 | M02-F0-W10-S01-R02 | 2310 s | `refill_pfn_corrupt` / refill PFN | SDC (orig SDC) | PASS |
| M03 | M03-F0-W11-S01-R05 | 1090 s | `mmu_fault_activate` / `tlb_lookup_miss_false_hit` | SDC (orig SDC) | PASS |
| M04 | M04-F0-W12-S01-R05 | 1112 s | `mmu_fault_activate` / `tlb_lookup_hit_pfn_subst` | SDC (orig SDC) | PASS |
| M05 | M05-F0-W13-S01-R05 | 1090 s | `mmu_fault_activate` / `ptw_insertPartialTableEntry` | SDC (orig SDC) | PASS |
| M06 | M06-F0-W10-S01-R02 | 2853 s | `mmu_fault_activate` / `ptw_doLongDescriptor_valid_clear` | DETECTED_CONTAINED (orig DETECTED_CONTAINED) | PASS |
| M07 | M07-F0-W14-S01-R05 | 1092 s | `mmu_fault_activate` / `mmu_checkPermissions64` | SDC (orig SDC) | PASS |
| M08 | M08-F0-W10-S01-R01 | 2304 s | `mmu_fault_activate` / `mmu_translate_set_paddr` | SDC (orig SDC) | PASS |

All eight runs:

- activated the intended hook (activation kind and fault site match);
- consumed the fault downstream (`FULL` propagation) and produced a
  `COMPLETE` trace;
- reproduced the original terminal state and oracle result
  (M06 `PASS_EXPECTED_DETECTION`, the others `FAIL`);
- reported no validator contradictions.

`MMU_8_Model_Smoke_Test_Results.csv` records the trace/verdict SHA256 and the
machine-readable comparison.

## 6. Result

```
MMU_REPRODUCIBILITY_GATE=PASS
```

The final branch independently clones, builds, passes all 40 describe plans,
and runs all eight models with matching semantics. This is the precondition
for the cleanup white-list. No historical asset has been deleted; permanent
deletion awaits researcher approval.
