# Agent J — LSU v3.3.2 60-context matrix (A01, A03, FW02, FW05, SQ01, SQ03)

- Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
- Driver: `python3 tools/lsu_v332_matrix.py --models A01,A03,FW02,FW05,SQ01,SQ03 --roles fault,control --contexts 1,2,3,4,5 --out-csv audit_v3_3_2/controls/LSU_Fault_Control_Pair_Final_J.csv` (exit 0, 60 rows, run ~22:12–22:23 CST)
- Binary SHA-256 (all 60 runs): `070d68a688464fa737e6bf102f44a27e911dc29d15142d77c82ec2083115f5ca`
- Sources of truth: `audit_v3_3_2/runs/<model>-R<ctx>-<role>/summary.json`, `pilot_meta.json`, `trace_v31.jsonl`, raw logs. Terminal/oracle are taken from `pilot_meta.classification`; the driver CSV `terminal` column is empty for non-A03 runs because `pilot_meta.json` has no top-level `terminal` field.

## Fault runs (injection_count / terminal / oracle pass)

| Model | R01 | R02 | R03 | R04 | R05 |
|---|---|---|---|---|---|
| A01 | 1 / SDC / False | 1 / SQUASHED / True | 1 / UNRESOLVED / True | 1 / SDC / False | 1 / SDC / False |
| A03 | 20000 / HANG / False | 20000 / HANG / False | 20000 / HANG / False | 20000 / HANG / False | 20000 / HANG / False |
| FW02 | 1 / SDC / False | 1 / SDC / False | 1 / MASKED / True | 1 / SDC / False | 1 / SDC / False |
| FW05 | 1 / SDC / False | 1 / SDC / False | 1 / SDC / False | 1 / SDC / False | 1 / SDC / False |
| SQ01 | 1 / SDC / False | 1 / SDC / False | 1 / SDC / False | 1 / SDC / False | 1 / SDC / False |
| SQ03 | 1 / MASKED / True | 1 / MASKED / True | 1 / MASKED / True | 1 / MASKED / True | 1 / MASKED / True |

### First injection identity (fault runs)

| Run | dyn_inst_seq | PC / VA / addr | key identity fields |
|---|---|---|---|
| A01-R01 | 12978 | pc=-, old_addr=493000 | old_addr=493000 -> new_addr=493008; is_load=1; size 8->8 |
| A01-R02 | 13638 | pc=-, old_addr=493ff8 | old_addr=493ff8 -> new_addr=493ff0; is_load=1; size 8->8 |
| A01-R03 | 14049 | pc=-, old_addr=493040 | old_addr=493040 -> new_addr=493048; is_load=1; size 16->16 |
| A01-R04 | 14719 | pc=-, old_addr=493230 | old_addr=493230 -> new_addr=493238; is_load=1; size 8->8 |
| A01-R05 | 15086 | pc=-, old_addr=493368 | old_addr=493368 -> new_addr=493360; is_load=1; size 8->8 |
| A03-R01 | first_affected seq=12989 | pc=400598, golden_ea=493008 -> actual_ea=493000 | activation tick=15691445;bit=3;mode=a03_bit3_stuck0_load; first affected ordinal=1060 reason=STUCK_APPLIED; log capped at 20000 injections |
| A03-R02 | first_affected seq=13638 | pc=40068c, golden_ea=493ff8 -> actual_ea=493ff0 | activation tick=16150365;bit=3;mode=a03_bit3_stuck0_load; first affected ordinal=1098 reason=STUCK_APPLIED; log capped at 20000 injections |
| A03-R03 | first_affected seq=14594 | pc=4006d0, golden_ea=493208 -> actual_ea=493200 | activation tick=16301670;bit=3;mode=a03_bit3_stuck0_load; first affected ordinal=1171 reason=STUCK_APPLIED; log capped at 20000 injections |
| A03-R04 | first_affected seq=14744 | pc=4006d0, golden_ea=493238 -> actual_ea=493230 | activation tick=16534210;bit=3;mode=a03_bit3_stuck0_load; first affected ordinal=1177 reason=STUCK_APPLIED; log capped at 20000 injections |
| A03-R05 | first_affected seq=15086 | pc=4006d0, golden_ea=493368 -> actual_ea=493360 | activation tick=16612750;bit=3;mode=a03_bit3_stuck0_load; first affected ordinal=1215 reason=STUCK_APPLIED; log capped at 20000 injections |
| FW02-R01 | 12243 | pc=-, 0x4919d0 | forward decision suppressed; load_addr=0x4919d0 (ops: load_seq=12243, store_seq=12241) |
| FW02-R02 | 12365 | pc=-, 0x4919f8 | forward decision suppressed; load_addr=0x4919f8 (ops: load_seq=12365, store_seq=12363) |
| FW02-R03 | 12524 | pc=-, 0x491a58 | forward decision suppressed; load_addr=0x491a58 (ops: load_seq=12524, store_seq=12522) |
| FW02-R04 | 12776 | pc=-, 0x4919c2 | forward decision suppressed; load_addr=0x4919c2 (ops: load_seq=12776, store_seq=12775) |
| FW02-R05 | 13436 | pc=-, 0x4919b0 | forward decision suppressed; load_addr=0x4919b0 (ops: load_seq=13436, store_seq=13435) |
| FW05-R01 | 16084 | pc=0x400564, load_addr=0x4919c8 | load_addr=0x4919c8; true_store_seq=16083; alt_store_seq=16082; selected=alt_store; wrong_source_substitution=1; data_differs=1; addr_unchanged=0 |
| FW05-R02 | 23684 | pc=0x400564, load_addr=0x491a48 | load_addr=0x491a48; true_store_seq=23683; alt_store_seq=23682; selected=alt_store; wrong_source_substitution=1; data_differs=1; addr_unchanged=0 |
| FW05-R03 | 31284 | pc=0x400564, load_addr=0x491ac8 | load_addr=0x491ac8; true_store_seq=31283; alt_store_seq=31282; selected=alt_store; wrong_source_substitution=1; data_differs=1; addr_unchanged=0 |
| FW05-R04 | 38884 | pc=0x400564, load_addr=0x491b48 | load_addr=0x491b48; true_store_seq=38883; alt_store_seq=38882; selected=alt_store; wrong_source_substitution=1; data_differs=1; addr_unchanged=0 |
| FW05-R05 | 46484 | pc=0x400564, load_addr=0x4919c8 | load_addr=0x4919c8; true_store_seq=46483; alt_store_seq=46482; selected=alt_store; wrong_source_substitution=1; data_differs=1; addr_unchanged=0 |
| SQ01-R01 | 13328 | pc=-, addr=0x4919f0 | saved_byte 0x6d->0x65; queue=SQ idx=956 gen=1306 size=8 |
| SQ01-R02 | 15122 | pc=-, addr=0x491ac0 | saved_byte 0x87->0x8f; queue=SQ idx=982 gen=1332 size=8 |
| SQ01-R03 | 16847 | pc=-, addr=0x491b88 | saved_byte 0xa0->0xa8; queue=SQ idx=1007 gen=1357 size=8 |
| SQ01-R04 | 18641 | pc=-, addr=0x491c58 | saved_byte 0xba->0xb2; queue=SQ idx=1033 gen=1383 size=8 |
| SQ01-R05 | 20435 | pc=-, addr=0x491d28 | saved_byte 0xd4->0xdc; queue=SQ idx=1059 gen=1409 size=8 |
| SQ03-R01 | 13328 | pc=0x40053c, store_addr=0x4919f0 | canwb 0->1; stores_to_wb 0->1; store_addr=0x4919f0 size=8; sq_entry=956/1306 |
| SQ03-R02 | 15122 | pc=0x40053c, store_addr=0x491ac0 | canwb 0->1; stores_to_wb 0->1; store_addr=0x491ac0 size=8; sq_entry=982/1332 |
| SQ03-R03 | 16847 | pc=0x40053c, store_addr=0x491b88 | canwb 0->1; stores_to_wb 0->1; store_addr=0x491b88 size=8; sq_entry=1007/1357 |
| SQ03-R04 | 18641 | pc=0x40053c, store_addr=0x491c58 | canwb 0->1; stores_to_wb 0->1; store_addr=0x491c58 size=8; sq_entry=1033/1383 |
| SQ03-R05 | 20435 | pc=0x40053c, store_addr=0x491d28 | canwb 0->1; stores_to_wb 0->1; store_addr=0x491d28 size=8; sq_entry=1059/1409 |

## Controls

- Controls meeting all conditions (injection_count==0, oracle PASS, exit 0, COMPLETE trace, no misfire): **30/30**
- FW02 controls: command has **no injector mount** (only `--chaos_propagation` / `--prop_trace_file`); 5/5 zero injections, oracle PASS.
- A01/A03 controls: `--chaos_addrpath` mounted at `--probability 0.0`; 10/10 zero injections, oracle PASS.
- FW05/SQ01/SQ03 controls: `--chaos_lsqfwd --lsq_struct_mode ...` mounted at `--probability 0.0`; 15/15 zero injections, oracle PASS.
- Every control: `control_misfire=false`, terminal `UNRESOLVED` / reason `NO_INJECTION_EVENT` (honest no-fault baseline, not relabeled).

## Fault terminal tally

SDC 17 (A01×3, FW02×4, FW05×5, SQ01×5) · MASKED 6 (FW02×1, SQ03×5) · SQUASHED 1 (A01 R02) · UNRESOLVED 1 (A01 R03) · HANG 5 (A03, 30 s bound)

## Anomalies / blockers (observed, not inferred)

1. **Driver CSV path bug**: `tools/lsu_v332_matrix.py::write_csv()` opens the module-global `SUMMARY_CSV` instead of its `path` argument, so the run wrote `audit_v3_3_2/controls/LSU_Fault_Control_Pair_Final.csv` despite printing `wrote ..._J.csv`. The real 60-row output was preserved by copying it to `audit_v3_3_2/controls/LSU_Fault_Control_Pair_Final_J.csv`. No source file was edited.
2. **A01-R03-fault is not a clean accept**: gem5 exited 0 and oracle PASSed, but `run_pilot` exited 1 (`accepted=false`) with `UNRESOLVED_NO_REGISTER_WRITEBACK_EVIDENCE`; the fault chain has 9 events but no register writeback. Reported as UNRESOLVED, not MASKED.
3. **A03 faults HANG by construction**: 30 s wall-clock bound, exit 124, `faults_injected: 20000` (log cap, `capped=true`); no trace conversion and no terminal classification — do not relabel as MASKED. First activation/affected events are in each `summary.json.a03`.
4. Driver CSV `terminal` column is empty for all non-A03 runs (pilot_meta stores terminal under `classification.terminal_state`); real terminals above come from that field.

## Machine-readable rows

```json
{
 "A01-R01-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "A01-R01-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "seq": 12978
  },
  "first_injection_detail": "site=lsq_pushRequest_PRE;family=addrpath;is_load=1;old_size=8;new_size=8;old_addr=493000;new_addr=493008",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "A01-R02-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "A01-R02-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "INDIRECT_EVIDENCE",
  "first_injection": {
   "seq": 13638
  },
  "first_injection_detail": "site=lsq_pushRequest_PRE;family=addrpath;is_load=1;old_size=8;new_size=8;old_addr=493ff8;new_addr=493ff0",
  "injection_count": 1,
  "oracle": true,
  "terminal": "SQUASHED",
  "terminal_reason": "TARGET_SQUASHED_NO_COMMIT",
  "timed_out": null
 },
 "A01-R03-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "A01-R03-fault": {
  "a03": null,
  "accepted": false,
  "exit_code": 1,
  "fault_causality": "INDIRECT_EVIDENCE",
  "first_injection": {
   "seq": 14049
  },
  "first_injection_detail": "site=lsq_pushRequest_PRE;family=addrpath;is_load=1;old_size=16;new_size=16;old_addr=493040;new_addr=493048",
  "injection_count": 1,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "terminal_reason": "UNRESOLVED_NO_REGISTER_WRITEBACK_EVIDENCE",
  "timed_out": null
 },
 "A01-R04-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "A01-R04-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "seq": 14719
  },
  "first_injection_detail": "site=lsq_pushRequest_PRE;family=addrpath;is_load=1;old_size=8;new_size=8;old_addr=493230;new_addr=493238",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "A01-R05-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "A01-R05-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "seq": 15086
  },
  "first_injection_detail": "site=lsq_pushRequest_PRE;family=addrpath;is_load=1;old_size=8;new_size=8;old_addr=493368;new_addr=493360",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "A03-R01-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "A03-R01-fault": {
  "a03": {
   "capped": true,
   "first_activation": "A03_ACTIVATION: tick=15691445;bit=3;mode=a03_bit3_stuck0_load",
   "first_affected": "A03_STREAM: event_ordinal=1060;dyn_inst_seq=12989;pc=400598;eligible=1;affected=1;golden_ea=493008;actual_ea=493000;bit=3;reason=STUCK_APPLIED",
   "injections": 20000,
   "last_line": "Tick: 165742115, Site: lsq_pushRequest_PRE, mode=a03_bit3_stuck0_load, old_addr=0x493c88, new_addr=0x493c80, old_size=4, new_size=4, faults_injected: 20000",
   "stream_rows": 113377
  },
  "accepted": null,
  "exit_code": 124,
  "fault_causality": null,
  "first_injection": {},
  "first_injection_detail": null,
  "injection_count": 20000,
  "oracle": false,
  "terminal": "HANG",
  "terminal_reason": null,
  "timed_out": true
 },
 "A03-R02-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "A03-R02-fault": {
  "a03": {
   "capped": true,
   "first_activation": "A03_ACTIVATION: tick=16150365;bit=3;mode=a03_bit3_stuck0_load",
   "first_affected": "A03_STREAM: event_ordinal=1098;dyn_inst_seq=13638;pc=40068c;eligible=1;affected=1;golden_ea=493ff8;actual_ea=493ff0;bit=3;reason=STUCK_APPLIED",
   "injections": 20000,
   "last_line": "Tick: 166034330, Site: lsq_pushRequest_PRE, mode=a03_bit3_stuck0_load, old_addr=0x493c88, new_addr=0x493c80, old_size=4, new_size=4, faults_injected: 20000",
   "stream_rows": 114673
  },
  "accepted": null,
  "exit_code": 124,
  "fault_causality": null,
  "first_injection": {},
  "first_injection_detail": null,
  "injection_count": 20000,
  "oracle": false,
  "terminal": "HANG",
  "terminal_reason": null,
  "timed_out": true
 },
 "A03-R03-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "A03-R03-fault": {
  "a03": {
   "capped": true,
   "first_activation": "A03_ACTIVATION: tick=16301670;bit=3;mode=a03_bit3_stuck0_load",
   "first_affected": "A03_STREAM: event_ordinal=1171;dyn_inst_seq=14594;pc=4006d0;eligible=1;affected=1;golden_ea=493208;actual_ea=493200;bit=3;reason=STUCK_APPLIED",
   "injections": 20000,
   "last_line": "Tick: 166327700, Site: lsq_pushRequest_PRE, mode=a03_bit3_stuck0_load, old_addr=0x493c88, new_addr=0x493c80, old_size=4, new_size=4, faults_injected: 20000",
   "stream_rows": 113494
  },
  "accepted": null,
  "exit_code": 124,
  "fault_causality": null,
  "first_injection": {},
  "first_injection_detail": null,
  "injection_count": 20000,
  "oracle": false,
  "terminal": "HANG",
  "terminal_reason": null,
  "timed_out": true
 },
 "A03-R04-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "A03-R04-fault": {
  "a03": {
   "capped": true,
   "first_activation": "A03_ACTIVATION: tick=16534210;bit=3;mode=a03_bit3_stuck0_load",
   "first_affected": "A03_STREAM: event_ordinal=1177;dyn_inst_seq=14744;pc=4006d0;eligible=1;affected=1;golden_ea=493238;actual_ea=493230;bit=3;reason=STUCK_APPLIED",
   "injections": 20000,
   "last_line": "Tick: 166621070, Site: lsq_pushRequest_PRE, mode=a03_bit3_stuck0_load, old_addr=0x493c88, new_addr=0x493c80, old_size=4, new_size=4, faults_injected: 20000",
   "stream_rows": 115067
  },
  "accepted": null,
  "exit_code": 124,
  "fault_causality": null,
  "first_injection": {},
  "first_injection_detail": null,
  "injection_count": 20000,
  "oracle": false,
  "terminal": "HANG",
  "terminal_reason": null,
  "timed_out": true
 },
 "A03-R05-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "A03-R05-fault": {
  "a03": {
   "capped": true,
   "first_activation": "A03_ACTIVATION: tick=16612750;bit=3;mode=a03_bit3_stuck0_load",
   "first_affected": "A03_STREAM: event_ordinal=1215;dyn_inst_seq=15086;pc=4006d0;eligible=1;affected=1;golden_ea=493368;actual_ea=493360;bit=3;reason=STUCK_APPLIED",
   "injections": 20000,
   "last_line": "Tick: 166913285, Site: lsq_pushRequest_PRE, mode=a03_bit3_stuck0_load, old_addr=0x493c88, new_addr=0x493c80, old_size=4, new_size=4, faults_injected: 20000",
   "stream_rows": 114998
  },
  "accepted": null,
  "exit_code": 124,
  "fault_causality": null,
  "first_injection": {},
  "first_injection_detail": null,
  "injection_count": 20000,
  "oracle": false,
  "terminal": "HANG",
  "terminal_reason": null,
  "timed_out": true
 },
 "FW02-R01-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "FW02-R01-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "seq": 12243
  },
  "first_injection_detail": "site=lsq_fwd_decision;family=addrpath;is_load=1;old_size=8;new_size=8;old_addr=4919d0;new_addr=4919d0",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "FW02-R02-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "FW02-R02-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "seq": 12365
  },
  "first_injection_detail": "site=lsq_fwd_decision;family=addrpath;is_load=1;old_size=8;new_size=8;old_addr=4919f8;new_addr=4919f8",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "FW02-R03-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "FW02-R03-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "seq": 12524
  },
  "first_injection_detail": "site=lsq_fwd_decision;family=addrpath;is_load=1;old_size=8;new_size=8;old_addr=491a58;new_addr=491a58",
  "injection_count": 1,
  "oracle": true,
  "terminal": "MASKED",
  "terminal_reason": "TARGET_COMMITTED_DATA_VALUE_PRESENT",
  "timed_out": null
 },
 "FW02-R04-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "FW02-R04-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "seq": 12776
  },
  "first_injection_detail": "site=lsq_fwd_decision;family=addrpath;is_load=1;old_size=4;new_size=4;old_addr=4919c2;new_addr=4919c2",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "FW02-R05-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "FW02-R05-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "seq": 13436
  },
  "first_injection_detail": "site=lsq_fwd_decision;family=addrpath;is_load=1;old_size=8;new_size=8;old_addr=4919b0;new_addr=4919b0",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "FW05-R01-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "FW05-R01-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "eligible_ordinal": "200",
   "load_seq": "16084",
   "lq_entry_id": "942",
   "seq": 16084
  },
  "first_injection_detail": "site=store->load_forward_decision;family=fw05;model=FW05;definition=FW05-DEF-v1;target_pair_id=FW05-L16084-T16083-A16082-K16884945;load_seq=16084;load_pc=0x400564;true_store_seq=16083;alt_store_seq=16082;true_addr=0x4919c8;alt_addr=0x4919c8;load_addr=0x4919c8;load_size=8;true_store_size=8;alt_store_size=8;true_data_fnv=866b543c5e0028ef;alt_data_fnv=592cd57b595306aa;selected_source=alt_store;wrong_source_substitution=1;data_differs=1;sq_entry_id=1944;sq_entry_generation=2296;lq_entry_id=942;lq_entry_generation=1414;eligible_ordinal=200;eligible_forwarding_pair_ordinal=200;event_ordinal=200;seed=1025137124;address_modified=0;size_modified=0;execution_attempt_id=1;replay_generation=0",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "FW05-R02-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "FW05-R02-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "eligible_ordinal": "600",
   "load_seq": "23684",
   "lq_entry_id": "1342",
   "seq": 23684
  },
  "first_injection_detail": "site=store->load_forward_decision;family=fw05;model=FW05;definition=FW05-DEF-v1;target_pair_id=FW05-L23684-T23683-A23682-K18424945;load_seq=23684;load_pc=0x400564;true_store_seq=23683;alt_store_seq=23682;true_addr=0x491a48;alt_addr=0x491a48;load_addr=0x491a48;load_size=8;true_store_size=8;alt_store_size=8;true_data_fnv=064887667f42724e;alt_data_fnv=608c2596b3b237ab;selected_source=alt_store;wrong_source_substitution=1;data_differs=1;sq_entry_id=3944;sq_entry_generation=4296;lq_entry_id=1342;lq_entry_generation=1814;eligible_ordinal=600;eligible_forwarding_pair_ordinal=600;event_ordinal=600;seed=1653118510;address_modified=0;size_modified=0;execution_attempt_id=1;replay_generation=0",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "FW05-R03-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "FW05-R03-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "eligible_ordinal": "1000",
   "load_seq": "31284",
   "lq_entry_id": "1742",
   "seq": 31284
  },
  "first_injection_detail": "site=store->load_forward_decision;family=fw05;model=FW05;definition=FW05-DEF-v1;target_pair_id=FW05-L31284-T31283-A31282-K19964945;load_seq=31284;load_pc=0x400564;true_store_seq=31283;alt_store_seq=31282;true_addr=0x491ac8;alt_addr=0x491ac8;load_addr=0x491ac8;load_size=8;true_store_size=8;alt_store_size=8;true_data_fnv=8bf4459123a057c9;alt_data_fnv=1b75ccec43c2c813;selected_source=alt_store;wrong_source_substitution=1;data_differs=1;sq_entry_id=5944;sq_entry_generation=6296;lq_entry_id=1742;lq_entry_generation=2214;eligible_ordinal=1000;eligible_forwarding_pair_ordinal=1000;event_ordinal=1000;seed=2442802213;address_modified=0;size_modified=0;execution_attempt_id=1;replay_generation=0",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "FW05-R04-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "FW05-R04-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "eligible_ordinal": "1400",
   "load_seq": "38884",
   "lq_entry_id": "2142",
   "seq": 38884
  },
  "first_injection_detail": "site=store->load_forward_decision;family=fw05;model=FW05;definition=FW05-DEF-v1;target_pair_id=FW05-L38884-T38883-A38882-K21504945;load_seq=38884;load_pc=0x400564;true_store_seq=38883;alt_store_seq=38882;true_addr=0x491b48;alt_addr=0x491b48;load_addr=0x491b48;load_size=8;true_store_size=8;alt_store_size=8;true_data_fnv=62a695d4ab880920;alt_data_fnv=20cd2544bbfdf85b;selected_source=alt_store;wrong_source_substitution=1;data_differs=1;sq_entry_id=7944;sq_entry_generation=8296;lq_entry_id=2142;lq_entry_generation=2614;eligible_ordinal=1400;eligible_forwarding_pair_ordinal=1400;event_ordinal=1400;seed=899944922;address_modified=0;size_modified=0;execution_attempt_id=1;replay_generation=0",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "FW05-R05-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "FW05-R05-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "eligible_ordinal": "1800",
   "load_seq": "46484",
   "lq_entry_id": "2542",
   "seq": 46484
  },
  "first_injection_detail": "site=store->load_forward_decision;family=fw05;model=FW05;definition=FW05-DEF-v1;target_pair_id=FW05-L46484-T46483-A46482-K23044945;load_seq=46484;load_pc=0x400564;true_store_seq=46483;alt_store_seq=46482;true_addr=0x4919c8;alt_addr=0x4919c8;load_addr=0x4919c8;load_size=8;true_store_size=8;alt_store_size=8;true_data_fnv=784348533e526143;alt_data_fnv=1e518ea0775630e3;selected_source=alt_store;wrong_source_substitution=1;data_differs=1;sq_entry_id=9944;sq_entry_generation=10296;lq_entry_id=2542;lq_entry_generation=3014;eligible_ordinal=1800;eligible_forwarding_pair_ordinal=1800;event_ordinal=1800;seed=2836530945;address_modified=0;size_modified=0;execution_attempt_id=1;replay_generation=0",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "SQ01-R01-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "SQ01-R01-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "addr": "0x4919f0",
   "seq": 13328
  },
  "first_injection_detail": "site=lsq_write_sq_entry;mode=sq01_bit3;queue=SQ;index=956;generation=1306;size=8;addr=0x4919f0;old_byte=0x6d;new_byte=0x65;value_changed=1",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "SQ01-R02-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "SQ01-R02-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "addr": "0x491ac0",
   "seq": 15122
  },
  "first_injection_detail": "site=lsq_write_sq_entry;mode=sq01_bit3;queue=SQ;index=982;generation=1332;size=8;addr=0x491ac0;old_byte=0x87;new_byte=0x8f;value_changed=1",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "SQ01-R03-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "SQ01-R03-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "addr": "0x491b88",
   "seq": 16847
  },
  "first_injection_detail": "site=lsq_write_sq_entry;mode=sq01_bit3;queue=SQ;index=1007;generation=1357;size=8;addr=0x491b88;old_byte=0xa0;new_byte=0xa8;value_changed=1",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "SQ01-R04-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "SQ01-R04-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "addr": "0x491c58",
   "seq": 18641
  },
  "first_injection_detail": "site=lsq_write_sq_entry;mode=sq01_bit3;queue=SQ;index=1033;generation=1383;size=8;addr=0x491c58;old_byte=0xba;new_byte=0xb2;value_changed=1",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "SQ01-R05-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "SQ01-R05-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "addr": "0x491d28",
   "seq": 20435
  },
  "first_injection_detail": "site=lsq_write_sq_entry;mode=sq01_bit3;queue=SQ;index=1059;generation=1409;size=8;addr=0x491d28;old_byte=0xd4;new_byte=0xdc;value_changed=1",
  "injection_count": 1,
  "oracle": false,
  "terminal": "SDC",
  "terminal_reason": "ORACLE_FAIL",
  "timed_out": null
 },
 "SQ03-R01-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "SQ03-R01-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "eligible_ordinal": "1021",
   "seq": 13328,
   "store_seq": "13328"
  },
  "first_injection_detail": "site=executeStore_canWB;family=sq03;model=SQ03;store_seq=13328;store_pc=0x40053c;store_addr=0x4919f0;store_size=8;sq_entry_id=956;sq_entry_generation=1306;canwb_before=0;canwb_after=1;stores_to_wb_before=0;stores_to_wb_after=1;inject_tick=16372510;eligible_ordinal=1021;event_ordinal=1021;seed=2214819981;address_modified=0;size_modified=0;data_modified=0",
  "injection_count": 1,
  "oracle": true,
  "terminal": "MASKED",
  "terminal_reason": "STORE_COMMITTED_LANE_CONSUMED_ORACLE_PASS",
  "timed_out": null
 },
 "SQ03-R02-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "SQ03-R02-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "eligible_ordinal": "1047",
   "seq": 15122,
   "store_seq": "15122"
  },
  "first_injection_detail": "site=executeStore_canWB;family=sq03;model=SQ03;store_seq=15122;store_pc=0x40053c;store_addr=0x491ac0;store_size=8;sq_entry_id=982;sq_entry_generation=1332;canwb_before=0;canwb_after=1;stores_to_wb_before=0;stores_to_wb_after=1;inject_tick=17001600;eligible_ordinal=1047;event_ordinal=1047;seed=1486471869;address_modified=0;size_modified=0;data_modified=0",
  "injection_count": 1,
  "oracle": true,
  "terminal": "MASKED",
  "terminal_reason": "STORE_COMMITTED_LANE_CONSUMED_ORACLE_PASS",
  "timed_out": null
 },
 "SQ03-R03-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "SQ03-R03-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "eligible_ordinal": "1072",
   "seq": 16847,
   "store_seq": "16847"
  },
  "first_injection_detail": "site=executeStore_canWB;family=sq03;model=SQ03;store_seq=16847;store_pc=0x40053c;store_addr=0x491b88;store_size=8;sq_entry_id=1007;sq_entry_generation=1357;canwb_before=0;canwb_after=1;stores_to_wb_before=0;stores_to_wb_after=1;inject_tick=17488240;eligible_ordinal=1072;event_ordinal=1072;seed=3102670938;address_modified=0;size_modified=0;data_modified=0",
  "injection_count": 1,
  "oracle": true,
  "terminal": "MASKED",
  "terminal_reason": "STORE_COMMITTED_LANE_CONSUMED_ORACLE_PASS",
  "timed_out": null
 },
 "SQ03-R04-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "SQ03-R04-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "eligible_ordinal": "1098",
   "seq": 18641,
   "store_seq": "18641"
  },
  "first_injection_detail": "site=executeStore_canWB;family=sq03;model=SQ03;store_seq=18641;store_pc=0x40053c;store_addr=0x491c58;store_size=8;sq_entry_id=1033;sq_entry_generation=1383;canwb_before=0;canwb_after=1;stores_to_wb_before=0;stores_to_wb_after=1;inject_tick=17987200;eligible_ordinal=1098;event_ordinal=1098;seed=3974203372;address_modified=0;size_modified=0;data_modified=0",
  "injection_count": 1,
  "oracle": true,
  "terminal": "MASKED",
  "terminal_reason": "STORE_COMMITTED_LANE_CONSUMED_ORACLE_PASS",
  "timed_out": null
 },
 "SQ03-R05-control": {
  "cond_ok": true,
  "control_misfire": false,
  "exit_code": 0,
  "injection_count": 0,
  "oracle": true,
  "terminal": "UNRESOLVED",
  "trace_completeness": "COMPLETE"
 },
 "SQ03-R05-fault": {
  "a03": null,
  "accepted": true,
  "exit_code": 0,
  "fault_causality": "DIRECT_DATAFLOW_EVIDENCE",
  "first_injection": {
   "eligible_ordinal": "1124",
   "seq": 20435,
   "store_seq": "20435"
  },
  "first_injection_detail": "site=executeStore_canWB;family=sq03;model=SQ03;store_seq=20435;store_pc=0x40053c;store_addr=0x491d28;store_size=8;sq_entry_id=1059;sq_entry_generation=1409;canwb_before=0;canwb_after=1;stores_to_wb_before=0;stores_to_wb_after=1;inject_tick=18628225;eligible_ordinal=1124;event_ordinal=1124;seed=729970077;address_modified=0;size_modified=0;data_modified=0",
  "injection_count": 1,
  "oracle": true,
  "terminal": "MASKED",
  "terminal_reason": "STORE_COMMITTED_LANE_CONSUMED_ORACLE_PASS",
  "timed_out": null
 }
}
```
