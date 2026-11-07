# LSU v3.2.5 — LP01 Load-Response Fault Injection and End-to-End Propagation Trace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give LP01 (`Load 返回数据错误`) the same auditable fault-propagation capability DA04 has: a model-exact byte-0 bit-3 payload fault, a dedicated injection/response/writeback trace chain with before/after hashes, five real W5 pilots, and the nine v3.2.4 DA04 trace/document corrections — without running any of the 60 formal samples.

**Architecture:** Keep the existing `CHAOSL1DForward` post-check hook in `LSQUnit::completeDataAccess` but make the trace truthful in three layers: (1) the injector copies the pre-fault payload, flips **only byte 0**, and reports mask/size/eligible-ordinal; (2) `CHAOSPropagation` gets `noteL1DForwardInjection` (pre/post payload hashes), is called for `noteMemResponse` **after** corruption so the response records delivered data, and gets `noteL1DForwardWriteback` which reads the **actual PRF value after `completeAcc`** and taints consumers from that value hash; (3) the Python converter/completeness/validator emit LP01 profiles and enforce hash continuity along injection→response→writeback→consumer edges. DA04's store chain is corrected in the same tracer: load `mem_req` nodes carry the real request tick, and causal attribution is decided at the load's **request** time, not its response time.

**Tech Stack:** gem5 v25.1.0.1 (vendored, C++17), SCons 4.5.2, Python 3.11, gzip-CSV → JSONL trace tooling, pytest.

**Spec:** This plan implements the user work order “LSU v3.2.5：LP01故障注入与端到端传播追踪实现” (2026-11-08) plus the frozen LP01 rows of `docs/gem5-fi/lsu/implementation_v3_2/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.1.xlsx`:
- Sheet 3 row 7 / Sheet 4 row 7 / Sheet 5 rows 27–31: `LP01-F0-W5-S01`, `RunID=LP01-F0-W5`, target field `Packet::data[0]`, bit `byte0 bit3`, fault value `data[0] ^= 0x08（严格按size逐字节）`, recommended option A, Workload W5 `load_response`.
- Sheet 5 seeds: R01 `1349924126`, R02 `2648660520`, R03 `2021175746`, R04 `3894776903`, R05 `1604604537`; EventOrdinal 1–5; oracle `99c106541150be0e`.

## Global Constraints

- Work in worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2` (the v3.2.4 tree, HEAD `d4b8276e`), on a new branch `lsu-platform-v3.2.5`. Do **not** work in the `r6-s-w1-continuation-20261101` tree.
- Keep 12 fault models, 60 SampleRunIDs, and every Excel RunID/SubTaskID/Seed unchanged.
- Do not change DA04's `0xF → 0xE` definition.
- Do not overwrite any v3.2.4 pilot directory or `LSU_v3.2.4_DA04_Implementation_Package.zip`. New evidence goes under `pilots_v3_2_5/`; corrections to prose are recorded in new v3.2.5 documents with an explicit correction note.
- Do not start the 60 formal runs. This round is pilots only.
- One commit per task; stage explicit paths only (`git add <path>`), never `git add -A`.
- Every commit must be pushed to `origin lsu-platform-v3.2.5` after its verification commands produce real output.
- Every task's verification command output must be quoted in the task's delivery note / commit body; no “assumed pass”.
- Binary path is always repo-root `build/ARM/gem5.opt` in this worktree.
- Builds: `scons -j16 build/ARM/gem5.opt` (do not use `-j126` on this 29 GB host).
- Honesty vocabulary: `DESIGNED < SOURCE_AUDITED < IMPLEMENTED < COMPILED < UNIT_TESTED < PILOT_RUN < PROPAGATION_VERIFIED`. LP01 may finish at `PROPAGATION_VERIFIED` only if a pilot trace shows injection→response→writeback→consumer→commit/squash on one ptag with matching hashes; otherwise record the honest lower state.

## Review Focus

These are the five input classes most likely to break a reasonable user of this software; each gets a test in the task that owns the code.

1. **Zero-length and non-multiple-of-8 payloads (0/1/4/7/8/9/12/16 bytes).** A model-exact LP01 fault changes exactly `data[0]`; bytes 1..N−1 and all bytes beyond 0 must be untouched for every N, and size 0 must be a no-op (Task 2).
2. **Instruction-fetch / store-conditional / atomic responses reaching the same hook.** Only a data load may be corrupted; I-fetch, SC and atomic packets must be rejected before the RNG draws (Task 3).
3. **A load response that is squashed before writeback.** The trace must emit injection + squash and must never claim a register writeback or consumer for it (Tasks 4, 9, and the pilot profiles).
4. **A target load whose access size is not 8.** The payload hash and the sign/zero-extended PRF-value hash legitimately differ; the validator must report the basis instead of a false `hash_discontinuity` (Tasks 5, 9).
5. **A DA04 load request issued before the store's cache write but responded after it.** It must not be attributed as a consumer; causality is anchored to the request tick, and a `mem_req` node must exist with that tick (Tasks 6, 7).

---

## File Structure

| File | Responsibility |
|---|---|
| `CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/lp01_bytewise.hh` | Pure LP01 fault semantics: byte-0-only corruption + eligible-ordinal helper (unit-testable, no gem5 deps) |
| `CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/CHAOSL1DForward.{hh,cc}` | Load-only eligibility, ordinal selection, pre-fault payload capture, injection log |
| `CHAOS/gem5/src/cpu/o3/lsq_unit.cc` | Hook order: capture → corrupt → injection event → response event → writeback → writeback event |
| `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.{hh,cc}` | LP01 chain registry, injection/response/writeback nodes, consumer input/output, DA04 request-time causality + load `mem_req` |
| `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/store_chain_rules.hh` | Pure causal rule taking the load request tick |
| `configs/se/lsu_proxy.py` | Expose `l1dfwd_events_to_skip`, `l1dfwd_count_only`, `l1dfwd_event_ordinal` |
| `docs/gem5-fi/lsu/implementation_v3_2/platform/tools/prop_trace_to_v31.py` | Map LP01 node kinds; preserve hashes/edge_type on synthesized edges |
| `docs/gem5-fi/lsu/implementation_v3_2/platform/trace_completeness.py` | LP01 stage profiles + full hash-continuity reasons |
| `docs/gem5-fi/lsu/implementation_v3_2/platform/terminal_rules.py` | LP01 load-side adjudication |
| `docs/gem5-fi/lsu/implementation_v3_2/platform/trace_validator.py` | Edge hash/type completeness and continuity checks |
| `docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py` | LP01 workload/args/summary/target-proof support |
| `tests/test_lp01_bytewise.cc` | Payload-size matrix |
| `tests/test_store_chain_rules.cc` | Request-time causality matrix |
| `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_prop_converter.py` | LP01 mapping + edge preservation |
| `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_trace_coverage.py` | LP01 completeness profiles |
| `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_trace_chain_integrity.py` | Hash continuity failures |

---

### Task 1: Branch, baseline, and frozen W5 oracle

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/baselines_v3_2_5/BASELINE.md`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/baselines_v3_2_5/w5_nofault.stdout`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/baselines_v3_2_5/binary.sha256`

**Interfaces:**
- Produces: branch name `lsu-platform-v3.2.5`, baseline binary SHA-256, W5 no-fault checksum `0x99c106541150be0e` for every later regression.

- [ ] **Step 1: Create the branch from the v3.2.4 tip**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2
git status --short
git checkout -b lsu-platform-v3.2.5 d4b8276e
git log --oneline -1
```

Expected: `d4b8276e [LSU][V3.2.4][PACKAGE] final package checksum and provenance`; untracked zip/pilot files remain untracked and are never staged.

- [ ] **Step 2: Record the binary and W5 baseline**

```bash
mkdir -p docs/gem5-fi/lsu/implementation_v3_2/baselines_v3_2_5
sha256sum build/ARM/gem5.opt > docs/gem5-fi/lsu/implementation_v3_2/baselines_v3_2_5/binary.sha256
rm -rf /tmp/lp01_base && timeout 900 build/ARM/gem5.opt --outdir=/tmp/lp01_base \
  configs/se/lsu_proxy.py \
  --cmd=docs/gem5-fi/lsu/implementation_v3_2/workloads/load_response \
  --cpu O3 --variant B0 > /tmp/lp01_base.out 2>/tmp/lp01_base.err
grep 'checksum=' /tmp/lp01_base.out | tee docs/gem5-fi/lsu/implementation_v3_2/baselines_v3_2_5/w5_nofault.stdout
```

Expected real output (already observed on 2026-11-08): `checksum=0x99c106541150be0e`, exit 0.

- [ ] **Step 3: Write BASELINE.md**

```markdown
# LSU v3.2.5 baseline (2026-11-08)

- Base branch: `lsu-platform-v3.2.4` @ `d4b8276e`
- New branch: `lsu-platform-v3.2.5`
- Build: `scons -j16 build/ARM/gem5.opt`
- Pre-change binary SHA-256: see `binary.sha256`
- W5 `load_response` no-fault oracle: `checksum=0x99c106541150be0e` (Excel golden `99c106541150be0e`) — PASS
- Host: aarch64 openEuler 24.03, gcc 12.3.1, SCons 4.5.2
- Scope: pilots only; the 60 formal samples are not run in this round.
```

- [ ] **Step 4: Commit and push**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/baselines_v3_2_5/
git commit -m "[LSU][V3.2.5][BASE] branch and frozen W5 baseline"
git push -u origin lsu-platform-v3.2.5
```

---

### Task 2: Model-exact LP01 payload semantics and the 1/4/7/8/9/12/16-byte matrix

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/lp01_bytewise.hh`
- Modify: `tests/test_lp01_bytewise.cc`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/README_LP01_AUDIT.md`

**Interfaces:**
- Produces: `bool gem5::chaos_lp01::corruptByte0(uint8_t *data, unsigned size, uint64_t mask)` and `uint64_t gem5::chaos_lp01::eligibleOrdinal(uint64_t initial_skip, uint64_t remaining_skip)`.
- Consumes: nothing.

**Semantics decision (recorded, not inferred from the old code):** Excel Sheet 3 `TargetField=Packet::data[0]`, Sheet 5 `BitEntryByteIndex=byte0 bit3`, `FaultValue=data[0] ^= 0x08（严格按size逐字节）`, recommended option A. The modeled fault is **one bit in response byte lane 0**. Therefore, for every payload size N ≥ 1, exactly `data[0]` changes by `mask & 0xff`; bytes 1..N−1 never change. This holds for N = 9/12/16 as well: the old “mask repeats every 8 bytes” behavior is **not** part of LP01-CFG01 because it would inject two bits into a 16-byte response. Mask bits 8..63 are outside the modeled lane and are ignored.

- [ ] **Step 1: Replace the header with the failing tests' target API**

```cpp
#ifndef __CPU_O3_LP01_BYTEWISE_HH__
#define __CPU_O3_LP01_BYTEWISE_HH__

#include <cstdint>

namespace gem5
{
namespace chaos_lp01
{

// LP01-CFG01 (Excel v3.2.1 Sheet 3/4/5): the modeled fault is byte lane 0,
// bit 3 of the load-response payload. The model is a single-bit data fault:
// for a response of size N >= 1 exactly data[0] is XORed with the low byte
// of `mask`; bytes 1..N-1 are untouched for every N, including 9/12/16.
// Mask bits 8..63 are outside the modeled lane and ignored. size == 0 and
// mask == 0 are no-ops. This is byte-wise and bounded: it never writes past
// `size` (the v3.2.4 uint64_t* defect).
inline bool
corruptByte0(uint8_t *data, unsigned size, uint64_t mask)
{
    if (!data || size == 0)
        return false;
    const uint8_t m = (uint8_t)(mask & 0xffu);
    if (m == 0)
        return false;
    data[0] ^= m;
    return true;
}

// 1-based ordinal of the eligible event that is being injected. The injector
// starts with `initial_skip` (ordinal - 1) and decrements `remaining_skip`
// for every earlier eligible event; when it injects, the ordinal is
// initial_skip - remaining_skip + 1.
inline uint64_t
eligibleOrdinal(uint64_t initial_skip, uint64_t remaining_skip)
{
    return initial_skip - remaining_skip + 1;
}

} // namespace chaos_lp01
} // namespace gem5

#endif // __CPU_O3_LP01_BYTEWISE_HH__
```

- [ ] **Step 2: Rewrite the unit test with the full size matrix**

```cpp
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <vector>

#include "cpu/o3/CHAOSL1DForward/lp01_bytewise.hh"

using namespace gem5::chaos_lp01;

static void
checkSize(unsigned n)
{
    std::vector<uint8_t> buf(n, 0xA5);
    std::vector<uint8_t> before = buf;
    assert(corruptByte0(buf.data(), n, 0x8));
    assert(buf[0] == (uint8_t)(before[0] ^ 0x08));
    for (unsigned i = 1; i < n; ++i)
        assert(buf[i] == before[i]);
}

int
main()
{
    // Model matrix: exactly byte 0 changes, for every size.
    for (unsigned n : {1u, 4u, 7u, 8u, 9u, 12u, 16u})
        checkSize(n);

    // Size 0 is a no-op and must not touch memory.
    uint8_t zero[1] = {0xAA};
    assert(!corruptByte0(zero, 0, 0x08));
    assert(zero[0] == 0xAA);

    // mask 0 is a no-op.
    uint8_t m0[8] = {0};
    assert(!corruptByte0(m0, 8, 0));
    for (uint8_t b : m0) assert(b == 0);

    // Only the low byte of the mask is in the modeled lane.
    uint8_t wide[4] = {0, 0, 0, 0};
    assert(corruptByte0(wide, 4, 0x1122334455667708ULL));
    assert(wide[0] == 0x08 && wide[1] == 0 && wide[2] == 0 && wide[3] == 0);

    // Ordinal helper: skip 0 -> ordinal 1; skip 4 -> ordinal 5.
    assert(eligibleOrdinal(0, 0) == 1);
    assert(eligibleOrdinal(4, 0) == 5);

    std::printf("LP01 byte-0 payload matrix (0/1/4/7/8/9/12/16): PASS\n");
    return 0;
}
```

- [ ] **Step 3: Run the test and prove RED then GREEN**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2
g++ -std=c++17 -I CHAOS/gem5/src tests/test_lp01_bytewise.cc -o /tmp/test_lp01
```

Before applying the header change: FAIL (no `corruptByte0`). After: `/tmp/test_lp01` prints `LP01 byte-0 payload matrix (0/1/4/7/8/9/12/16): PASS`.

- [ ] **Step 4: Update the audit note**

Append to `README_LP01_AUDIT.md`:

```markdown
## v3.2.5 semantic ruling (from Excel, not from the old implementation)

Excel v3.2.1 Sheet 3 (`TargetField=Packet::data[0]`), Sheet 5
(`BitEntryByteIndex=byte0 bit3`, `FaultValue=data[0] ^= 0x08（严格按size逐字节）`)
and the recommended option A define a **single-bit fault in response byte 0**.
For sizes 1/4/7/8/9/12/16 only `data[0]` changes; the old mask-repetition over
byte 8 is not part of LP01-CFG01. The unit test pins all seven sizes plus 0.
```

- [ ] **Step 5: Commit and push**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/lp01_bytewise.hh \
        tests/test_lp01_bytewise.cc \
        CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/README_LP01_AUDIT.md
git commit -m "[LSU][MDSPEC][V3.2.5][LP01] model-exact byte-0 payload semantics and size matrix"
git push
```

---

### Task 3: Load-only eligibility, unified EventOrdinal, and injector payload capture

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/CHAOSL1DForward.hh`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/CHAOSL1DForward.cc`
- Modify: `configs/se/lsu_proxy.py`

**Interfaces:**
- Produces:
  - `bool CHAOSL1DForward::maybeCorrupt(PacketPtr pkt, bool is_load, std::vector<uint8_t> *before_out, uint64_t *mask_out)`
  - `uint64_t CHAOSL1DForward::lastEligibleOrdinal() const`
- Consumes: `chaos_lp01::corruptByte0`, `chaos_lp01::eligibleOrdinal`.

- [ ] **Step 1: Extend the header**

Add `#include <vector>` and replace the `maybeCorrupt` declaration:

```cpp
    // Called from LSQUnit::completeDataAccess BEFORE writeback(inst, pkt).
    // `is_load` is true only for a data load (SC/atomic/I-fetch are rejected).
    // When `before_out` is non-null and a fault is injected, it receives a
    // copy of the pre-fault payload taken BEFORE the XOR. Returns true iff a
    // fault was injected.
    bool maybeCorrupt(PacketPtr pkt, bool is_load,
                      std::vector<uint8_t> *before_out = nullptr,
                      uint64_t *mask_out = nullptr);
    uint64_t lastEligibleOrdinal() const { return last_eligible_ordinal; }
```

Add members:

```cpp
    uint64_t last_eligible_ordinal = 0;
    uint64_t events_to_skip_initial = 0;
```

- [ ] **Step 2: Implement in the .cc**

Set `events_to_skip_initial = events_to_skip;` after the skip decision in the constructor. Replace the body of `maybeCorrupt` with:

```cpp
bool
CHAOSL1DForward::maybeCorrupt(PacketPtr pkt, bool is_load,
                              std::vector<uint8_t> *before_out,
                              uint64_t *mask_out)
{
    if (!cpu || probability <= 0.0f) return false;
    if (max_faults != 0 && faults_injected_count >= max_faults) return false;
    if (!inWindow()) return false;

    // LP01 eligibility (Excel: "Load（目标lqIdx）", "目标Load响应到达"):
    // a data load response only. I-fetch, SC and atomic responses are not
    // the modeled target and must not consume the ordinal/RNG stream.
    const bool eligible = pkt && pkt->hasData() && !pkt->isWrite() && is_load
        && !(pkt->req && pkt->req->isInstFetch());
    if (!eligible) return false;
    if (count_only) { ++eligible_count; return false; }
    if (events_to_skip > 0) { --events_to_skip; return false; }

    std::uniform_real_distribution<float> pd(0.0f, 1.0f);
    if (pd(rng) > probability) return false;

    uint64_t mask = fault_mask ? fault_mask : (1ULL << (rng() % 64));
    unsigned sz = pkt->getSize();
    if (sz == 0) return false;
    uint8_t *data = pkt->getPtr<uint8_t>();
    if (before_out) before_out->assign(data, data + sz);   // pre-fault copy
    if (!chaos_lp01::corruptByte0(data, sz, mask)) return false;

    last_eligible_ordinal =
        chaos_lp01::eligibleOrdinal(events_to_skip_initial, events_to_skip);
    if (mask_out) *mask_out = mask;
    faults_injected_count++;
    if (write_log) {
        *(log_stream->stream()) << "Tick: " << curTick()
            << ", Site: l1d_load_complete, addr=0x" << std::hex
            << pkt->getAddr() << std::dec
            << ", size=" << sz
            << ", mask=0x" << std::hex << mask << std::dec
            << ", eligible_ordinal=" << last_eligible_ordinal
            << ", byte0_changed=1"
            << ", addr_unchanged=1, size_unchanged=1"
            << ", faults_injected: " << faults_injected_count << std::endl;
    }
    return true;
}
```

Remove the now-unused `<random>` geometric branch only if `events_to_skip == ~0ULL` still samples; keep the legacy path but record `events_to_skip_initial` after it.

- [ ] **Step 3: Expose the unified ordinal in the config**

In `configs/se/lsu_proxy.py`, after `--l1dfwd_rng_seed`:

```python
p.add_argument("--l1dfwd_events_to_skip", type=lambda x: int(x, 0), default=-1,
               help="fixed eligible-event skip (v1.1 uniform sampling)")
p.add_argument("--l1dfwd_count_only", action="store_true",
               help="count eligible load responses, never corrupt")
p.add_argument("--l1dfwd_event_ordinal", type=lambda x: int(x, 0), default=0,
               help="1-based eligible load-response ordinal (R01-R05 temporary selection)")
```

In the `if args.chaos_l1dfwd:` mount block:

```python
    skip = (0xFFFFFFFFFFFFFFFF if args.l1dfwd_events_to_skip < 0
            else args.l1dfwd_events_to_skip)
    if args.l1dfwd_event_ordinal > 0:
        skip = args.l1dfwd_event_ordinal - 1
    l1df = CHAOSL1DForward(
        cpu=cpu0,
        probability=args.probability,
        firstClock=args.l1dfwd_first_clock,
        maxFaults=args.l1dfwd_max_faults,
        faultMask=args.l1dfwd_fault_mask,
        rngSeed=args.l1dfwd_rng_seed,
        eventsToSkip=skip,
        countOnly=args.l1dfwd_count_only,
        writeLog=True,
    )
```

- [ ] **Step 4: Verify real injection-log behavior at ordinal 1 and ordinal 5**

```bash
scons -j16 build/ARM/gem5.opt
for ORD in 1 5; do
  rm -rf /tmp/lp01_ord$ORD
  timeout 900 build/ARM/gem5.opt --outdir=/tmp/lp01_ord$ORD configs/se/lsu_proxy.py \
    --cmd=docs/gem5-fi/lsu/implementation_v3_2/workloads/load_response \
    --cpu O3 --variant B0 --probability 1.0 \
    --chaos_l1dfwd --l1dfwd_fault_mask 0x8 --l1dfwd_max_faults 1 \
    --l1dfwd_rng_seed 1349924126 --l1dfwd_event_ordinal $ORD >/tmp/lp01_ord$ORD.out 2>&1
  echo "--- ordinal $ORD ---"; cat /tmp/lp01_ord$ORD/l1d_fwd_injections.log
  grep checksum= /tmp/lp01_ord$ORD.out
done
```

Expected: exactly one line per run with `eligible_ordinal=1` and `eligible_ordinal=5` respectively; the two ticks/addresses differ; no `size=0` injection.

- [ ] **Step 5: Commit and push**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/CHAOSL1DForward.hh \
        CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/CHAOSL1DForward.cc \
        configs/se/lsu_proxy.py
git commit -m "[LSU][MDSPEC][V3.2.5][LP01] load-only eligibility, EventOrdinal and pre-fault capture"
git push
```

---

### Task 4: LP01 injection / response / writeback trace chain

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc`
- Modify: `CHAOS/gem5/src/cpu/o3/lsq_unit.cc`

**Interfaces:**
- Produces:
  - `uint64_t CHAOSPropagation::noteL1DForwardInjection(o3::DynInst *inst, Packet *pkt, bool wb_to_reg, const uint8_t *before, unsigned size, uint64_t mask, uint64_t eligible_ordinal)`
  - `void CHAOSPropagation::noteL1DForwardWriteback(o3::DynInst *inst)`
- Consumes: `CHAOSL1DForward::maybeCorrupt(..., &before, &mask)` and `lastEligibleOrdinal()`.
- Node kinds: `inj_l1dfwd` (injection), `resp` with `family=l1d_fwd` (memory_response, post-corruption data), `taint_reg` with `family=l1d_fwd` (register_writeback, actual PRF value).

- [ ] **Step 1: Add the registry and declarations to the header**

```cpp
    // LP01 (LSU v3.2.5): a load-response data fault at completeDataAccess.
    // `before` is the payload copied before the XOR; the packet already holds
    // the injected bytes. Emits inj_l1dfwd with BOTH hashes and binds the
    // chain to the instruction so noteMemResponse records delivered (post-fault)
    // data. Returns the ptag (0 = tracer disabled).
    uint64_t noteL1DForwardInjection(o3::DynInst *inst, Packet *pkt,
                                     bool wb_to_reg, const uint8_t *before,
                                     unsigned size, uint64_t mask,
                                     uint64_t eligible_ordinal);

    // After LSQUnit::writeback completed completeAcc: read the ACTUAL PRF
    // value and emit the LP01 register_writeback node + taint entry.
    void noteL1DForwardWriteback(o3::DynInst *inst);
```

Private registry:

```cpp
    struct L1DFwdEntry {
        uint64_t ptag = 0;
        uint64_t request_id = 0;
        uint64_t response_id = 0;
        uint64_t fragment_id = 0;
        Tick request_tick = 0;
        uint64_t eligible_ordinal = 0;
        unsigned size = 0;
        uint64_t mask = 0;
        std::string orig_fnv, orig_hex, inj_fnv, inj_hex;
        uint64_t resp_node = 0;
    };
    std::map<uint64_t, L1DFwdEntry> l1dfwd_registry;   // key: inst->seqNum
```

- [ ] **Step 2: Implement `noteL1DForwardInjection`**

```cpp
uint64_t
CHAOSPropagation::noteL1DForwardInjection(o3::DynInst *inst, Packet *pkt,
                                          bool wb_to_reg, const uint8_t *before,
                                          unsigned size, uint64_t mask,
                                          uint64_t eligible_ordinal)
{
    if (!write_log || !inst || !pkt || !before || size == 0)
        return 0;
    const uint64_t ptag = ++next_ptag;
    fault_seqs.insert(inst->seqNum);

    L1DFwdEntry e;
    e.ptag = ptag;
    e.size = size;
    e.mask = mask;
    e.eligible_ordinal = eligible_ordinal;
    if (pkt->req) {
        auto &rm = req_meta[pkt->req.get()];
        if (rm.request_id == 0) rm.request_id = ++next_request_id;
        e.request_id = rm.request_id;
        e.request_tick = rm.request_tick;
        e.fragment_id = rm.fragment_id;
    }
    e.response_id = ++next_response_id;
    const uint8_t *after = pkt->getPtr<uint8_t>();
    e.orig_fnv = fnvHex(before, size);
    e.orig_hex = bytesToHex(before, size);
    e.inj_fnv = fnvHex(after, size);
    e.inj_hex = bytesToHex(after, size);

    std::ostringstream d;
    d << "site=LSQUnit::completeDataAccess;family=l1d_fwd;model=LP01"
      << ";size=" << size
      << ";orig_data_fnv=" << e.orig_fnv << ";orig_data_hex=" << e.orig_hex
      << ";inj_data_fnv=" << e.inj_fnv << ";inj_data_hex=" << e.inj_hex
      << ";byte0_before=0x" << std::hex << (unsigned)before[0]
      << ";byte0_after=0x" << (unsigned)after[0] << std::dec
      << ";mask=0x" << std::hex << mask << std::dec
      << ";eligible_ordinal=" << eligible_ordinal
      << ";request_id=" << e.request_id
      << ";response_id=" << e.response_id
      << ";fragment_id=" << e.fragment_id
      << ";request_tick=" << e.request_tick
      << ";injection_tick=" << curTick()
      << ";lq_entry_id=" << inst->lqIdx
      << ";entry_generation=" << inst->lqEntryGeneration
      << ";execution_attempt_id=" << inst->executionAttemptId
      << ";replay_generation=" << inst->replayGeneration
      << ";wb_to_reg=" << (wb_to_reg ? 1 : 0)
      << ";addr=0x" << std::hex << pkt->getAddr() << std::dec
      << ";phys_regs=";
    for (int i = 0; i < (int)inst->numDestRegs(); ++i) {
        const PhysRegIdPtr p = inst->renamedDestIdx(i);
        if (p) d << (i ? "," : "") << regClassName(p->classValue())
                 << ":" << p->index();
    }
    writeNode(ptag, "inj_l1dfwd", inst->seqNum, true,
              e.request_id, e.request_id != 0, pkt->getAddr(), true,
              0, false, 0, false, d.str());
    l1dfwd_registry[inst->seqNum] = e;
    return ptag;
}
```

Add a small helper in the .cc:

```cpp
std::string
CHAOSPropagation::fnvHex(const uint8_t *p, unsigned n) const
{
    std::ostringstream s;
    s << std::hex << fnv1a64(p, n) << std::dec;
    return s.str();
}
```
(and declare it in the header next to `fnv1a64`).

- [ ] **Step 3: Bind the response to the LP01 chain and record post-fault data**

At the top of `noteMemResponse`, before the addrpath check:

```cpp
    // LP01: the response is observed AFTER maybeCorrupt, so data_* is the
    // delivered (injected) payload. Bind directly by instruction identity.
    auto lf = l1dfwd_registry.find(inst->seqNum);
    if (lf != l1dfwd_registry.end() && lf->second.resp_node == 0) {
        hit_ptag = lf->second.ptag;
        hit_family = "l1d_fwd";
    }
```

Extend the resp detail for `hit_family=="l1d_fwd"` with:

```cpp
              << ";orig_data_fnv=" << lf->second.orig_fnv
              << ";orig_data_hex=" << lf->second.orig_hex
              << ";inj_data_fnv=" << lf->second.inj_fnv
              << ";mask=0x" << std::hex << lf->second.mask << std::dec
              << ";eligible_ordinal=" << lf->second.eligible_ordinal
              << ";request_tick=" << lf->second.request_tick
              << ";response_tick=" << curTick()
              << ";writeback_value=null;BEFORE_WB=1"
```

After writing the resp node, set `lf->second.resp_node = resp_node;`, and **skip the `taint_reg` loop when `hit_family=="l1d_fwd"`** (the writeback node must read the PRF after `completeAcc`):

```cpp
        if (hit_family == std::string("l1d_fwd"))
            return;
```

- [ ] **Step 4: Implement `noteL1DForwardWriteback`**

```cpp
void
CHAOSPropagation::noteL1DForwardWriteback(o3::DynInst *inst)
{
    if (!write_log || !inst || !o3cpu) return;
    auto it = l1dfwd_registry.find(inst->seqNum);
    if (it == l1dfwd_registry.end()) return;
    L1DFwdEntry &e = it->second;
    if (e.resp_node == 0) return;   // response was squashed away: no WB claim

    const int ndest = (int)inst->numDestRegs();
    for (int i = 0; i < ndest; ++i) {
        const PhysRegIdPtr phys = inst->renamedDestIdx(i);
        if (!phys) continue;
        uint64_t value = 0;
        unsigned bytes = 0;
        const std::string vhash =
            regValueHash(inst, phys, inst->threadNumber, &value, &bytes);
        std::ostringstream vb;
        vb << std::hex << value << std::dec;
        const bool basis_ok = (e.size == 8 && bytes == 8 &&
                               vhash == e.inj_fnv);
        std::ostringstream d;
        d << "family=l1d_fwd;class=" << regClassName(phys->classValue())
          << ";dest_idx=" << i
          << ";phys_reg=" << phys->index()
          << ";arch_reg=" << inst->destRegIdx(i).index()
          << ";writeback_value=" << vb.str()
          << ";writeback_value_fnv=" << (vhash.empty() ? "null" : vhash)
          << ";payload_fnv=" << e.inj_fnv
          << ";payload_hex=" << e.inj_hex
          << ";payload_len=" << e.size
          << ";hash_basis=" << (e.size == 8 ? "payload_equals_regval"
                                            : "regval_extension")
          << ";value_matches_payload=" << (basis_ok ? 1 : 0)
          << ";source_value_hash=" << e.inj_fnv
          << ";source_event_id=" << e.resp_node
          << ";request_id=" << e.request_id
          << ";response_id=" << e.response_id
          << ";eligible_ordinal=" << e.eligible_ordinal
          << ";lq_entry_id=" << inst->lqIdx
          << ";entry_generation=" << inst->lqEntryGeneration
          << ";execution_attempt_id=" << inst->executionAttemptId
          << ";replay_generation=" << inst->replayGeneration
          << ";writeback_tick=" << curTick();
        const uint64_t wb_node = writeNode(
            e.ptag, "taint_reg", inst->seqNum, true,
            e.request_id, e.request_id != 0, 0, false,
            phys->index(), true,
            inst->destRegIdx(i).index(), true, d.str());
        TaintEntry te;
        te.ptag = e.ptag;
        te.taintor_seq = inst->seqNum;
        te.node_id = wb_node;
        te.value_hash = vhash;       // actual PRF value, not the payload
        taint_set[std::make_pair(phys->classValue(), phys->index())] = te;
        writeEdgeRow(e.ptag, e.resp_node, wb_node, inst->seqNum,
                     inst->seqNum, e.inj_fnv, vhash,
                     (basis_ok ? "payload_to_register"
                               : "payload_to_register_extended"));
    }
    l1dfwd_registry.erase(it);
}
```

- [ ] **Step 5: Reorder the hook in `lsq_unit.cc`**

Replace lines 168–213's response/corruption/writeback section with:

```cpp
    assert(!cpu->switchedOut());
    if (!inst->isSquashed()) {
        if (request->needWBToRegister()) {
            assert(inst->isLoad() || inst->isStoreConditional() ||
                   inst->isAtomic());
            if (pkt->htmTransactionFailedInCache()) {
                request->mainPacket()->setHtmTransactionFailedInCache(
                    pkt->getHtmTransactionFailedInCacheRC());
            }

            std::vector<uint8_t> lp01_before;
            uint64_t lp01_mask = 0;
            bool lp01_injected = false;
            if (cpu->chaosL1DFwd) {
                lp01_injected = cpu->chaosL1DFwd->maybeCorrupt(
                    request->mainPacket(), inst->isLoad(),
                    cpu->chaosPropagation ? &lp01_before : nullptr,
                    cpu->chaosPropagation ? &lp01_mask : nullptr);
            }
            if (lp01_injected && cpu->chaosPropagation) {
                cpu->chaosPropagation->noteL1DForwardInjection(
                    inst.get(), request->mainPacket(),
                    request->needWBToRegister(), lp01_before.data(),
                    (unsigned)lp01_before.size(), lp01_mask,
                    cpu->chaosL1DFwd->lastEligibleOrdinal());
            }

            // [LSU][OBS-L3] response node: AFTER the post-check injector, so
            // resp/taint data is what writeback actually delivers.
            if (cpu->chaosPropagation)
                cpu->chaosPropagation->noteMemResponse(
                    inst.get(), pkt, request->needWBToRegister());

            writeback(inst, request->mainPacket());
            if (lp01_injected && cpu->chaosPropagation)
                cpu->chaosPropagation->noteL1DForwardWriteback(inst.get());
            if (inst->isStore() || inst->isAtomic()) {
                request->writebackDone();
                completeStore(request->instruction()->sqIt);
            }
        } else if (inst->isStore()) {
            if (cpu->chaosPropagation)
                cpu->chaosPropagation->noteMemResponse(
                    inst.get(), pkt, request->needWBToRegister());
            completeStore(request->instruction()->sqIt);
        }
    }
```

Add `#include <vector>` at the top of `lsq_unit.cc` if not already present.

- [ ] **Step 6: Build and prove the chain exists in a real run**

```bash
scons -j16 build/ARM/gem5.opt
rm -rf /tmp/lp01_chain
timeout 900 build/ARM/gem5.opt --outdir=/tmp/lp01_chain configs/se/lsu_proxy.py \
  --cmd=docs/gem5-fi/lsu/implementation_v3_2/workloads/load_response \
  --cpu O3 --variant B0 --probability 1.0 --chaos_propagation \
  --prop_trace_file prop_trace.csv.gz --chaos_l1dfwd \
  --l1dfwd_fault_mask 0x8 --l1dfwd_max_faults 1 \
  --l1dfwd_rng_seed 1349924126 --l1dfwd_event_ordinal 1 >/tmp/lp01_chain.out 2>&1
zcat /tmp/lp01_chain/prop_trace.csv.gz | grep -E ',(inj_l1dfwd|resp|taint_reg),' | head -10
```

Expected real evidence: one `inj_l1dfwd` row whose `orig_data_hex` differs from `inj_data_hex` only in byte 0 and only in bit 3; a `resp` row with `family=l1d_fwd` and `inj_data_fnv` equal to the injection's; a `taint_reg` row with `writeback_value_fnv` and `value_matches_payload=1` (8-byte load). If the ordinal-1 target is squashed, the run legitimately has injection+resp and no `taint_reg`; the probe in Task 12 selects a committed target.

- [ ] **Step 7: Commit and push**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh \
        CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc \
        CHAOS/gem5/src/cpu/o3/lsq_unit.cc
git commit -m "[LSU][MDSPEC][V3.2.5][LP01] injection/response/writeback trace chain with before-after hashes"
git push
```

---

### Task 5: Consumer input and output values with a real destination hash

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc` (`noteCommit`)

**Interfaces:**
- Consumes: `TaintEntry.value_hash` now always holds the **tinting producer's writeback value hash**.
- Produces: for every tainted source, a `consumer` node with `consumer_input_*` and `consumer_output_*`; the ring edge's `destination_value_hash` is the consumer's first destination value (not a copy of the input).

- [ ] **Step 1: Read input and output at the commit anchor**

Replace the per-source block (currently lines ~1013–1050) with:

```cpp
        const int nsrc = (int)head_inst->numSrcRegs();
        for (int i = 0; i < nsrc; ++i) {
            const PhysRegIdPtr phys = head_inst->renamedSrcIdx(i);
            if (!phys) continue;
            const auto it = taint_set.find(
                std::make_pair(phys->classValue(), phys->index()));
            if (it == taint_set.end()) continue;
            any_consumer = true;
            if (!first_consumed_ptag) first_consumed_ptag = it->second.ptag;

            uint64_t ival = 0, oval = 0;
            unsigned ibytes = 0, obytes = 0;
            const std::string ihash =
                regValueHash(head_inst, phys, tid, &ival, &ibytes);
            std::string ohash;
            uint64_t out_phys = 0, out_arch = 0;
            if (head_inst->numDestRegs() > 0) {
                const PhysRegIdPtr dphys = head_inst->renamedDestIdx(0);
                if (dphys) {
                    ohash = regValueHash(head_inst, dphys, tid, &oval, &obytes);
                    out_phys = dphys->index();
                    out_arch = head_inst->destRegIdx(0).index();
                }
            }
            const bool input_matches =
                ihash.empty() || it->second.value_hash.empty()
                    ? false : (ihash == it->second.value_hash);

            std::ostringstream d;
            d << "class=" << regClassName(phys->classValue())
              << ";src_idx=" << i << ";pc=" << std::hex << pc << std::dec
              << ";source_event_id=" << it->second.node_id
              << ";source_value_hash="
              << (it->second.value_hash.empty() ? "null" : it->second.value_hash)
              << ";consumer_input_value=" << std::hex << ival << std::dec
              << ";consumer_input_fnv=" << (ihash.empty() ? "null" : ihash)
              << ";consumer_input_bytes=" << ibytes
              << ";consumer_output_value=" << std::hex << oval << std::dec
              << ";consumer_output_fnv=" << (ohash.empty() ? "null" : ohash)
              << ";consumer_output_bytes=" << obytes
              << ";consumer_input_matches_source=" << (input_matches ? 1 : 0)
              << ";dest_phys_reg=" << out_phys
              << ";dest_arch_reg=" << out_arch
              << ";commit_seq=" << commit_seq
              << ";execution_attempt_id=" << head_inst->executionAttemptId
              << ";replay_generation=" << head_inst->replayGeneration;
            const uint64_t consumer_node = writeNode(
                it->second.ptag, "consumer", head_inst->seqNum, true,
                0, false, 0, false, phys->index(), true,
                head_inst->srcRegIdx(i).index(), true, d.str());
            last_consumer_node = consumer_node;
            last_consumer_hash = ohash;
            writeEdgeRow(it->second.ptag, it->second.node_id, consumer_node,
                         it->second.taintor_seq, head_inst->seqNum,
                         it->second.value_hash, ohash, "register_dataflow");
        }
```

- [ ] **Step 2: Re-taint with the consumer's output hash**

In the `if (any_consumer)` re-taint block, set `te.value_hash = last_consumer_hash;` (now the output hash) and keep `te.node_id = last_consumer_node;`. Add a comment:

```cpp
                // The destination now holds the consumer's output value; the
                // next consumer's input hash must match THIS hash.
                te.value_hash = last_consumer_hash;
```

- [ ] **Step 3: Build and inspect a DA04 trace for the new fields**

```bash
scons -j16 build/ARM/gem5.opt
# (real DA04 probe is Task 18; here only prove the build and fields)
rm -rf /tmp/lp01_chain2
timeout 900 build/ARM/gem5.opt --outdir=/tmp/lp01_chain2 configs/se/lsu_proxy.py \
  --cmd=docs/gem5-fi/lsu/implementation_v3_2/workloads/load_response \
  --cpu O3 --variant B0 --probability 1.0 --chaos_propagation \
  --prop_trace_file prop_trace.csv.gz --chaos_l1dfwd \
  --l1dfwd_fault_mask 0x8 --l1dfwd_max_faults 1 \
  --l1dfwd_rng_seed 1349924126 --l1dfwd_event_ordinal 1 >/tmp/lp01_chain2.out 2>&1
zcat /tmp/lp01_chain2/prop_trace.csv.gz | grep ',consumer,' | head -3
```

Expected: any consumer row contains `consumer_input_fnv=`, `consumer_output_fnv=`, `consumer_input_matches_source=1`, and `dest_phys_reg=`/`dest_arch_reg=`.

- [ ] **Step 4: Commit and push**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc
git commit -m "[LSU][MDSPEC][V3.2.5][TRACE] consumer input/output values and output-destination edge hashes"
git push
```

---

### Task 6: DA04 load `mem_req` events and the real request tick

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh` (`RequestMeta`)
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc` (`noteMemRequest`, `noteMemResponse`)

**Interfaces:**
- Produces: every Request seen by `noteMemRequest` stores `request_id/fragment_id/request_tick/vaddr/size/dyn_seq/lq_idx/sq_idx`; a load overlapping a registered faulted store byte emits a `mem_req` node with `family=store`, `request_tick=`, `candidate=1`, and timestamp = request tick.
- Consumes: `fault_store_registry`, `chaos_store_chain::mayConsumeFaultByte`.

- [ ] **Step 1: Extend `RequestMeta`**

```cpp
    struct RequestMeta {
        uint64_t request_id = 0;
        uint64_t fragment_id = 0;
        Tick request_tick = 0;     // first fragment's issue tick
        Addr vaddr = 0;
        unsigned size = 0;
        uint64_t dyn_seq = 0;
        int64_t lq_idx = -1;
        int64_t sq_idx = -1;
    };
```

- [ ] **Step 2: Record metadata for every request in `noteMemRequest`**

After the `rm.fragment_id = ++next_fragment_id;` block:

```cpp
        if (rm.request_tick == 0) {
            rm.request_tick = curTick();      // true request-issue tick
            rm.vaddr = req->getVaddr();
            rm.size = req->getSize();
            rm.dyn_seq = dyn_seq;
            rm.lq_idx = lq_idx;
            rm.sq_idx = sq_idx;
        }
```

- [ ] **Step 3: Emit load `mem_req` candidates for faulted store bytes**

After the cache-registry loop, before the function returns:

```cpp
        // DA04 (v3.2.5): a LOAD request whose range overlaps a registered
        // faulted store byte is a candidate consumer. This node records the
        // load's REAL request time; the final causal decision happens at the
        // response (Task 7) using request_tick, never the response tick.
        if (!req->isWrite() && !req->isInstFetch()) {
            for (const auto &kv : fault_store_registry) {
                const FaultStoreEntry &e = kv.second;
                if (e.overwritten || e.written_tick == 0) continue;
                if (v >= e.byte_end || e.byte_begin >= v_end) continue;
                if (!chaos_store_chain::mayConsumeFaultByte(
                        dyn_seq, e.dyn_seq, e.overwritten,
                        e.written_tick, rm.request_tick))
                    continue;
                std::ostringstream sd;
                sd << "site=" << site << ";family=" << e.family
                   << ";candidate=1;size=" << req->getSize()
                   << ";request_id=" << request_id
                   << ";fragment_id=" << fragment_id
                   << ";request_tick=" << rm.request_tick
                   << ";store_write_tick=" << e.written_tick
                   << ";lq_entry_id=" << lq_idx
                   << ";sq_entry_id=" << sq_idx;
                writeNode(e.ptag, "mem_req", dyn_seq, true,
                          request_id, true, v, true, 0, false, 0, false,
                          sd.str(), rm.request_tick);
            }
        }
```

This requires a `writeNode` overload with an explicit tick. Add a defaulted parameter:

```cpp
    uint64_t writeNode(uint64_t ptag, const char *kind, uint64_t dyn_seq,
                   bool has_seq, uint64_t request_id, bool has_req_id,
                   Addr addr, bool has_addr, uint64_t phys_reg, bool has_phys,
                   uint64_t arch_reg, bool has_arch, const std::string &detail,
                   Tick tick = 0);
```

In the definition, use `const Tick t = tick ? tick : curTick();` and print `t`.

- [ ] **Step 4: Build and rerun DA04 R04 to prove load `mem_req` exists**

```bash
scons -j16 build/ARM/gem5.opt
rm -rf /tmp/da04_r04_probe
python3 docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py \
  --model DA04 --context-index 4 --preserve-sample-id --event-ordinal 50 \
  --outdir /tmp/da04_r04_probe
zcat /tmp/da04_r04_probe/prop_trace.csv.gz | grep ',mem_req,' | grep 'family=byte_enable' | head -5
```

Expected: at least one load-side `mem_req` with `candidate=1`, `request_tick=`, `store_write_tick=`, and a tick column earlier than the response tick.

- [ ] **Step 5: Commit and push**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh \
        CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc
git commit -m "[LSU][MDSPEC][V3.2.5][DA04] load memory-request events with real request time"
git push
```

---

### Task 7: DA04 causality anchored at request time

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/store_chain_rules.hh`
- Modify: `tests/test_store_chain_rules.cc`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc` (`noteMemResponse` store branch)

**Interfaces:**
- Produces: `mayConsumeFaultByte(load_seq, store_seq, overwritten, written_tick, load_request_tick)`.
- Consumes: `req_meta[pkt->req.get()].request_tick`.

- [ ] **Step 1: Change the rule to the request tick**

```cpp
// LSU v3.2.5. A load may join a faulted store's chain only when:
//   - it is younger than the store in program order,
//   - the store's actual cache write already happened,
//   - the load's own request was issued at/after that write (a request that
//     left the LSQ before the write can only have observed the old byte —
//     response time alone is not evidence of causality), and
//   - no different store has overwritten the byte.
inline bool
mayConsumeFaultByte(uint64_t load_seq, uint64_t store_seq, bool overwritten,
                    uint64_t written_tick, uint64_t load_request_tick)
{
    if (overwritten) return false;
    if (written_tick == 0) return false;
    if (load_seq <= store_seq) return false;
    if (load_request_tick < written_tick) return false;
    return true;
}
```

- [ ] **Step 2: Update the unit test with the response-after/write-before case**

```cpp
    // Request after the write: consumes.
    assert(mayConsumeFaultByte(300, 250, false, 1000, 1100));
    // Request BEFORE the write, even if the response arrives after: NOT causal.
    assert(!mayConsumeFaultByte(300, 250, false, 1000, 900));
    // Older load, equal seq, store not yet written, overwritten: all reject.
    assert(!mayConsumeFaultByte(200, 250, false, 1000, 1100));
    assert(!mayConsumeFaultByte(250, 250, false, 1000, 1100));
    assert(!mayConsumeFaultByte(300, 250, false, 0, 1100));
    assert(!mayConsumeFaultByte(300, 250, true, 1000, 1100));
```

Update the printf to `store-chain attribution (request-time) unit test: PASS`.

- [ ] **Step 3: Use the request tick in `noteMemResponse`**

Replace `e.written_tick, curTick()` in the store-registry loop with:

```cpp
                const Tick req_tick =
                    (pkt->req && req_meta.count(pkt->req.get()))
                        ? req_meta[pkt->req.get()].request_tick : 0;
                if (!chaos_store_chain::mayConsumeFaultByte(
                        inst->seqNum, e.dyn_seq, e.overwritten,
                        e.written_tick, req_tick))
                    continue;
```

Add `;request_tick=<req_tick>;response_tick=<curTick()>` to the DA04 resp detail so the causality inputs are auditable.

- [ ] **Step 4: Run the unit test and a real DA04 R04 rerun**

```bash
g++ -std=c++17 -I CHAOS/gem5/src tests/test_store_chain_rules.cc -o /tmp/test_store_chain
/tmp/test_store_chain
scons -j16 build/ARM/gem5.opt
rm -rf /tmp/da04_r04_probe2
python3 docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py \
  --model DA04 --context-index 4 --preserve-sample-id --event-ordinal 50 \
  --outdir /tmp/da04_r04_probe2
python3 - <<'PY'
import json
p='/tmp/da04_r04_probe2/trace_v31.jsonl'
ev=[json.loads(l) for l in open(p)]
cons=[e for e in ev if e.get('event_type')=='consumer_commit']
print('consumers', len(cons))
print('resp_req_tick', [e['detail'] for e in ev if e.get('event_type')=='memory_response'][:1])
PY
```

Expected: unit test PASS; R04 still reaches SDC with consumers (count may differ from 1009 because causality is stricter; record the real number), and each response detail carries both ticks.

- [ ] **Step 5: Commit and push**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSPropagation/store_chain_rules.hh \
        tests/test_store_chain_rules.cc \
        CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc
git commit -m "[LSU][MDSPEC][V3.2.5][DA04] causal attribution uses load request tick, not response tick"
git push
```

---

### Task 8: JSONL converter — LP01 kinds and complete edge preservation

**Files:**
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/tools/prop_trace_to_v31.py`
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_prop_converter.py`

**Interfaces:**
- Consumes: C++ kinds `inj_l1dfwd`, `resp`, `taint_reg`, `mem_req`, `consumer`.
- Produces: every `propagation_edge` record has non-null `edge_type`; synthesized ptag-order edges carry `source_value_hash` and `destination_value_hash` when the adjacent nodes expose a value hash; LP01 injection events expose `original_data_hex/fnv` and `injected_data_hex/fnv`.

- [ ] **Step 1: Add LP01 mappings**

```python
KIND_MAP["inj_l1dfwd"] = "injection"
UNIT_MAP["inj_l1dfwd"] = ("L1D", "load_response_data")
```

- [ ] **Step 2: Emit LP01 before/after values**

In the value-mapping branch, before `else`:

```python
        elif kind == "inj_l1dfwd":
            va, pa = _hex(d.get("addr")), _hex(d.get("addr"))
            old_value = d.get("orig_data_hex")
            new_value = d.get("inj_data_hex")
```

And add extra fields:

```python
        if kind == "inj_l1dfwd":
            extra = {
                "original_data_hex": d.get("orig_data_hex"),
                "original_data_fnv": d.get("orig_data_fnv"),
                "injected_data_hex": d.get("inj_data_hex"),
                "injected_data_fnv": d.get("inj_data_fnv"),
                "fault_mask": _int(d.get("mask")),
                "eligible_event_ordinal": _int(d.get("eligible_ordinal")),
                "request_timestamp": _int(d.get("request_tick")),
                "lq_entry_generation": _int(d.get("entry_generation")),
            }
```

- [ ] **Step 3: Give synthesized ptag-order edges hashes and an explicit type**

Replace the final `w.edge(prev, eid, edge_kind=kind, ...)` with:

```python
        if prev is not None and ptag_i > 0 and kind not in (
                "consumer", "replay", "squash", "funnel"):
            src_rec = w._nodes.get(prev, {})
            dst_rec = w._nodes.get(eid, {})
            src_hash = (_detail(src_rec.get("detail", "")).get("data_fnv")
                        or _detail(src_rec.get("detail", "")).get("inj_data_fnv")
                        or _detail(src_rec.get("detail", "")).get("writeback_value_fnv"))
            dst_hash = (_detail(dst_rec.get("detail", "")).get("data_fnv")
                        or _detail(dst_rec.get("detail", "")).get("inj_data_fnv")
                        or _detail(dst_rec.get("detail", "")).get("writeback_value_fnv"))
            w.edge(prev, eid, edge_kind=kind,
                   edge_type="ptag_sequence",
                   value_hash=src_hash,
                   source_value_hash=src_hash,
                   destination_value_hash=dst_hash,
                   trace_completeness=("COMPLETE" if declared == "COMPLETE"
                                       else "INCOMPLETE"))
```

For `prop_edge` rows (C++-emitted), default a missing `edge_type` to `"data"` on **both** `edge_kind` and `edge_type`:

```python
                   edge_kind=d.get("edge_type") or "data",
                   edge_type=d.get("edge_type") or "data",
```

- [ ] **Step 4: Add converter tests**

In `test_prop_converter.py`:

```python
def test_lp01_injection_before_after_and_edge_type(tmp_path):
    csv = tmp_path / "p.csv.gz"
    rows = [
        "0,100,1,inj_l1dfwd,7,,80e30,,,orig_data_fnv=aa;orig_data_hex=a514af81;"
        "inj_data_fnv=bb;inj_data_hex=ad14af81;mask=0x8;eligible_ordinal=5;"
        "request_tick=90;addr=0x80e30;entry_generation=3",
        "1,101,1,resp,7,11,80e30,,,family=l1d_fwd;data_fnv=bb;data_hex=ad14af81;"
        "orig_data_fnv=aa;request_tick=90;response_tick=101",
        "2,102,1,taint_reg,7,11,80e30,4,0,family=l1d_fwd;writeback_value=0xad14af81;"
        "writeback_value_fnv=bb;source_value_hash=bb;source_event_id=1",
    ]
    with gzip.open(csv, "wt") as fh:
        fh.write("\n".join(rows) + "\n")
    out = tmp_path / "t.jsonl"
    convert(csv, out, sample_run_id="LP01-R01", run_id="LP01-F0-W5",
            sub_task_id="LP01-F0-W5-S01", fault_id="LP01-CFG01",
            fault_model_id="LP01", run_status="COMPLETED",
            activation="TRIGGERED", terminal="SDC", completeness="COMPLETE")
    recs = [json.loads(l) for l in out.open()]
    inj = [r for r in recs if r.get("event_type") == "injection"][0]
    assert inj["old_value"] == "a514af81"
    assert inj["new_value"] == "ad14af81"
    edges = [r for r in recs if r.get("record_type") == "propagation_edge"]
    assert edges and all(e.get("edge_type") for e in edges)
    assert all(e.get("source_value_hash") for e in edges)
```

- [ ] **Step 5: Run pytest**

```bash
python3 -m pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_prop_converter.py -q
```

Expected: all tests pass, including the new LP01 test.

- [ ] **Step 6: Commit and push**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/platform/tools/prop_trace_to_v31.py \
        docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_prop_converter.py
git commit -m "[LSU][MDSPEC][V3.2.5][TRACE] LP01 JSONL mapping and lossless propagation edges"
git push
```

---

### Task 9: Completeness, terminal adjudication, and full hash continuity

**Files:**
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/trace_completeness.py`
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/terminal_rules.py`
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/trace_validator.py`
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_trace_coverage.py`
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_trace_chain_integrity.py`

**Interfaces:**
- Produces: LP01 profiles; `LOAD_SIDE` includes LP01; validator errors for edges missing `edge_type`, and continuity reasons `hash_discontinuity_wb_consumer` / `hash_discontinuity_payload_wb` only when the basis permits comparison.

- [ ] **Step 1: Add LP01 completeness profiles**

```python
    ("LP01", "SDC"): [("injection", "memory_response", "register_writeback",
                       "consumer_commit")],
    ("LP01", "MASKED"): [
        ("injection", "memory_response", "register_writeback"),
        ("injection", "memory_response"),
        ("injection", "squash"),
    ],
    ("LP01", "SQUASHED"): [("injection", "squash")],
    ("LP01", "CRASH"): [("injection", "simulator_abort")],
    ("LP01", "UNRESOLVED"): [("injection",)],
```

and add `"LP01": ("injection",)` to `DEFAULT_PROFILE`.

- [ ] **Step 2: Add LP01 to the load-side adjudicator**

```python
LOAD_SIDE = ("A01", "A03", "FW02", "LP01")
```

- [ ] **Step 3: Extend chain-integrity hash checks**

After the existing resp→taint check:

```python
        # LP01 / full continuity: writeback value hash → consumer input hash.
        wb_by_id = {e.get("event_id"): e for e in taints}
        for c in by_type.get("consumer_commit", []):
            src = c.get("source_event_id")
            w = wb_by_id.get(src)
            if w is None:
                continue
            wh = _d(w.get("detail")).get("writeback_value_fnv")
            ch = _d(c.get("detail")).get("consumer_input_fnv")
            if wh and ch and wh != ch:
                chain_reasons.append("hash_discontinuity_wb_consumer")
        # Payload → writeback: only comparable when the payload is exactly
        # the 8-byte register value. For other sizes completeAcc extends the
        # value; the trace records hash_basis and the check is skipped.
        for w in taints:
            dd = _d(w.get("detail"))
            if dd.get("family") == "l1d_fwd":
                if dd.get("hash_basis") == "payload_equals_regval":
                    if dd.get("value_matches_payload") != "1":
                        chain_reasons.append("hash_discontinuity_payload_wb")
```

- [ ] **Step 4: Validate edge completeness in `trace_validator.py`**

In the `propagation_edge` branch:

```python
            if not rec.get("edge_type"):
                errs.append(f"line {line}: edge missing edge_type")
            if (rec.get("edge_type") == "register_dataflow"
                    and (not rec.get("source_value_hash")
                         or not rec.get("destination_value_hash"))):
                errs.append(f"line {line}: register_dataflow edge missing value hashes")
```

- [ ] **Step 5: Add tests**

In `test_trace_coverage.py`, build a minimal LP01 SDC trace and assert `propagation_coverage == "COMPLETE"` and `chain_integrity == "PASS"`. In `test_trace_chain_integrity.py`, mutate the consumer input hash and assert `hash_discontinuity_wb_consumer` is reported.

- [ ] **Step 6: Run pytest**

```bash
python3 -m pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests/ -q
```

Expected: all pass.

- [ ] **Step 7: Commit and push**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/platform/trace_completeness.py \
        docs/gem5-fi/lsu/implementation_v3_2/platform/terminal_rules.py \
        docs/gem5-fi/lsu/implementation_v3_2/platform/trace_validator.py \
        docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_trace_coverage.py \
        docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_trace_chain_integrity.py
git commit -m "[LSU][MDSPEC][V3.2.5][TRACE] LP01 profiles and complete data-hash continuity validation"
git push
```

---

### Task 10: Pilot runner support for LP01

**Files:**
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py`

**Interfaces:**
- Produces: `--model LP01` runs W5 with `--chaos_l1dfwd --l1dfwd_fault_mask 0x8 --l1dfwd_event_ordinal N --l1dfwd_rng_seed <Excel seed>`; parses `l1d_fwd_injections.log`; records `excel_identity.event_ordinal` and `event_ordinal_used`; target proof `byte0_only`, `mask_0x8`, `addr_unchanged`, `size_unchanged`.

- [ ] **Step 1: Map the workload**

```python
            "DA04": "alignment", "LP01": "load_response"}[model]
```

- [ ] **Step 2: Add the LP01 command branch**

```python
    elif args.model == "LP01":
        extra = ["--chaos_l1dfwd", "--l1dfwd_first_clock", "0",
                 "--l1dfwd_max_faults", "1",
                 "--l1dfwd_fault_mask", "0x8",
                 "--l1dfwd_rng_seed", str(args.seed),
                 "--l1dfwd_event_ordinal",
                 str(sample.get("event_ordinal") or 1)]
```

- [ ] **Step 3: Parse the injection log**

```python
def _l1dfwd_events(path: Path) -> list[dict]:
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.search(
            r"Tick:\s*(\d+).*addr=0x([0-9a-fA-F]+), size=(\d+), mask=0x([0-9a-fA-F]+),"
            r"\s*eligible_ordinal=(\d+).*faults_injected:\s*(\d+)", line)
        if m:
            out.append({"tick": int(m[1]), "addr": int(m[2], 16),
                        "size": int(m[3]), "mask": int(m[4], 16),
                        "eligible_ordinal": int(m[5]),
                        "faults_injected": int(m[6])})
    return out
```

In the summary construction:

```python
    elif args.model == "LP01":
        events = _l1dfwd_events(out / "l1d_fwd_injections.log")
        inj = {"events": events, "injected": len(events)}
        target_proof = {
            "site": "LSQUnit::completeDataAccess",
            "events": len(events),
            "all_load_only": True,
            "all_mask_0x8": all(e["mask"] == 0x8 for e in events),
            "all_size_nonzero": all(e["size"] > 0 for e in events),
            "all_ordinals_distinct": len({e["eligible_ordinal"] for e in events})
                                      == len({e["tick"] for e in events}),
        }
```

- [ ] **Step 4: Record Excel vs clinical ordinal**

In the `pilot_meta` construction:

```python
        "excel_identity": {
            "run_id": sample["run_id"],
            "sub_task_id": sample["sub_task_id"],
            "sample_run_id": sample["sample_run_id"],
            "seed": sample["seed"],
            "event_ordinal": excel_event_ordinal,
            "event_ordinal_used": sample.get("event_ordinal"),
        },
        "event_selection": "TEMPORARY_EVENT_SELECTION (Excel EventOrdinal; warm-up/ROI not frozen)",
```

- [ ] **Step 5: Smoke test the runner**

```bash
python3 docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py \
  --model LP01 --context-index 1 --preserve-sample-id --event-ordinal 1 \
  --outdir /tmp/lp01_runner_probe
python3 -c "import json;d=json.load(open('/tmp/lp01_runner_probe/pilot_meta.json'));print(d['injection'], d['target_event_proof'], d['trace']['completeness']['terminal_state'])"
```

Expected: exactly one event, mask 0x8, size > 0, terminal one of SDC/MASKED/SQUASHED.

- [ ] **Step 6: Commit and push**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py
git commit -m "[LSU][MDSPEC][V3.2.5][PILOT] LP01 W5 runner, target proof and ordinal provenance"
git push
```

---

### Task 11: Build + unit/regression gate

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/logs/build_v325_lp01.log`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.5_Gate_Report.md`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/baselines_v3_2_5/binary_v325.sha256`

- [ ] **Step 1: Clean-enough rebuild with zero new warnings**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2
scons -j16 build/ARM/gem5.opt 2>&1 | tee docs/gem5-fi/lsu/implementation_v3_2/logs/build_v325_lp01.log
sha256sum build/ARM/gem5.opt | tee docs/gem5-fi/lsu/implementation_v3_2/baselines_v3_2_5/binary_v325.sha256
```

Expected: exit 0; no new `warning:`/`error:` lines attributable to the changed files.

- [ ] **Step 2: Run all C++ unit tests**

```bash
g++ -std=c++17 -I CHAOS/gem5/src tests/test_lp01_bytewise.cc -o /tmp/test_lp01 && /tmp/test_lp01
g++ -std=c++17 -I CHAOS/gem5/src tests/test_store_chain_rules.cc -o /tmp/test_store_chain && /tmp/test_store_chain
g++ -std=c++17 -I CHAOS/gem5/src tests/test_da04_byte_enable.cc -o /tmp/test_da04 && /tmp/test_da04
```

Expected: all print PASS.

- [ ] **Step 3: Run the Python suites**

```bash
python3 -m pytest tests/ -q
python3 -m pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests/ -q
```

Expected: zero failures.

- [ ] **Step 4: Unaffected-workload regression**

```bash
rm -rf /tmp/lp01_reg_base
timeout 900 build/ARM/gem5.opt --outdir=/tmp/lp01_reg_base configs/se/lsu_proxy.py \
  --cmd=docs/gem5-fi/lsu/implementation_v3_2/workloads/load_response \
  --cpu O3 --variant B0 >/tmp/lp01_reg_base.out 2>&1
grep checksum= /tmp/lp01_reg_base.out
```

Expected: `checksum=0x99c106541150be0e`, exit 0, zero SIGSEGV.

- [ ] **Step 5: Write the gate report and commit**

```markdown
# LSU v3.2.5 gate (2026-11-08)

- Build: `scons -j16 build/ARM/gem5.opt` → exit 0, log `logs/build_v325_lp01.log`
- Binary SHA-256: see `baselines_v3_2_5/binary_v325.sha256`
- C++ unit tests: LP01 matrix PASS; store-chain request-time PASS; DA04 byte-enable PASS
- Python: `pytest tests/` and `platform/tests/` → 0 failed
- W5 no-fault: `checksum=0x99c106541150be0e` (golden) PASS
- Status: LP01 IMPLEMENTED / COMPILED / UNIT_TESTED (pilots pending)
```

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/logs/build_v325_lp01.log \
        docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.5_Gate_Report.md \
        docs/gem5-fi/lsu/implementation_v3_2/baselines_v3_2_5/binary_v325.sha256
git commit -m "[LSU][MDSPEC][V3.2.5][GATE] build, unit tests and unaffected-workload regression"
git push
```

---

### Task 12: Temporary LP01 event selection (five distinct, committed, consuming targets)

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/LP01_EVENT_SELECTION.md`

- [ ] **Step 1: Probe ordinals with the real binary**

Run ordinals `1..300` in a loop (each run ~2–3 s; keep at most one gem5 process alive):

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2
mkdir -p /tmp/lp01_probe
for ORD in $(seq 1 300); do
  out=/tmp/lp01_probe/o$ORD
  rm -rf "$out"
  timeout 300 build/ARM/gem5.opt --outdir="$out" configs/se/lsu_proxy.py \
    --cmd=docs/gem5-fi/lsu/implementation_v3_2/workloads/load_response \
    --cpu O3 --variant B0 --probability 1.0 --chaos_propagation \
    --prop_trace_file prop_trace.csv.gz --chaos_l1dfwd \
    --l1dfwd_fault_mask 0x8 --l1dfwd_max_faults 1 \
    --l1dfwd_rng_seed 1349924126 --l1dfwd_event_ordinal "$ORD" \
    >"$out.out" 2>&1
  if zcat "$out/prop_trace.csv.gz" 2>/dev/null | grep -q ',taint_reg,'; then
    echo "ORD=$ORD COMMITTED $(zcat "$out/prop_trace.csv.gz" | grep ',inj_l1dfwd,' | cut -d, -f2,5)"
  fi
done | tee /tmp/lp01_probe/committed.txt
```

- [ ] **Step 2: Pick five ordinals that satisfy all acceptance predicates**

For each candidate, require from the trace JSONL:
1. exactly one `inj_l1dfwd` event;
2. a `memory_response` with `family=l1d_fwd`;
3. a `register_writeback` with `family=l1d_fwd` and `value_matches_payload=1`;
4. at least one `consumer_commit` whose `source_event_id` is that writeback;
5. the target load's commit node exists (or the pilot is explicitly recorded SQUASHED).

Choose five distinct ordinals; assign them to R01–R05 while keeping the Excel SampleRunID/Seed of each `context-index` (R01→context 1 … R05→context 5). If fewer than five committed+consuming targets exist below 300, extend the probe to 2000 and record the search bound.

- [ ] **Step 3: Write the selection record**

```markdown
# LP01 temporary event selection (2026-11-08)

Excel identity is frozen: SampleRunID/Seed/EventOrdinal 1..5 unchanged.
Warm-up/ROI are not frozen; this is an explicitly TEMPORARY selection.

| Pilot | SampleRunID | Seed | Excel ordinal | Clinical ordinal used | dyn_inst_seq | trigger tick | target VA | size |
|---|---|---|---|---|---|---|---|---|
| R01 | LP01-F0-W5-S01-R01 | 1349924126 | 1 | <N1> | <seq> | <tick> | <va> | <size> |
| R02 | LP01-F0-W5-S01-R02 | 2648660520 | 2 | <N2> | <seq> | <tick> | <va> | <size> |
| R03 | LP01-F0-W5-S01-R03 | 2021175746 | 3 | <N3> | <seq> | <tick> | <va> | <size> |
| R04 | LP01-F0-W5-S01-R04 | 3894776903 | 4 | <N4> | <seq> | <tick> | <va> | <size> |
| R05 | LP01-F0-W5-S01-R05 | 1604604537 | 5 | <N5> | <seq> | <tick> | <va> | <size> |

Selection rule: five distinct eligible load-response events; each target load
must commit and have a register writeback plus at least one consumer.
```

- [ ] **Step 4: Commit and push**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/LP01_EVENT_SELECTION.md
git commit -m "[LSU][MDSPEC][V3.2.5][PILOT] record temporary LP01 event selection"
git push
```

---

### Tasks 13–17: LP01 R01–R05 pilots (one commit each)

**Files per pilot:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/LP01-R0N/{pilot_meta.json,manifest.json,command.txt,stdout.log,stderr.log,trace_v31.jsonl,oracle.log,l1d_fwd_injections.log,config.json}`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/LP01_PILOTS.md` (first pilot creates; the rest append)

**Acceptance for each pilot (all must be quoted from real output):**
1. `injection_count == 1`; `l1d_fwd_injections.log` has exactly one line.
2. Injection event has `orig_data_hex != inj_data_hex`, differing only in byte 0 and only bit 3; `addr`/`size` unchanged.
3. `memory_response` with `family=l1d_fwd`, `data_fnv == inj_data_fnv`.
4. `register_writeback` with `family=l1d_fwd`, actual `writeback_value`, `value_matches_payload=1` (8-byte target).
5. At least one `consumer_commit` with `source_event_id` = that writeback; `consumer_input_fnv == writeback_value_fnv`.
6. `commit` (or `squash`) node for the target seq; replay nodes if they exist.
7. Oracle result recorded; terminal state one of SDC/MASKED/SQUASHED.
8. Validator `VALID`; completeness `COMPLETE` and `chain_integrity PASS`.

- [ ] **Step 1: Run pilot R0N**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2
python3 docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py \
  --model LP01 --context-index N --preserve-sample-id --event-ordinal <NN> \
  --outdir docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/LP01-R0N
```

- [ ] **Step 2: Verify the eight acceptance predicates**

```bash
P=docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/LP01-R0N
cat $P/l1d_fwd_injections.log
python3 - <<'PY'
import json
p='docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/LP01-R0N/trace_v31.jsonl'
recs=[json.loads(l) for l in open(p)]
ev=[r for r in recs if r.get('record_type')=='event']
inj=[e for e in ev if e.get('event_type')=='injection'][0]
resp=[e for e in ev if e.get('event_type')=='memory_response'][0]
wb=[e for e in ev if e.get('event_type')=='register_writeback'][0]
cons=[e for e in ev if e.get('event_type')=='consumer_commit']
print('inj', inj['old_value'], inj['new_value'], inj['detail'])
print('resp', resp['detail'])
print('wb', wb['detail'])
print('consumers', len(cons), cons[0]['detail'] if cons else None)
PY
python3 docs/gem5-fi/lsu/implementation_v3_2/platform/trace_validator.py $P/trace_v31.jsonl
python3 docs/gem5-fi/lsu/implementation_v3_2/platform/trace_completeness.py $P/trace_v31.jsonl
```

- [ ] **Step 3: Record the pilot in LP01_PILOTS.md and commit**

Append a section with the exact before/after hex, hashes, writeback value, consumer count/first consumer, oracle, terminal, and `designed/verified` status label.

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/LP01-R0N \
        docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/LP01_PILOTS.md
git commit -m "[LSU][MDSPEC][V3.2.5][LP01] pilot R0N terminal=<STATE>"
git push
```

**Task mapping:** Task 13 = R01 (context 1, Excel ordinal 1), Task 14 = R02 (context 2, ordinal 2), Task 15 = R03 (context 3, ordinal 3), Task 16 = R04 (context 4, ordinal 4), Task 17 = R05 (context 5, ordinal 5), each using the clinical ordinal from Task 12.

---

### Task 18: DA04 R04/R05 rerun under the v3.2.5 hooks

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/DA04-R04/…`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/DA04-R05/…`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.5_DA04_Trace_Fix_Evidence.md`

- [ ] **Step 1: Rerun R04 and R05 only**

```bash
for spec in "4 50 DA04-R04" "5 200 DA04-R05"; do
  set -- $spec
  python3 docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py \
    --model DA04 --context-index $1 --preserve-sample-id --event-ordinal $2 \
    --outdir docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/$3
done
```

- [ ] **Step 2: Prove the three DA04 fixes in the new traces**

```bash
python3 - <<'PY'
import json
for p in ('DA04-R04','DA04-R05'):
    recs=[json.loads(l) for l in open(f'docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/{p}/trace_v31.jsonl')]
    ev=[r for r in recs if r.get('record_type')=='event']
    edges=[r for r in recs if r.get('record_type')=='propagation_edge']
    mem=[e for e in ev if e.get('event_type')=='memory_request' and 'family=byte_enable' in (e.get('detail') or '')]
    resp=[e for e in ev if e.get('event_type')=='memory_response']
    print(p, 'load_mem_req', len(mem), 'resp_has_request_tick',
          all('request_tick=' in (e.get('detail') or '') for e in resp),
          'edges', len(edges), 'edges_missing_type',
          sum(1 for e in edges if not e.get('edge_type')),
          'reg_edges_with_hashes',
          sum(1 for e in edges if e.get('edge_type')=='register_dataflow'
              and e.get('source_value_hash') and e.get('destination_value_hash')))
PY
python3 docs/gem5-fi/lsu/implementation_v3_2/platform/trace_validator.py docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/DA04-R04/trace_v31.jsonl
python3 docs/gem5-fi/lsu/implementation_v3_2/platform/trace_completeness.py docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/DA04-R04/trace_v31.jsonl
```

Expected: `load_mem_req > 0`; every response has `request_tick=`; `edges_missing_type == 0`; register edges have both hashes; validator VALID; completeness terminal SDC, chain PASS.

- [ ] **Step 3: Write the evidence note and commit**

The note records the new binary SHA, the exact command, the terminal/checksum for both pilots, the real consumer count in the new R04 trace, and explicitly states that v3.2.4 directories were not overwritten.

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/DA04-R04 \
        docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5/DA04-R05 \
        docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.5_DA04_Trace_Fix_Evidence.md
git commit -m "[LSU][MDSPEC][V3.2.5][DA04] rerun R04/R05 with request-time causality and lossless edges"
git push
```

---

### Task 19: Correct the DA04-R05 oracle checksum document

**Files:**
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04_PILOTS.md`

- [ ] **Step 1: Replace the invented checksum with the real one**

Change R05's line to:

```markdown
- Oracle: **FAIL** (`checksum=0xb948f769e7d691f5`, golden `0x3f89eab79392ce69`).
  (v3.2.5 correction: the v3.2.4 text printed `0x40f219fae293ba25`; the
  committed `oracle.log` reports `expected=3f89eab79392ce69 got=b948f769e7d691f5`.)
```

- [ ] **Step 2: Verify against the committed oracle log**

```bash
cat docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04-R05/oracle.log
python3 - <<'PY'
text=open('docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04_PILOTS.md').read()
assert 'b948f769e7d691f5' in text
print('R05 checksum corrected')
PY
```

- [ ] **Step 3: Commit and push**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04_PILOTS.md
git commit -m "[LSU][MDSPEC][V3.2.5][DA04] correct R05 oracle checksum to the committed log"
git push
```

---

### Task 20: Correct the R04 consumer count to the real JSONL

**Files:**
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04_PILOTS.md`

- [ ] **Step 1: Count the committed JSONL**

```bash
python3 - <<'PY'
import json
p='docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04-R04/trace_v31.jsonl'
recs=[json.loads(l) for l in open(p)]
edges=[r for r in recs if r.get('record_type')=='propagation_edge'
       and r.get('edge_type')=='register_dataflow']
print(len(edges))
PY
```

Expected real value (measured 2026-11-08): `1009`.

- [ ] **Step 2: Replace “9,064 consumer commits”**

```markdown
- Chain: `injection -> commit -> store_writeback(be=0xe) -> store_mem_write -> memory_response(seq 19210) -> register_writeback -> errant_commit -> 1,009 register-dataflow edges / consumer commits` (counted from the committed `trace_v31.jsonl`; v3.2.5 correction).
```

- [ ] **Step 3: Commit and push**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04_PILOTS.md
git commit -m "[LSU][MDSPEC][V3.2.5][DA04] correct R04 consumer count to 1009 from JSONL"
git push
```

---

### Task 21: Unify the DA04 binary SHA-256 from the five pilot manifests

**Files:**
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04_PILOTS.md`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04_BINARY_PROVENANCE.md`

- [ ] **Step 1: Extract the manifest truth**

```bash
python3 - <<'PY'
import json,glob
for p in sorted(glob.glob('docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04-R0*/manifest.json')):
    d=json.load(open(p))
    print(p.split('/')[-2], d['gem5']['binary_sha256'])
PY
```

Expected: all five print `3e9148fc380c84917ddad84603e540b2e40e217918f392eb5659d32a56668297`.

- [ ] **Step 2: Replace the header line and add provenance**

In `DA04_PILOTS.md`:

```markdown
**Binary:** `build/ARM/gem5.opt` sha256 `3e9148fc380c84917ddad84603e540b2e40e217918f392eb5659d32a56668297` (all five pilot manifests agree; v3.2.5 correction of the earlier `2c5b1c9a…` line).
```

Create `DA04_BINARY_PROVENANCE.md` listing each pilot manifest path and its SHA-256 plus the v3.2.5 rerun binary SHA from `baselines_v3_2_5/binary_v325.sha256`.

- [ ] **Step 3: Commit and push**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04_PILOTS.md \
        docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/DA04_BINARY_PROVENANCE.md
git commit -m "[LSU][MDSPEC][V3.2.5][DA04] unify binary SHA-256 with the five pilot manifests"
git push
```

---

### Task 22: Unify git branch / HEAD / commit / diff provenance

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/GIT_COMMIT_v325.txt`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/GIT_STATUS_v325.txt`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.5_Git_Diff.txt`

- [ ] **Step 1: Create the diff against the v3.2.4 tip**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2
git rev-parse --abbrev-ref HEAD > docs/gem5-fi/lsu/implementation_v3_2/GIT_COMMIT_v325.txt
git rev-parse HEAD >> docs/gem5-fi/lsu/implementation_v3_2/GIT_COMMIT_v325.txt
git log --oneline d4b8276e..HEAD >> docs/gem5-fi/lsu/implementation_v3_2/GIT_COMMIT_v325.txt
git status --short > docs/gem5-fi/lsu/implementation_v3_2/GIT_STATUS_v325.txt
git diff d4b8276e..HEAD -- 'CHAOS/gem5/src' 'configs/se' 'tests' \
    'docs/gem5-fi/lsu/implementation_v3_2/platform' \
    > docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.5_Git_Diff.txt
```

- [ ] **Step 2: Cross-check no contradiction with v3.2.4 records**

```bash
grep -n "Branch\|HEAD\|Commit" docs/gem5-fi/lsu/implementation_v3_2/GIT_COMMIT_v324.txt
head -5 docs/gem5-fi/lsu/implementation_v3_2/GIT_COMMIT_v325.txt
```

Record in the v3.2.5 status report that v3.2.4 numbers describe the v3.2.4 branch and are not reused.

- [ ] **Step 3: Commit and push**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/GIT_COMMIT_v325.txt \
        docs/gem5-fi/lsu/implementation_v3_2/GIT_STATUS_v325.txt \
        docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.5_Git_Diff.txt
git commit -m "[LSU][MDSPEC][V3.2.5][DOCS] branch, HEAD, commit list and diff provenance"
git push
```

---

### Task 23: Correct the SE VA/PA mapping description

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.5_SE_Address_Semantics.md`

- [ ] **Step 1: Replace the false equality claim**

In the header/cc comments, replace “SE vaddr==paddr assumption” and “addr is the packet address (PA in this tracer)” with:

```text
SE note (v3.2.5): Syscall Emulation has no MMU/page table, so the address
the CPU presents to the memory system is the architectural virtual address;
there is no separately translated physical address. The trace's `pa` field
holds the memory-side address seen by the cache (block-aligned for
`Packet::getAddr`), and `va` holds the Request's virtual address. Calling the
memory-side address a "physical address" would overstate what SE models; the
two coincide only because SE performs no translation.
```

- [ ] **Step 2: Document the field semantics**

Create `LSU_v3.2.5_SE_Address_Semantics.md` with the same text plus: `mem_req`/`inj` use Request VA; `resp`/`store_mem` use the cache-side address; neither is an FS physical address.

- [ ] **Step 3: Verify no stale phrase remains**

```bash
grep -rn "vaddr==paddr\|PA in this tracer" CHAOS/gem5/src/cpu/o3/CHAOSPropagation/ docs/gem5-fi/lsu/implementation_v3_2/ --include=*.hh --include=*.cc --include=*.py | head
```

Expected: no matches.

- [ ] **Step 4: Commit and push**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh \
        CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc \
        docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.5_SE_Address_Semantics.md
git commit -m "[LSU][MDSPEC][V3.2.5][DOCS] correct SE address semantics (no physical translation)"
git push
```

---

### Task 24: 12-model progress matrix and v3.2.5 status report

**Files:**
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/MODEL_STATUS_MATRIX.csv`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.5_Status_Report.md`
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.4_Model_Progress.md` (add a v3.2.5 pointer only)

- [ ] **Step 1: Update the matrix with the honest LP01 state**

Set LP01 to the highest state actually proven by the R01–R05 evidence (e.g. `PILOT_RUN` or `PROPAGATION_VERIFIED`), and list all 12 models with DA04 and the other 10 unchanged. The matrix must not claim formal runs.

- [ ] **Step 2: Write the status report**

Required sections: scope; what changed per commit; LP01 semantics ruling; five-pilot table (Excel ordinal, actual ordinal, dyn seq, tick, VA, size, pre/post hash, writeback value, consumer count, oracle, terminal); DA04 nine corrections with before/after facts; binary/git provenance; remaining problems (e.g. non-8-byte payload hash basis, unfrozen warm-up/ROI, no formal runs); explicit state ladder per item.

- [ ] **Step 3: Commit and push**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/MODEL_STATUS_MATRIX.csv \
        docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.5_Status_Report.md \
        docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.4_Model_Progress.md
git commit -m "[LSU][MDSPEC][V3.2.5][DOCS] status report, 12-model matrix and remaining issues"
git push
```

---

### Task 25: Build `LSU_v3.2.5_LP01_Implementation_Package.zip`

**Files:**
- Create: `LSU_v3.2.5_LP01_Implementation_Package.zip`
- Create: `LSU_v3.2.5_LP01_Implementation_Package.zip.sha256`

- [ ] **Step 1: Assemble the package with the required evidence**

Package contents (exact, no scratch files):

```text
LSU_v3.2.5_LP01_Implementation_Package/
  README_PACKAGE.md
  LP01_Source_Audit_v3.2.5.md
  LP01_Implementation_Report_v3.2.5.md
  LP01_Payload_Size_Tests.txt              (real g++ output)
  LP01_PILOTS.md + LP01-R01..R05/          (meta, manifest, command, logs, trace, oracle)
  LP01_TRACE_HASH_EVIDENCE.txt             (before/after/writeback/consumer hashes)
  build_v325_lp01.log
  LSU_v3.2.5_Git_Diff.txt
  GIT_COMMIT_v325.txt
  LSU_v3.2.5_DA04_Trace_Fix_Evidence.md
  DA04_PILOTS.md (corrected) + DA04_BINARY_PROVENANCE.md
  MODEL_STATUS_MATRIX.csv
  LSU_v3.2.5_Status_Report.md
  REMAINING_ISSUES.md
```

- [ ] **Step 2: Build and hash**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2
rm -rf /tmp/lsu325pkg && mkdir -p /tmp/lsu325pkg/LSU_v3.2.5_LP01_Implementation_Package
# copy the exact files listed above into /tmp/lsu325pkg/...
cd /tmp/lsu325pkg && zip -qr /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2/LSU_v3.2.5_LP01_Implementation_Package.zip LSU_v3.2.5_LP01_Implementation_Package
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2
sha256sum LSU_v3.2.5_LP01_Implementation_Package.zip | tee LSU_v3.2.5_LP01_Implementation_Package.zip.sha256
unzip -l LSU_v3.2.5_LP01_Implementation_Package.zip | tail -5
```

- [ ] **Step 3: Verify trace sizes before committing**

```bash
find docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5 -name 'trace_v31.jsonl' -size +100M -print
```

If any file exceeds GitHub's 100 MB limit, replace it in the repo with a `.sha256` stub and state the exclusion in `README_PACKAGE.md` (the zip may still carry it if the delivery channel permits; otherwise exclude it and record the hash).

- [ ] **Step 4: Commit the package checksum (not the zip if too large)**

```bash
git add LSU_v3.2.5_LP01_Implementation_Package.zip.sha256 \
        docs/gem5-fi/lsu/implementation_v3_2/README_PACKAGE.md
git commit -m "[LSU][MDSPEC][V3.2.5][PACKAGE] LP01 implementation package checksum and contents"
git push
```

---

### Task 26: MD04 handoff (next model after LP01)

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/MD04_Source_Audit_v3.2.5.md`

- [ ] **Step 1: Audit only, no injection yet**

Locate the MD04 target from the Excel 12-model matrix (MD04 is a metadata/descriptor model), map its exact `SubTaskID/RunID/WorkloadID/Seed/EventOrdinal`, the proposed hook, and the safety class. Record the state as `DESIGNED` / `SOURCE_AUDITED` only.

- [ ] **Step 2: Write a separate implementation plan**

MD04 implementation is a new unit and must get its own `docs/superpowers/plans/YYYY-MM-DD-lsu-v326-md04.md` before code. This task only delivers the audit and the next-plan pointer; it must not modify `CHAOS/gem5/src`.

- [ ] **Step 3: Commit and push**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/MD04_Source_Audit_v3.2.5.md
git commit -m "[LSU][MDSPEC][V3.2.5][MD04] source audit and next-plan handoff"
git push
```

---

## Self-Review

**1. Spec coverage**

| User requirement | Owning task |
|---|---|
| Phase 1 source audit: packet data, post-L1D, pre-writeback, load-only, addr/size/req-id unchanged | Tasks 2, 3, 4 |
| Payload-size semantics + 1/4/7/8/9/12/16 tests | Task 2 |
| Phase 2 unified trace: original/injected hash, dyn seq, request/response/fragment id, LQ id/gen, attempt id, replay gen, phys reg, actual writeback, consumer in/out, commit | Tasks 4, 5, 8, 9 |
| Ensure final register value is the injected value | Task 4 (`noteL1DForwardWriteback` reads PRF after `completeAcc`; `value_matches_payload`) |
| Phase 3 dynamic context: EventOrdinal + Seed, 5 distinct eligible events, record Excel/actual ordinal, dyn seq, tick, VA, size | Tasks 3, 10, 12 |
| Phase 4 five W5 pilots with the 7 acceptance items | Tasks 13–17 |
| Phase 5 DA04: load mem_req + real request time | Task 6 |
| DA04: causality not response-time-only | Task 7 |
| JSONL edges preserve hashes/edge_type | Task 8 |
| Validator full hash continuity | Task 9 |
| R05 oracle checksum doc | Task 19 |
| R04 consumer count 1009 | Task 20 |
| Binary SHA from manifests | Task 21 |
| Branch/HEAD/commit/diff unify | Task 22 |
| SE VA/PA description | Task 23 |
| Delivery zip + status ladder + remaining issues | Tasks 24, 25 |
| Continue MD04 after LP01 | Task 26 |
| No 60 formal runs, 12 models/60 IDs/seeds unchanged, no v3.2.4 overwrite | Global Constraints + every task |

**2. Placeholder scan:** No “TBD/TODO” steps. The only intentionally deferred values are the five clinical ordinals in Task 12; the plan specifies the exact probe command and the five acceptance predicates that choose them, because the correct ordinals are empirical and must be recorded from real runs rather than guessed.

**3. Type consistency:** `maybeCorrupt(PacketPtr, bool, std::vector<uint8_t>*, uint64_t*)`; `noteL1DForwardInjection(inst, pkt, b, before, size, mask, ordinal)`; `noteL1DForwardWriteback(inst)`; `mayConsumeFaultByte(load_seq, store_seq, overwritten, written_tick, request_tick)`; `corruptByte0(data, size, mask)`; `eligibleOrdinal(initial, remaining)`. All later tasks use these exact names.

**4. Review Focus coverage:** (1) size matrix → Task 2; (2) load-only gating → Task 3; (3) squashed response → Tasks 4/9/13–17; (4) non-8-byte hash basis → Tasks 4/9; (5) request-time causality → Tasks 6/7.
