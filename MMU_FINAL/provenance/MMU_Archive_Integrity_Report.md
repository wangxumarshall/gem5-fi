# MMU Archive Integrity Report

Date: 2026-11-15 (0202 server)
Branch: `mmu-final-reproducible`
Source closure: `60f1a8760410288128061d85582e5395b24c0106`
Frozen binary: `b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185`

## Commands executed and real output

```
$ python3 MMU_FINAL/reproduction/verify_archive.py
manifest files : 1514
formal samples : 40
controls       : 28
repeat traces  : 10
MMU_ARCHIVE_INTEGRITY=PASS

$ python3 MMU_FINAL/reproduction/validate_results.py
formal samples : 40
terminal       : {'DETECTED_CONTAINED': 5, 'SDC': 31, 'SQUASHED': 4}
activation     : {'ACTIVATED': 40}
trace          : {'COMPLETE': 40}
controls       : 28 unique / 40 sample mappings
repeat         : activation/propagation/terminal 10/10 MATCH
MMU_RESULT_INVARIANTS=PASS
```

## What was checked

1. **1514 archived files** match `MMU_Final_Results_SHA256.txt` byte-for-byte.
2. **40 formal sample directories**, each checked against its own
   `SHA256/SHA256SUMS.txt`: 758 source-side hashes across all samples
   (including binary/source/workload prefixes) passed with 0 mismatches;
   438 relative evidence files were re-checked in the staged tree with 0
   mismatches.
3. **28 control oracles** match the recorded SHA256 in `Control_Map.csv`;
   all 28 controls are `ZERO_PROVEN` and `PASS`.
4. **10 repeat traces** match `trace_index.csv` (10/10).
5. The 40-sample matrix is 40 rows with terminal **31 SDC / 5
   DETECTED_CONTAINED / 4 SQUASHED**, activation 40/40, trace COMPLETE 40/40.
6. The two A02 reruns (`M06-F0-W10-S01-R04`, `M08-F0-W10-S01-R04`) are the
   authoritative samples; the superseded A01 evidence is archived under
   `results/formal/superseded_attempt_A01/`.

## Known discrepancies (reported, not hidden)

| Item | Recorded | Recomputed | Status |
|---|---|---|---|
| Checkpoint digest | `4aa1ba38...` (sorted file-manifest digest) | `ab200657...` (sha256 of `SHA256SUMS.txt`) | `RECORDED_DIGEST_NOT_REPRODUCED`; checkpoint still exercised by the independent smoke test |
| Build binary | `b3eb1559...` | same on 0202 | PASS |
| Disk template | `bb872707...` | same; all 37 historical disk images match | PASS |

The checkpoint directory contains all 10 files, but no tested sorted-manifest
method reproduced the originally recorded `4aa1ba...` value. The discrepancy
is recorded in `External_Artifacts_Manifest.json`.

## External assets

`vmlinux` (227 MB) and `mmu_template.img` (2.36 GB) are
`EXTERNAL_ASSET_NOT_YET_DISTRIBUTED`; they are absent from GitHub and have no
public URL. This blocks external full-system execution but does not affect the
archived result integrity. `External_Artifacts_Manifest.json` records size,
SHA256 and retrieval status for every asset.
