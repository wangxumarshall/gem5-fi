# A03-R02 Trace Closure — Final Report

**Model:** A03 (persistent stuck-at address family) · **Context:** R02 · **Run:** `A03-R02-fault`
**New binary:** `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd`
**Config:** `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`
**Evidence:** `audit_v3_3_3/trace_closure/runs/A03-R02-fault/`
**Status:** **PASS — COMPLETE_CAUSAL_CHAIN (SDC)**. Not reclassified as SQUASHED; no C++ hook was needed.

## 1. Decision

The earlier `QUALIFIED` was a **parser-anchor defect**, not a missing runtime event.

- The model's `first_affected` record is `event_ordinal=1094 / dyn_inst_seq=13718 / pc=40068c`.
- 13718 is a **speculative instance**; it is squashed at tick 16170770 by `triggering_seq=13717`
  (`squash_cause=unrelated;fault_caused=0`) before any response or writeback. Its trace has only
  seven nodes and no `resp`/`taint_reg`/consumer.
- A03 is a **persistent** stuck-at bit3=0 fault. The first affected load that actually commits is
  **`dyn_inst_seq=13772` (pc=400678, ordinal 1099)**: `resp.data_hex=ab`, `taint_reg x1=ab`,
  `errant_commit commit_seq=6495`, then consumers 13774/13775 feed the wrong value into the FNV
  checksum accumulator.
- The application prints `d48b947fc08d5a75`; the golden value is `728e604ffcec539d`.
  Agent A's offline recomputation reproduced the printed value exactly from the six corrupted bytes
  plus the 32 repeated odd 8-byte blocks, so the SDC is empirical, not inferred.

**The correct terminal is SDC with a complete causal chain, anchored at 13772.** The 13718 squash
is preserved as provenance, not used as the causal anchor.

## 2. Evidence (real output)

```
A03_ACTIVATION: tick=16170385;bit=3;mode=a03_bit3_stuck0_load
A03_STUCK_LIFECYCLE: fault_id=1;bit=3;...;eligible_events=51303;applications=51222;
  already_stuck=81;activation_ordinal=1094;activation_dyn_inst_seq=13718;
  activation_pc=40068c;activation_golden_ea=493ff8
```

13718's complete trace (squashed before response):

```
5332,16169615,0,lq_lifecycle,13718,...,action=alloc
5334,16170385,1,inj,13718,,493ff8,...,old_addr=493ff8;new_addr=493ff0
5335,16170385,1,addr_form,13718,,493ff0,...,old_addr=493ff8;new_addr=493ff0
5337,16170385,1,a03_stream,13718,,493ff0,...,event_ordinal=1094;affected=1;reason=STUCK_APPLIED
5338,16170385,1,mem_req,13718,74,493ff0,...,request_id=74
5339,16170770,0,squash,13718,...,triggering_seq=13717;squash_cause=unrelated;fault_caused=0
5340,16170770,0,lq_lifecycle,13718,...,action=free;reason=squash
```

The real chain (13772):

```
5371,16201570,4,inj,13772,,493019,...,old_addr=493019;new_addr=493011
5373,16201570,4,a03_stream,13772,,493011,...,event_ordinal=1099;affected=1
5374,16201570,4,mem_req,13772,70,493011,...
5410,16214660,4,resp,13772,70,78011,...,data_hex=ab;data_fnv=af64264c86026a4a
5411,16214660,4,taint_reg,13772,70,,53,1,...,arch_reg=1;writeback_value=ab
5419,16215430,0,commit,13772,...,trigger=fault_instruction_commit;pc=400678;commit_seq=6495
5420,16215430,4,errant_commit,13772,...,trigger=faulting_load_commit;commit_seq=6495
5423,16215815,4,consumer,13774,...,pc=40067c;source_event_id=5411;
     consumer_input_value=ab;consumer_output_value=9f278f06cc7314a9
5429,16216970,4,consumer,13775,...,pc=400680;source_event_id=5423
```

Re-graded result on the new run:

```
$ python3 tools/lsu_v333_qualified.py A03 audit_v3_3_3/trace_closure/runs/A03-R02-fault
status  PASS
missing []
terminal APPLICATION_CHECKSUM;ORACLE_FAIL_SDC;POST_ORACLE_INTERNAL_WATCHDOG
anchor 13772 400678 ERRANT_COMMIT_AFTER_UNRELATED_SQUASH
load_result data_hex=ab;data_fnv=af64264c86026a4a;request_id=70
writeback arch_reg=1;phys_reg=53;writeback_value_fnv=5da39ae7a43fa14e;writeback_value=ab
consumer dyn_inst_seq=13775;pc=400680;src_idx=1;commit_seq=6498
```

The new 22-run pilot reproduced the old terminal exactly: `checksum=d48b947fc08d5a75`,
`terminal=SDC`, `stream_rows=51303`, `affected_rows=51222`. The Control run (`probability=0`)
has `checksum=728e604ffcec539d`, `ORACLE_PASS`, `injection_count=0`.

## 3. Change made

`tools/lsu_v333_qualified.py`:

- `_scan_prop_trace()` now retains `errant_commit`, `squash` and the RP01 flush records.
- `_a03()` first anchors on the model's first affected seq. If that seq has no `resp`, it re-anchors
  on the run's `errant_commit.dyn_inst_seq` (13772) and re-scans. The original 13718 row and its
  squash record are kept in `evidence.first_affected_squash`.

**No C++ change; no binary impact for A03.** Behavior, seed, ordinal and checksum are unchanged.

## 4. Residual uncertainty (honest)

1. The identity of `triggering_seq=13717` is not recorded in prop_trace; the "loop branch
   mispredict" reading is a strong inference from control flow and the strict `seq-1` squash
   pattern, not a directly recorded PC.
2. The post-oracle `POST_ORACLE_SIM_HANG` correlates with the atomic-lock load at `pc=401a04`
   having its bit3 cleared, but the checksum was already written before the hang; this does not
   affect the SDC terminal.
3. The offline recomputation proves the observed corruption set **can** explain the checksum; it
   cannot prove it is the unique possible explanation.
