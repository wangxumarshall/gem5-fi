# LP01 injection identity (v3.3.2, P0-4)

Goal: the LP01 injection record must identify the **target instruction**
(dyn_inst_seq, PC, VA), not only a physical address, while preserving every
existing field: PA, request_id, response_id, LQ identity, before/after data
hashes, writeback and downstream consumer evidence.

## Files changed (Agent C ownership only)

| File | Change |
|---|---|
| `CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/CHAOSL1DForward.hh` | forward-declare `o3::DynInst`; `maybeCorrupt` takes `o3::DynInst *inst` |
| `CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/CHAOSL1DForward.cc` | include `cpu/o3/dyn_inst.hh`; new signature; identity fields in `l1d_fwd_injections.log` |
| `CHAOS/gem5/src/cpu/o3/lsq_unit.cc` | call site passes `inst.get()` (one block, no other change) |
| `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc` | `noteL1DForwardInjection` detail gains `;dyn_inst_seq=`, `;pc=0x`, `;vaddr=0x` |
| `tests/test_lp01_bytewise.cc` | format assertions scoped to the emitting functions + call-site check |

`CHAOSPropagation.hh` was **not** changed: the signature of
`noteL1DForwardInjection` is unchanged.

## Exact new signature

```cpp
bool maybeCorrupt(o3::DynInst *inst, PacketPtr pkt, bool is_load,
                  std::vector<uint8_t> *before_out = nullptr,
                  uint64_t *mask_out = nullptr);
```

Call site (`lsq_unit.cc`, `LSQUnit::completeDataAccess`):

```cpp
lp01_injected = cpu->chaosL1DFwd->maybeCorrupt(
    inst.get(), request->mainPacket(), inst->isLoad(),
    cpu->chaosPropagation ? &lp01_before : nullptr,
    cpu->chaosPropagation ? &lp01_mask : nullptr);
```

The byte-0 XOR (`chaos_lp01::corruptByte0`), eligibility predicate, sampling
window, RNG draw, ordinal accounting and `maxFaults` behavior are untouched.

## Record fields

### `l1d_fwd_injections.log` (CHAOSL1DForward) — one line per injection

Pre-existing: `Tick`, `Site: l1d_load_complete`, `addr` (PA), `size`, `mask`,
`eligible_ordinal`, `byte0_changed`, `addr_unchanged`, `size_unchanged`,
`faults_injected`.

Added: `pa` (same value as `addr`, explicit label), `va`
(`pkt->req->getVaddr()`), `pc` (`inst->pcState().instAddr()`),
`dyn_inst_seq` (`inst->seqNum`), `lq_entry_id` (`inst->lqIdx`),
`entry_generation` (`inst->lqEntryGeneration`), `request_id`.

`request_id` is logged as `0` **in this file**: the request id lives in
`CHAOSPropagation::req_meta` and is (re)assigned inside
`noteL1DForwardInjection()`, which runs immediately after this call. The
injector has no handle on the tracer, so the authoritative request id is the
one in the paired `inj_l1dfwd` row. This is stated in the source comment.

### `inj_l1dfwd` detail (CHAOSPropagation) — newline-terminal row per injection

Pre-existing (kept, verified by the test): `site`, `family`, `model`, `size`,
`orig_data_fnv`, `orig_data_hex`, `inj_data_fnv`, `inj_data_hex`,
`byte0_before`, `byte0_after`, `mask`, `eligible_ordinal`, `request_id`,
`response_id`, `fragment_id`, `request_tick`, `injection_tick`, `lq_entry_id`,
`entry_generation`, `execution_attempt_id`, `replay_generation`, `wb_to_reg`,
`addr` (PA), `phys_regs`.

Added: `dyn_inst_seq` (`inst->seqNum`), `pc` (hex, `instAddr()`), `vaddr`
(hex, `pkt->req->getVaddr()`; `0` when the request has no vaddr).

### Unchanged, already available

`noteL1DForwardWriteback` (`taint_reg` / `register_writeback`) and the consumer
edges emitted by the propagation tracer already carry `dyn_inst_seq`,
`request_id`, `response_id`, `lq_entry_id`, `entry_generation`,
`execution_attempt_id`, `replay_generation`, source/consumer hashes. This patch
does not alter them; it makes the **injection** node carry the same identity
that writeback/consumer nodes already had.

## Test

Command (the documented one for this test, run from the repo root):

```
g++ -std=c++17 -I CHAOS/gem5/src tests/test_lp01_bytewise.cc -o /tmp/test_lp01 && /tmp/test_lp01
```

Real output:

```
LP01 byte-0 payload matrix (0/1/4/7/8/9/12/16): PASS
LP01 identity record (l1d_fwd_injections.log + inj_l1dfwd): PASS
exit=0
```

The identity assertions are **not vacuous**: the same test compiled against a
detached copy of the tree with `";pc=0x"` removed from the propagation tracer
aborts:

```
test_lp01_red: tests/test_lp01_bytewise.cc:143: int main(): Assertion `contains(note, f)' failed.
Aborted (core dumped)
exit=134
```

Assertions are scoped by slicing the source between the emitting function's
definition and the next function, so a token elsewhere in the file cannot
satisfy them. The call-site assertion slices
`chaosL1DFwd->maybeCorrupt(` … `);` and requires `inst.get()`.

## Residual risks

- **Not compiled against gem5.** Per role split Agent C does not run scons; the
  C++ edits were not build-verified. The changes use only existing APIs
  (`DynInst::pcState()/seqNum/lqIdx/lqEntryGeneration`, `Request::getVaddr()/
  hasVaddr()`), already used in the same files, but a build is required before
  claiming a pass.
- `request_id` in `l1d_fwd_injections.log` is always `0` by construction (see
  above). Consumers needing it must read the `inj_l1dfwd` row.
- Log-line format is append/extend only: `addr=` keeps its position and value;
  new fields are inserted between existing fields, so strict positional
  parsers of `l1d_fwd_injections.log` should be re-checked.
- The red check used scratch copies under `/tmp`; the repository was not
  modified by it.
