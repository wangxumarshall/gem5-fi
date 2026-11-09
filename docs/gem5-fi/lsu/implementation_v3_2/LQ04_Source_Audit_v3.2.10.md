# LQ04 Source Audit — v3.2.10 (LSQUnit / LSQRequest lifetime paths)

**Date:** 2026-11-09
**Audit target:** `CHAOS/gem5/src/cpu/o3/lsq_unit.hh`, `CHAOS/gem5/src/cpu/o3/lsq_unit.cc`,
`CHAOS/gem5/src/cpu/o3/lsq.hh`, `CHAOS/gem5/src/cpu/o3/lsq.cc`
**Audited at:** commit `37692d2beffcb73fc9303ad9de4c6bb341d5de71` (branch
`lsu-platform-v3.2.10`; byte-identical to the authoritative v3.2.9 baseline
worktree — see `LSU_v3.2.10_Baseline_Verification.md` §4)
**Purpose:** verify, with real file:line evidence, what the literal LQ04 fault
(`LQEntry::_valid := 0` + `LQEntry::_request := nullptr` after `executeLoad`,
no pop, no free, no reuse) actually does in the vendored gem5 O3 LSQ, and answer
audit questions A–D before any implementation commit.

Every line number below was re-read in the audited tree on 2026-11-09. Where
this audit corrects the design spec §2 or the Excel v3.2.4 hook-audit row, the
correction is marked **[CORRECTION]** and the verified fact is given.

---

## 1. Structure map (verified file:line)

### 1.1 The LQ entry (`lsq_unit.hh`)

- `LSQUnit::LSQEntry` (nested class): **`lsq_unit.hh:95-147`**. Fields:
  `_inst` (`:99`), `_request` (`:101`, default `nullptr`), `_size` (`:103`),
  `_valid` (`:105`, default `false`).
- `using LQEntry = LSQEntry;` **`:197`**; `using LoadQueue = CircularQueue<LQEntry>;`
  **`:208`**. `SQEntry` derives from `LSQEntry` (`:149`) — the shared base means
  the LQ04 injector must target `loadQueue` entries only, never `storeQueue`.
- `_valid` **write sites**: `set()` writes `_valid = true` at **`:133`**;
  `clear()` writes `_valid = false` at **`:124`**; default member initializer
  `:105`. There are no other operational writes.
- `_request` **write sites** (all five verified):
  - destructor `~LSQEntry()` sets `_request = nullptr` at **`:112`** (after
    `freeLSQEntry()` at `:111` when non-null; body `:108-114`);
  - `clear()` sets `_request = nullptr` at **`:123`** (after calling
    `_request->freeLSQEntry()` at `:120-122` when non-null);
  - `setRequest()` at **`:138`**;
  - `LSQ::LSQRequest::install()` — **`lsq.cc:1115-1125`**, load branch
    `_port.loadQueue[_inst->lqIdx].setRequest(this)` at `:1119`;
  - `LSQUnit::read()` — `load_entry.setRequest(request)` at
    **`lsq_unit.cc:1554`** (function `:1548` ff.).
- `clear()` therefore (a) frees the request via `freeLSQEntry()` iff
  `_request != nullptr` (`:120-122`) and (b) invalidates the entry (`:124`).

### 1.2 Allocation (`lsq_unit.cc`)

- `LSQUnit::insertLoad`: **`lsq_unit.cc:371-440`** (name line `:372`).
  `assert(!loadQueue.back().valid())` at **`:386`**; `loadQueue.back().set(load_inst)`
  at `:387`; `loadQueue.advance_tail()` at `:382` grows the circular queue.
- Generation: `load_inst->lqEntryGeneration = ++lqEntryGeneration;` at **`:388`**.
  **[CORRECTION to spec §2 wording]** the generation is **not** "stored on both
  entry and DynInst": the counter `lqEntryGeneration` is an `LSQUnit` member
  (**`lsq_unit.hh:464`**) and the value is stored **on the DynInst** (field
  `dyn_inst.hh:356`). The `LSQEntry` itself has no generation field; entry-reuse
  disambiguation is DynInst-side (`lqIdx` `dyn_inst.hh:352` + `lqEntryGeneration`).
- Existing CHAOS trace hook: `noteLQLifecycle(..., "alloc"/"reuse", "insert")`
  at **`:390-396`** (emits the `lq_lifecycle action=alloc` records the v3.2.10
  workload acceptance criteria count).

### 1.3 Execute / send (`lsq_unit.cc`, `lsq.cc`)

- `LSQUnit::executeLoad`: **`lsq_unit.cc:696-767`** (name line `:697`);
  `load_fault = inst->initiateAcc();` at **`:713`**.
- The request is built and sent by the `LSQ::pushRequest` chain:
  `LSQ::pushRequest` **`lsq.cc:765`** (declared `lsq.hh:902`) constructs the
  `LSQRequest` (writes `_inst->savedRequest` at `lsq.cc:989/1064/1622`);
  `LSQ::read` **`lsq.cc:1682-1689`** dispatches to `LSQUnit::read`
  (**`lsq_unit.cc:1548`**), which installs the request on the entry
  (`setRequest` `:1554`) and sends it to the cache.

### 1.4 Response path (`lsq_unit.cc`, `lsq.cc`)

Chain (each hop verified):

1. `LSQUnit::recvTimingResp` **`lsq_unit.cc:97-108`** — recovers the request
   from `pkt->senderState` at **`:100`**; skips if `request->isReleased()`.
2. `LSQ::recvTimingResp` starts at **`lsq.cc:448`** (name line `:449`) —
   recovers the request from `pkt->senderState` at `:461` and dispatches by
   `request->contextId()` at `:464` (the function continues past `:464` with
   invalidate handling, which is not on this path).
3. `LSQ::SingleDataRequest::recvTimingResp` **`lsq.cc:1247-1256`** (name line
   `:1248`) — calls `_port.completeDataAccess(pkt)` at **`:1253`**
   (`SplitDataRequest::recvTimingResp` follows at `:1258` ff.).
4. `LSQUnit::completeDataAccess` **`lsq_unit.cc:110-232`** — recovers the
   request from `pkt->senderState` at **`:113`** and the instruction from
   `request->instruction()` at `:114`.

**The response path never reads the LQEntry.** The whole of
`completeDataAccess` (`:110-232`) was read: it operates on `request` and `inst`
only (writeback at `:212`, store completion at `:219-229`); no
`loadQueue[...]` access exists anywhere in the chain
`LSQUnit::recvTimingResp → LSQ::recvTimingResp → LSQRequest::recvTimingResp →
completeDataAccess`.

### 1.5 Commit (`lsq_unit.cc`)

- `LSQUnit::commitLoad`: **`:859-885`** — `assert(loadQueue.front().valid())`
  at **`:862`**; existing `noteLQLifecycle(..., "free", "commit")` at
  `:878-880`; `loadQueue.front().clear()` at `:881`; `loadQueue.pop_front()`
  at `:882`.
- `LSQUnit::commitLoads`: **`:887-896`** — pre-loop invariant
  `assert(loadQueue.size() == 0 || loadQueue.front().valid())` at **`:890`**.

### 1.6 Squash (`lsq_unit.cc`)

- `LSQUnit::squash`: **`:1111-1161`** — the while loop (`:1118-1119`) tests only
  `loadQueue.back().instruction()->seqNum > squashed_num`; it **never checks
  `valid()`**. Per entry: `setSquashed()` `:1156`, `clear()` `:1157`,
  `pop_back()` `:1159`; existing `noteSquash`/`noteLQLifecycle(..., "free",
  "squash")` at `:1146-1153`.

### 1.7 Drain sanity (`lsq_unit.cc`)

- `LSQUnit::drainSanityCheck`: **`:339-347`** —
  `assert(!loadQueue[i].valid())` for every slot at **`:343`**.

### 1.8 Readers of `LQEntry::_request` and their guards (answer B evidence)

All `request()`/`hasRequest()` readers in `lsq_unit.cc` were enumerated
(`grep -n -E "request\(\)|hasRequest\(\)"`):

| Reader site | Guard | Verdict for `_request = nullptr` |
|---|---|---|
| `checkSnoop` `:526`, `:540` | `request &&` `:529`; `\|\| !request` `:541` (function `:500-582`) | guarded, skipped |
| `checkViolations` (MD04 block) `:656`, `:660` | `loadIt->request() &&` inline `:656`, `?:` `:660` (function `:584-691`) | guarded, skipped |
| `startStaleTranslationFlush` `:1478-1483` | `entry.valid() && entry.hasRequest()` `:1478`, `:1482` (function `:1472-1485`) | guarded, skipped |
| `checkStaleTranslations` `:1492-1498` | `entry.valid() && entry.hasRequest()` `:1492`, `:1497` (function `:1487-1503`) | guarded, skipped |
| `:933-934`, `:975`, `:979`, `:1460`, `:1636-1637`, `:1662` | store-queue paths (`storeWBIt`, `store_it`) | not LQ entries — unaffected by an LQ fault |
| `executeLoad` `:750`, `executeStore` `:807` | `inst->hasRequest()` — `DynInst::savedRequest`-based, not the entry | unaffected |

### 1.9 Request ownership (`lsq.hh`, `dyn_inst.hh`, `lsq.cc`)

- `LSQ::LSQRequest` is self-managed: **`lsq.hh:539-588`** — `freeLSQEntry()`
  `:538-542` (`release(Flag::LSQEntryFreed)`), `discard()` `:547-551`
  (`release(Flag::Discarded)`). `delete this` sites: `packetReplied()` `:553-560`
  (requires `_numOutstandingPackets == 0 && isReleased()`), `writebackDone()`
  `:569-577`, `squashTranslation()` `:579-588`. So the request is destroyed only
  after release (`freeLSQEntry()`/`discard()`) **and** zero outstanding packets.
- `DynInst::savedRequest` is a raw back-pointer: **`dyn_inst.hh:370`**
  (`LSQ::LSQRequest *savedRequest;`). Written `lsq.cc:989/1064/1622`, cleared
  `lsq.cc:1169`, read `lsq.cc:816`.

---

## 2. Pre-existing CHAOS state around the audit target

- **No executable LQ04 hook exists.** The only "L04"-labeled code in the response
  path is the comment + observation call at `lsq.cc:451-455`
  ("LSU W5 L04: response-pairing corruption … redirect the response to the WRONG
  LSQ unit"): the actual statement is `chaosLsuF6Observe(ChaOSLsuEvent::CasSuccess);`
  — an F6 event-source observation/counter (`chaos_lsu_trigger.hh:68-74`),
  not a fault injection. This matches Excel v3.2.4 sheet 4 row 4 (`T4` "无",
  `X4` "NEEDS_HOOK").
- **The LSU-track trigger already supports ordinal selection.**
  `chaos_lsu_trigger.hh` implements the event-normalized F0–F6 tiers
  (`ChaOSLsuTier` `:44`; `ChaOSLsuTrigger` `:89-237`). The F0 arm honors
  `event_ordinal` (`next_fire = warmup_events + event_ordinal`, `:167-181`), and
  `onF6Event()` `:210-221` honors it for F6. D4's ordinal semantics can be
  built on this trigger family.
- **Existing LQ lifecycle trace points** (reused by v3.2.10, not duplicated):
  `insertLoad` alloc/reuse `:390-396`, `commitLoad` free/commit `:878-880`,
  `squash` free/squash `:1146-1153`.
- **Adjacent injector hooks** (must not be disturbed): LP01 post-check in
  `completeDataAccess` `:185-203`, `noteMemResponse` `:205-210`,
  `noteChainWriteback`/`noteL1DForwardWriteback` `:213-218`; L03
  violation-view corruption in `checkViolations` `:607-616`; MD04
  violation-suppression `:647-667`.
- **[CORRECTION to Excel v3.2.4 sheet 4 row 4 `G4`]** the row cites
  "LSQUnit::insertLoad (353-414); commitLoad (775-798); squash (986-1020)" —
  these line ranges are stale relative to the audited tree (verified:
  `insertLoad` `:371-440`, `commitLoad` `:859-885`, `squash` `:1111-1161`).
  The v3.2.5 Excel (Task 12) must carry the corrected ranges; the stale ranges
  presumably date from the earlier `LSU_Source_Code_Evidence_v3.md` audit.

---

## 3. Audit answers A–D

**A. Clearing `_valid` (to 0), leaving the entry in place.**
The in-flight response still finds its request through `pkt->senderState`
(`lsq_unit.cc:100`, `:113`; `lsq.cc:461`); it is not dropped, not replayed, and
not mis-associated — the load completes and writes back normally
(`completeDataAccess` `:110-232`). The fault becomes visible only at the
lifetime boundary: `commitLoad`'s `assert(loadQueue.front().valid())` (`:862`,
reached via `commitLoads` `:890-894`) or `drainSanityCheck`'s
`assert(!loadQueue[i].valid())` (`:343`) fire and abort gem5 — an unrecoverable
simulator state, not an architectural effect. If the entry is squashed first,
`squash()` (`:1111-1161`) never checks `valid()`, so it completes normally and
`clear()`/`pop_back()` (`:1157-1159`) remove the entry.

**B. Clearing `_request` (to nullptr), leaving the entry in place.**
No dangling pointer and no use-after-free: every LQ-side reader guards
(§1.8: `checkSnoop` `:529/:541`, `checkViolations` `:656/:660`,
`startStaleTranslationFlush`/`checkStaleTranslations` `:1478/:1482/:1492/:1497`
— the latter two also require `valid()`, which the fault also clears). But the
entry is the only owner that hands the request to `freeLSQEntry()` at
commit/squash (`clear()` `:120-122`, destructor `:110-112`): nulling `_request`
without a side channel leaks one `LSQRequest` (it can never be released, so its
self-delete at `lsq.hh:559/:575/:586` never fires) and skips
stale-translation handling for that entry. This is exactly why D2 requires the
opaque side channel with an exact boundary restore.

**C. Not popping / not reusing the slot.**
The circular-queue size is unchanged, so occupancy, head/tail and back-pressure
accounting are unchanged; `insertLoad` cannot touch the slot until
`pop_front` (`:882`), and its `assert(!loadQueue.back().valid())` (`:386`)
stays satisfied because the fault does not pop or `set()` the slot. The only
unrecoverable part of the literal definition is the commit-time `valid()`
invariant of answer A. Note `SQEntry` shares the `LSQEntry` base (`:149`): the
fault must be scoped to `loadQueue` entries only.

**D. Observable propagation under the literal definition.**
There is no response loss, no wrong response binding, no fault-induced replay
and no data corruption: the response is bound by `senderState` and delivers the
correct payload to the correct instruction. The literal fault's only effects
are (i) the commit-time assert abort (an unrecoverable simulator state), or
(ii) with the invariant handled per D2, a trace-visible invalid-entry interval
plus the load's normal, correct writeback. This is an honest **negative**
result for the research question (the Excel's hypothesized
"错误响应/丢失/错配→Replay/Commit异常或SDC" does not occur under the literal
field fault); it must be reported as such and must not be dressed up as SDC.

---

## 4. Gate verdict

**IMPLEMENTABLE_WITH_CONDITIONS.**

- No use-after-free and no dangling request (answers A/B/C) — the literal field
  fault is memory-safe in the audited tree.
- Condition 1 (commit integrity): the literal `valid=0` violates the commit
  invariant (`lsq_unit.cc:862`, `:890`, `:343`); D2's side-channel restore at
  the commit/squash boundary is mandatory, and only the `commitLoads()` pre-loop
  check (`:890`) and `drainSanityCheck()` (`:343`) may accept the explicitly
  corrupted entry — `commitLoad()` restores before its own
  `assert(front().valid())`.
- Condition 2 (honesty): the literal fault does not produce the hypothesized
  response loss/SDC (answer D); expected terminal is `MASKED` with the
  sender-state association recorded as positive evidence (D1). No manufactured
  SDC.
- Condition 3 (no leak): `_request` must be restorable so the normal `clear()`
  frees it (D2); a nulled-without-restore implementation leaks one `LSQRequest`
  per injection (answer B).

The binding decisions D1–D6 are frozen verbatim in
`LQ04_Definition_Freeze_v3.2.10.md`.
