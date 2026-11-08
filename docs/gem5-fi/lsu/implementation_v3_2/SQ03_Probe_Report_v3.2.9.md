# SQ03_Propagation_Probe (v3.2.9, exploratory)

Independent IDs `SQ03-PROBE-F0-P00` (control) and `SQ03-PROBE-F0-P01`
(fault); seed 3141592653; ordinal 1; workload `workloads/sq03_probe`
(store to an address, same-address later load, dependent consume, checksum).
Not one of the 60 samples; no formal Excel row was changed.

## Results (final binary d6e60863…)

| Run | injection | `_canWB` tick | store_wb node | actual `store_mem_write` | commit | complete | checksum |
|---|---|---:|---:|---:|---:|---:|---|
| P01 fault | 1 (seq 18, sq 1/gen 1) | 140910 | 140910 | 200970 | 149380 | 201740 | `0x1053baee7edccdb1` |
| P00 control | 0 | — | — | — (store not registered) | — | — | `0x1053baee7edccdb1` |

Both runs: exit 0, no HANG, no watchdog expiry. The probe performs 128
store→same-address-load pairs; the trace carries 136 SQ-forwarding
decisions in both runs, and the multiset
`(load_seq, forward_data_fnv, store_seq)` is **identical** between fault and
control. The application checksum is identical.

## Microarchitectural conclusion

`_canWB` only controls when the committed store is sent to the cache. A
same-address younger load is satisfied by **store-to-load forwarding from the
SQ entry**, whose data is already present; moving the writeback permission
earlier (140910) does not move the cache update (200970) relative to the
loads, and does not change the forwarded bytes. Early writeback permission
therefore does not make data visible earlier to a load and cannot change an
application value through this path. The control's absence of `store_wb` /
`store_mem` nodes is expected: without an injection the store is not
registered as a fault store, so those diagnostic nodes are not emitted; the
forwarding comparison and checksum supply the matched evidence.

No consumer difference, no SDC. This does not invalidate SQ03 as a
timing-only model; it bounds its application-visible effect.
