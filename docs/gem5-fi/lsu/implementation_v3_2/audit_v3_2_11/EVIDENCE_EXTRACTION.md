# LSU v3.2.11 — Task 9: archived raw-trace extraction and hash verification (B2)

**Extraction date:** 2026-11-10
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.11`, branch `lsu-platform-v3.2.11`, HEAD `776558fc6b6fbdc5d6e7921360e22fea76d5ca82`
**Scope (task brief):** extract only the pilot evidence sets whose raw `trace_v31.jsonl` is not in-tree — SQ01 (v3.2.3 archive), FW05 (v3.2.7), SQ03 (v3.2.8), SP05 (v3.2.9) — into `audit_v3_2_11/extracted_evidence/` (gitignored scratch), write a `.sha256` sidecar next to every extracted trace, verify each hash against the recorded checksum sources, and prove the historical `pilots_v3_2_*` trees were untouched. No file under any `pilots_v3_2_*` was read-write; every archive/pilot access was read-only.

## 1. Source archives

| Model / run set | Archive path | SHA256 | Bytes | Notes |
|---|---|---|---|---|
| SQ01 (v3.2.3 runs) | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2/LSU_v3.2.3_Propagation_Closure_Package.zip` | `1e3e8377f20d03bb3ee9a1d41e5e715f95c8e6df732a8d432a0aa56bc267b141` | 41804968 | zip-internal prefix `package_staging_v323/evidence/pilots_v3_2_3/`; byte-identical copy is git-tracked in this repo at `docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.3_Propagation_Closure_Package.zip` |
| FW05 (v3.2.7 runs) | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.10/LSU_v3.2.7_MD04_Config_Freeze_FW05_Implementation_Package.zip` | `186e7059a47b404fd8fbc5e93d0ba471fee4adc2beb0ff7aee4a60c5b4712038` | 16466069 | zip-internal prefix `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_7/` (repo-shaped paths; `-j` junk-path extraction is mandatory so nothing lands in the historical `pilots_v3_2_7/`) |
| SQ03 (v3.2.8 runs) | `/tmp/LSU_v3.2.8_FW05_ConfigFreeze_SQ03_Pilot_Package.zip` | `40a3da53dfdf39b2ca07382c5770973f1e977695e6d79cf7740729aee129c155` | 71849774 | zip-internal prefix `LSU_v3.2.8_PACKAGE/B_SQ03/pilots/`; identical copy at `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2/LSU_v3.2.8_FW05_ConfigFreeze_SQ03_Pilot_Package.zip` (same SHA256) |
| SP05 (v3.2.9 runs) | `/tmp/LSU_v3.2.9_SP05_Implementation_SQ03_Propagation_FW05_Closure_Package.zip` | `9f2974312361b286191b124b3a0d7a2e57b91a9f6207ad5c708563240cddc18f` | 44315671 | zip-internal prefix `LSU_v3.2.9_PACKAGE/A_SP05/pilots/`; identical copy at `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2/LSU_v3.2.9_SP05_Implementation_SQ03_Propagation_FW05_Closure_Package.zip` (same SHA256) |

A fifth archive was located and hashed but deliberately **not** extracted (out of Task 9 scope): `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2/LSU_v3.2.4_DA04_Implementation_Package.zip`, SHA256 `8413a130ad76d7d894c47886fe806a114c450f02b0db5b3ff423875cb7f6fdc3`, 43234587 bytes — it contains the **v3.2.4 SQ01 re-run** traces at `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/SQ01-R0*/trace_v31.jsonl` (~197.7 MB each). Pointer recorded for the SQ01 audit task (§9).

## 2. What was extracted (and how)

Per pilot, exactly these 10 files: `trace_v31.jsonl`, `pilot_meta.json`, `manifest.json`, `oracle.log`, `stdout.log`, `stderr.log`, `config.json`, `config.ini`, `stats.txt`, `lsq_fwd_injections.log` (the injection log for all four models). Deliberately not extracted: `prop_trace.csv.gz` (compressed raw CSV, not in the task's file list), `citations.bib`, `command.txt` — they remain in the archives.

Extraction used `unzip -j` (junk paths) with an explicit per-pilot, per-file argument list, targeting `extracted_evidence/<MODEL>_v3_2_<X>/<MODEL>-R0Y/`. `-j` is mandatory for the v3.2.7 zip, whose members carry repo-shaped paths (`docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_7/FW05-R01/...`); without it the extraction would write into the historical `pilots_v3_2_7/` directory, which is forbidden.

Exact script run (complete content of `/tmp/task9_extract.sh`, verbatim):

```bash
#!/bin/bash
# Task 9 evidence extraction — explicit per-pilot, per-file lists only.
set -u
WT=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.11
EV=$WT/docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence
Z3=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2/LSU_v3.2.3_Propagation_Closure_Package.zip
Z7=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.10/LSU_v3.2.7_MD04_Config_Freeze_FW05_Implementation_Package.zip
Z8=/tmp/LSU_v3.2.8_FW05_ConfigFreeze_SQ03_Pilot_Package.zip
Z9=/tmp/LSU_v3.2.9_SP05_Implementation_SQ03_Propagation_FW05_Closure_Package.zip
FILES="trace_v31.jsonl pilot_meta.json manifest.json oracle.log stdout.log stderr.log config.json config.ini stats.txt lsq_fwd_injections.log"

declare -A PREFIX=(
  [SQ01]="package_staging_v323/evidence/pilots_v3_2_3"
  [FW05]="docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_7"
  [SQ03]="LSU_v3.2.8_PACKAGE/B_SQ03/pilots"
  [SP05]="LSU_v3.2.9_PACKAGE/A_SP05/pilots"
)
declare -A ZIP=( [SQ01]=$Z3 [FW05]=$Z7 [SQ03]=$Z8 [SP05]=$Z9 )
declare -A VINT=( [SQ01]=v3_2_3 [FW05]=v3_2_7 [SQ03]=v3_2_8 [SP05]=v3_2_9 )

mkdir -p "$EV"
for m in SQ01 FW05 SQ03 SP05; do
  for r in 01 02 03 04 05; do
    p=${PREFIX[$m]}/${m}-R$r
    d=$EV/${m}_${VINT[$m]}/${m}-R$r
    mkdir -p "$d"
    for f in $FILES; do
      out=$(unzip -j -o -q "${ZIP[$m]}" "$p/$f" -d "$d" 2>&1); rc=$?
      if [ $rc -ne 0 ]; then
        echo "MISSING rc=$rc ${m}-R$r/$f :: $out"
      fi
    done
    echo "DONE ${m}-R$r ($(ls "$d" | wc -l) files)"
  done
done
```

Result (complete real output — 20 `DONE` lines, zero `MISSING` lines, i.e. all 200 requested file extractions returned exit 0):

```
DONE SQ01-R01 (10 files)
DONE SQ01-R02 (10 files)
DONE SQ01-R03 (10 files)
DONE SQ01-R04 (10 files)
DONE SQ01-R05 (10 files)
DONE FW05-R01 (10 files)
DONE FW05-R02 (10 files)
DONE FW05-R03 (10 files)
DONE FW05-R04 (10 files)
DONE FW05-R05 (10 files)
DONE SQ03-R01 (10 files)
DONE SQ03-R02 (10 files)
DONE SQ03-R03 (10 files)
DONE SQ03-R04 (10 files)
DONE SQ03-R05 (10 files)
DONE SP05-R01 (10 files)
DONE SP05-R02 (10 files)
DONE SP05-R03 (10 files)
DONE SP05-R04 (10 files)
DONE SP05-R05 (10 files)
```

Extracted volume: 2.5 GiB total — `SQ01_v3_2_3` 946M, `FW05_v3_2_7` 186M, `SQ03_v3_2_8` 941M, `SP05_v3_2_9` 445M (50 files each: 5 pilots x 10 files). The directory is gitignored via the new `.gitignore` entry `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/` (appended; no existing entry modified; verified with `git check-ignore -v`).

## 3. Sidecars

Every extracted pilot dir now carries `trace_v31.jsonl.sha256` written as `sha256sum trace_v31.jsonl` run inside that dir — format `<sha256>  trace_v31.jsonl` (two spaces, bare filename), matching the v3.2.4 sibling sidecar convention and the input the Task 8 audit tool's `HASH_MISMATCH` check reads. Example (`SQ01_v3_2_3/SQ01-R01/trace_v31.jsonl.sha256`):

```
8a251073b2ea3c1d26a06ec60ee2a482c2d8fce3062168f51a86cda195737934  trace_v31.jsonl
```

## 4. Hash verification against the recorded checksum sources

Method: compute SHA256 of each extracted `trace_v31.jsonl`, then compare with every recorded source for that pilot. 40 comparisons total: **35 MATCH, 5 MISMATCH**. Every mismatch is the v3.2.4 sibling source (§4.2) — a different run set, not a corruption of the extracted bytes. **No extracted pilot is `missing=HASH_MISMATCH`** against the recorded source of its own vintage.

### 4.1 SQ01 — v3.2.3 archive bytes

Repo `pilots_v3_2_3/TRACE_STORAGE.md` + per-pilot sidecars `pilots_v3_2_3/SQ01-R0*/trace_v31.jsonl.sha256` (identical values inside the v3.2.3 zip, both as per-pilot sidecars and in `package_staging_v323/SHA256SUMS.txt`):

```
8a251073b2ea3c1d26a06ec60ee2a482c2d8fce3062168f51a86cda195737934  SQ01-R01
37d67752b5ec7391dab1bbc5480ff1874ed41f0251b03c2318a7bc4a04f7c977  SQ01-R02
c03e906ad08b0e7d29a4fd1f50bfe759fd9102d57a9ea671e771d43568405614  SQ01-R03
bc127211a91df02788c25aea586fc8c4c735b63df69b871744c6ea08cf90eefa  SQ01-R04
9b115f2ad9234311ba83e01f45fffc7fac91109d4d1113d3b2f0bf3929b182c7  SQ01-R05
```

Sibling set `pilots_v3_2_4/SQ01-R0*/trace_v31.jsonl.sha256` (the v3.2.4 re-runs, same seeds, post-fix tool — see §4.2):

```
c8aad1bba0dbcdaae4add24e5b5cd240111fd2856a81b096a450fe447a0706e1  SQ01-R01
143f2b920188ff037005b9b09111b76c6a005337e27f05c945d6c1a463c9bee9  SQ01-R02
68b3fac17fa7e71d6a02f6e6f6575a2017af749fd6efc9f91a70dd6cb3d7bc17  SQ01-R03
0d34891e1bccd057f95d5664cae0f1f7fec10241406710598832e4c24d752605  SQ01-R04
f6df766d9e7ce07cc84b92a61b1ac190da32941cfbea1fed9f1a9764a0cb87ed  SQ01-R05
```

| Pilot | computed SHA256 (extracted `trace_v31.jsonl`) | verdict vs each recorded source |
|---|---|---|
| SQ01-R01 | `8a251073b2ea3c1d26a06ec60ee2a482c2d8fce3062168f51a86cda195737934` | repo pilots_v3_2_3 sidecar: **MATCH**; v3.2.3 zip sidecar: **MATCH**; v3.2.3 zip SHA256SUMS.txt: **MATCH**; repo pilots_v3_2_4 sidecar (sibling run set): **MISMATCH** |
| SQ01-R02 | `37d67752b5ec7391dab1bbc5480ff1874ed41f0251b03c2318a7bc4a04f7c977` | repo pilots_v3_2_3 sidecar: **MATCH**; v3.2.3 zip sidecar: **MATCH**; v3.2.3 zip SHA256SUMS.txt: **MATCH**; repo pilots_v3_2_4 sidecar (sibling run set): **MISMATCH** |
| SQ01-R03 | `c03e906ad08b0e7d29a4fd1f50bfe759fd9102d57a9ea671e771d43568405614` | repo pilots_v3_2_3 sidecar: **MATCH**; v3.2.3 zip sidecar: **MATCH**; v3.2.3 zip SHA256SUMS.txt: **MATCH**; repo pilots_v3_2_4 sidecar (sibling run set): **MISMATCH** |
| SQ01-R04 | `bc127211a91df02788c25aea586fc8c4c735b63df69b871744c6ea08cf90eefa` | repo pilots_v3_2_3 sidecar: **MATCH**; v3.2.3 zip sidecar: **MATCH**; v3.2.3 zip SHA256SUMS.txt: **MATCH**; repo pilots_v3_2_4 sidecar (sibling run set): **MISMATCH** |
| SQ01-R05 | `9b115f2ad9234311ba83e01f45fffc7fac91109d4d1113d3b2f0bf3929b182c7` | repo pilots_v3_2_3 sidecar: **MATCH**; v3.2.3 zip sidecar: **MATCH**; v3.2.3 zip SHA256SUMS.txt: **MATCH**; repo pilots_v3_2_4 sidecar (sibling run set): **MISMATCH** |

### 4.2 SQ01 v3.2.4 siblings — expected divergence, documented

The five MISMATCH rows are the `pilots_v3_2_4/SQ01-R0*/trace_v31.jsonl.sha256` sidecars. These record the **v3.2.4 re-runs** (same seeds — e.g. R01 seed 591611458 in both vintages' `pilot_meta.json` — re-executed after the v3.2.4-round SQ01 fix, hence different trace bytes, ~197.7 MB vs 198 MB), not the v3.2.3 archive contents. The v3.2.4 raw traces are not in-tree and not in the v3.2.3 package; they live in `LSU_v3.2.4_DA04_Implementation_Package.zip` (§1). This is provenance divergence between two run sets, not a hash failure of either: each vintage's bytes match that vintage's recorded sources exactly. The per-model SQ01 audit (Tasks 10-20) must state which run set it audits and must not mix them.

### 4.3 FW05 — v3.2.7 archive bytes

Repo `pilots_v3_2_7/FW05_TRACE_STORAGE.md` (trace lines):

```
FW05-R01 trace_v31.jsonl ceb35e24fdb0f10024848b830978fadf4734cbe307f43ebba08ce9d44e35c96d
FW05-R02 trace_v31.jsonl fda5ade60c88ceaa5ff7587064a33f646cd873f90bf25237be0435a3b143e928
FW05-R03 trace_v31.jsonl 6f4d61961b6204f1654cc181f442722dbac504c2765ceff9d27bad068ae7acca
FW05-R04 trace_v31.jsonl 069c517fa6db244be0023fae6cf6539f833d0d5e704445acd38feef0a2b5c232
FW05-R05 trace_v31.jsonl b163a39e6a621e5bcde3eac5c7aff19a8d2a7d5e61c87ca8b69852d83a60d26f
```

| Pilot | computed SHA256 (extracted `trace_v31.jsonl`) | verdict vs each recorded source |
|---|---|---|
| FW05-R01 | `ceb35e24fdb0f10024848b830978fadf4734cbe307f43ebba08ce9d44e35c96d` | repo pilots_v3_2_7/FW05_TRACE_STORAGE.md: **MATCH** |
| FW05-R02 | `fda5ade60c88ceaa5ff7587064a33f646cd873f90bf25237be0435a3b143e928` | repo pilots_v3_2_7/FW05_TRACE_STORAGE.md: **MATCH** |
| FW05-R03 | `6f4d61961b6204f1654cc181f442722dbac504c2765ceff9d27bad068ae7acca` | repo pilots_v3_2_7/FW05_TRACE_STORAGE.md: **MATCH** |
| FW05-R04 | `069c517fa6db244be0023fae6cf6539f833d0d5e704445acd38feef0a2b5c232` | repo pilots_v3_2_7/FW05_TRACE_STORAGE.md: **MATCH** |
| FW05-R05 | `b163a39e6a621e5bcde3eac5c7aff19a8d2a7d5e61c87ca8b69852d83a60d26f` | repo pilots_v3_2_7/FW05_TRACE_STORAGE.md: **MATCH** |

### 4.4 SQ03 — v3.2.8 archive bytes

Repo `pilots_v3_2_8/SQ03_TRACE_STORAGE.md` (trace lines; identical values in the v3.2.8 zip's `LSU_v3.2.8_PACKAGE/SHA256SUMS`):

```
SQ03-R01 trace_v31.jsonl 60d96fb27d03d50928b52f810dc5de07fbec45b9c6520f2f75f80cb944944c5b
SQ03-R02 trace_v31.jsonl fa6a9056cf80026089c6c14b53485589f76c8a29ad1681bc5272033ec4b8aff7
SQ03-R03 trace_v31.jsonl 8a983c81f2b0d1d240cc6c64245579a10ff3c1a7834a40e4fbfe067382aad908
SQ03-R04 trace_v31.jsonl 476bc41aa8ae5f22113614a5cc06a0a1cc9500a843cc886f1efb95bcac3a26e1
SQ03-R05 trace_v31.jsonl e91ef970cfc6298d0382f2ffd2bc7856a5c91da73b6c3a703306bea15ef0b8c2
```

| Pilot | computed SHA256 (extracted `trace_v31.jsonl`) | verdict vs each recorded source |
|---|---|---|
| SQ03-R01 | `60d96fb27d03d50928b52f810dc5de07fbec45b9c6520f2f75f80cb944944c5b` | repo pilots_v3_2_8/SQ03_TRACE_STORAGE.md: **MATCH**; v3.2.8 zip SHA256SUMS: **MATCH** |
| SQ03-R02 | `fa6a9056cf80026089c6c14b53485589f76c8a29ad1681bc5272033ec4b8aff7` | repo pilots_v3_2_8/SQ03_TRACE_STORAGE.md: **MATCH**; v3.2.8 zip SHA256SUMS: **MATCH** |
| SQ03-R03 | `8a983c81f2b0d1d240cc6c64245579a10ff3c1a7834a40e4fbfe067382aad908` | repo pilots_v3_2_8/SQ03_TRACE_STORAGE.md: **MATCH**; v3.2.8 zip SHA256SUMS: **MATCH** |
| SQ03-R04 | `476bc41aa8ae5f22113614a5cc06a0a1cc9500a843cc886f1efb95bcac3a26e1` | repo pilots_v3_2_8/SQ03_TRACE_STORAGE.md: **MATCH**; v3.2.8 zip SHA256SUMS: **MATCH** |
| SQ03-R05 | `e91ef970cfc6298d0382f2ffd2bc7856a5c91da73b6c3a703306bea15ef0b8c2` | repo pilots_v3_2_8/SQ03_TRACE_STORAGE.md: **MATCH**; v3.2.8 zip SHA256SUMS: **MATCH** |

### 4.5 SP05 — v3.2.9 archive bytes

`evidence_v3_2_9/SP05_v329_EVIDENCE.csv` does **not** record a trace hash (its columns are pilot/seed/ordinal/binary_sha256/injection/terminal/oracle/checksum/... — no trace SHA256 column; verified against the CSV header). The recorded source used instead is the v3.2.9 zip's own `LSU_v3.2.9_PACKAGE/SHA256SUMS` (package-freeze manifest):

```
0001110b1ce82efdbd308d91bbcd059cafac160d406e43e0f849b5010559dca8  ./A_SP05/pilots/SP05-R01/trace_v31.jsonl
12eb7ce46ea6d2fe7219ead8314cf5aeefabee99acc37a242bc3e09cd5c73ef9  ./A_SP05/pilots/SP05-R02/trace_v31.jsonl
ee4ad6918a4dabab674972fbccb347155d78acd3d12378551ee5dcd378bdf5eb  ./A_SP05/pilots/SP05-R03/trace_v31.jsonl
19e50df5a0830626779d2a7e6d8b8cfec768be16721ce3fe22c98296f748b8d2  ./A_SP05/pilots/SP05-R04/trace_v31.jsonl
bcacefa2a9ec0ec680204e71643e0013a560000a0d621fe6284c93ffa787c3a3  ./A_SP05/pilots/SP05-R05/trace_v31.jsonl
```

| Pilot | computed SHA256 (extracted `trace_v31.jsonl`) | verdict vs each recorded source |
|---|---|---|
| SP05-R01 | `0001110b1ce82efdbd308d91bbcd059cafac160d406e43e0f849b5010559dca8` | v3.2.9 zip SHA256SUMS: **MATCH** |
| SP05-R02 | `12eb7ce46ea6d2fe7219ead8314cf5aeefabee99acc37a242bc3e09cd5c73ef9` | v3.2.9 zip SHA256SUMS: **MATCH** |
| SP05-R03 | `ee4ad6918a4dabab674972fbccb347155d78acd3d12378551ee5dcd378bdf5eb` | v3.2.9 zip SHA256SUMS: **MATCH** |
| SP05-R04 | `19e50df5a0830626779d2a7e6d8b8cfec768be16721ce3fe22c98296f748b8d2` | v3.2.9 zip SHA256SUMS: **MATCH** |
| SP05-R05 | `bcacefa2a9ec0ec680204e71643e0013a560000a0d621fe6284c93ffa787c3a3` | v3.2.9 zip SHA256SUMS: **MATCH** |

## 5. Full file inventory with SHA256 (200 files)

Generated by `find . -type f ! -name "*.sha256" | sort | while read f; do sha256sum "$f"; done` inside `extracted_evidence/` (sidecars excluded; they repeat the trace hash of §4). Paths relative to `extracted_evidence/`.

### 5.1 SQ01_v3_2_3

```
d6d8fb6a04d252204763589119b43b64558e9fabd50bb9469401d0022cae5975  ./SQ01_v3_2_3/SQ01-R01/config.ini
20b49d4a0aec5422864f82883ed1e3260ec0da09361956a30f8e4430245a36b6  ./SQ01_v3_2_3/SQ01-R01/config.json
4bc95c6f8f7feb08f1fc70b3e5755b3d3fee6325a66c25ac26f02b21451374ca  ./SQ01_v3_2_3/SQ01-R01/lsq_fwd_injections.log
59766ebcc8f7811f7a3e463802f268cb62e8c572eefd24ff5632103e88147105  ./SQ01_v3_2_3/SQ01-R01/manifest.json
44a02828133c60cda9765bbe6bc58de05361838350732c8c0bdc3c2cca9b29fc  ./SQ01_v3_2_3/SQ01-R01/oracle.log
d8b4f30c94c66555bf26a8943f2529635b41b0efcb00720ca7fffd69a2d92d65  ./SQ01_v3_2_3/SQ01-R01/pilot_meta.json
8f8b8ced2c8dd4a71a701bc7809d9def624fe628c59a89bff921d50ab2269556  ./SQ01_v3_2_3/SQ01-R01/stats.txt
32b304ab96750d84527a1f8301eaf7291e36eb50a052c304a6c180029cf8cdcd  ./SQ01_v3_2_3/SQ01-R01/stderr.log
a56b9ccad6cee18396e6f61f6c5c60bd2ca054530d22e3ea4ff798d9dbb7c68b  ./SQ01_v3_2_3/SQ01-R01/stdout.log
8a251073b2ea3c1d26a06ec60ee2a482c2d8fce3062168f51a86cda195737934  ./SQ01_v3_2_3/SQ01-R01/trace_v31.jsonl
6d116a0ad0d0e5d04ff1d8be9071253518435a5f041bcfd17686b70608973a8b  ./SQ01_v3_2_3/SQ01-R02/config.ini
51293e4cc903bf3e74a47267e511b8ea0e0524e9585a6bbace7ec4203f1b24f9  ./SQ01_v3_2_3/SQ01-R02/config.json
a826895f01360ce8eeccffa529a3934badd3e4c8b05c6551a5feee075651861f  ./SQ01_v3_2_3/SQ01-R02/lsq_fwd_injections.log
0b98b17565628d36b4d1cb19d3b174cc1f9fd74e2b84277e6cf2d38ccfd1c333  ./SQ01_v3_2_3/SQ01-R02/manifest.json
44a02828133c60cda9765bbe6bc58de05361838350732c8c0bdc3c2cca9b29fc  ./SQ01_v3_2_3/SQ01-R02/oracle.log
cb379b58e3bcff55d59269778e8652eda8eb191078677897b90ce413749c935a  ./SQ01_v3_2_3/SQ01-R02/pilot_meta.json
754e5d7f8b1b778d0a7b26077671f2fbc8affc62e5ceae81fcb803c08a9eaaaf  ./SQ01_v3_2_3/SQ01-R02/stats.txt
32b304ab96750d84527a1f8301eaf7291e36eb50a052c304a6c180029cf8cdcd  ./SQ01_v3_2_3/SQ01-R02/stderr.log
ad5f105fba3aad7214e97813230a259544d452b8659d639458b49b8002e0525b  ./SQ01_v3_2_3/SQ01-R02/stdout.log
37d67752b5ec7391dab1bbc5480ff1874ed41f0251b03c2318a7bc4a04f7c977  ./SQ01_v3_2_3/SQ01-R02/trace_v31.jsonl
2c3db5a6cb2d19de63015be6d7accf207dd7cf29a48e54774cdfbc95a9bf7e4d  ./SQ01_v3_2_3/SQ01-R03/config.ini
cd668b950c4dac345298c4ea9c616d17bbb0b025ad2a66e445940783dd7c5c61  ./SQ01_v3_2_3/SQ01-R03/config.json
5f069b3d3645b9ab186893cae6694d939a2f09ea7fdf230104c57493c1f60ec0  ./SQ01_v3_2_3/SQ01-R03/lsq_fwd_injections.log
54b8c7f9ce81ce6480b3ff27a29618847024a2e1831f9af148aeaa40f515a289  ./SQ01_v3_2_3/SQ01-R03/manifest.json
44a02828133c60cda9765bbe6bc58de05361838350732c8c0bdc3c2cca9b29fc  ./SQ01_v3_2_3/SQ01-R03/oracle.log
7169c6d2f15252e01cbd854334ad22089bf9906f2055edf94786377510e8ddff  ./SQ01_v3_2_3/SQ01-R03/pilot_meta.json
fbf1d1cec616b410cbbef891a73500057e55ecec590dc76f77a8073b2d5248ce  ./SQ01_v3_2_3/SQ01-R03/stats.txt
32b304ab96750d84527a1f8301eaf7291e36eb50a052c304a6c180029cf8cdcd  ./SQ01_v3_2_3/SQ01-R03/stderr.log
002c85c417f8ad51f703beadaafdf1d4ede84b5b14c00dc9f77e2b187dfad749  ./SQ01_v3_2_3/SQ01-R03/stdout.log
c03e906ad08b0e7d29a4fd1f50bfe759fd9102d57a9ea671e771d43568405614  ./SQ01_v3_2_3/SQ01-R03/trace_v31.jsonl
f4daeb70e0d63f8a73ea6f679d47f7c43e6e75a64becc1fe8418f0188ef26377  ./SQ01_v3_2_3/SQ01-R04/config.ini
fe00eaa3ff6ecd9f4cc42ee3507d1a369ca0f7a38e15f8a74c229579970b246e  ./SQ01_v3_2_3/SQ01-R04/config.json
7fe2426e9ca2401272dfb694f54d0a83bed790760cd2fe936cdaad144cbb4337  ./SQ01_v3_2_3/SQ01-R04/lsq_fwd_injections.log
5c811b8a49d724e9ad6436741050656ef562846546ea4366d321484c4457f18a  ./SQ01_v3_2_3/SQ01-R04/manifest.json
44a02828133c60cda9765bbe6bc58de05361838350732c8c0bdc3c2cca9b29fc  ./SQ01_v3_2_3/SQ01-R04/oracle.log
d067eec4a1e244488f9d0d5cda03441711fd3e042b70edb054f65533c3d70e3f  ./SQ01_v3_2_3/SQ01-R04/pilot_meta.json
7bbe5028198ff1732bafed0b8bb772b79b7226190fb72e463459e63094984e65  ./SQ01_v3_2_3/SQ01-R04/stats.txt
32b304ab96750d84527a1f8301eaf7291e36eb50a052c304a6c180029cf8cdcd  ./SQ01_v3_2_3/SQ01-R04/stderr.log
4eaa0a7959869e77d290a690f121418fb5086191cdaef668b78612df4ee46935  ./SQ01_v3_2_3/SQ01-R04/stdout.log
bc127211a91df02788c25aea586fc8c4c735b63df69b871744c6ea08cf90eefa  ./SQ01_v3_2_3/SQ01-R04/trace_v31.jsonl
d829bf00ddd527bbc21e2f786c4911f1a258951d5c5fe15653c98097365b88f6  ./SQ01_v3_2_3/SQ01-R05/config.ini
fb06c1014f42794b1d1ecc56a7a62f41a74189287d20ff0b52a76e31e025ec44  ./SQ01_v3_2_3/SQ01-R05/config.json
7fb723a6bf229ee9b1f7ff3e8c4a4224856a1c51cc0be03a253a63cd540ddafa  ./SQ01_v3_2_3/SQ01-R05/lsq_fwd_injections.log
1afd10434bc85a90f629fc712697b479c32f0e69d4fb429e560c67a9d5130af6  ./SQ01_v3_2_3/SQ01-R05/manifest.json
44a02828133c60cda9765bbe6bc58de05361838350732c8c0bdc3c2cca9b29fc  ./SQ01_v3_2_3/SQ01-R05/oracle.log
66e093fd8c6b11293a1cc29680cd0f57f602a8f374ceeab82de7b87a938f2db3  ./SQ01_v3_2_3/SQ01-R05/pilot_meta.json
9ca9ba7ebec77a3768a86f4b451b4825e90c986911a36c102eb8f80f39859596  ./SQ01_v3_2_3/SQ01-R05/stats.txt
32b304ab96750d84527a1f8301eaf7291e36eb50a052c304a6c180029cf8cdcd  ./SQ01_v3_2_3/SQ01-R05/stderr.log
457ed135749a552b41b1cc7d863b98e0bda2b572023de9b5659ed82a240f8f6d  ./SQ01_v3_2_3/SQ01-R05/stdout.log
9b115f2ad9234311ba83e01f45fffc7fac91109d4d1113d3b2f0bf3929b182c7  ./SQ01_v3_2_3/SQ01-R05/trace_v31.jsonl
```

### 5.2 FW05_v3_2_7

```
5a8e4436e5f559331c883e0764c576935606e858fdfca3478d699caf70ee710f  ./FW05_v3_2_7/FW05-R01/config.ini
1dbe80a065feaa1822ea9e2cb471212e948b8d28a271dbf805c6ab349338c522  ./FW05_v3_2_7/FW05-R01/config.json
e1eca3b492467f6e157459d109012f315ef4ebedadf6205f8990d46db91cf8e8  ./FW05_v3_2_7/FW05-R01/lsq_fwd_injections.log
58bda247c5b08697c53aebb860227f3c0cb9497817631b1468f2757f588c014e  ./FW05_v3_2_7/FW05-R01/manifest.json
ee950ada34ff00150918f918f0b35bff8fb346397f6e876f0bcb36abb2862507  ./FW05_v3_2_7/FW05-R01/oracle.log
f4d96f2a7abf4c539ea65e96e03c8f59a96df3bce792c62aa9a95051696872a0  ./FW05_v3_2_7/FW05-R01/pilot_meta.json
8d415c68791c256ebca7adff5648ebe78c71d641685d3351d67cec393d374d46  ./FW05_v3_2_7/FW05-R01/stats.txt
b49f155d15e5a1bc37e4ce6ec6dee232c816049f298df91b4bdb06084c235b7f  ./FW05_v3_2_7/FW05-R01/stderr.log
5c940210541f0b390264a0149107a6d922023cae270464db7c77f5046a0cb7ad  ./FW05_v3_2_7/FW05-R01/stdout.log
ceb35e24fdb0f10024848b830978fadf4734cbe307f43ebba08ce9d44e35c96d  ./FW05_v3_2_7/FW05-R01/trace_v31.jsonl
6d96855a7b3af4f0bf9306e7b93c8651b95f25e787f63c3b83444eab2a4dca5d  ./FW05_v3_2_7/FW05-R02/config.ini
88556f61673cfffd5935aef5d535b4975e8b7cd32121f4a18af53080e58fb982  ./FW05_v3_2_7/FW05-R02/config.json
ead4adeb66a417db908761e8e02ee18ceb88707cba4ad33bb1eb95d8ab8b5f2c  ./FW05_v3_2_7/FW05-R02/lsq_fwd_injections.log
51ece691563f882972ed8717d247cc96f27cb48201b529957875c583ce9ff5e7  ./FW05_v3_2_7/FW05-R02/manifest.json
a3d2a3dd0a81151be2f37b7b17da69d6b16580fade09668c0f86cac9190fa307  ./FW05_v3_2_7/FW05-R02/oracle.log
6f2f699f81b6956e25678829af17e3e31fc8168cadb24d848f33bf1fcca95e1e  ./FW05_v3_2_7/FW05-R02/pilot_meta.json
e7d65a116c69f909761849f697c8f29aa75fee48d9abe375da68cfad1cce1ec5  ./FW05_v3_2_7/FW05-R02/stats.txt
b49f155d15e5a1bc37e4ce6ec6dee232c816049f298df91b4bdb06084c235b7f  ./FW05_v3_2_7/FW05-R02/stderr.log
8816dd11f234ccb29a5339fe859e0776f0268a693dbb6404ef048d6cb76e953a  ./FW05_v3_2_7/FW05-R02/stdout.log
fda5ade60c88ceaa5ff7587064a33f646cd873f90bf25237be0435a3b143e928  ./FW05_v3_2_7/FW05-R02/trace_v31.jsonl
48c8413b96ea863481a984d7ea895edf80ed0f8761ee869f6b2906fcb0b5b064  ./FW05_v3_2_7/FW05-R03/config.ini
8cf1737524a3481cc20a2bcb3b58d1380e11a35c85943300b70a195834b2b133  ./FW05_v3_2_7/FW05-R03/config.json
af486d7308076a9a847fd8af232976847af9bb7db014ceebf8c11c3b571f0032  ./FW05_v3_2_7/FW05-R03/lsq_fwd_injections.log
68fa5b5ce74f6309aab45e615f761090ce78f2ced92ca99a565b227c831d5c93  ./FW05_v3_2_7/FW05-R03/manifest.json
15541cb44322928447d137558479cc58c8bf482b6cf7b10007787434f0de5b72  ./FW05_v3_2_7/FW05-R03/oracle.log
8fbda3d9367df09072a412d09f5cbb8fdae44d46aebb5dbaa6f7e1e043bf0d24  ./FW05_v3_2_7/FW05-R03/pilot_meta.json
8a51138c55a1ef6b2c85ae7b7ba3f8cae19abb5a354d248e711b251912111a58  ./FW05_v3_2_7/FW05-R03/stats.txt
b49f155d15e5a1bc37e4ce6ec6dee232c816049f298df91b4bdb06084c235b7f  ./FW05_v3_2_7/FW05-R03/stderr.log
82acb7933a70b4d3f23be071b5d6b5952fbcaa7c5b26df287d3bdeb55daa18c3  ./FW05_v3_2_7/FW05-R03/stdout.log
6f4d61961b6204f1654cc181f442722dbac504c2765ceff9d27bad068ae7acca  ./FW05_v3_2_7/FW05-R03/trace_v31.jsonl
5f35cc54cca32e9cb7d38f818f231e4ee6b84dd997109f59469c8c257577460e  ./FW05_v3_2_7/FW05-R04/config.ini
ea055bf9bee7b0561a90fae2e960e1c17cd9eee10517f44a34a91cb47c1c945a  ./FW05_v3_2_7/FW05-R04/config.json
67840fa06b96612a40f28a758c3a5fd8e7e3eb1a9568331bea420625f43457e3  ./FW05_v3_2_7/FW05-R04/lsq_fwd_injections.log
5d6a322b4d9e1ba75063a874b0a4f2358e9b4ea5ad65bc098c9d6263c1ff2a37  ./FW05_v3_2_7/FW05-R04/manifest.json
25bdcb28e424406b80a63c8964d8900b7e9560c9b4dfadeef822bcea3a10d68c  ./FW05_v3_2_7/FW05-R04/oracle.log
b1da75de1cfe730938d575485441c097483b29e54f7fa75e06faa5e260e5ada2  ./FW05_v3_2_7/FW05-R04/pilot_meta.json
2302e95f037bc43371420603e9da782d6b6436ec8bb4eaac189f5f5b93c5639d  ./FW05_v3_2_7/FW05-R04/stats.txt
b49f155d15e5a1bc37e4ce6ec6dee232c816049f298df91b4bdb06084c235b7f  ./FW05_v3_2_7/FW05-R04/stderr.log
baeb4c9e98628c76dcbae9aa1acaf0b0710fc011636b4931bb810a62a60361a2  ./FW05_v3_2_7/FW05-R04/stdout.log
069c517fa6db244be0023fae6cf6539f833d0d5e704445acd38feef0a2b5c232  ./FW05_v3_2_7/FW05-R04/trace_v31.jsonl
4c9a8c777dc817af297c701d1298f481cf4844fb6069688292fd44b83dab89a2  ./FW05_v3_2_7/FW05-R05/config.ini
b8ecfc2226c1f7895de5b4612a2f3dfee4cf0403c889e4f9888620da1f189f5c  ./FW05_v3_2_7/FW05-R05/config.json
83830c06e1f794d7e31e0e089206c66c2638d0dd2904e21f5c95900e3c66f6bd  ./FW05_v3_2_7/FW05-R05/lsq_fwd_injections.log
9f7384de0af433d2f272b36a579c40296dffd10ed641ca44b747add34dcb36fe  ./FW05_v3_2_7/FW05-R05/manifest.json
41da02ac46708e37215ed90da128858fff3eb669459de35e26172a41d6ec4d1d  ./FW05_v3_2_7/FW05-R05/oracle.log
4bfc79d540dba89c7ee2b137a615907a8828828219c509b2c950520048a16601  ./FW05_v3_2_7/FW05-R05/pilot_meta.json
762df6839a71e9f7c4680242f7230eb7a258737fef3549f1b1eb7f967539d915  ./FW05_v3_2_7/FW05-R05/stats.txt
b49f155d15e5a1bc37e4ce6ec6dee232c816049f298df91b4bdb06084c235b7f  ./FW05_v3_2_7/FW05-R05/stderr.log
4071c46ba0204b1459a52a7191f40f43ba40b428675ad1dcb1e5b2653777727b  ./FW05_v3_2_7/FW05-R05/stdout.log
b163a39e6a621e5bcde3eac5c7aff19a8d2a7d5e61c87ca8b69852d83a60d26f  ./FW05_v3_2_7/FW05-R05/trace_v31.jsonl
```

### 5.3 SQ03_v3_2_8

```
46c169acc3b2cd75ea811b97e5c0a06df5dce043283ef877fae3913dc1ce9c2f  ./SQ03_v3_2_8/SQ03-R01/config.ini
3bee1f589145d3f4b7707beb1016133e80e6ad1b6aea1d4b7461de078b192d55  ./SQ03_v3_2_8/SQ03-R01/config.json
0d2dc00a0d7f0be5962b293c5e9a44fadb67b1ee07fb634f182165c6a60184ec  ./SQ03_v3_2_8/SQ03-R01/lsq_fwd_injections.log
ee586143fa59a2ec637abd610534abb818323291d5a42e7cad312264f3deb1d2  ./SQ03_v3_2_8/SQ03-R01/manifest.json
44a02828133c60cda9765bbe6bc58de05361838350732c8c0bdc3c2cca9b29fc  ./SQ03_v3_2_8/SQ03-R01/oracle.log
6f5efd8367ef3c0f658162b00d715ee315cf25377f4c0ec71465f3d6d44dbc6e  ./SQ03_v3_2_8/SQ03-R01/pilot_meta.json
a831e53a380a7bbe96f8afe06fcaa7970b874d93d2bc1fc749c06d4ffb3827c6  ./SQ03_v3_2_8/SQ03-R01/stats.txt
32b304ab96750d84527a1f8301eaf7291e36eb50a052c304a6c180029cf8cdcd  ./SQ03_v3_2_8/SQ03-R01/stderr.log
1f748cbfb5908a4d2f64b68a501b5422121e7a2a87da5e748057ab786dbceb2b  ./SQ03_v3_2_8/SQ03-R01/stdout.log
60d96fb27d03d50928b52f810dc5de07fbec45b9c6520f2f75f80cb944944c5b  ./SQ03_v3_2_8/SQ03-R01/trace_v31.jsonl
72d09d5883307cf449b6b965ac4ff92215afa1024fb5d522dee4c565f3b6b646  ./SQ03_v3_2_8/SQ03-R02/config.ini
d535ff307f80fc3af4f681734e05b710c9afed54dea07c2ec286ef963634226f  ./SQ03_v3_2_8/SQ03-R02/config.json
afe123ab2972fc69f434c4da3f841f0eca657dd8fab4ce31fa567cdb6b0338e6  ./SQ03_v3_2_8/SQ03-R02/lsq_fwd_injections.log
4a61b770d8280574c603425a67fc962359917d103b4935478d7bc73953de3c7c  ./SQ03_v3_2_8/SQ03-R02/manifest.json
44a02828133c60cda9765bbe6bc58de05361838350732c8c0bdc3c2cca9b29fc  ./SQ03_v3_2_8/SQ03-R02/oracle.log
9110043027c517e0485f9a6a8b882d1f3eb5224323d576d939bd653d8db423f3  ./SQ03_v3_2_8/SQ03-R02/pilot_meta.json
982e283b1ac2d763cd3adfc4e4304281030f414043d8d737730c887242fd7f8b  ./SQ03_v3_2_8/SQ03-R02/stats.txt
32b304ab96750d84527a1f8301eaf7291e36eb50a052c304a6c180029cf8cdcd  ./SQ03_v3_2_8/SQ03-R02/stderr.log
de7049f098a7d6e3deb1eb55d01f5bc4a31ce8200da4b728ee2d32b9738983de  ./SQ03_v3_2_8/SQ03-R02/stdout.log
fa6a9056cf80026089c6c14b53485589f76c8a29ad1681bc5272033ec4b8aff7  ./SQ03_v3_2_8/SQ03-R02/trace_v31.jsonl
9b2df85c0c92cedc2f5ea8c68f52c9c5541d3c77ab2a1ef5a47281924c16bfdb  ./SQ03_v3_2_8/SQ03-R03/config.ini
2929b68e2a09a7373e98724f98b9b3b4cedda51b5b79c41e1b08afb14ed2f24f  ./SQ03_v3_2_8/SQ03-R03/config.json
31fd21e020cc2a9255deed2180a32c4e6e53f094a3d57a9c2e23ad5cecaab5a1  ./SQ03_v3_2_8/SQ03-R03/lsq_fwd_injections.log
ae0cc84217157b20b1d05fbb09d69c11fe20af50770f18ef5bfaa51402f4eac9  ./SQ03_v3_2_8/SQ03-R03/manifest.json
44a02828133c60cda9765bbe6bc58de05361838350732c8c0bdc3c2cca9b29fc  ./SQ03_v3_2_8/SQ03-R03/oracle.log
d20aadad5a573d1d14a978f9a2e82915fc77051ec64c13424a5098e1ab4d0850  ./SQ03_v3_2_8/SQ03-R03/pilot_meta.json
5dd4d97bf4c86e1d041bdd6f90ecf1763604d59e85ab22ea3313dbee3e2fca75  ./SQ03_v3_2_8/SQ03-R03/stats.txt
32b304ab96750d84527a1f8301eaf7291e36eb50a052c304a6c180029cf8cdcd  ./SQ03_v3_2_8/SQ03-R03/stderr.log
fa94554922f29a4eaa8a76237f286c9088541e417277cd60ae4182e3c9db5225  ./SQ03_v3_2_8/SQ03-R03/stdout.log
8a983c81f2b0d1d240cc6c64245579a10ff3c1a7834a40e4fbfe067382aad908  ./SQ03_v3_2_8/SQ03-R03/trace_v31.jsonl
e80680736f9215bf0e2cc1bf18d51f27af5ee934b5c593734aa69232e9594bca  ./SQ03_v3_2_8/SQ03-R04/config.ini
233beccccc6f495fc2932f672fd9486c48e97c9546355561a94c2da208cab030  ./SQ03_v3_2_8/SQ03-R04/config.json
8d4f08b381d0d691641fd0eb53ed3c2ec750ef3b09ea1761d844b05f27677bb1  ./SQ03_v3_2_8/SQ03-R04/lsq_fwd_injections.log
82886086dd9c3ed9ed0c5b078f4fd78c84a01cb31d7aaf232e0c30629949142a  ./SQ03_v3_2_8/SQ03-R04/manifest.json
44a02828133c60cda9765bbe6bc58de05361838350732c8c0bdc3c2cca9b29fc  ./SQ03_v3_2_8/SQ03-R04/oracle.log
f5d6c086edaa5c97348e18a91d73d0e6fe0844fabc19c4778cbaf4fbccb224c7  ./SQ03_v3_2_8/SQ03-R04/pilot_meta.json
ad4aa6eaf4a78d19c0c36789554c72c876f8c3097067ba1b7f80910dfcb84d4c  ./SQ03_v3_2_8/SQ03-R04/stats.txt
32b304ab96750d84527a1f8301eaf7291e36eb50a052c304a6c180029cf8cdcd  ./SQ03_v3_2_8/SQ03-R04/stderr.log
f5f73cda97b0bdcfef6dfb6bf8ea841869ddf1796fef7587ef4c615c9213f308  ./SQ03_v3_2_8/SQ03-R04/stdout.log
476bc41aa8ae5f22113614a5cc06a0a1cc9500a843cc886f1efb95bcac3a26e1  ./SQ03_v3_2_8/SQ03-R04/trace_v31.jsonl
1ce66a1bbe8c73dd483288f54489020c5d730cd52fb10ac79617cfc3ef21877c  ./SQ03_v3_2_8/SQ03-R05/config.ini
82432a1d96943e107739ae51787e5231260bd421b7ab6fb4b9d626c19ecfc42e  ./SQ03_v3_2_8/SQ03-R05/config.json
b834301c280cf472dc201aee977d0e95d8ad9684b4a93e888d54a26d0bc3a31e  ./SQ03_v3_2_8/SQ03-R05/lsq_fwd_injections.log
bbb2d039dfc40125ce6786c36000f6a32009b0bd1884f12479ee5ec238202a00  ./SQ03_v3_2_8/SQ03-R05/manifest.json
44a02828133c60cda9765bbe6bc58de05361838350732c8c0bdc3c2cca9b29fc  ./SQ03_v3_2_8/SQ03-R05/oracle.log
95072e7123b439f8bcb9385eec3fa3e7e811d1609e79e9a263511aaea02440de  ./SQ03_v3_2_8/SQ03-R05/pilot_meta.json
6f1f7f8486b3ed498924ffeb38fd63953c7621c2992c6c287a2f4c1afffa2ada  ./SQ03_v3_2_8/SQ03-R05/stats.txt
32b304ab96750d84527a1f8301eaf7291e36eb50a052c304a6c180029cf8cdcd  ./SQ03_v3_2_8/SQ03-R05/stderr.log
69f4a1e77bb3eb17872d251b6eada384674e7d0d53eb7b8cc46687c7113b28f9  ./SQ03_v3_2_8/SQ03-R05/stdout.log
e91ef970cfc6298d0382f2ffd2bc7856a5c91da73b6c3a703306bea15ef0b8c2  ./SQ03_v3_2_8/SQ03-R05/trace_v31.jsonl
```

### 5.4 SP05_v3_2_9

```
ac0632e571df26585667525929cfd574feb9374cbf5d73eb7a0f5cab120f6ba4  ./SP05_v3_2_9/SP05-R01/config.ini
552eba65ff99f460c6207503e377b46d704549c6a8df6b4ed7adb150ee291b35  ./SP05_v3_2_9/SP05-R01/config.json
f9aeffffa0dfdc6150ca3e054b26e1c0572c42e5dac85b844b175eb4b7831ec2  ./SP05_v3_2_9/SP05-R01/lsq_fwd_injections.log
e4571203386fa64d2464ddf5a35c00e98cf8b8002f5a335850a37abaa6547cff  ./SP05_v3_2_9/SP05-R01/manifest.json
e35c1bdd536a130772a3e1e7d17a2ff84c5a26a9b965a2ab20b9f1259ad4e00a  ./SP05_v3_2_9/SP05-R01/oracle.log
226ec03087038f53799bda58f45679b24c54d464f61833f8deb632df790aaef9  ./SP05_v3_2_9/SP05-R01/pilot_meta.json
138c57dd7f413d2a6eb6ff185b395bb042f6e370b4050e9fce0b7ce74d773811  ./SP05_v3_2_9/SP05-R01/stats.txt
38e67d244f3b854112f0e75fd3f6081c7ad3bae2495d0110223d584a93612b49  ./SP05_v3_2_9/SP05-R01/stderr.log
565e0eb6125c717600791e10b46f623ecc770b3c0e8fc12698c0bac4857d1d33  ./SP05_v3_2_9/SP05-R01/stdout.log
0001110b1ce82efdbd308d91bbcd059cafac160d406e43e0f849b5010559dca8  ./SP05_v3_2_9/SP05-R01/trace_v31.jsonl
d8e00347eaa759c3abafdb227a507dd27717e43e1ce31a4d06a29db06612287f  ./SP05_v3_2_9/SP05-R02/config.ini
b9954c4afcc760faf438d70bae4aa9e28ebbd7f0346f2eb78fe5afea55f384b2  ./SP05_v3_2_9/SP05-R02/config.json
d83b4c2f1f70fd62da7b2c43bba9359a268dcb3c6c0d7026e3d9e0a58d2974e1  ./SP05_v3_2_9/SP05-R02/lsq_fwd_injections.log
6d1347aba69bf6eff287fc08b0b6ef22fcd73fe02ab33cfd59cfce0ace504cfd  ./SP05_v3_2_9/SP05-R02/manifest.json
e35c1bdd536a130772a3e1e7d17a2ff84c5a26a9b965a2ab20b9f1259ad4e00a  ./SP05_v3_2_9/SP05-R02/oracle.log
b4d4fe420ec59c60edac38d28302ebf2a5bf415456bce46143c25cde3b1dd551  ./SP05_v3_2_9/SP05-R02/pilot_meta.json
f39a037aeecd3c857dc254341f562de97c23cb6841745a239653c2a186344988  ./SP05_v3_2_9/SP05-R02/stats.txt
38e67d244f3b854112f0e75fd3f6081c7ad3bae2495d0110223d584a93612b49  ./SP05_v3_2_9/SP05-R02/stderr.log
a353f84ae9b65c32b1aef1d179692968cca4dec0be8e67a917d4339094e2579e  ./SP05_v3_2_9/SP05-R02/stdout.log
12eb7ce46ea6d2fe7219ead8314cf5aeefabee99acc37a242bc3e09cd5c73ef9  ./SP05_v3_2_9/SP05-R02/trace_v31.jsonl
668743f35cfb94a353cb03d7887b0ee96f8964298e7cbc5f2ffb7feb52fb7c91  ./SP05_v3_2_9/SP05-R03/config.ini
33d498a5eb70f41e661b7d7c15390b9038543a4f17750f8d9acb4df1390ffd7b  ./SP05_v3_2_9/SP05-R03/config.json
88c007a1cce099557665ed5592d53bd51ab4977ca5eb5275ffa798a028a8f50c  ./SP05_v3_2_9/SP05-R03/lsq_fwd_injections.log
8dd2ae9650188ca44e1080f1d647d561c1e278bde4a37a20ff291b8251f29b8a  ./SP05_v3_2_9/SP05-R03/manifest.json
e35c1bdd536a130772a3e1e7d17a2ff84c5a26a9b965a2ab20b9f1259ad4e00a  ./SP05_v3_2_9/SP05-R03/oracle.log
6b31f42d4a57bcde9603ab113b8780f5e7edecf8f841fa5463365466a1407b82  ./SP05_v3_2_9/SP05-R03/pilot_meta.json
6dfc998d58d0f10a0e86a9b94ccfa2fb0583d9273b70c00bb964e7c91d2c4c3f  ./SP05_v3_2_9/SP05-R03/stats.txt
38e67d244f3b854112f0e75fd3f6081c7ad3bae2495d0110223d584a93612b49  ./SP05_v3_2_9/SP05-R03/stderr.log
42d2b49ae0266060b76d7bac5236248f23e2c2ceb6f50d0d1d440e6101eda08d  ./SP05_v3_2_9/SP05-R03/stdout.log
ee4ad6918a4dabab674972fbccb347155d78acd3d12378551ee5dcd378bdf5eb  ./SP05_v3_2_9/SP05-R03/trace_v31.jsonl
9b1fc77867c0eab827c3178a1440797e05c18edbbb81b3365db6ea7626ec089b  ./SP05_v3_2_9/SP05-R04/config.ini
2b7e7c9b417bfe9874ea021ff1787897a253608b3daa009b79e4487e285b86c8  ./SP05_v3_2_9/SP05-R04/config.json
b2f5c77e968739faee5ec605bddf3959fe25f4102d9c67fba446bc5a61f9d20c  ./SP05_v3_2_9/SP05-R04/lsq_fwd_injections.log
1124174411d11dbf2a42ae8ffacb82242450b8296fa3c784026e224caff8473a  ./SP05_v3_2_9/SP05-R04/manifest.json
e35c1bdd536a130772a3e1e7d17a2ff84c5a26a9b965a2ab20b9f1259ad4e00a  ./SP05_v3_2_9/SP05-R04/oracle.log
c5b7f6f89b7439caee44b9b2dfc5c0fa093ab5f6be7ba1beea8c34e2edb51f00  ./SP05_v3_2_9/SP05-R04/pilot_meta.json
27f2b2bc1cc5d3dd812bd04f3922dc46770371a992286e05481e97fe8721df13  ./SP05_v3_2_9/SP05-R04/stats.txt
38e67d244f3b854112f0e75fd3f6081c7ad3bae2495d0110223d584a93612b49  ./SP05_v3_2_9/SP05-R04/stderr.log
182cf7cc9bfbd5923e99cec50d64c9d7b4e20ab841edfca122b0fbdabd3e2d27  ./SP05_v3_2_9/SP05-R04/stdout.log
19e50df5a0830626779d2a7e6d8b8cfec768be16721ce3fe22c98296f748b8d2  ./SP05_v3_2_9/SP05-R04/trace_v31.jsonl
4860dd27c9b1bf2dd2e0ce15d7632ec0b03ea717383a47204c045cac501a2a4a  ./SP05_v3_2_9/SP05-R05/config.ini
b24f1bf67a9ed18eeb79425257824bcd66fcbbf02d31dfea9a7e03d4ad1df89c  ./SP05_v3_2_9/SP05-R05/config.json
9cdd35aac22741f70fec92bc56e589dff58757d53dc1b43b9c7a6ad568e2c35b  ./SP05_v3_2_9/SP05-R05/lsq_fwd_injections.log
eb93c56b016e47bc7afbe2c632efb1b817886fd53b5ce5196958480803c771fb  ./SP05_v3_2_9/SP05-R05/manifest.json
e35c1bdd536a130772a3e1e7d17a2ff84c5a26a9b965a2ab20b9f1259ad4e00a  ./SP05_v3_2_9/SP05-R05/oracle.log
4a6e1d47fc52d7b068ee039d90a20998e1f922caf5ace247fa6b271ebbe93b53  ./SP05_v3_2_9/SP05-R05/pilot_meta.json
03fe4daf7e3427b1b64b7286f3fe22ec319755b901aff3ff09cf61b7f9f27870  ./SP05_v3_2_9/SP05-R05/stats.txt
38e67d244f3b854112f0e75fd3f6081c7ad3bae2495d0110223d584a93612b49  ./SP05_v3_2_9/SP05-R05/stderr.log
82cab7a325c450622dc199eb08c17c8a6ee6012488cffffd6d2f6d35cd714490  ./SP05_v3_2_9/SP05-R05/stdout.log
bcacefa2a9ec0ec680204e71643e0013a560000a0d621fe6284c93ffa787c3a3  ./SP05_v3_2_9/SP05-R05/trace_v31.jsonl
```

## 6. Missing files

**None.** All 20 pilots x 10 required files were present in their archives and extracted (200/200, zero unzip failures). Two honest clarifications:

- `oracle.log` **is present in all four archived vintages** (59 bytes each, e.g. `expected=ba3b3185e541ad03 got=ba3b3185e541ad03` / `ORACLE_PASS`). The known `ORACLE_FILE_MISSING` gap affects the in-tree v3.2.1-v3.2.6 pilots (kept only in `pilot_meta`), not these four archives.
- The in-tree dirs are thinner than the archives: `pilots_v3_2_3/SQ01-R01` and `pilots_v3_2_8/SQ03-R01` track everything except `trace_v31.jsonl` (>100 MB, GitHub limit; sidecar only), while `pilots_v3_2_7/FW05-R01` additionally lacks `oracle.log`, `stderr.log` and `lsq_fwd_injections.log` (gitignored `*.log`, never force-added), and SP05 has no in-tree pilot dir at all. The archives are therefore the only source for those files — which is why this extraction includes them.

## 7. History untouched (before/after proof)

Before extraction (and unchanged after):

```
$ git status --short docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_*
(no output — empty)
$ sha256sum docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R01/trace_v31.jsonl
d136131613fb009392f3f5829f370ce2ee415b442227439d6f8149597af99425  docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R01/trace_v31.jsonl
```

The LQ04-R01 hash equals the recorded value in `DELIVERABLES_SHA256_v3210.txt` line 51 (`d136131613fb009392f3f5829f370ce2ee415b442227439d6f8149597af99425  13_five_pilots/LQ04-R01/trace_v31.jsonl`, the v3.2.10 package manifest for the same trace bytes) and equals `sha256sum` of the git blob at HEAD (`git show HEAD:.../LQ04-R01/trace_v31.jsonl | sha256sum` → same value). After extraction both checks were re-run with identical results, and the repo-wide `git status --short` showed only ` M .gitignore`.

## 8. Task 8 audit tool runs on the extracted evidence (one pilot per model)

Command pattern (run from the worktree root; `--binary-sha` is each pilot's `manifest.json`-recorded binary SHA256, exercising the B9 match path; wrapped in `/usr/bin/time -v`-style resource measurement via `-f`):

```bash
/usr/bin/time -f "  elapsed=%es maxrss=%MkB" python3 tools/lsu_propagation_audit.py \
  --model <M> \
  --pilot-dir docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/<M>_v3_2_X/<M>-R01 \
  --binary-sha <manifest-recorded SHA> --json /tmp/task9_audit_<M>.json
```

Real outputs (verbatim, incl. `/usr/bin/time` resource line):

```
### SQ01 (SQ01_v3_2_3/SQ01-R01, --binary-sha 8eb7ce8d76ab63d90dbd00694efb90c7c2545da47ad07ecf5325399274a3b682)
model=SQ01 pilots=1 binary_splits=0
  docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SQ01_v3_2_3/SQ01-R01: classification=LIFECYCLE_ONLY missing=[NO_EARLY_ANOMALY_EVENT,NO_INTERMEDIATE_PROPAGATION_EVENT,NO_REGISTER_WRITEBACK_EVENT,NO_CONSUMER_EDGE]
FinalClassification=LIFECYCLE_ONLY
FaultEffectPropagationCoverage=LIFECYCLE_ONLY(1/1)
StructuralChainCompleteness=COMPLETE(1/1)
MissingEvidence=NO_EARLY_ANOMALY_EVENT;NO_INTERMEDIATE_PROPAGATION_EVENT;NO_REGISTER_WRITEBACK_EVENT;NO_CONSUMER_EDGE
SupplementaryPilotRequired=4
  elapsed=8.18s maxrss=19828kB

### FW05 (FW05_v3_2_7/FW05-R01, --binary-sha 8377c011bb5916be67fa1132232440ae7f8be02351c3034624a339319a545bec)
model=FW05 pilots=1 binary_splits=0
  docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/FW05_v3_2_7/FW05-R01: classification=LIFECYCLE_ONLY missing=[NO_CONSUMER_EDGE,NO_COMMIT_EVENT]
FinalClassification=LIFECYCLE_ONLY
FaultEffectPropagationCoverage=LIFECYCLE_ONLY(1/1)
StructuralChainCompleteness=COMPLETE(1/1)
MissingEvidence=NO_CONSUMER_EDGE;NO_COMMIT_EVENT
SupplementaryPilotRequired=2
  elapsed=1.54s maxrss=19844kB

### SQ03 (SQ03_v3_2_8/SQ03-R01, --binary-sha b988b7503cdf1feab10b99d09ec85df84b42eb385396142e0b7be6a197c63a45)
model=SQ03 pilots=1 binary_splits=0
  docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SQ03_v3_2_8/SQ03-R01: classification=LIFECYCLE_ONLY missing=[NO_REGISTER_WRITEBACK_EVENT,NO_CONSUMER_EDGE]
FinalClassification=LIFECYCLE_ONLY
FaultEffectPropagationCoverage=LIFECYCLE_ONLY(1/1)
StructuralChainCompleteness=COMPLETE(1/1)
MissingEvidence=NO_REGISTER_WRITEBACK_EVENT;NO_CONSUMER_EDGE
SupplementaryPilotRequired=2
  elapsed=8.12s maxrss=19840kB

### SP05 (SP05_v3_2_9/SP05-R01, --binary-sha 303c610d2dcca81340f0feae58fc449c8550d1daac6ff965a3387efd2189a0c0)
model=SP05 pilots=1 binary_splits=0
  docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/extracted_evidence/SP05_v3_2_9/SP05-R01: classification=LIFECYCLE_ONLY missing=[NO_EARLY_ANOMALY_EVENT,NO_REGISTER_WRITEBACK_EVENT,NO_CONSUMER_EDGE,NO_COMMIT_EVENT]
FinalClassification=LIFECYCLE_ONLY
FaultEffectPropagationCoverage=LIFECYCLE_ONLY(1/1)
StructuralChainCompleteness=COMPLETE(1/1)
MissingEvidence=NO_EARLY_ANOMALY_EVENT;NO_REGISTER_WRITEBACK_EVENT;NO_CONSUMER_EDGE;NO_COMMIT_EVENT
SupplementaryPilotRequired=4
  elapsed=3.89s maxrss=19844kB
```

Key facts from the four runs:

- **No extraction-defect codes**: zero `HASH_MISMATCH` (sidecar == computed hash), zero `BINARY_SHA_MISMATCH` / `BINARY_SHA_UNRECORDED` (manifest-recorded binary SHAs matched), zero `ORACLE_FILE_MISSING` / `ORACLE_META_INCONSISTENT` (`oracle.log` present and agreeing with `pilot_meta.oracle_pass` in all four).
- The missing-evidence codes that do appear are chain-stage gaps (`NO_EARLY_ANOMALY_EVENT`, `NO_INTERMEDIATE_PROPAGATION_EVENT`, `NO_REGISTER_WRITEBACK_EVENT`, `NO_CONSUMER_EDGE`, `NO_COMMIT_EVENT`) — model semantics for the per-model audit tasks, not evidence-integrity defects. All four R01 pilots classify `LIFECYCLE_ONLY` with `StructuralChainCompleteness=COMPLETE(1/1)` and a verified oracle (e.g. SQ01-R01 expected `ba3b3185e541ad03` == actual, pass=true; FW05-R01 adjudicated SQUASHED / `TARGET_SQUASHED_NO_COMMIT` vs observed MASKED).
- Streaming confirmed on the extracted evidence: peak RSS ~19.8 MB on the 198 MB SQ01-R01 and 197 MB SQ03-R01 traces (8.2 s / 8.1 s elapsed).

## 9. Notes for the downstream tasks (10-20, 21, 22/B8)

1. **SQ01 has two run sets.** The v3.2.3 bytes (extracted here, hash-verified) and the v3.2.4 re-runs (archive located in §1, not extracted). The SQ01 audit must pick its set explicitly and cite the corresponding sidecars.
2. **SP05's `SP05_v329_EVIDENCE.csv` has no trace-hash column**; the v3.2.9 zip's `SHA256SUMS` is the recorded checksum source used (all MATCH).
3. `extracted_evidence/` is regenerable scratch: the archives' SHA256s (§1) plus the commands in §2/§3 reproduce it byte-identically; the committed evidence is this index, never the extracted bytes.
4. FW05-R01's audit adjudication (SQUASHED vs observed MASKED) and the stage-gap codes per model are inputs for the per-model reports and the B8 supplementary-pilot decision — not to be re-litigated in this extraction record.
