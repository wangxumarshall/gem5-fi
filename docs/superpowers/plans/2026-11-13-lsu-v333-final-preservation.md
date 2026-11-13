# LSU v3.3.3 Final Repository Preservation & Historical Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve the LSU v3.3.3 formal campaign as one reproducible GitHub freeze branch + one external raw-data archive with two recoverable copies, prove it reproduces from the remote, and deliver a deletion candidate list for researcher approval — **without deleting anything this round**.

**Architecture:** Inventory the formal worktree (`lsu-platform-v3.2.12`, branch `lsu-v3.3.1-context-workload-20261111` @ `7067805d`) and copy the 401 MB formal results ZIP, the 1.1 GB formal binary, build log, config and source manifest into an archive root **outside every worktree** (`/home/sdc/lsu-v333-archive`). Build a freeze branch at `7067805d` in a **temporary** worktree, add documentation/manifests/result index only (no C++ or semantics changes), push it, and prove a fresh clone can pass preflight, print the 120-task dry run, verify all hashes, and regenerate the final collector/report outputs from the archived raw data. Cleanup is read-only analysis producing CSVs; deletion waits for approval.

**Tech Stack:** git (worktree/clone/tag), bash, Python 3 stdlib (`json`, `csv`, `hashlib`, `zipfile`), `sha256sum`, `unzip`, gem5 SE runner tools (`tools/lsu_v332_matrix.py`, `tools/lsu_v333_*`), pytest.

**Spec:** Researcher mandate of 2026-11-13 (sections I–XII, quoted in the session). There is no separate spec file; this plan is the operative decomposition. Every "do not" in the mandate is a Global Constraint below.

## Global Constraints

- **No deletion this round.** No `rm`, no `git push --delete`, no remote branch wildcards. Deletion executes only after researcher approval of the packet.
- **No force push.** Never overwrite an existing remote branch or tag. If `lsu-formal-v3.3.3-frozen` / `lsu-v3.3.3-formal-accepted` already exist, stop and report their targets.
- **Do not modify** formal C++ source, fault-model semantics, seeds, SampleRunIDs, workloads, ROI, or frozen classification. Archive-added files are documentation/manifests/reports only.
- **Do not claim** the archive HEAD is the binary's build commit. Always distinguish: Formal Build Source Commit `e3293856`, Final Tooling Commit `7067805d`, Archive Tag Commit, Archive Branch HEAD, Binary SHA256 `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd`.
- **Never `git add -A`.** Stage explicit paths only.
- **No new permanent worktree.** Freeze and reproduction use `/tmp` or a clearly temporary path, removed at the end.
- **Raw traces never enter git.** Keep only small result indexes (Excel + CSVs, total < 1 MB) in the repo.
- **Public repo:** `wangxumarshall/gem5-fi` is PUBLIC. Do **not** upload raw campaign data to GitHub Releases/LFS without explicit researcher approval; two on-host independent copies are the deliverable this round, and the off-host copy is an approval item.
- **Formal worktree is read-only evidence.** Never write inside `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12` except its existing untracked evidence stays untouched; all new outputs go to `/home/sdc/lsu-v333-archive`.
- **Every claim needs real output.** Quote command output in the reports; no predicted results.

## Review Focus

These are the failure modes most likely to produce a plausible-but-wrong archive:

1. **Hardcoded `ROOT`** in all five `final_config/*.sh` scripts points at `lsu-platform-v3.2.12`. A fresh clone runs the *old* worktree, not itself. Reproduction must use runtime-transformed copies and record their SHA256 — never edit the originals.
2. **Wrong provenance document.** `audit_v3_3_3/LSU_Final_Binary_Provenance.md` still says `1126e0fd` and "final 120-pair matrix"; the authoritative doc is `audit_v3_3_3/trace_closure/final_config/LSU_Final_Binary_Provenance.md` (`62e1b1be`). The stale file must be preserved and labeled superseded, not deleted or trusted.
3. **123 top-level dirs ≠ 123 runs.** The campaign root has 120 run dirs plus `collector_full/`, `collector_manifest/`, `collector_manifest.stage2-failed-20261113/`. Counting dirs naively overstates runs.
4. **`ORACLE_FAIL` is a result, not a crash.** 43 tasks are `ORACLE_FAIL` (fault runs with terminal SDC); 0 `FAILED`, 0 `HASH_MISMATCH`, 0 `TIMEOUT`, 0 `OUTPUT_INCOMPLETE`. Never "fix" or reclassify them.
5. **Symlinked run files.** Top-level run files are symlinks to `attempts/attempt_001/`; the ZIP stores dereferenced copies. Hash comparisons must be against the extracted/ZIP content, not symlink targets that may later move.
6. **Hardlinked binary.** `audit_v3_3_3/binary/gem5.opt.v333-62e1b1be` and `build/ARM/gem5.opt` may share an inode. Remove/clean the worktree and both names vanish. The archive copy must be a real byte copy (`cp`, not `ln`).
7. **Submodule `gem5-fs`** is a ~3 GB external repo not needed for SE formal reproduction. Clone without `--recurse-submodules` and record the omission explicitly.
8. **Duplicate-looking CSVs** (`LSU_Fault_Control_Audit.csv` vs `LSU_Fault_Control_Final_Audit.csv`, readiness variants) may or may not be byte-identical. Compare SHA256 before calling anything a duplicate.

---

## Verified Inventory (facts the implementer must not re-derive)

| Item | Verified value |
|---|---|
| Formal worktree | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12` |
| Formal branch / HEAD | `lsu-v3.3.1-context-workload-20261111` @ `7067805d9d24b185872cc06e3768a1e4dc5fa475` |
| Formal C++ source commit | `e329385616ba6c5f13bf44bc019e829d27e0c81f`; ancestor of `7067805d`; `git diff --stat e3293856..7067805d -- CHAOS/gem5/src` is empty |
| Commits after `e3293856` | 24 (tooling/report/launch/docs/tests only) |
| Formal binary | `build/ARM/gem5.opt` = `audit_v3_3_3/binary/gem5.opt.v333-62e1b1be`, SHA256 `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd`, 1,149,269,352 bytes |
| Formal config | `configs/se/lsu_proxy.py` SHA256 `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225` (working tree and `HEAD` agree) |
| Campaign root | `runs/lsu/formal_v333_final_20261112`, 3.2 GB, 120 run dirs (60 fault / 60 control), 120 `attempt_001` dirs, 3 non-run dirs (`collector_full`, `collector_manifest`, `collector_manifest.stage2-failed-20261113`) |
| Campaign index | 120 tasks: 77 `COMPLETED`, 43 `ORACLE_FAIL`, 0 of every failure state |
| Results ZIP | `LSU_v3.3.3_Final_Formal_Results_Accepted.zip`, 400,982,936 bytes, SHA256 `cece176a894edf139209c21fd219d031f4c0ea99a60cc2664addd743ac2df235`, 4138 entries, `unzip -t` OK |
| Contexts | 12 models (A01, A03, DA04, FW02, FW05, LP01, LQ04, MD04, RP01, SP05, SQ01, SQ03) × 5 contexts (R01–R05) × 2 roles; 60 unique SampleRunIDs, 60 unique seeds, fault/control share the same SampleRunID and seed |
| Workload ELFs | 9 ELF SHA256 values frozen in `campaign_identity.json` and `LSU_Final_Binary_Provenance.md` |
| Source manifest | `audit_v3_3_3/trace_closure/final_config/SOURCE_MANIFEST.sha256`, 7 C++ files |
| GitHub | `git@github.com:wangxumarshall/gem5-fi.git`, default `main`, **public**, 71 remote heads, 83 local branches, 38 registered worktrees (verified at execution; an earlier snapshot showed 40) |
| Disk | `/home` 46 GB free; `/tmp` 9.2 GB free |
| Running jobs | No gem5 / `lsu_v332_matrix` process observed; only stale per-slot lock files under `.tmp_lsu_conc/` |

## Output Locations

- Archive root (outside all worktrees): `/home/sdc/lsu-v333-archive/`
  - `raw/` — the formal results ZIP + `.sha256`
  - `raw_extracted/` — extracted verification copy (second recoverable copy)
  - `binary/` — real byte copy of the formal binary
  - `build/` — build log; `config/` — config snapshot; `manifests/` — source manifest + `final_config/`
  - `analysis/` — subagent CSV/manifest outputs
  - `approval/` — `LSU_Final_Cleanup_Approval_Packet.zip`
- Freeze worktree (temporary): `/tmp/lsu-freeze-20261113`
- Reproduction checkout (temporary): `/home/sdc/lsu-v333-repro-20261113` (not `/tmp`: needs 1.1 GB binary + 3.2 GB regenerated campaign)
- Repo docs: `docs/lsu/formal-v3.3.3/`

---

### Task 1: Preflight and archive root

**Files:**
- Create: `/home/sdc/lsu-v333-archive/{raw,raw_extracted,binary,build,config,manifests,analysis,approval}/`
- Create: `/home/sdc/lsu-v333-archive/LSU_Archive_SHA256SUMS` (finalized in Task 8)

**Interfaces:**
- Produces: `$ARCH` populated with the ZIP, binary, build log, config and source manifest; all later tasks read from `$ARCH`.

- [ ] **Step 1: Confirm no campaign process is running**

Run:
```bash
ps -eo pid,etime,cmd | grep -E '[g]em5\.opt|[l]su_v332_matrix|[l]su_v333' || true
```
Expected: no output (the campaign is complete). Record the output verbatim in the preservation report.

- [ ] **Step 2: Re-verify the three frozen hashes**

Run:
```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
sha256sum build/ARM/gem5.opt audit_v3_3_3/binary/gem5.opt.v333-62e1b1be configs/se/lsu_proxy.py
unzip -t LSU_v3.3.3_Final_Formal_Results_Accepted.zip | tail -1
cat LSU_v3.3.3_Final_Formal_Results_Accepted.zip.sha256
```
Expected: both binaries `62e1b1be…`, config `8309da72…`, zip "No errors detected", zip SHA `cece176a…`.

- [ ] **Step 3: Create the archive root and copy the recovery set**

Run:
```bash
export ARCH=/home/sdc/lsu-v333-archive
mkdir -p "$ARCH"/{raw,raw_extracted,binary,build,config,manifests,analysis,approval}
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
cp -p LSU_v3.3.3_Final_Formal_Results_Accepted.zip \
      LSU_v3.3.3_Final_Formal_Results_Accepted.zip.sha256 "$ARCH/raw/"
cp -p audit_v3_3_3/binary/gem5.opt.v333-62e1b1be "$ARCH/binary/gem5.opt.v333-62e1b1be"
cp -p audit_v3_3_3/trace_closure/baseline/build.log "$ARCH/build/"
cp -p configs/se/lsu_proxy.py "$ARCH/config/lsu_proxy.py"
cp -p audit_v3_3_3/trace_closure/final_config/SOURCE_MANIFEST.sha256 "$ARCH/manifests/"
cp -rp audit_v3_3_3/trace_closure/final_config "$ARCH/manifests/final_config"
```
Expected: `cp` exits 0. Verify the binary is a real copy, not a hardlink:
```bash
stat -c '%i %h %s %n' "$ARCH/binary/gem5.opt.v333-62e1b1be" \
  /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/build/ARM/gem5.opt
```
Expected: different inodes. Record both.

- [ ] **Step 4: Verify the copies**

Run:
```bash
cd "$ARCH"
sha256sum raw/LSU_v3.3.3_Final_Formal_Results_Accepted.zip \
          binary/gem5.opt.v333-62e1b1be config/lsu_proxy.py
```
Expected: `cece176a…`, `62e1b1be…`, `8309da72…`.

- [ ] **Step 5: Extract the verification copy**

Run:
```bash
cd "$ARCH"
unzip -q raw/LSU_v3.3.3_Final_Formal_Results_Accepted.zip -d raw_extracted
test -d raw_extracted/formal_v333_final_20261112 && echo EXTRACTED
find raw_extracted/formal_v333_final_20261112 -maxdepth 1 -mindepth 1 -type d -name '*-fault' | wc -l
find raw_extracted/formal_v333_final_20261112 -maxdepth 1 -mindepth 1 -type d -name '*-control' | wc -l
```
Expected: `EXTRACTED`, `60`, `60`.

- [ ] **Step 6: Record free space and sizes**

Run:
```bash
df -h /home | tail -1
du -sb "$ARCH"/raw "$ARCH"/raw_extracted "$ARCH"/binary
```
Expected: sizes ≈ 401 MB, ≈ 3.2 GB (6.7 GB logical due to symlink duplication), 1.1 GB.

---

### Task 2: Source closure manifest (Agent A)

**Files:**
- Create: `$ARCH/analysis/LSU_Formal_Source_Closure_Manifest.csv`
- Create: `$ARCH/analysis/agent_a_source_report.md`
- Later copied to: `docs/lsu/formal-v3.3.3/LSU_Formal_Source_Closure_Manifest.csv`

**Interfaces:**
- Consumes: `$ARCH/manifests/SOURCE_MANIFEST.sha256`, `$ARCH/manifests/final_config/`.
- Produces: CSV columns exactly `Item,Path,Value,SHA256,SourceCommit,VerifiedBy,Notes`; the report names the three commits and states whether the source is sufficient to rebuild the binary.

- [ ] **Step 1: Verify commit ancestry and absence of C++ drift**

Run in the formal worktree:
```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
git merge-base --is-ancestor e3293856 7067805d && echo 'e329 IS ancestor of 7067805d'
git diff --stat e3293856 7067805d -- CHAOS/gem5/src | wc -l
git diff --stat 7067805d -- CHAOS/gem5/src | wc -l
git status --porcelain --untracked-files=no | wc -l
```
Expected: `e329 IS ancestor…`, `0`, `0`, `0`.

- [ ] **Step 2: Verify every source-manifest file**

Run:
```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
sha256sum -c audit_v3_3_3/trace_closure/final_config/SOURCE_MANIFEST.sha256
```
Expected: 7 × `OK` (CHAOSPropagation .cc/.hh, CHAOSLSQFwd .cc/.hh, lsq.cc/.hh/unit.cc).

- [ ] **Step 3: Verify the config blob at the commit, not just the worktree**

Run:
```bash
git show 7067805d:configs/se/lsu_proxy.py | sha256sum
git show e3293856:configs/se/lsu_proxy.py | sha256sum
```
Expected: both `8309da72…`.

- [ ] **Step 4: Inventory the buildable source closure**

Run:
```bash
git ls-tree -r --name-only 7067805d -- CHAOS/gem5/src | wc -l
git ls-tree -r --name-only 7067805d -- configs/se tools workloads tests | wc -l
git ls-tree -r --name-only 7067805d -- CHAOS/gem5/src/cpu/o3 | grep -E 'CHAOS|lsq' | head -40
```
Expected: non-zero counts; all CHAOS*/lsq sources present. Record counts in the CSV. Do not build.

- [ ] **Step 5: Write the CSV and report**

Write `$ARCH/analysis/LSU_Formal_Source_Closure_Manifest.csv` with rows for: formal binary, config, source commit, tooling commit, build log, each of the 7 source files, the `final_config/` scripts, the runner/collector/oracle tooling entry points (`tools/lsu_v332_matrix.py`, `tools/lsu_v333_*.py`, `tools/classify.py`, `tools/runner.py`). Each row carries the SHA256 actually measured in Steps 1–4. In `agent_a_source_report.md`, state: (a) `e3293856` contains the final C++ content; (b) `7067805d` differs only outside `CHAOS/gem5/src`; (c) rebuild is possible in principle from the branch + vendored tree, but this round does **not** rebuild; (d) the build was an incremental SCons build whose log is archived.

---

### Task 3: Workload and context manifest (Agent B)

**Files:**
- Create: `$ARCH/analysis/LSU_Formal_Workload_Context_Manifest.csv`
- Create: `$ARCH/analysis/agent_b_context_report.md`
- Later copied to: `docs/lsu/formal-v3.3.3/LSU_Formal_Workload_Context_Manifest.csv`

**Interfaces:**
- Consumes: `runs/lsu/formal_v333_final_20261112/campaign_identity.json`, `audit_v3_3_3/trace_closure/final_config/LSU_Final_Campaign_Manifest_Template.csv`, `audit_v3_3_3/LSU_60Context_Final_Readiness.csv`, ELF files under `workloads/`.
- Produces: one CSV with columns `ModelID,Workload,ELFPath,ELF_SHA256,ContextID,SampleRunID,Seed,ROI_Start,ROI_End,ROI_N,Warmup,Percentile,EligibleEventOrdinal,DynInstSeq,PC,VA,PA,Role,FaultControlPair,SourcePath,Verified`.

- [ ] **Step 1: Verify the 120-row matrix and 60 unique contexts**

Run:
```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
python3 - <<'PY'
import csv, json
rows=list(csv.DictReader(open('audit_v3_3_3/trace_closure/final_config/LSU_Final_Campaign_Manifest_Template.csv')))
f=[r for r in rows if r['Role']=='fault']; c=[r for r in rows if r['Role']=='control']
print('rows',len(rows),'fault',len(f),'control',len(c))
print('unique SampleRunID',len({r['SampleRunID'] for r in f}))
print('unique seeds',len({r['Seed'] for r in rows}))
print('pair ids equal',{(r['ModelID'],r['ContextID']) for r in f}=={(r['ModelID'],r['ContextID']) for r in c})
print('pair seeds equal',all(next(x for x in c if (x['ModelID'],x['ContextID'])==(r['ModelID'],r['ContextID']))['Seed']==r['Seed'] for r in f))
print('models',sorted({r['ModelID'] for r in rows}))
print('contexts',sorted({r['ContextID'] for r in rows}))
PY
```
Expected: `rows 120 fault 60 control 60`, `unique SampleRunID 60`, `unique seeds 60`, both pairing checks `True`, 12 models, `['R01'..'R05']`.

- [ ] **Step 2: Verify every executed ELF hash against the frozen identity**

Run:
```bash
python3 - <<'PY'
import hashlib, json, csv, pathlib
wt=pathlib.Path('/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12')
ident=json.load(open(wt/'runs/lsu/formal_v333_final_20261112/campaign_identity.json'))
rows=list(csv.DictReader(open(wt/'audit_v3_3_3/trace_closure/final_config/LSU_Final_Campaign_Manifest_Template.csv')))
pairs={(r['Workload'],r['ELF']) for r in rows}
for wl,elf in sorted(pairs):
    p=wt/elf
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    print(wl, h==ident['elf_sha'].get(wl), h)
PY
```
Expected: every line `True`; 9 workloads. If any `False`, stop — do not continue.

- [ ] **Step 3: Verify ROI/percentile/ordinal evidence**

Run:
```bash
python3 - <<'PY'
import csv
rows=list(csv.DictReader(open('/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/audit_v3_3_3/trace_closure/final_config/LSU_Final_Campaign_Manifest_Template.csv')))
for m in sorted({r['ModelID'] for r in rows}):
    rs=[r for r in rows if r['ModelID']==m and r['Role']=='fault']
    print(m, [(r['ContextID'], r['Percentile'], r['EligibleEventOrdinal'], r['ROI_Start'], r['ROI_End'], r['ROI_N']) for r in rs])
PY
```
Expected: five 10/30/50/70/90 percentiles per model, distinct ordinals, non-empty ROI. Record in the CSV.

- [ ] **Step 4: Record workload sources and toolchain**

Run:
```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
for w in agu_addrmodes fw05_forward sq_reload_v3212 alignment load_response lq_lifetime_ordinal sq_forward_w4v2 replay_partial_v332 md04_violations_v332; do
  find workloads -maxdepth 3 -name "$w" -o -name "$w.c" -o -name "$w.cc" -o -name "$w.S" -o -name "*${w}*.sh" | sort
done
gcc --version | head -1
```
Expected: a source or compile script for each workload (or an explicit `n/a` where the ELF is historical); host gcc version recorded.

- [ ] **Step 5: Write the CSV and report**

Merge the 120 manifest rows with the 60 context identities into `LSU_Formal_Workload_Context_Manifest.csv`. Report: 60 contexts, 60 seeds, 60 SampleRunIDs, 9 ELF hashes, fault/control pairing. Use `n/a` — never a silent zero — for any field not evidenced.

---

### Task 4: Formal raw-data archive manifest (Agent C)

**Files:**
- Create: `$ARCH/analysis/LSU_Formal_Raw_Data_Archive_Manifest.csv`
- Create: `$ARCH/analysis/agent_c_rawdata_report.md`
- Later copied to: `docs/lsu/formal-v3.3.3/LSU_Formal_Raw_Data_Archive_Manifest.csv`

**Interfaces:**
- Consumes: `$ARCH/raw_extracted/formal_v333_final_20261112/`.
- Produces: CSV columns `RunID,ModelID,ContextID,Role,Attempts,CanonicalAttempt,Files,Bytes,TraceSHA256,SummarySHA256,ManifestSHA256,OracleResult,TerminalState,CampaignID,BinarySHA,ConfigSHA,Included`; report distinguishes formal from pilot data.

- [ ] **Step 1: Verify all raw-run hashes in the extracted archive**

Run:
```bash
cd /home/sdc/lsu-v333-archive/raw_extracted/formal_v333_final_20261112
sha256sum --quiet -c SHA256SUMS.raw_runs
```
Expected: no `FAILED` lines; exit 0. If the file lists relative `./...` paths, run from this directory; record the exact command.

- [ ] **Step 2: Verify campaign-level deliverables**

Run:
```bash
cd /home/sdc/lsu-v333-archive/raw_extracted/formal_v333_final_20261112
sha256sum --quiet -c SHA256SUMS.deliverables
```
Expected: exit 0. Record any file listed there that is missing from the ZIP (there must be none).

- [ ] **Step 3: Count and classify runs vs non-run directories**

Run:
```bash
python3 - <<'PY'
import json
from pathlib import Path
r=Path('/home/sdc/lsu-v333-archive/raw_extracted/formal_v333_final_20261112')
dirs=[d for d in r.iterdir() if d.is_dir()]
runs=[d for d in dirs if d.name.endswith('-fault') or d.name.endswith('-control')]
other=[d.name for d in dirs if d not in runs]
idx=json.load(open(r/'campaign_index.json'))
print('dirs',len(dirs),'runs',len(runs),'other',sorted(other))
print('index task_count',idx['task_count'],'counts',idx['counts'])
print('attempts',sum(1 for d in runs for _ in (d/'attempts').glob('attempt_*')))
print('trace_v31',sum(1 for d in runs if (d/'trace_v31.jsonl').exists() or (d/'attempts/attempt_001/trace_v31.jsonl').exists()))
print('prop_trace',sum(1 for d in runs if (d/'prop_trace.csv.gz').exists() or (d/'attempts/attempt_001/prop_trace.csv.gz').exists()))
PY
```
Expected (verified during execution): `dirs 123 runs 120 other ['collector_full','collector_manifest','collector_manifest.stage2-failed-20261113']`, `task_count 120`, `attempts 120`, **`trace_v31 105`** (the 15 direct-driver runs — A03 fault R01–R05 and RP01 fault+control R01–R05 — have no `trace_v31.jsonl`, by design), **`prop_trace 120`** (all runs carry `prop_trace.csv.gz`). Document this split as a limitation; never manufacture the 15 missing `trace_v31` files.

- [ ] **Step 4: Verify every run's frozen identity**

Run:
```bash
python3 - <<'PY'
import json
from pathlib import Path
r=Path('/home/sdc/lsu-v333-archive/raw_extracted/formal_v333_final_20261112')
bad=[]
for d in sorted(x for x in r.iterdir() if x.name.endswith(('-fault','-control'))):
    m=json.load(open(d/'manifest.json'))
    if m.get('Binary_SHA256')!='62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd': bad.append((d.name,'binary'))
    if m.get('Config_SHA256')!='8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225': bad.append((d.name,'config'))
    c=json.load(open(d/'campaign.json'))
    if c.get('campaign_id')!='LSU-V333-FINAL-20261112': bad.append((d.name,'campaign'))
print('checked',120,'bad',bad)
PY
```
Expected: `bad []`. (If manifest key names differ, read one manifest first and adjust the key names; do not weaken the check.)

- [ ] **Step 5: Separate formal from pilot evidence**

Run:
```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
du -sh audit_v3_3_3/runs audit_v3_3_3/runs_685d88f7 runs/lsu/formal_v333 2>/dev/null
find audit_v3_3_3/runs -maxdepth 1 -mindepth 1 -type d | wc -l
```
Expected: pilot/Pre-Formal evidence exists only under the audit paths and must be labeled non-formal. Record sizes and counts; never merge them into the manifest.

- [ ] **Step 6: Write the CSV and report**

Per run, record attempt count (1), canonical attempt (`attempt_001`), file count, bytes, SHA256 of trace/summary/manifest, oracle result, terminal state, binary/config/campaign IDs, and `Included=FORMAL`. Report: 120 runs, 120 attempts, 0 retries, 43 `ORACLE_FAIL` = terminal SDC evidence, 3 non-run dirs explicitly preserved (`collector_manifest.stage2-failed-20261113` is marked `NON_CANONICAL` in `SHA256SUMS.deliverables`).

---

### Task 5: Git branch and server file cleanup candidates (Agent D, read-only)

**Files:**
- Create: `$ARCH/analysis/LSU_Git_Branch_Cleanup_Candidates.csv`
- Create: `$ARCH/analysis/LSU_Server_Cleanup_Candidates.csv`
- Create: `$ARCH/analysis/agent_d_cleanup_report.md`
- Later copied to: `docs/lsu/formal-v3.3.3/`

**Interfaces:**
- Consumes: `git for-each-ref`, `git worktree list`, `git tag --contains`, `du`, `stat`, `sha256sum`.
- Produces: branch CSV columns `Branch,Scope,Head,LastCommitDate,LastCommitSubject,ContainsUniqueCommitsVsFreeze,UniqueCommitCountVsFreeze,UniqueCommitCountVsFiDing,UsedByWorktree,ReferencedByTag,ContainsUnarchivedSource,SuggestedAction,Risk,Reason`; server CSV columns as mandated in section IX.

- [ ] **Step 1: Enumerate branches with relationships**

Run from `/home/sdc/gem5-fi-ding`:
```bash
git for-each-ref --format='%(refname:short)|%(objectname)|%(committerdate:iso8601)|%(subject)' refs/heads refs/remotes/origin > /tmp/branches.txt
git worktree list --porcelain > /tmp/worktrees.txt
git tag --format='%(refname:short)|%(objectname)|%(subject)' > /tmp/tags.txt
```
Then for each LSU-looking branch compute:
```bash
git rev-list --count <branch> --not 7067805d
git rev-list --count <branch> --not fi-ding
git merge-base --is-ancestor <branch> 7067805d && echo contained
```
Expected: 83 local heads, 71 remote heads; classify every branch. Keep `fi-ding`, `lsu-formal-v3.3.3-frozen`, the tag, and any branch that still has unique unarchived work or is used by a registered worktree.

- [ ] **Step 2: Identify worktree usage and live processes**

Run:
```bash
git worktree list
ps -eo pid,cmd | grep -E '[g]em5\.opt|[l]su_' || true
```
Expected: 40 worktrees; no live LSU process. Mark any branch checked out in a worktree as `KEEP_ACTIVE_WORKTREE`.

- [ ] **Step 3: Inventory server LSU history**

Scan only LSU-related paths; explicitly exclude other projects/MMU:
```bash
du -sh /home/sdc/gem5-fi-ding /home/sdc/gem5-fi-ding/runs /home/sdc/gem5-fi-ding/runs/lsu \
       /home/sdc/gem5-fi-ding/.claude/worktrees/* 2>/dev/null | sort -h > /tmp/du_lsu.txt
find /home/sdc/gem5-fi-ding -maxdepth 3 \( -iname '*LSU*' -o -iname '*lsu*' \) | head -200 > /tmp/lsu_paths.txt
```
For each candidate record: absolute path, type, size, phase, mtime, `DependsOnFormalRun` (must be `NO` for any deletion candidate), `ArchivedCopy` (path + SHA or `NONE`), `SHA256`, recommended action, `NeedsApproval=YES`.

- [ ] **Step 4: Hash duplicate candidates**

Run SHA256 over every `gem5.opt` and every ZIP larger than 10 MB in LSU paths:
```bash
find /home/sdc/gem5-fi-ding -path '*/build/ARM/gem5.opt' -o -name 'LSU_*.zip' | while read f; do
  printf '%s  %s\n' "$(sha256sum "$f" | cut -d' ' -f1)" "$f"
done | sort
```
Expected: distinguish `62e1b1be` (formal), `1126e0fd` (pre-closure), `6db026e7`/`63f50c40` (other builds), and the several `LSU_v3.3.x` ZIPs. Never call two files duplicates on name alone.

- [ ] **Step 5: Write both CSVs and the report**

Every deletion candidate must be `NeedsApproval=YES`; the report's headline is a count and total bytes, not a deletion. Explicitly list what is **not** safe to delete: the campaign root, the formal binary, `final_config/`, the stale-vs-authoritative provenance docs, any active worktree, and any lock file.

---

### Task 6: Create, document, push, and tag the freeze branch

**Files:**
- Create (temporary worktree): `/tmp/lsu-freeze-20261113` on branch `lsu-formal-v3.3.3-frozen`
- Create: `docs/lsu/formal-v3.3.3/{README.md,PROVENANCE.md,results/,repro/}` and the Task 2–5 artifacts
- Commit-message prefixes: `[LSU][V3.3.3][ARCHIVE]`, `[LSU][V3.3.3][MANIFEST]`, `[LSU][V3.3.3][CLEANUP]`, `[LSU][V3.3.3][REPRO]`

**Interfaces:**
- Consumes: `$ARCH/analysis/*`, Task 1 archive.
- Produces: remote branch `lsu-formal-v3.3.3-frozen`, annotated tag `lsu-v3.3.3-formal-accepted`.

- [ ] **Step 1: Fail closed if the branch or tag exists**

Run:
```bash
git ls-remote --heads origin refs/heads/lsu-formal-v3.3.3-frozen
git ls-remote --tags origin refs/tags/lsu-v3.3.3-formal-accepted
git branch --list lsu-formal-v3.3.3-frozen
git tag -l lsu-v3.3.3-formal-accepted
```
Expected: all four empty. If any is non-empty, **stop** and report its target; do not overwrite.

- [ ] **Step 2: Create the temporary freeze worktree at the final tooling commit**

Run:
```bash
cd /home/sdc/gem5-fi-ding
git worktree add /tmp/lsu-freeze-20261113 -b lsu-formal-v3.3.3-frozen 7067805d
cd /tmp/lsu-freeze-20261113
git rev-parse HEAD HEAD^{tree} HEAD:CHAOS/gem5/src
git diff --stat e3293856 HEAD -- CHAOS/gem5/src | wc -l
```
Expected: HEAD `7067805d…`, non-zero tree hashes, diff count `0`. Record the `CHAOS/gem5/src` subtree hash — Task 7 compares it.

- [ ] **Step 3: Add README and PROVENANCE (commit 1)**

`README.md` records the three identities explicitly:
- Formal Build Source Commit: `e3293856` (C++ tree content)
- Final Tooling Commit: `7067805d` (campaign tooling/docs, no C++ drift)
- Binary SHA256: `62e1b1be…`; Config SHA256: `8309da72…`
- Campaign ID: `LSU-V333-FINAL-20261112`; 12 models × 5 contexts × 2 roles
- Raw archive location `/home/sdc/lsu-v333-archive/` + ZIP SHA `cece176a…`
- Frozen limitations: SP05 QUALIFIED, RP01 TRACE_INCOMPLETE, A03-R02 COMPLETE_CAUSAL_CHAIN
- Note that `audit_v3_3_3/LSU_Final_Binary_Provenance.md` (`1126e0fd`) is **superseded** by `audit_v3_3_3/trace_closure/final_config/LSU_Final_Binary_Provenance.md` (`62e1b1be`).

Also copy this plan file into the branch so the repo records why each unit was committed:
```bash
mkdir -p docs/superpowers/plans
cp /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-w1-continuation-20261101/docs/superpowers/plans/2026-11-13-lsu-v333-final-preservation.md docs/superpowers/plans/
```

Stage explicitly:
```bash
git add docs/lsu/formal-v3.3.3/README.md docs/lsu/formal-v3.3.3/PROVENANCE.md \
        docs/lsu/formal-v3.3.3/LSU_Formal_Source_Closure_Manifest.csv \
        docs/superpowers/plans/2026-11-13-lsu-v333-final-preservation.md
git commit -m "[LSU][V3.3.3][ARCHIVE] freeze formal source provenance and source closure manifest"
```

- [ ] **Step 4: Add workload/context and raw-data manifests (commit 2)**

```bash
git add docs/lsu/formal-v3.3.3/LSU_Formal_Workload_Context_Manifest.csv \
        docs/lsu/formal-v3.3.3/LSU_Formal_Raw_Data_Archive_Manifest.csv
git commit -m "[LSU][V3.3.3][MANIFEST] freeze 12 models, 60 contexts, 60 seeds and 120-run archive index"
```

- [ ] **Step 5: Add the small result index (commit 3)**

Copy only small files (< 1 MB total) from `$ARCH/raw_extracted/formal_v333_final_20261112/`:
`LSU_60Context_Causal_Propagation_Final.csv`, `LSU_60Context_Final_Readiness.csv`, `LSU_Control_Audit_Formal.csv`, `LSU_Fault_Control_Pair_RAW.csv`, `LSU_Final_Oracle_Summary.csv`, `LSU_V333_FINAL_ACCEPTANCE_REPORT.md`, `LSU_V333_FINAL_EVIDENCE_NORMALIZATION_REPORT.md`, `LSU_Evidence_Completeness_Audit.csv`, `LSU_A03_Injection_Count_Semantics.csv`, `LSU_Final_Experiment_Config.xlsx`, `campaign_index.json`, `campaign_identity.json`, `SHA256SUMS.raw_runs`, `SHA256SUMS.deliverables`.

```bash
git add docs/lsu/formal-v3.3.3/results/
git commit -m "[LSU][V3.3.3][ARCHIVE] add final result index and acceptance evidence"
```

- [ ] **Step 6: Add cleanup candidates, proposed plan, and reproduction tooling (commit 4)**

Copy Task 2–5 CSVs and reports, plus `repro/` scripts. `repro/reproduce_from_clone.sh` must:
```bash
# runtime-transform the frozen scripts; originals stay byte-identical
sed "s#^ROOT=.*#ROOT=$CLONE#" audit_v3_3_3/trace_closure/final_config/01_launch_campaign.sh > "$CLONE/.repro/01.sh"
```
and record `sha256sum` of each transformed copy. Include a README stating this wrapper exists only because the frozen scripts hardcode the original worktree path.

```bash
git add docs/lsu/formal-v3.3.3/LSU_Git_Branch_Cleanup_Candidates.csv \
        docs/lsu/formal-v3.3.3/LSU_Server_Cleanup_Candidates.csv \
        docs/lsu/formal-v3.3.3/LSU_Proposed_Deletion_Plan.md \
        docs/lsu/formal-v3.3.3/repro/
git commit -m "[LSU][V3.3.3][CLEANUP] add branch and server deletion candidates (no deletion executed)"
```

- [ ] **Step 7: Push the branch**

Run:
```bash
git push -u origin lsu-formal-v3.3.3-frozen
```
Expected: new branch created; no force. Verify:
```bash
git ls-remote --heads origin refs/heads/lsu-formal-v3.3.3-frozen
```
Expected: the local HEAD SHA.

- [ ] **Step 8: Write the frozen branch report**

`LSU_GitHub_Frozen_Branch_Report.md` records: branch name, HEAD SHA, tree SHA, `CHAOS/gem5/src` subtree SHA, tag name (pending), push command output, and the three-identity table. Commit and push it (docs-only commit 5). Do **not** tag yet; the tag is created after reproduction so it can state what was verified.

---

### Task 7: Remote independent reproduction (Agent E + main)

**Files:**
- Create: `/home/sdc/lsu-v333-repro-20261113` (temporary clone; removed only after the packet is built and the researcher approves further cleanup — this round it is evidence, so keep it)
- Create: `$ARCH/analysis/LSU_Reproducibility_Verification.md`
- Later copied to: `docs/lsu/formal-v3.3.3/LSU_Reproducibility_Verification.md`

**Interfaces:**
- Consumes: the remote branch, `$ARCH/binary/`, `$ARCH/raw_extracted/`, `docs/lsu/formal-v3.3.3/repro/`.
- Produces: a report with ten pass/fail checks, each quoting real output.

- [ ] **Step 1: Clone from the remote (no submodules)**

Run:
```bash
git clone --branch lsu-formal-v3.3.3-frozen \
  git@github.com:wangxumarshall/gem5-fi.git /home/sdc/lsu-v333-repro-20261113
cd /home/sdc/lsu-v333-repro-20261113
git log --oneline -3
```
Expected: clone succeeds; HEAD equals the pushed branch HEAD; `gem5-fs/` is empty (submodule intentionally not initialized — SE formal does not use it).

- [ ] **Step 2: Verify source and config identity from the clone**

Run:
```bash
cd /home/sdc/lsu-v333-repro-20261113
sha256sum --quiet -c audit_v3_3_3/trace_closure/final_config/SOURCE_MANIFEST.sha256 && echo SOURCE_OK
sha256sum configs/se/lsu_proxy.py
git rev-parse HEAD:CHAOS/gem5/src
```
Expected: 7 × `OK`; config `8309da72…`; subtree hash equals the value recorded in Task 6 Step 2.

- [ ] **Step 3: Restore the preserved binary into the clone**

Run:
```bash
mkdir -p build/ARM
cp /home/sdc/lsu-v333-archive/binary/gem5.opt.v333-62e1b1be build/ARM/gem5.opt
chmod +x build/ARM/gem5.opt
sha256sum build/ARM/gem5.opt
```
Expected: `62e1b1be…`.

- [ ] **Step 4: Run the 120-task dry run from the clone**

Run:
```bash
mkdir -p .repro
for s in 01_launch_campaign.sh 02_manifest_only.sh 03_full_collector.sh 04_final_reports.sh launch_commands_final.sh; do
  sed "s#^ROOT=.*#ROOT=$PWD#" "audit_v3_3_3/trace_closure/final_config/$s" > ".repro/$s"
  chmod +x ".repro/$s"
  sha256sum ".repro/$s"
done
bash .repro/01_launch_campaign.sh --dry-run
```
Expected: `dry-run: 120 commands; no run dirs written`; exit 0; no `runs/lsu/formal_v333_final_20261112/` created in the clone. Record the transformed-script SHAs.

- [ ] **Step 5: Verify the 60 SampleRunIDs and 60 seeds**

Run the Task 3 Step 1 script inside the clone. Expected identical output.

- [ ] **Step 6: Verify the archived raw data is readable and hash-clean**

Run:
```bash
cd /home/sdc/lsu-v333-archive/raw_extracted/formal_v333_final_20261112
sha256sum --quiet -c SHA256SUMS.raw_runs && echo RAW_OK
sha256sum --quiet -c SHA256SUMS.deliverables && echo DELIVERABLES_OK
```
Expected: `RAW_OK`, `DELIVERABLES_OK`.

- [ ] **Step 7: Regenerate the collector and final reports from archived data**

Run (the clone's campaign root must be populated from the archive):
```bash
cd /home/sdc/lsu-v333-repro-20261113
mkdir -p runs/lsu
cp -a /home/sdc/lsu-v333-archive/raw_extracted/formal_v333_final_20261112 runs/lsu/
bash .repro/02_manifest_only.sh
bash .repro/03_full_collector.sh
FORCE=1 bash .repro/04_final_reports.sh
```
Expected: each stage exits 0. Compare regenerated `LSU_60Context_Causal_Propagation_Final.csv`, `LSU_60Context_Final_Readiness.csv`, `LSU_Control_Audit_Formal.csv`, `collector_full/LSU_120Run_Campaign_Manifest.csv`, `collector_full/LSU_60Fault_60Control_Pair_Map.csv`, `collector_full/LSU_Control_Zero_Proof_Final.csv` and the two XLSX files against `SHA256SUMS.deliverables`. Record exact SHA256 matches and any non-deterministic difference (e.g. timestamp metadata) with its cause. **Do not rerun the 120 experiments.**

- [ ] **Step 8: Run the affected test suite**

Run:
```bash
cd /home/sdc/lsu-v333-repro-20261113
python3 -m pytest tests/test_lsu_v333_control_proof.py tests/test_lsu_v333_control.py \
  tests/test_lsu_v333_final_launch_acceptance.py tests/test_lsu_v333_lock_resume.py \
  tests/test_lsu_v333_manifest_isolation.py tests/test_lsu_v333_propagation.py \
  tests/test_lsu_v333_provenance.py tests/test_lsu_v333_qualified.py \
  tests/test_lsu_v333_runner_errors.py tests/test_lsu_v333_shell_pipeline.py \
  tests/test_lsu_v333_synthetic.py tests/test_lsu_v333_workbook.py -q
```
Expected: all pass; record the count. This is the unaffected regression check.

- [ ] **Step 9: Write the ten-check report**

`LSU_Reproducibility_Verification.md` lists: (1) source fetch, (2) submodule status, (3) workload source + ELF completeness, (4) config location/hash, (5) tests, (6) 120-task dry run, (7) 60 SampleRunIDs/seeds, (8) all hash checks, (9) raw archive readable, (10) reports/Excel regenerated. Each line states PASS/FAIL and quotes the command output. State plainly that no rebuild was performed and no byte-identical binary claim is made.

---

### Task 8: Approval packet, tag, and stop

**Files:**
- Create: `$ARCH/approval/LSU_Final_Cleanup_Approval_Packet.zip`
- Create/update: `docs/lsu/formal-v3.3.3/LSU_Final_Preservation_Report.md`, `LSU_Archive_SHA256SUMS`, `LSU_Reproducibility_Verification.md`
- Tag: `lsu-v3.3.3-formal-accepted`

**Interfaces:**
- Consumes: everything above.
- Produces: packet ZIP + SHA256, pushed branch/tag, final report with the mandated statistics, and an explicit stop.

- [ ] **Step 1: Finalize `LSU_Archive_SHA256SUMS`**

Run:
```bash
cd /home/sdc/lsu-v333-archive
sha256sum raw/LSU_v3.3.3_Final_Formal_Results_Accepted.zip \
          binary/gem5.opt.v333-62e1b1be config/lsu_proxy.py \
          build/build.log manifests/SOURCE_MANIFEST.sha256 > LSU_Archive_SHA256SUMS
cat LSU_Archive_SHA256SUMS
```
Expected: the three known hashes plus the build log and source manifest.

- [ ] **Step 2: Write the preservation report with real statistics**

`LSU_Final_Preservation_Report.md` must fill every mandated statistic from measured output:
- total LSU historical server data size (from `du`)
- size that must be retained for the formal experiment
- archived + verified size
- cleanup-candidate size (sum of `NeedsApproval=YES` rows)
- number of old LSU branches recommended for deletion
- number of branches that must be kept
- number of archive copies (ZIP in worktree + ZIP in archive + extracted archive; binary original + archive copy)
- remote freeze branch push status
- remote reproduction result
Include the three-identity table and the frozen limitations.

- [ ] **Step 3: Copy the verification report into the branch and commit**

```bash
cd /tmp/lsu-freeze-20261113
cp /home/sdc/lsu-v333-archive/analysis/LSU_Reproducibility_Verification.md docs/lsu/formal-v3.3.3/
cp /home/sdc/lsu-v333-archive/LSU_Archive_SHA256SUMS docs/lsu/formal-v3.3.3/
cp /home/sdc/lsu-v333-archive/analysis/LSU_Final_Preservation_Report.md docs/lsu/formal-v3.3.3/
git add docs/lsu/formal-v3.3.3/LSU_Reproducibility_Verification.md \
        docs/lsu/formal-v3.3.3/LSU_Archive_SHA256SUMS \
        docs/lsu/formal-v3.3.3/LSU_Final_Preservation_Report.md
git diff --stat HEAD~1..HEAD   # must touch docs only, no CHAOS/gem5/src
git commit -m "[LSU][V3.3.3][REPRO] record remote reproduction evidence and archive checksums"
git push origin lsu-formal-v3.3.3-frozen
```
Expected: push succeeds (fast-forward); the last commit is docs-only. Note in the report that reproduction verified the parent commit (added above) and this commit adds only the verification evidence.

- [ ] **Step 4: Tag the final archive HEAD**

Run:
```bash
cd /tmp/lsu-freeze-20261113
git tag -a lsu-v3.3.3-formal-accepted -m "LSU v3.3.3 formal accepted archive

Formal build source commit: e3293856 (C++ tree content)
Final tooling commit: 7067805d
Binary SHA256: 62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd
Config SHA256: 8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225
Campaign: LSU-V333-FINAL-20261112 (120 runs)
Raw archive SHA256: cece176a894edf139209c21fd219d031f4c0ea99a60cc2664addd743ac2df235"
git push origin lsu-v3.3.3-formal-accepted
git ls-remote --tags origin refs/tags/lsu-v3.3.3-formal-accepted
```
Expected: tag pushed and visible. If the tag already exists remotely, stop.

- [ ] **Step 5: Build the approval packet**

Copy the ten mandated files into a staging dir and zip:
```bash
cd /home/sdc/lsu-v333-archive/approval
cp ../analysis/LSU_Final_Preservation_Report.md .
cp /tmp/lsu-freeze-20261113/docs/lsu/formal-v3.3.3/LSU_Formal_Source_Closure_Manifest.csv .
cp /tmp/lsu-freeze-20261113/docs/lsu/formal-v3.3.3/LSU_Formal_Workload_Context_Manifest.csv .
cp /tmp/lsu-freeze-20261113/docs/lsu/formal-v3.3.3/LSU_Formal_Raw_Data_Archive_Manifest.csv .
cp /tmp/lsu-freeze-20261113/docs/lsu/formal-v3.3.3/LSU_GitHub_Frozen_Branch_Report.md .
cp /tmp/lsu-freeze-20261113/docs/lsu/formal-v3.3.3/LSU_Git_Branch_Cleanup_Candidates.csv .
cp /tmp/lsu-freeze-20261113/docs/lsu/formal-v3.3.3/LSU_Server_Cleanup_Candidates.csv .
cp /tmp/lsu-freeze-20261113/docs/lsu/formal-v3.3.3/LSU_Reproducibility_Verification.md .
cp ../LSU_Archive_SHA256SUMS .
cp /tmp/lsu-freeze-20261113/docs/lsu/formal-v3.3.3/LSU_Proposed_Deletion_Plan.md .
zip -9 LSU_Final_Cleanup_Approval_Packet.zip LSU_*.md LSU_*.csv LSU_Archive_SHA256SUMS
sha256sum LSU_Final_Cleanup_Approval_Packet.zip
```
Expected: exactly the ten mandated files; SHA recorded.

- [ ] **Step 6: Remove the temporary freeze worktree (no branch deletion)**

Run:
```bash
cd /home/sdc/gem5-fi-ding
git worktree remove /tmp/lsu-freeze-20261113
git worktree list | grep lsu-freeze || echo 'freeze temp worktree removed'
git branch --list lsu-formal-v3.3.3-frozen
```
Expected: worktree gone; branch remains. Do **not** remove `/home/sdc/lsu-v333-repro-20261113` yet — it is reproduction evidence; list it as a cleanup candidate.

- [ ] **Step 7: Stop and report**

Deliver to the researcher: the packet path + SHA256, the ten statistics, branch/tag push status, reproduction PASS/FAIL per check, and the explicit statement: **no deletion executed; waiting for approval of `LSU_Proposed_Deletion_Plan.md`.**

---

## Self-Review Against the Mandate

- **Preservation before cleanup:** Tasks 1–4 archive and verify; Task 5 is read-only; Task 8 stops before deletion. ✅
- **Formal archive content:** 120 runs, attempts, traces, summaries, oracle, injection records, zero proofs, campaign index, manifest, Excel, SHA256SUMS, version info — verified in Task 4 and indexed in commit 3. ✅
- **Two recoverable copies:** ZIP in worktree + ZIP and extracted tree in `/home/sdc/lsu-v333-archive`; binary original + real byte copy. Off-host copy is an explicit approval item because the repo is public. ✅
- **Freeze branch tracing:** branch at `7067805d`, documented `e3293856` C++ content, no C++ drift, tag at archive HEAD, three identities separated. ✅
- **Independent reproduction:** fresh remote clone, hash checks, dry run, tests, collector/report regeneration. ✅
- **Branch/server cleanup candidates:** Tasks 5 with explicit keep rules and no wildcard deletion. ✅
- **Approval packet:** all ten named files. ✅
- **Do-not list honored:** no force push, no `git add -A`, no semantics changes, no raw traces in git, no 120-run rerun, no new permanent worktree. ✅
