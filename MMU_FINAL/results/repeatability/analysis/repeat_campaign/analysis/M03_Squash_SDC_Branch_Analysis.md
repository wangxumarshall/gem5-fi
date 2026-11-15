# M03 Squash / SDC Branch Analysis

## REP-FINAL-MMU-M03-R01-01 / R01

- Activation: MATCH; Propagation: MATCH; Terminal: MATCH
- Formal terminal SQUASHED → repeat SQUASHED
- Repeat oracle: `W11_RESULT ctx=R01 va=0x4004000000 pid_a=318 pid_b=319 pfn_a=0x83543 pfn_b=0x83542 pagemap=ok marker_a=0xa5 marker_b=0x5a observed=0x5a branch=0 stage=0 b_signal=0 asid_source=trace pin_cpu=cpu0 handshake=ready_rewarm expect=0x5a result=PASS`

## REP-FINAL-MMU-M03-R05-01 / R05

- Activation: MATCH; Propagation: MATCH; Terminal: MATCH
- Formal terminal SDC → repeat SDC
- Repeat oracle: `W11_RESULT ctx=R05 va=0x4005000000 pid_a=318 pid_b=319 pfn_a=0x83543 pfn_b=0x83542 pagemap=ok marker_a=0xa5 marker_b=0x5a observed=0xa5 branch=0 stage=0 b_signal=0 asid_source=trace pin_cpu=cpu0 handshake=ready_rewarm expect=0x5a result=FAIL`

R01-R04 must remain SQUASHED; R05 must remain SDC. No model or fault parameter was changed.
