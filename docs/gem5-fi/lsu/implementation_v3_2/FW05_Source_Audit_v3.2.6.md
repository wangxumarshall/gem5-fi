# FW05 source audit (handoff)

**State:** DESIGNED / SOURCE_AUDITED. No code or pilot in this round.

## Frozen identity (Excel v3.2.1)

| Field | Value |
|---|---|
| Model | FW05 (部分重叠数据拼接错误) |
| Unit | FWD |
| Mode | F6 |
| SubTask / RunID | `FW05-F6-W8-S01` / `FW05-F6-W8` |
| Workload | W8 `alignment` |
| Location | `CHAOSLSQFwd::maybeSubstituteSource` |
| Target | `store_it._idx` / `alt_src` |
| Normal | `true_src` = youngest matching store |
| Fault | copy `alt_src` = older store data |
| Recommended | A: wrong-source forwarding (existing hook); B: true multi-store splice is NOT SUPPORTED; C: delete is forbidden |
| Oracle | `3f89eab79392ce69` |
| Seeds | R01 1025137124 (remaining seeds in Excel) |

## Source mapping

`CHAOSLSQFwd::maybeSubstituteSource(load_data, true_src, copy_size,
alt_src, alt_size, vaddr)` already implements option A in
`StructMode::FwdSourceSub`. The eligibility is an older SQ entry with data
(a real multiple-candidate forwarding). FW05 needs a dedicated mode/ordinal,
trace registration of the wrong-source copy, and the same consumer-hash
discipline as v3.2.6.

## Next step

Write `docs/superpowers/plans/YYYY-MM-DD-lsu-v327-fw05.md` before code. The
existing `maybeSubstituteSource` hook is the intended implementation point;
do not start from `CHAOSL1DForward`.
