# R6-A F0 eligible-stream census — 2026-10-28

binary: CHAOS/gem5/build/ARM/gem5.opt sha256 bdf824964e30844f08a35707d105aa27da6fdc92e575dc2742d4075474c8aa75
method: tier=F0, warmup=1, span=1000000 (no fire), propagation off; read CHAOS_LSU_TRIGGER summary
evidence: /home/sdc/gem5-fi-ding/runs/lsu/r6_a_census/<model>_<workload>/run.out

| model | workload | attempted | eligible |
|---|---|---|---|
| A01 | agu_addrmodes | 2777 | 2777 |
| A01 | gap_bfs | 265019 | 265019 |
| A02 | agu_addrmodes | 2777 | 2777 |
| A02 | gap_bfs | 265019 | 265019 |
| A04 | agu_addrmodes | 2800 | 2800 |
| A04 | mini_check | 3207 | 3207 |
| A05 | agu_addrmodes | 2800 | 2800 |
| A08 | agu_addrmodes | 2800 | 2800 |
| A07 | agu_addrmodes | 2795 | 2795 (pre-existing R4-5.8) |
| A07 | sq_forward | 2579 | 2579 (pre-existing R4-5.8) |

These values feed `ADDRPATH_F0_SPAN` (tools/lsu_campaign.py); A 族 F0 现在
参数化为 warmup=1 + span=实测值。A04-F0-W3 seed1 复跑（span 2800）无 EARLY_BIAS。
