# LP01 implementation report (LSU v3.2.5)

## Hook order in `LSQUnit::completeDataAccess`

1. `maybeCorrupt(mainPacket, inst->isLoad(), &before, &mask)` — copies the
   pre-fault payload, XORs byte 0, records the eligible ordinal.
2. `noteL1DForwardInjection(...)` — writes `inj_l1dfwd` with
   `orig_data_hex/fnv`, `inj_data_hex/fnv`, request/response/fragment ids,
   LQ entry/generation, attempt id, replay generation, phys regs.
3. `noteMemResponse(...)` — after corruption, writes `resp` with
   `family=l1d_fwd` and the post-injection data hash; skips the pre-writeback
   taint loop for this family.
4. `writeback(inst, mainPacket)` — `completeAcc` writes the PRF.
5. `noteL1DForwardWriteback(inst)` — reads the **actual PRF value**,
   writes `register_writeback` (`writeback_value`, `writeback_value_fnv`,
   `payload_fnv`, `hash_basis`, `value_matches_payload`) and taints consumers
   with that value hash.
6. `noteCommit` — consumer input/output values; edges carry the destination
   register value hash; re-taint uses the consumer output hash.

## Key guarantee

The value that reaches the register is the value the injector wrote: the
writeback node's hash is computed from `getReg(renamedDestIdx(i))` after
`completeAcc`, and for an 8-byte load it equals the injected payload hash
(`value_matches_payload=1` in all five pilots).

## Compatibility

- DA04's `0xF→0xE` byte-enable definition is unchanged.
- Other injectors' response snapshots are unaffected: `noteMemResponse` was
  moved after the post-check injector, but only the LP01 family consumes the
  moved position.
- The DA04 store chain now uses the load request tick and emits load
  `mem_req` events.

## Verification

Build exit 0; C++ tests PASS; 72 platform tests pass; W5 no-fault oracle
PASS; five LP01 pilots accepted with COMPLETE traces and PASS chain
integrity.
