# LQ04 Source Audit — line-number corrections (LSU v3.2.11, task A2)

**Date:** 2026-11-10
**Audit target:** `CHAOS/gem5/src/cpu/o3/lsq_unit.cc` — the v3.2.10 LQ04
implementation source (injector hook, side channel, boundary restore).
**Audited at:** commit `8f32a897` on branch `lsu-platform-v3.2.11`
(worktree `.claude/worktrees/lsu-platform-v3.2.11`), clean tree. The audited
file was last modified by `a6abe75d` "[LSU][MDSPEC][V3.2.10][LQ04] inject at
executeLoad with response probe and boundary restore trace" (2026-11-09) —
i.e. the file is exactly the v3.2.10 post-implementation state and has not
changed since.

**Purpose:** correct the stale source-line references and function-responsibility
descriptions carried by Excel v3.2.5 sheet `4.源码Hook审计` row 4 (LQ04) against
the real v3.2.10 source, and hand Task 7 the exact values to transcribe into the
v3.2.6 workbook. This is the second correction pass on the same row:
`LQ04_Source_Audit_v3.2.10.md` §2 already flagged the Excel ranges as stale at
the pre-implementation baseline (`37692d2b`), but the correction was never
transcribed into the workbook, and the v3.2.10 implementation itself then shifted
the lines again. Both gaps are closed here.

**No fault-definition field is changed by this document** (see §5).

---

## 1. Verification commands (run at HEAD `8f32a897`; outputs quoted verbatim)

### 1.1 Definition name lines

```
$ grep -n "LSQUnit::insertLoad\|LSQUnit::executeLoad\|LSQUnit::lq04Restore\|LSQUnit::commitLoad\|LSQUnit::commitLoads\|LSQUnit::squash" CHAOS/gem5/src/cpu/o3/lsq_unit.cc
395:LSQUnit::insertLoad(const DynInstPtr &load_inst)
720:LSQUnit::executeLoad(const DynInstPtr &inst)
801:    // (LSQUnit::lq04Restore). No pop, no early free/reuse; the returned
928:LSQUnit::lq04Restore(LQEntry& entry, const char* reason)
946:LSQUnit::commitLoad()
976:LSQUnit::commitLoads(InstSeqNum &youngest_inst)
1203:LSQUnit::squash(const InstSeqNum &squashed_num)
```

Line 801 is a comment inside the LQ04 hook (it names `lq04Restore`), not a
definition. The six definitions sit at name lines **395 / 720 / 928 / 946 /
976 / 1203**.

### 1.2 Definition map (neighbor cross-check)

```
$ grep -n "^LSQUnit::" CHAOS/gem5/src/cpu/o3/lsq_unit.cc   (rows 350–1350)
379:LSQUnit::insert(const DynInstPtr &inst)
395:LSQUnit::insertLoad(const DynInstPtr &load_inst)
466:LSQUnit::insertStore(const DynInstPtr& store_inst)
...
720:LSQUnit::executeLoad(const DynInstPtr &inst)
834:LSQUnit::executeStore(const DynInstPtr &store_inst)
928:LSQUnit::lq04Restore(LQEntry& entry, const char* reason)
946:LSQUnit::commitLoad()
976:LSQUnit::commitLoads(InstSeqNum &youngest_inst)
990:LSQUnit::commitStores(InstSeqNum &youngest_inst)
...
1203:LSQUnit::squash(const InstSeqNum &squashed_num)
1341:LSQUnit::getLatestHtmUid() const
```

Every closing brace verified below is immediately followed by one blank line and
the next definition's return-type line, so the boundary map is self-consistent
with this list (no gaps, no overlaps).

### 1.3 Function boundaries (numbered source output)

Representative boundary evidence (all from `awk 'NR>=X && NR<=Y {printf "%d\t%s\n", NR, $0}'`
on the audited file):

```
394	void
395	LSQUnit::insertLoad(const DynInstPtr &load_inst)
396	{
397	    assert(!loadQueue.full());
...
462	    }
463	}
464
465	void
```

```
719	Fault
720	LSQUnit::executeLoad(const DynInstPtr &inst)
721	{
722	    // Execute a specific load.
...
830	    return load_fault;
831	}
832
833	Fault
```

```
796	    // LQ04 (LSU v3.2.10): the injection point, at the end of a successful
...
803	    // untouched. The whole block is inert unless CHAOSLQ04 is mounted.
804	    if (cpu->chaosLQ04 && load_fault == NoFault && inst->isLoad()) {
...
817	                e.corruptLifetime();
...
828	    }
829
830	    return load_fault;
831	}
```

```
927	void
928	LSQUnit::lq04Restore(LQEntry& entry, const char* reason)
929	{
930	    const DynInstPtr& inst = entry.instruction();
...
942	    entry.restoreLifetime();
943	}
944
945	void
```

```
945	void
946	LSQUnit::commitLoad()
947	{
948	    if (loadQueue.front().lq04Corrupt())
949	        lq04Restore(loadQueue.front(), "commit");
950	    assert(loadQueue.front().valid());
...
972	    stats.lqAvgOccupancy = queueOccupancy(loadQueue);
973	}
974
975	void
```

```
975	void
976	LSQUnit::commitLoads(InstSeqNum &youngest_inst)
977	{
978	    // LQ04: the head may still be visibly invalid when the fault window has
...
986	    }
987	}
988
989	void
```

```
1202	void
1203	LSQUnit::squash(const InstSeqNum &squashed_num)
1204	{
1205	    DPRINTF(LSQUnit, "Squashing until [sn:%lli]!" ...
...
1237	        if (loadQueue.back().lq04Corrupt())
1238	            lq04Restore(loadQueue.back(), "squash");
...
1250	        loadQueue.back().clear();
1252	        loadQueue.pop_back();
1253	        ++stats.squashedLoads;
1254	    }            <- closes the loadQueue while loop (NOT the function)
1256	    stats.lqAvgOccupancy = queueOccupancy(loadQueue);
...                <- HTM in-flight-uid fixup, :1258-1294
...                <- storeQueue squash while loop, :1296-1336
1337	    stats.sqAvgOccupancy = queueOccupancy(storeQueue);
1338	}
1339
1340	uint64_t
```

### 1.4 Verified boundary table

| function | return-type line | name line | `{` | body | closing `}` | span (return line → `}`) |
|---|---|---|---|---|---|---|
| `insertLoad` | 394 (`void`) | 395 | 396 | 397-462 | **463** | 394-463 |
| `executeLoad` | 719 (`Fault`) | 720 | 721 | 722-830 | **831** | 719-831 |
| LQ04 injection hook | — (inside `executeLoad`) | — | — | comment 796-803; injected block 804-828 | — | 796-828 |
| `lq04Restore` | 927 (`void`) | 928 | 929 | 930-942 | **943** | 927-943 |
| `commitLoad` | 945 (`void`) | 946 | 947 | 948-972 | **973** | 945-973 |
| `commitLoads` | 975 (`void`) | 976 | 977 | 978-986 | **987** | 975-987 |
| `squash` | 1202 (`void`) | 1203 | 1204 | 1205-1337 | **1338** | 1202-1338 |

---

## 2. Correction table (old Excel v3.2.5 → verified v3.2.10)

"Old Excel v3.2.5" quotes cell `G4` of sheet `4.源码Hook审计` verbatim (see §6).
"Verified v3.2.10" is the span from the return-type line through the closing
brace at HEAD `8f32a897` (§1.4). The "task-6 brief" column reconciles the ranges
the v3.2.11 task-6 brief expressed (name-line based) against this evidence.

| function | old Excel v3.2.5 (`G4`) | verified v3.2.10 (this HEAD) | task-6 brief expressed | evidence (command → line) | responsibility |
|---|---|---|---|---|---|
| `insertLoad` | `353-414` | **394-463** (name :395; body :397-462; `}` :463) | 395-464 — the end counts the blank separator :464; the closing brace is :463 | `grep -n` → `395:LSQUnit::insertLoad(...)`; `awk 'NR>=462&&NR<=465'` → `463 }`, `464` blank, `465 void` | Allocates the LQ entry: `advance_tail()` :405, `back().set(load_inst)` :410, assigns `lqEntryGeneration` :411 and `lqIdx` :412, emits the `alloc`/`reuse` lifecycle record :413-419. |
| `executeLoad` | *(absent — no line range in `G4`)* | **719-831** (name :720; body :722-830; `}` :831) | 720-831 — exact match | `grep -n` → `720:LSQUnit::executeLoad(...)`; `sed -n '830,831p'` → `return load_fault;` / `}` | Issues the memory request (`initiateAcc` :736), handles predication (:738-745, :763-778) and partial-fault/split retry (:750-759), returns the memory-order-violation fault for replay (:789-791), and **hosts the LQ04 injection hook at the function tail** (:796-828). |
| LQ04 injection hook | *(absent)* | **796-828** (comment :796-803; injected block :804-828), inside `executeLoad` | 796-828 — exact match | `sed -n '796,804p'`; `grep -n corruptLifetime` → `:817` | After a clean `executeLoad` round, the ordinal-selected target moves `valid`/`request` into the `LQEntry` side channel (`e.corruptLifetime()` :817); inert unless `CHAOSLQ04` is mounted. |
| `lq04Restore` | *(absent — function did not exist pre-implementation)* | **927-943** (name :928; body :930-942; `}` :943) | 928-943 — exact match | `grep -n` → `928:LSQUnit::lq04Restore(...)`; `sed -n '942,943p'` → `entry.restoreLifetime();` / `}` | Restores the side-channel-stashed request and valid bit at the commit/squash boundary (`entry.restoreLifetime()` :942) and emits the `restore` record (:934-941); no-op for never-corrupted entries. |
| `commitLoad` | `775-798` | **945-973** (name :946; body :948-972; `}` :973) | 946-974 — the end counts the blank separator :974; the closing brace is :973 | `grep -n` → `946:LSQUnit::commitLoad()`; `sed -n '948,950p'` → restore-before-assert | Restore-before-assert: `lq04Restore(front(), "commit")` :948-949 precedes `assert(front().valid())` :950; then frees/pops (`clear()` :969, `pop_front()` :970) after the `free`/`commit` lifecycle record :966-968. |
| `commitLoads` | *(absent)* | **975-987** (name :976; body :978-986; `}` :987) | 976-987 — exact match | `grep -n` → `976:LSQUnit::commitLoads(...)`; `sed -n '980,981p'` | Accepts a corrupt head before the loop: `assert(size()==0 \|\| front().valid() \|\| front().lq04Corrupt())` :980-981; then the while loop :983-986 calls `commitLoad()` :985. |
| `squash` | `986-1020` | **1202-1338** (name :1203; body :1205-1337; `}` :1338); LQ04 load-side window :1205-1254 | 1203-1253 — **truncated**: :1253 is `++stats.squashedLoads;`, the last statement of the load-side while loop (which closes at :1254); the function continues through the HTM-uid fixup (:1256-1294) and the store-side squash loop (:1296-1336), closing at :1338 | `grep -n` → `1203:LSQUnit::squash(...)`; `sed -n '1237,1238p'`; `awk 'NR>=1337&&NR<=1341'` → `1338 }`, `1340 uint64_t`, `1341 LSQUnit::getLatestHtmUid()` | Restores before clear/pop on the load side: `lq04Restore(back(), "squash")` :1237-1238 precedes `clear()` :1250 and `pop_back()` :1252; the loop never checks `valid()`. |

**Reconciliation with the task-6 brief.** Four of the brief's expressed ranges
match the verified evidence exactly (`executeLoad` 720-831, hook 796-828,
`lq04Restore` 928-943, `commitLoads` 976-987). Two include the blank separator
line after the closing brace instead of stopping at the brace (`insertLoad`
395-464 vs `}` :463; `commitLoad` 946-974 vs `}` :973) — a one-line
over-count. One is truncated (`squash` 1203-1253 vs `}` :1338). The
authoritative values for Task 7 to transcribe are the grep-verified spans in the
"verified v3.2.10" column; the brief's own parenthetical boundary data
(void :394 / name :395 / body 397-463 for `insertLoad`, etc.) is confirmed by
§1.3 except for the `squash` body end (:1253 is not the function end).

---

## 3. Per-function evidence and responsibilities

### 3.1 `LSQUnit::insertLoad` — `lsq_unit.cc:394-463`

Signature (`sed -n '394,396p'`):

```cpp
void
LSQUnit::insertLoad(const DynInstPtr &load_inst)
{
```

Responsibility: allocate the LQ entry for a dispatched load. Verified key
lines: `loadQueue.advance_tail()` **:405** (grows the circular queue);
`loadQueue.back().set(load_inst)` **:410** (writes `_valid = true`);
`load_inst->lqEntryGeneration = ++lqEntryGeneration;` **:411** (the generation
counter is an `LSQUnit` member, the value is stored on the DynInst — see
`LQ04_Source_Audit_v3.2.10.md` §1.2); `load_inst->lqIdx = loadQueue.tail();`
**:412**; and the pre-existing CHAOS lifecycle hook
`noteLQLifecycle(..., reused ? "reuse" : "alloc", "insert")` **:413-419**
(including the `lq_last_alloc` bookkeeping that classifies alloc vs reuse).
The LQ04 fault never touches this function: it does not pop, `set()` or free
the slot, so `assert(!loadQueue.back().valid())` (:409) stays satisfied.

### 3.2 `LSQUnit::executeLoad` — `lsq_unit.cc:719-831`

Signature (`sed -n '719,721p'`):

```cpp
Fault
LSQUnit::executeLoad(const DynInstPtr &inst)
{
```

Responsibility: execute one load issue round. Verified key lines:
`++inst->executionAttemptId;` **:723**; `load_fault = inst->initiateAcc();`
**:736** (issues the request — the `LSQ::pushRequest` chain installs it on the
entry via `LSQRequest::install`); predication handling
`if (load_fault == NoFault && !inst->readMemAccPredicate())` **:738-745** and
the fault/predicated-false send-to-commit path
`if (load_fault != NoFault || !inst->readPredicate())` **:763-778**;
partial-fault split retry **:750-759**; memory-order violation check
`Fault viol_fault = checkViolations(it, inst);` **:789** with
`return viol_fault;` **:790-791** (a violation returns immediately — the load
is replayed; a clean check falls through to the injection point). The LQ04
injection hook is hosted at the function tail, **:796-828**, immediately before
`return load_fault;` **:830**.

### 3.3 LQ04 injection hook — `lsq_unit.cc:796-828` (inside `executeLoad`)

Comment block **:796-803** (quoted in §1.3) and injected block **:804-828**:

```cpp
    if (cpu->chaosLQ04 && load_fault == NoFault && inst->isLoad()) {
        LQEntry &e = loadQueue[inst->lqIdx];
        if (chaos_lq04::isEligible(e.valid(), e.hasRequest(),
                                   inst->isSquashed(),
                                   inst->isExecuted())) {
            ...
                e.corruptLifetime();        // :817
            ...
        }
    }                                       // :828
```

Responsibility: the ordinal-selected target entry moves `valid`/`request` into
the `LQEntry` side channel (visibly `valid=0`, `request=nullptr`) after a
successful `executeLoad` round, until its commit/squash boundary. No pop, no
early free/reuse; the returned fault, the response binding (`pkt->senderState`)
and the data are untouched. The block is inert unless `CHAOSLQ04` is mounted.

### 3.4 `LSQUnit::lq04Restore` — `lsq_unit.cc:927-943`

Signature (`sed -n '927,929p'`):

```cpp
void
LSQUnit::lq04Restore(LQEntry& entry, const char* reason)
{
```

Responsibility: restore a corrupted entry's lifetime at its commit/squash
boundary. Preceded by the header comment **:923-926** ("The stashed request
moves back to `_request` and the entry becomes valid again, so the normal
`clear()`/`freeLSQEntry()` path runs unchanged. No-op for entries that were
never corrupted."). Body: `noteRestore` **:934-936** and
`noteLQLifecycle(..., "restore", reason)` **:937-941** emit the restore trace;
`entry.restoreLifetime();` **:942** moves the stashed request/valid back into
the entry. This function did not exist in the pre-implementation source, so the
v3.2.5 row has no old value for it.

### 3.5 `LSQUnit::commitLoad` — `lsq_unit.cc:945-973`

Signature (`sed -n '945,947p'`):

```cpp
void
LSQUnit::commitLoad()
{
```

Responsibility: retire the head load. The LQ04-relevant ordering is
restore-before-assert (**:948-950**):

```cpp
    if (loadQueue.front().lq04Corrupt())
        lq04Restore(loadQueue.front(), "commit");
    assert(loadQueue.front().valid());
```

then the free/pop: `noteLQLifecycle(..., "free", "commit")` **:966-968**,
`loadQueue.front().clear()` **:969** (frees the request via `freeLSQEntry()`
and writes `_valid = false`), `loadQueue.pop_front()` **:970**.

### 3.6 `LSQUnit::commitLoads` — `lsq_unit.cc:975-987`

Signature (`sed -n '975,977p'`):

```cpp
void
LSQUnit::commitLoads(InstSeqNum &youngest_inst)
{
```

Responsibility: commit head loads up to `youngest_inst`. Before the loop it
accepts a still-corrupt head (**:978-981**):

```cpp
    // LQ04: the head may still be visibly invalid when the fault window has
    // not closed yet; commitLoad() restores it before its own valid() check.
    assert(loadQueue.size() == 0 || loadQueue.front().valid()
            || loadQueue.front().lq04Corrupt());
```

The loop itself (**:983-986**) calls `commitLoad()` (**:985**), which restores
before its own `valid()` assert (§3.5).

### 3.7 `LSQUnit::squash` — `lsq_unit.cc:1202-1338`

Signature (`sed -n '1202,1204p'`):

```cpp
void
LSQUnit::squash(const InstSeqNum &squashed_num)
{
```

Responsibility: squashes younger loads and stores on a misprediction/flush.
The LQ04-relevant load side is the first while loop (**:1209-1254**), which
tests only `seqNum > squashed_num` and **never checks `valid()`**; per entry it
restores before clear/pop (**:1237-1238**, **:1250**, **:1252**):

```cpp
        if (loadQueue.back().lq04Corrupt())
            lq04Restore(loadQueue.back(), "squash");
        ...
        loadQueue.back().clear();
        ...
        loadQueue.pop_back();
        ++stats.squashedLoads;              // :1253 — loop tail, NOT function end
    }                                       // :1254 — closes the load while loop
```

The function then continues past :1254: `lqAvgOccupancy` update **:1256**, the
HTM in-flight-uid fixup **:1258-1294**, and the store-side squash while loop
**:1296-1336** (store `clear()` :1332, `pop_back()` :1334,
`++stats.squashedStores` :1335), closing with
`stats.sqAvgOccupancy = queueOccupancy(storeQueue);` **:1337** and the function
brace **:1338**. Any audit range that ends at :1253 or :1254 truncates the
function; the LQ04-relevant window within it is :1205-1254.

---

## 4. Frozen fault-definition fields are unchanged

This document corrects **only** source-line references and function-responsibility
descriptions. The frozen fault-definition fields are unchanged, verbatim, both in
Excel v3.2.5 sheet 4 row 4 and in `LQ04_Definition_Freeze_v3.2.10.md`
(FaultModelID `LQ04`, FaultConfigID `LQ04-CFG01`, decisions D1-D6 frozen
verbatim):

- **TargetField** — `H4`: `LQEntry::_valid / _request` (types `I4`: bool;
  `LSQRequest*`; `CircularQueue<LQEntry>`);
- **NormalValue** — `K4`/`AB4`: `valid=1，request在途`;
- **FaultValue** — `L4`/`AC4`: `executeLoad后清valid/request；不pop、不复用`;
- **InjectionTiming** — `M4`: `commitLoad/squash/释放路径` (freeze doc §
  header: `executeLoad后、响应到达前`);
- **Duration** — `N4`: `F0：单次；错误entry状态保留到重用/覆盖`.

No re-adjudication of the fault definition, the option ruling
(`AG4: ACCEPTED_BY_RESEARCHER_2026-11-08`, option A "仅提前失效"), or the
D1-D6 decisions occurs in this round.

---

## 5. Stale v3.2.5 values in Excel sheet 4 row 4 (quoted exactly)

Read with `openpyxl` (`data_only=True`) from
`docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.5.xlsx`,
sheet `4.源码Hook审计`, row 4 (ModelID `LQ04`, SubTaskID `LQ04-F0-W2-S01`):

- `G4` (FunctionName), verbatim:
  `LSQUnit::insertLoad (353-414); commitLoad (775-798); squash (986-1020); clear/pop_front`
- Stale ranges: **insertLoad 353-414**, **commitLoad 775-798**, **squash
  986-1020**, plus the unnumbered `clear/pop_front` tail. **No `executeLoad`
  line range exists anywhere in the row** — `executeLoad` appears only as
  unnumbered prose (`L4`/`AC4` `executeLoad后清valid/request；不pop、不复用`,
  `M4`, `S4` `implemented: CHAOSLQ04 SimObject + LQEntry side channel +
  executeLoad hook`), and **`lq04Restore` and `commitLoads` are entirely
  absent** (they postdate the row's original source snapshot).
- `W4` = `VERIFIED`, `X4` = `IMPLEMENTED_VERIFIED` — the row claims audit
  verification while carrying pre-implementation line numbers; that is the gap
  this document closes for Task 7.

**The stale values were already stale at publication.** The v3.2.5 workbook was
published at `6b52ab6e` ("[V3.2.10][EXCEL] publish v3.2.5 with LQ04 pilot
status", 2026-11-09) — *after* the implementation commits `6681edcf`
(LQEntry side channel + boundary restore) and `a6abe75d` (executeLoad inject
hook). Verified:

```
$ git show 6b52ab6e:CHAOS/gem5/src/cpu/o3/lsq_unit.cc | grep -n "LSQUnit::insertLoad\|LSQUnit::commitLoad()\|LSQUnit::squash"
395:LSQUnit::insertLoad(const DynInstPtr &load_inst)
946:LSQUnit::commitLoad()
1203:LSQUnit::squash(const InstSeqNum &squashed_num)
```

i.e. at workbook publication the source already matched today's positions
(:395/:946/:1203), and the `G4` ranges were carried over unrefreshed from an
earlier snapshot. Drift chain (all verified):

| function | Excel v3.2.5 `G4` | v3.2.10 audit @`37692d2b` (pre-implementation) | this HEAD `8f32a897` (post-implementation) |
|---|---|---|---|
| `insertLoad` | 353-414 | 371-440 (name :372) | 394-463 (name :395) |
| `executeLoad` | *(absent)* | 696-767 (name :697) | 719-831 (name :720) |
| LQ04 hook | *(absent)* | *(did not exist)* | 796-828 |
| `lq04Restore` | *(absent)* | *(did not exist)* | 927-943 (name :928) |
| `commitLoad` | 775-798 | 859-885 | 945-973 (name :946) |
| `commitLoads` | *(absent)* | 887-896 | 975-987 (name :976) |
| `squash` | 986-1020 | 1111-1161 | 1202-1338 (name :1203; load-side window 1205-1254) |

The `353-414`-era numbers predate the v3.2.9 baseline as well
(`git show 6681edcf^:CHAOS/gem5/src/cpu/o3/lsq_unit.cc` already has
`insertLoad` at :372) — they date from the original
`LSU_Source_Code_Evidence_v3.md` audit era cited by `AH4`, as already surmised
in `LQ04_Source_Audit_v3.2.10.md` §2.

---

## 6. Values Task 7 must transcribe into the v3.2.6 workbook (sheet 4, LQ04 row)

`FunctionName` (`G4`) replacement, evidence-backed:

```
LSQUnit::insertLoad (394-463); executeLoad (719-831, LQ04 hook 796-828);
lq04Restore (927-943); commitLoad (945-973); commitLoads (975-987);
squash (1202-1338, load-side window 1205-1254)
```

with the name lines :395/:720/:928/:946/:976/:1203 per §1.1, and the
per-function responsibilities of §2/§3. All other columns of the row — including
the frozen fields of §4 — are unchanged.
