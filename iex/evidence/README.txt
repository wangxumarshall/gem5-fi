IEX_WHEN_5x3_v3_2026-11-23 delivery
=====================================
Source:  /home/sdc/gem5-fi-IEX/when_5x3_v3
Results: /home/sdc/gem5-fi-IEX/when_5x3_v3/results/IEX_WHEN_5x3_v3_2026-11-23
Gem5:    /home/sdc/gem5-fi-IEX/when_5x3_v3/gem5 (branch when_5x3_v3, commit 1e8214e25b0518836c9778fd710794c023b9ca7b)

Scale: 7 models x 5 contexts x 3 ordinals = 105 Fault runs; 35 controls.
Faults completed: 105, valid injections: 105, FULL trace evidence: 105.
Terminals: {"SDC": 84, "MASKED": 21}.
Controls: 35/35 with N=128 (six contexts N=129 due to one final
speculative target instance; all three ordinals remain committed
episodes), three ordinals distinct, repeat census identical.

Contents
--------
fault_runs.csv            105 authoritative rows (latest attempt per CaseID)
controls.csv              35 Control N/ordinal/census/hash records
injections.csv            exact hook, PC, SeqNum, before/after, guard state
propagation_edges.csv     producer->consumer dynamic tags and read values
lifecycle.csv             issue/execute/writeback/commit/squash ticks
oracle_comparison.csv     selected-slot actual vs independent bigint oracle
failures_and_anomalies.csv  non-zero/missing attempts (kept, not deleted)
attempt_history.csv       every attempt; authoritative flag marks delivery row
evidence_index.json       CaseID -> latest attempt/trace/meta path + SHA256
matrix_status.csv         105-case status matrix
closure.json              G13 closure counts and artifact paths
source.diff               gem5 source changes from the v2 base
cpu_fu_config.txt         serialized O3/FU configuration
reproduce_commands.txt    exact rebuild/run commands
All_Raw_Traces.tar.zst    every raw trace (all attempts), restorable by CaseID
IEX_WHEN_5x3_v3_RESULTS_2026-11-23.xlsx  filled workbook copy

Trace archive path layout:
results/IEX_WHEN_5x3_v3_2026-11-23/runs/<CaseID>/attempt-NNNN/trace.jsonl
results/IEX_WHEN_5x3_v3_2026-11-23/controls/<ControlID>/attempt-NNNN/

Evidence policy
---------------
The classifier uses dynamic trace events only.  Data edges come from
renamed source physical tags and their allocation generation; no edge is
inferred from the final output.  C05 eligibility requires the designed
older CBNZ (PC-filtered) to be unresolved at the hook and to resolve at a
later tick.  C03 is MASKED because one EOR consumes the fault and both
raw and EOR result are overwritten before the only fixed store.
