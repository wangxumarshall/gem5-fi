# M05 Partial Walk-Cache Analysis

## REP-FINAL-MMU-M05-R05-01 / R05

- Activation: MATCH; Propagation: MATCH; Terminal: MATCH
- Formal terminal SDC → repeat SDC
- Repeat oracle: `W13_RESULT ctx=R05 target_va=0x4010000000 target_pfn=0x83575 decoy_va=0x4010200000 decoy_pfn=0x83544 alias_va=0x4010001000 observed=0x51 sentinel=0x7d decoy_sentinel=0x51 branch=0 pagemap=ok pfn_ok=1/1 signal=0 fault_phase=none partial_hit=TRACE_CONFIRMED result=FAIL`

The launch command carries explicit decoy VA 0x4010200000 and table base 0; no live-scan fallback.
