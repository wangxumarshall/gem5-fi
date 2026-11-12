# Agent D — Causal Propagation & Oracle Audit (LSU v3.3.3)

**Scope:** all 12 LSU models × R01–R05 = 60 contexts. Verify the chain
Injection → Activation → First Divergence → Downstream State → Consumer →
Commit/Squash/Replay/Recovery → Application Oracle / Valid Terminal.

**Mode:** read-only. No source/config/workload/tool/Excel/audit_v3_3_2 edits.
No gem5/pilot runs. Only this file was written. Scratch parsing scripts live
under `/tmp/agentD_*.py`.

## 0. Provenance and evidence base

| Item | Value |
|---|---|
| Worktree | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12` |
| Git HEAD (verified live) | `3097ad82e7066f18fc35cf64dcb612a05c1fc021` |
| Binary in every `command.txt` | `build/ARM/gem5.opt`, SHA256 `070d68a6…115f5ca` |
| Run evidence root | `AUD/runs/<MODEL>-R<NN>-{fault,control}/` |
| Analysis tables compared | `AUD/propagation/LSU_60Context_Causal_Propagation_Final.csv`, `AUD/LSU_60Context_Final_Readiness_Matrix.csv`, `AUD/controls/LSU_Fault_Control_Pair_Final.csv`, `AUD/roi/LSU_60Context_ROI_Percentile_Mapping.csv`, `AUD/roi/LSU_60Context_Distinctness_Audit.csv` |

Path abbreviations used in the tables (all resolve under the absolute base
above):

```
AUD = /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/audit_v3_3_2
R   = AUD/runs
F   = R/<MODEL>-R<NN>-fault
C   = R/<MODEL>-R<NN>-control
```

Every fault run's evidence was parsed directly (`trace_v31.jsonl`,
`prop_trace.csv.gz`, `summary.json`, `pilot_meta.json`, `oracle.log`,
`addrpath_injections.log`, `lsq_fwd_injections.log`, `md04_injections.log`,
`lq04_injections.log`, `l1d_fwd_injections.log`, `stdout.log`, `stderr.log`).
Control runs were parsed for every context (60/60) to confirm the
fault/control oracle pair.

### Raw artifact health (verified)

| Run family | trace_v31.jsonl | prop_trace.csv.gz | stats.txt | oracle.log |
|---|---|---|---|---|
| A01, FW02, FW05, SQ01, SQ03, SP05, DA04, LP01, MD04, LQ04 (50 runs) | present, parses, one summary record | present, gzip-complete | non-empty | present |
| A03 (5 runs) | **absent** (conversion skipped) | present but **truncated gzip** (`EOFError`), 1.48–1.50 M rows read | **0 bytes** | **absent** |
| RP01 (5 runs) | **absent** | present but **truncated gzip** (`EOFError`), 5.3–6.1 k rows read | **0 bytes in all 5 fault runs**; non-empty in controls (258,195 B) | **absent** |

### Headline result versus the analysis tables

Pipeline labels (propagation CSV / readiness matrix / control pairs):
**SDC 36, MASKED 12, HANG_TIMEOUT 5, HANG_WATCHDOG 5, SQUASHED 1,
UNRESOLVED 1.**

Raw-artifact result after this audit:

- **5 A03 rows are wrong.** Every A03 fault run printed its single final
  workload checksum (`agu_addrmodes.c:70-71`, bare 16 hex digits via
  `put_hex`) and all five differ from golden `728e604ffcec539d`. The raw
  application oracle is therefore **FAIL in 5/5**, i.e. **SDC**, not
  "NO_CHECKSUM_ON_PARTIAL_TRACE / HANG_TIMEOUT" (see D-01/D-12).
- **1 A01 row (R03) is mislabelled.** `a01_ea_discarded` records
  `applied_to_request=0;discard_reason=saved_request_reuse`; the response is
  byte-identical to `a01_golden_resp`. The fault never entered the memory
  request, so `UNRESOLVED_NO_REGISTER_WRITEBACK_EVIDENCE` is a misleading
  reason for an **INJECTION_NOT_ACTIVATED** outcome (D-03).
- **1 A01 row (R02, SQUASHED) is causally unsupported.** The only squash
  record says `squash_cause=unrelated; fault_caused=0` (D-07).
- **All 60 controls pass the oracle** (golden checksum), including the
  controls paired to every SDC context. `ControlProof=INJECTOR_ABSENT` is
  nevertheless wrong for 35 of them (D-10).

Net accounting at the level the raw artifacts permit:

- **36 SDC rows** are direct-dataflow supported and paired with a PASSing
  control.
- **9 of the 12 MASKED rows** are direct (LQ04 ×5 lifetime-restored, SQ03
  R01/R03/R04/R05 visibility-shift); **3 MASKED rows** are QUALIFIED
  (FW02 R03 value-identity, MD04 R01 inert-after-completion, SQ03 R02
  lifecycle-only) and must record their masking mechanism.
- **5 A03 rows** should change from HANG_TIMEOUT / NO_CHECKSUM to **SDC**
  (chain QUALIFIED because the trace is partial).
- **1 A01 SQUASHED row (R02)** must be qualified as an unrelated squash.
- **1 A01 UNRESOLVED row (R03)** should become INJECTION_NOT_ACTIVATED.
- **5 RP01 HANG_WATCHDOG rows** are supported by the raw in-simulator
  watchdog fatal, with the fixed-deadline/no-oracle caveat.

Sum: 36 + 9 + 3 + 5 + 1 + 1 + 5 = 60.

## 1. The 60-row causal table

Legend: **Inj** = injection evidence file/event that carries the target
identity; **Act** = activation / first attributable microarchitectural change;
**Div** = first divergence evidence; **Cons** = consumer evidence;
**C/S/R** = commit / squash / replay / recovery evidence; **Term** =
`pipeline-label → raw-artifact verdict`; **Oracle** = `oracle.log`
(expected vs got); **Chain** = YES / NO / QUALIFIED.

All paths are relative to `AUD` above (prefix `runs/`).

| # | Model | Ctx | Inj evidence | Act | Div | Cons | C/S/R | Term (pipeline → raw) | Oracle (oracle.log) | Chain | Defects |
|---|---|---|---|---|---|---|---|---|---|---|---|
|1|A01|R01|`runs/A01-R01-fault/trace_v31.jsonl` injection ptag=1 seq=12978 pc=400598 EA 0x493000→0x493008|`a01_ea` same tick 15691445|`a01_ea` (EA delta, bit3)|`a01_consumed` consumer_seq=12980 + 386 `consumer_commit`|`commit` commit_seq=6196 + `errant_commit` ptag=1|SDC → **SDC**|FAIL `7d6b7a7f8fd106b8` vs `728e604ffcec539d`|YES|D-06,D-07,D-16|
|2|A01|R02|same file seq=13638 pc=40068c EA 0x493ff8→0x493ff0|`a01_ea` tick 16150365|`a01_ea`; **no memory_response**|none (0 consumer commits)|`squash` tick 16150750, `squash_cause=unrelated;fault_caused=0`|SQUASHED → **SQUASHED_UNRELATED** (qualified)|PASS `728e604f…`|QUALIFIED|D-07,D-08|
|3|A01|R03|same file seq=14049 pc=4006a8 EA 0x493040→0x493048|`a01_ea` tick 16301670|`a01_ea_discarded applied_to_request=0;discard_reason=saved_request_reuse`; `a01_golden_resp` fnv=`a80414c2fc53631a` == `memory_response`|none (0)|`commit` commit_seq=6578 (golden data)|UNRESOLVED → **INJECTION_NOT_ACTIVATED**|PASS `728e604f…`|NO|D-03,D-04,D-11|
|4|A01|R04|same file seq=14719 pc=4006d0 EA 0x493230→0x493238|`a01_ea` tick 16534210|`a01_ea` + `memory_response` PA=0x78238 fnv=`6bb6e4d81e02ed4a`|`a01_consumed` consumer_seq=14721 + 260 `consumer_commit`|`commit` + `errant_commit`|SDC → **SDC**|FAIL `d395ca1ef3beedf2`|YES|D-06,D-16|
|5|A01|R05|same file seq=15086 pc=4006d0 EA 0x493368→0x493360|`a01_ea` tick 16612750|`a01_ea` + `memory_response` PA=0x78360 fnv=`a45ae217065c5385`|`a01_consumed` consumer_seq=15088 + 182 `consumer_commit`|`commit` + `errant_commit`|SDC → **SDC**|FAIL `d88663f985ee3f60`|YES|D-06,D-16|
|6|A03|R01|`runs/A03-R01-fault/addrpath_injections.log` `A03_ACTIVATION tick=15691445`; selected ordinal 1059|`a03_ea`/`inj` at first affected ordinal 1060, seq=12989|`A03_STREAM …golden_ea=493008;actual_ea=493000`; prop_trace `inj→addr_form→a03_stream→mem_req→resp(pa=78000,data=0010000000000000)→taint_reg→commit→errant_commit`|447 `consumer` rows in prop_trace|`commit` + 1 `errant_commit` (prop_trace); no trace_v31|HANG_TIMEOUT → **SDC (oracle FAIL); trace/harness incomplete**|**stdout checksum `1fd794b8489219e1` ≠ `728e604ffcec539d`; control = `728e604f…`**|QUALIFIED|D-01,D-12,D-14,D-17|
|7|A03|R02|same log, activation tick 16150365; selected 1098|first affected ordinal 1098 seq=13638|`A03_STREAM golden=493ff8 actual=493ff0`|consumer rows present|no trace_v31|HANG_TIMEOUT → **SDC (oracle FAIL)**|stdout `9fc828ecfead80f9` ≠ golden|QUALIFIED|D-01,D-12,D-17|
|8|A03|R03|activation tick 16301670; selected 1137|first affected ordinal **1171** seq=14594 (selected 1137 was ALREADY_STUCK)|`A03_STREAM golden=493208 actual=493200`|consumer rows present|no trace_v31|HANG_TIMEOUT → **SDC (oracle FAIL)**|stdout `bfccf156021968dd` ≠ golden|QUALIFIED|D-01,D-12,D-14,D-17|
|9|A03|R04|activation tick 16534210; selected 1176|first affected ordinal **1177** seq=14744|`A03_STREAM golden=493238 actual=493230`|consumer rows present|no trace_v31|HANG_TIMEOUT → **SDC (oracle FAIL)**|stdout `191a781887e50cec` ≠ golden|QUALIFIED|D-01,D-12,D-14,D-17|
|10|A03|R05|activation tick 16612750; selected 1215|first affected ordinal 1215 seq=15086|`A03_STREAM golden=493368 actual=493360`|consumer rows present|no trace_v31|HANG_TIMEOUT → **SDC (oracle FAIL)**|stdout `20057ce453d4f1e9` ≠ golden|QUALIFIED|D-01,D-12,D-17|
|11|FW02|R01|`runs/FW02-R01-fault/trace_v31.jsonl` injection ptag=1 seq=12243 vaddr=0x4919d0|`fw02_decision normal_decision=forwarded fault_decision=suppressed memory_path=1`|`forwarding_decision decision=suppressed forward_data_hex=null`|332 `consumer_commit`|`commit`+`errant_commit`; writeback fnv=`a8c7f832281a39c5` (stale zero)|SDC → **SDC**|FAIL `676dff1818cbded5` vs `1f4cbf14327717df`|YES|D-06|
|12|FW02|R02|same file seq=12479 vaddr=0x491a30|`fw02_decision suppressed` tick 15448510|`forwarding_decision suppressed`|308 `consumer_commit`|`commit`+`errant_commit`|SDC → **SDC**|FAIL `29b16643211339f1`|YES|D-06|
|13|FW02|R03|same file seq=12587 vaddr=0x491a90|`fw02_decision suppressed` tick 15492785|`forwarding_decision decision=suppressed **but** forward_data_hex=null and memory path returns store data `b2a73c741d213d8a` = `store_data_fnv`|284 `consumer_commit`|`commit`+`errant_commit`; writeback = correct store value|MASKED → **MASKED (value preserved by alternate path)**|PASS `1f4cbf14327717df`|QUALIFIED|D-08|
|14|FW02|R04|same file seq=13344 pc=400620 vaddr=0x4919c0|`fw02_decision suppressed`|`forwarding_decision suppressed`; memory fnv=`2b4259dc0383ac71`|250 `consumer_commit`|`commit`+`errant_commit`|SDC → **SDC**|FAIL `5f1fdfa8a4f1fd1f`|YES|D-06|
|15|FW02|R05|same file seq=13572 pc=400658 vaddr=0x4919e8|`fw02_decision suppressed`|`forwarding_decision suppressed`; memory fnv=`61ed996654de3fb6`|222 `consumer_commit`|`commit`+`errant_commit`|SDC → **SDC**|FAIL `c1474304e3fb580f`|YES|D-06|
|16|FW05|R01|`runs/FW05-R01-fault/trace_v31.jsonl` injection ptag=1 seq=16084 lq=942 sq=1944 ord=200; `true_store_seq=16083 alt_store_seq=16082; true_data_fnv=866b543c5e0028ef; alt_data_fnv=592cd57b595306aa; selected_source=alt_store`|`forwarding_decision forward_data_hex=2748444444444444` (alt store data)|`register_writeback writeback_value_fnv=592cd57b595306aa` (alt), `value_matches_payload=1`|1803 `consumer_commit` (pc 400568)|`commit`+`errant_commit`; later `fw05_reload` seq=50952 reads `af647b4c8602fab9` (`reads_true_store=0;reads_alt_store=0`)|SDC → **SDC**|FAIL `549c9e0347adad9f` vs `67afad307642983e`|YES|D-06,D-07|
|17|FW05|R02|same file seq=23684 lq=1342 sq=3944 ord=600|alt store selected|writeback fnv=`608c2596b3b237ab`|1403 consumers|commit+errant; reload 51720|SDC → **SDC**|FAIL `549c9e0347ada27f`|YES|D-07|
|18|FW05|R03|same file seq=31284 lq=1742 sq=5944 ord=1000|alt store selected|writeback fnv=`1b75ccec43c2c813`|1003 consumers|commit+errant; reload 52488|SDC → **SDC**|FAIL `549c9e0347ada75f`|YES|D-07|
|19|FW05|R04|same file seq=38884 lq=2142 sq=7944 ord=1400|alt store selected|writeback fnv=`20cd2544bbfdf85b`|603 consumers|commit+errant; reload 53256|SDC → **SDC**|FAIL `549c9e0347ada43f`|YES|D-07|
|20|FW05|R05|same file seq=46484 lq=2542 sq=9944 ord=1800|alt store selected|writeback fnv=`1e518ea0775630e3`|203 consumers|commit+errant; reload 50952|SDC → **SDC**|FAIL `549c9e0347adb91f`|YES|D-07|
|21|SQ01|R01|`runs/SQ01-R01-fault/trace_v31.jsonl` injection ptag=1 seq=13328 sq=956; `mode=sq01_bit3 old_byte=0x6d new_byte=0x65 value_changed=1`|`store_writeback data_hex=657b78717e6b7d7f`|`sq01_chain data_before=0x6d data_after=0x65 data_diverged=1`; `store_mem_write`; reload 13330 hash `21d267b2c8b57721`|`sq01_chain consumer_seq=13333 consumer_hash=21d267…`; 2039 `consumer_commit`|store `commit`; reload `errant_commit`; `chain_verdict=COMPLETE_CHAIN`|SDC → **SDC**|FAIL `7927a4e45a3271dc` vs `7df5034c23f3e703`|YES|D-06|
|22|SQ01|R02|same file seq=15122 sq=982; 0x87→0x8f|store_writeback data reflects 0x8f|`sq01_chain data_diverged=1`; reload 15124 `d4e59c4d90e5da05`|consumer 15127 `d4e59c4d…`; 1597 commits|commit+errant; COMPLETE_CHAIN|SDC → **SDC**|FAIL `580f7a29038389ac`|YES|D-06|
|23|SQ01|R03|same file seq=16847 sq=1007; 0xa0→0xa8|store_writeback data reflects 0xa8|reload 16849 `336b5d682cbd2549`|consumer 16852; 1172 commits|commit+errant; COMPLETE_CHAIN|SDC → **SDC**|FAIL `a372640bc071881c`|YES|D-06|
|24|SQ01|R04|same file seq=18641 sq=1033; 0xba→0xb2|store_writeback data reflects 0xb2|reload 18643 `e0a15931b120dcb5`|consumer 18646; 730 commits|commit+errant; COMPLETE_CHAIN|SDC → **SDC**|FAIL `406db02f8dc2912c`|YES|D-06|
|25|SQ01|R05|same file seq=20435 sq=1059; 0xd4→0xdc|store_writeback data reflects 0xdc|reload 20437 `4cd11d8e73a6f3e1`|consumer 20440; 288 commits|commit+errant; COMPLETE_CHAIN|SDC → **SDC**|FAIL `1aea82f645a9ac9c`|YES|D-06|
|26|SQ03|R01|`runs/SQ03-R01-fault/trace_v31.jsonl` injection ptag=1 seq=13328 sq=956 `canwb_before=0 canwb_after=1`|`store_writeback` at inject tick 16372510; `sq03_complete` 16373280|`sq03_effect visible_before_commit=1 effect_outcome=CHAIN_VISIBILITY_MOVED`; reload 13330 `b6180e0c195fd2e9`|1883 `consumer_commit`|store `commit` 16376745; reload `errant_commit`|MASKED → **MASKED (visibility shift)**|PASS `7df5034c23f3e703`|YES|D-08,D-13|
|27|SQ03|R02|same file seq=15122 sq=982 canwb 0→1|store_writeback at 17001600|`sq03_effect visible_before_commit=0 effect_outcome=LIFECYCLE_ONLY`; reload `9f995d89be67e92d`|1467 commits|commit+errant|MASKED → **MASKED (lifecycle only)**|PASS `7df5034c…`|QUALIFIED|D-08,D-13|
|28|SQ03|R03|same file seq=16847 sq=1007|store_writeback at 17488240|`visible_before_commit=1 CHAIN_VISIBILITY_MOVED`; reload `fde383c67ac034f1`|1067 commits|commit+errant|MASKED → **MASKED (visibility shift)**|PASS|YES|D-13|
|29|SQ03|R04|same file seq=18641 sq=1033|store_writeback at 17987200|`visible_before_commit=1`; reload `aa2be3d3d60e3c9d`|651 commits|commit+errant|MASKED → **MASKED (visibility shift)**|PASS|YES|D-13|
|30|SQ03|R05|same file seq=20435 sq=1059|store_writeback at 18628225|`visible_before_commit=1`; reload `c7d78aff5e06edf9`|235 commits|commit+errant|MASKED → **MASKED (visibility shift)**|PASS|YES|D-13|
|31|SP05|R01|`runs/SP05-R01-fault/trace_v31.jsonl` injection ptag=1 seq=13328 sq=956 `site=writebackStores_prematureComplete old=0 new=1`|`sp05_complete` same tick 16377515|`sp05_stage write_skipped=1 drain_tick=0 store_data_fnv=null reload_data_hash=a8c7f832281a39c5 stage_outcome=RELOAD_UNVERIFIABLE`|2039 `consumer_commit`|**no `commit` node, no `store_writeback`**; reload `errant_commit` 16380980|SDC → **SDC (data unverifiable)**|FAIL `c7a1b3a591c68328` vs `7df5034c23f3e703`|QUALIFIED|D-09|
|32|SP05|R02|same file seq=15122 sq=982|sp05_complete 17006605|write_skipped=1 store_data_fnv=null reload=a8c7…|1597 commits|no commit; errant|SDC → **SDC (data unverifiable)**|FAIL `34890178967da568`|QUALIFIED|D-09|
|33|SP05|R03|same file seq=16847 sq=1007|sp05_complete 17493245|write_skipped=1 store_data_fnv=null|1172 commits|no commit; errant|SDC → **SDC (data unverifiable)**|FAIL `225c6839dd319a5c`|QUALIFIED|D-09|
|34|SP05|R04|same file seq=18641 sq=1033|sp05_complete 17992205|write_skipped=1 store_data_fnv=null|730 commits|no commit; errant|SDC → **SDC (data unverifiable)**|FAIL `d42d86ee46895884`|QUALIFIED|D-09|
|35|SP05|R05|same file seq=20435 sq=1059|sp05_complete 18633230|write_skipped=1 store_data_fnv=null|288 commits|no commit; errant|SDC → **SDC (data unverifiable)**|FAIL `c6e1c98b1480efd4`|QUALIFIED|D-09|
|36|DA04|R01|`runs/DA04-R01-fault/trace_v31.jsonl` injection ptag=1 seq=14320 sq=1563 `site=lsq_pushRequest family=byte_enable old_be=0xf new_be=0xe addr=0x491b29 store_data_hex=867c1a0a`|`store_writeback be_mask=0xe data_hex=867c1a0a` (byte0 dropped)|`store_mem_write`; first reload pa=0x76b29 seq=19698 data `5d43c378a3361260`|8299 `consumer_commit`; second reload seq=27626 pa=0x76b29 `af64184c86025280`|store `commit` 17107090; reload `errant_commit` 17956015|SDC → **SDC**|FAIL `3e59e830cae2994d` vs `3f89eab79392ce69`|YES|D-06|
|37|DA04|R02|same file seq=15345 sq=1768 be 0xf→0xe addr=0x491e5d|store_writeback be_mask=0xe|reload 20723 `96452275ee07f707`|6454 commits|commit+errant|SDC → **SDC**|FAIL `0662cfc41d9f69c5`|YES|D-06|
|38|DA04|R03|same file seq=16365 sq=1972 be 0xf→0xe addr=0x49218d|store_writeback be_mask=0xe|reload 21743 `58f6a775cb1eca8b`|4618 commits|commit+errant|SDC → **SDC**|FAIL `438883f08de29ebd`|YES|D-06|
|39|DA04|R04|same file seq=17390 sq=2177 be 0xf→0xe addr=0x4924c1|store_writeback be_mask=0xe|reload 22768 `3f2e4378011b2ad8`|2773 commits|commit+errant|SDC → **SDC**|FAIL `b3509db52b9c9bb1`|YES|D-06|
|40|DA04|R05|same file seq=18415 sq=2382 be 0xf→0xe addr=0x4927f5|store_writeback be_mask=0xe|reload 23793 `6f86377547052c04`|928 commits|commit+errant|SDC → **SDC**|FAIL `ceb55fc389a4e601`|YES|D-06|
|41|LP01|R01|`runs/LP01-R01-fault/trace_v31.jsonl` injection ptag=1 seq=34741 pc=0x400588 lq=2407 `site=LSQUnit::completeDataAccess byte0_before=0x27 byte0_after=0x2f mask=0x8`|`memory_response data_hex=2f` (corrupted)|`register_writeback writeback_value=2f payload_fnv=af63a24c860189fe hash_basis=regval_extension`|29956 `consumer_commit` (pc 40058c/400590)|`commit`+`errant_commit` 22479380|SDC → **SDC**|FAIL `45692737702410c6` vs `99c106541150be0e`|YES|D-06,D-07|
|42|LP01|R02|same file seq=54709 lq=5735 byte0 0x42→0x4a|memory_response 0x4a|writeback fnv `9d4580cf5145a74f`|23300 consumers|commit+errant|SDC → **SDC**|FAIL `2403e0e3d8fa2df6`|YES|D-07|
|43|LP01|R03|same file seq=74677 lq=9063 byte0 0x5c→0x54|memory_response 0x54|writeback fnv `db3b0ee167243b91`|16644 consumers|commit+errant|SDC → **SDC**|FAIL `a1438ad1e689f106`|YES|D-07|
|44|LP01|R04|same file seq=94645 lq=12391 byte0 0x76→0x7e|memory_response 0x7e|writeback fnv `31adf41a7693dcbb`|9988 consumers|commit+errant|SDC → **SDC**|FAIL `1d4bc99bd20fe5d6`|YES|D-07|
|45|LP01|R05|same file seq=114613 lq=15719 byte0 0x90→0x98|memory_response 0x98|writeback fnv `dae2590a62e3d5d`|3332 consumers|commit+errant|SDC → **SDC**|FAIL `3eef05b0e0f2d1f6`|YES|D-07|
|46|MD04|R01|`runs/MD04-R01-fault/trace_v31.jsonl` injection ptag=1 seq=125104 store_seq=125103 `site=LSQUnit::checkViolations load_complete=1`|violation suppression; `register_writeback value=0 fnv=a8c7f832281a39c5 source_value_hash=null late_binding=1`|no `memory_response`; no store data in trace|6643 `consumer_commit` (pc 4005f0…)|`commit`+`errant_commit`|MASKED → **MASKED_INERT_COMPLETED_LOAD** (qualified)|PASS `22be5ae3364d0c9f`|QUALIFIED|D-08,D-18|
|47|MD04|R02|same file seq=141725 store_seq=141724 `load_addr=0x494990 store_addr=0x494994 load_complete=0`|violation suppression|`memory_response data_hex=0001020304050607`; writeback same|5107 commits (pc 4006a8…)|commit+errant|SDC → **SDC**|FAIL `b828f386364d0c9f`|YES|D-18|
|48|MD04|R03|same file seq=147152 store_seq=147151 load_complete=0|violation suppression|`memory_response data_fnv=a8c7f832281a39c5` (stale zero)|4599 commits|commit+errant|SDC → **SDC**|FAIL `52ad1266adaca05a`|YES|D-18|
|49|MD04|R04|same file seq=171530 store_seq=171529 load_complete=0|violation suppression|`memory_response a8c7…`|2555 commits|commit+errant|SDC → **SDC**|FAIL `ace925b2aa5f41e2`|YES|D-18|
|50|MD04|R05|same file seq=188215 store_seq=188213 load 16B vs store 8B, load_complete=0|violation suppression|`memory_response c764b9d990f3b283`; **two** `register_writeback` (`f3189772d9a6ea7a`, `21eab9b7d8d02d14`)|1025 commits|commit+errant|SDC → **SDC**|FAIL `e92c4d2296d3e7ca`|YES (2nd writeback needs replay attribution)|D-06,D-18|
|51|LQ04|R01|`runs/LQ04-R01-fault/trace_v31.jsonl` injection ptag=1 seq=3 pc=0x400338 lq=1 `site=executeLoad_post valid_before=1 valid_after=0 request_before=1 request_after=0 data_unchanged=1 no_pop=1 no_reuse=1`|`memory_response entry_valid_at_response=0 entry_request_at_response=0 data_unchanged=1`|same (LQ-entry visibility anomaly)|326 `consumer_commit`|`commit`; `lq_lifecycle action=restore reason=commit`|MASKED → **MASKED (lifetime restored at commit)**|PASS `b097eb83f71545cb`|YES|D-06,D-12|
|52|LQ04|R02|same file seq=4 lq=2 valid 1→0 request 1→0|memory_response entry_valid=0|visibility anomaly|327 commits|commit+restore|MASKED → **MASKED**|PASS|YES|D-06|
|53|LQ04|R03|same file seq=5 lq=3|memory_response entry_valid=0|visibility anomaly|326 commits|commit+restore|MASKED → **MASKED**|PASS|YES|D-06|
|54|LQ04|R04|same file seq=6 lq=4|memory_response entry_valid=0|visibility anomaly|326 commits|commit+restore|MASKED → **MASKED**|PASS|YES|D-06|
|55|LQ04|R05|same file seq=7 lq=5|memory_response entry_valid=0|visibility anomaly|327 commits|commit+restore|MASKED → **MASKED**|PASS|YES|D-06|
|56|RP01|R01|`runs/RP01-R01-fault/lsq_fwd_injections.log` `RP01_SKIP_REPLAY ordinal=26 load_seq=16293 load_pc=4195680 lq_idx=774 lq_gen=1283 store_seq=16292 replay_gen_pre=0 replay_gen_post=1 in_instsToReplay_pre=0 in_instsToReplay_post=0 tick=16967335`|skip of the rescheduleMemInst call; `in_instsToReplay_post` 1→0 vs ordinals 1–25|same skip line; stdout has no further `RP01_ELIGIBLE`|none (no architectural consumer; workload never completes)|`CHAOS_RP01_WATCHDOG_EXPIRED …tick=7700000000 injected=1 eligible=26` (`stderr.log`, fatal; `CHAOSLSQFwd.cc:620`)|HANG_WATCHDOG → **HANG_WATCHDOG (fatal watchdog abort)**; summary.json says CRASH|no checksum (control `f3b1c554273d23f7`)|YES|D-02,D-17,D-23|
|57|RP01|R02|same log ordinal=77 load_seq=23229 lq=825 gen=1334 store=23228|in_instsToReplay_post 1→0|same|none|watchdog tick=7700000000 eligible=77 fatal|HANG_WATCHDOG → **HANG_WATCHDOG**|no checksum|YES|D-02,D-17|
|58|RP01|R03|ordinal=128 load_seq=30165 lq=876 gen=1385 store=30164|in_instsToReplay_post 1→0|same|none|watchdog eligible=128 fatal|HANG_WATCHDOG → **HANG_WATCHDOG**|no checksum|YES|D-02,D-17|
|59|RP01|R04|ordinal=179 load_seq=37101 lq=927 gen=1436 store=37100|in_instsToReplay_post 1→0|same|none|watchdog eligible=179 fatal|HANG_WATCHDOG → **HANG_WATCHDOG**|no checksum|YES|D-02,D-17|
|60|RP01|R05|ordinal=230 load_seq=44037 lq=978 gen=1487 store=44036|in_instsToReplay_post 1→0|same|none|watchdog eligible=230 fatal|HANG_WATCHDOG → **HANG_WATCHDOG**|no checksum|YES|D-02,D-17|

### Chain-closure summary

| Chain | Count | Contexts |
|---|---|---|
| YES | 45 | A01 R01,R04,R05; FW02 R01,R02,R04,R05; FW05 ×5; SQ01 ×5; SQ03 R01,R03,R04,R05; DA04 ×5; LP01 ×5; MD04 R02,R03,R04,R05; LQ04 ×5; RP01 ×5 |
| QUALIFIED | 14 | A01 R02; A03 ×5; FW02 R03; SQ03 R02; SP05 ×5; MD04 R01 |
| NO | 1 | A01 R03 (injection never applied) |
| TOTAL | 60 | 45 + 14 + 1 = 60 (the per-row "Chain" column is authoritative) |

## 2. Per-terminal-state audits

### 2.1 SDC — 36 pipeline-labelled + 5 A03 recovered = 41 raw

**What must hold:** an independent application-oracle FAIL (checksum mismatch)
with a correct paired control PASS, plus evidence that the fault reached
architectural state through the target instruction.

- **Controls:** 60/60 control runs print the golden checksum and
  `ORACLE_PASS` (A01 `728e604ffcec539d`, FW02 `1f4cbf14327717df`, FW05
  `67afad307642983e`, SQ01/SQ03/SP05 `7df5034c23f3e703`, DA04
  `3f89eab79392ce69`, LP01 `99c106541150be0e`, MD04 `22be5ae3364d0c9f`,
  LQ04 `b097eb83f71545cb`, RP01 `f3b1c554273d23f7`). Every SDC context has a
  paired control PASS.
- **A01 R01/R04/R05:** injection EA delta (0x493000→0x493008 etc.), memory
  response at the faulted PA, `register_writeback` fnv equal to the response,
  `commit`+`errant_commit`, `a01_consumed` (consumer_seq and input hash), then
  260/386/182 `consumer_commit`, and oracle FAIL. Chain closed at
  application oracle. Limitation: no golden-value counterpart for R01/R04/R05
  (only R03 has `a01_golden_resp`), see D-16.
- **FW02 R01/R02/R04/R05:** `fw02_decision fault_decision=suppressed`; the
  load is forced onto the memory path. In R01/R02/R04/R05 the memory returns
  the stale zero word `data_hex=0000000000000000` (`a8c7f832281a39c5`), which
  differs from the store data (`75b5d9074ea94640`, `24088c8834bae5c`,
  `8b068819710f562f`, `833deba36d7ea57c` respectively); the load commits and
  consumes. SDC supported.
- **FW05 ×5:** `selected_source=alt_store`; `register_writeback` equals the
  alt-store hash (`592cd57b…`, `608c2596…`, `1b75ccec…`, `20cd2544…`,
  `1e518ea0…`), commits, and 203–1803 consumers commit. The later
  `fw05_reload` reads neither true nor alt store, so it does not repair the
  consumed value. SDC supported.
- **SQ01 ×5:** store-data byte flip (`old_byte→new_byte`, `value_changed=1`)
  appears in `store_writeback data_hex`; `sq01_chain` ties
  `mem_write_hash == reload_data_hash == consumer_hash` with
  `chain_verdict=COMPLETE_CHAIN`. This is the cleanest SDC family.
- **DA04 ×5:** byte-enable mask fault (`old_be=0xf → new_be=0xe`) is visible
  in `store_writeback be_mask=0xe`; the reload at the same PA reads a value
  that differs from the later reload, then commits and consumes. SDC
  supported, though the second reload (a later overwrite) should be explained
  in the paper as a separate observation, not a repair.
- **LP01 ×5:** byte-level L1D fault (`byte0_before/after`, `mask=0x8`);
  `memory_response data_hex` and `register_writeback writeback_value` carry the
  injected byte; commits and 3.3k–30k consumers. SDC supported.
- **MD04 R02–R05:** violation suppression; the load commits with the stale
  value (`memory_response` present in R02–R05) and consumers commit; oracle
  FAIL. SDC supported. R05 has two `register_writeback` records (two
  attempts), which needs replay attribution in the trace (D-06).
- **SP05 ×5:** oracle FAIL is real, but the store-side data hash is `null`
  (`store_data_fnv=null`, `stage_outcome=RELOAD_UNVERIFIABLE`) and the trace
  has **no store writeback and no commit node** for the target store. The
  terminal SDC is supported only at oracle level; the chain is
  QUALIFIED (D-09).
- **A03 ×5 (recovered SDC):** the workload's final `put_hex` checksum is
  present in `stdout.log` and differs from golden in all five; the control is
  golden. `prop_trace.csv.gz` contains a direct chain for the first affected
  load (e.g. R01 seq 12989: `inj` 493008→493000 → `addr_form` → `a03_stream`
  → `mem_req pa=0x78000` → `resp data_hex=0010000000000000` → `taint_reg` →
  `commit` → `errant_commit`). SDC is real but the trace is partial and the
  path length is 52× the control (D-12).

### 2.2 MASKED — 12

The audit rule is "the error was produced and then overwritten/cancelled/
eliminated", not "no error". Applying it strictly:

- **LQ04 ×5 — MASKED by construction (PROVEN).** Injection records
  `valid 1→0`, `request 1→0`, `data_unchanged=1`, `no_pop=1`, `no_reuse=1`;
  `memory_response` records `entry_valid_at_response=0`,
  `entry_request_at_response=0`; the data path is bound by `senderState` and
  is byte-identical; `lq_lifecycle action=restore reason=commit` restores the
  entry. The state error is produced and eliminated; the data error is never
  produced. This is an honest MASKED but the causal table's
  `FirstDivergence=MEMORY_RESPONSE / Downstream=errant_commit` should be
  qualified as a lifetime/visibility anomaly (D-13).
- **SQ03 ×5 — MASKED (visibility timing shift, PROVEN).** `canwb_before=0`
  → `canwb_after=1`; `sq03_effect canwb_state_changed=1`. R01/R03/R04/R05
  have `visible_before_commit=1` and `effect_outcome=CHAIN_VISIBILITY_MOVED`
  (`DRAIN_BEFORE_COMMIT_WITH_RELOAD_CONSUMER`); R02 has
  `visible_before_commit=0`, `LIFECYCLE_ONLY`. The reload consumer reads the
  post-store data and the oracle passes, so the timing error is eliminated
  without a data error. **Verified value identity:** the decimal
  `store_writeback data_fnv` converted to 16 hex digits equals
  `reload_data_hash` in all five contexts (13121252959472046825 →
  `b6180e0c195fd2e9` R01; `9f995d89be67e92d` R02; `fde383c67ac034f1` R03;
  `aa2be3d3d60e3c9d` R04; `c7d78aff5e06edf9` R05), i.e. no data error was
  ever produced; the visibility shift is the only error. Supported, but the
  table must carry `effect_outcome/effect_reason` (D-13).
- **FW02 R03 — MASKED (value preserved, QUALIFIED).** The injected decision
  flips `forwarded → suppressed` (`fw02_decision`), but the memory path
  returns exactly the store data (`store_data_fnv=b2a73c741d213d8a`,
  `data_hex=fe9f000000000000`), and the writeback carries the same value. No
  wrong value is produced; the correct value is obtained by the alternate
  path. This is not "error produced then overwritten"; record the mechanism
  (D-08).
- **MD04 R01 — MASKED (inert, QUALIFIED).** The injector fired at
  `checkViolations` with `load_complete=1`, i.e. the violation suppression
  happens after the load already completed. The writeback is 0
  (`a8c7f832281a39c5`) with `source_value_hash=null`; no store data is traced,
  so neither a stale nor a correct value can be certified. Oracle PASS.
  Classify as "MASKED_INERT_COMPLETED_LOAD", not as classic masking (D-08,
  D-18).

### 2.3 SQUASHED — 1

- **A01 R02.** The target load (seq 13638) was squashed at tick 16150750 by
  `reason=lsq_squash; triggering_seq=13637`, and the injector's own record
  says `squash_cause=unrelated; fault_caused=0`. No `memory_response` exists,
  so the errant address never resolved. The literal requirement ("target
  squashed, did not enter architectural state") is met; **fault causation is
  not.** `pilot_meta.classification.observed_terminal=MASKED`,
  `fault_effect_reason=TRIGGERED_NO_DIVERGENCE`, `value_divergence_count=0`.
  The chain is QUALIFIED and the label must record `UNRELATED_SQUASH`
  (D-07).

### 2.4 CRASH / HANG

- **RP01 ×5 — HANG_WATCHDOG (PROVEN, in-simulator).** The watchdog is armed
  at startup (`CHAOSLSQFwd.cc:211-214`) for 20,000,000 cycles; at expiry it
  calls `fatal()` (`CHAOSLSQFwd.cc:620`). All five runs show
  `CHAOS_RP01_WATCHDOG_EXPIRED … tick=7700000000 injected=1 eligible=N` in
  `stderr.log` and `CHAOS_RP01_WATCHDOG=EXPIRED …` in
  `lsq_fwd_injections.log`; gem5 exits 1. The faulted R01 run's last captured
  event is at tick 16,968,875 while the control completes at
  `simTicks=36,304,345` (≈94.5 k cycles); the watchdog deadline is ~212× the
  control's total runtime, so the absence of completion is meaningful. The
  stdout logs contain **zero lines after the `RP01_SKIP_REPLAY` line** in all
  five contexts (verified by `awk '/RP01_SKIP_REPLAY/{s=1;next} s' | wc -l`
  = 0), i.e. no further eligible-violation/replay activity is reported for
  the remaining 7.68e9 ticks. This is
  an in-simulator deadline, not an external timeout. **But** it is a fixed
  deadline, not a progress-reset watchdog, and the terminal is a fatal abort,
  not an application terminal; no checksum is available (control
  `f3b1c554273d23f7`). The raw artifact also contradicts summary.json, which
  says `terminal=CRASH` and `rp01.watchdog=false` (D-02, D-17).
- **A03 ×5 — not a HANG.** `exit_code=124` comes from the 30 s wall-clock
  timeout in `tools/lsu_v332_matrix.py` (`A03_TIMEOUT=30`, `run_direct`). The
  guest had already produced its final checksum (see §2.1), the `prop_trace`
  shows continued progress to tick 866,774,755 / dyn_inst_seq 355,990, and
  `stats.txt` is 0 bytes (killed before stats dump). There is no in-simulator
  stall or progress-stall evidence; the external timeout alone cannot justify
  HANG. Current HANG_TIMEOUT label is unsupported (D-01/D-12).
- **No context's terminal is a guest exception, page-table fault, or libc
  abort.** The pipeline contains no CRASH row; the only `summary.json` CRASH
  labels are RP01's in-simulator watchdog `fatal()` aborts, whose raw cause
  is the watchdog (counted as HANG_WATCHDOG).

### 2.5 INJECTION_NOT_ACTIVATED / UNRESOLVED — 1

- **A01 R03.** `a01_ea_discarded` proves the injector computed the corrupted
  EA but set `applied_to_request=0; discard_reason=saved_request_reuse`. The
  `a01_golden_resp` and `memory_response` carry the same fnv
  (`a80414c2fc53631a`), and the target commits with the golden value; oracle
  PASS. The correct terminal is INJECTION_NOT_ACTIVATED with reason
  `DISCARDED_SAVED_REQUEST_REUSE`, not UNRESOLVED. `terminal_rules.py` cannot
  distinguish "applied but no writeback" from "discarded", which is the root
  cause (D-03).

## 3. Analysis-table versus raw-artifact contradictions

1. **A03 oracle/terminal (5 rows).** `propagation` says
   `ApplicationOracle=NO_CHECKSUM_ON_PARTIAL_TRACE` and `HANG_TIMEOUT`; raw
   `stdout.log` contains a final checksum different from golden in 5/5. The
   readiness matrix repeats the same wrong values. Root: the A03 parser looks
   for `checksum=0x…` while `agu_addrmodes.c` prints a bare 16-hex string.
2. **RP01 terminal (5 rows).** `summary.json` says `terminal=CRASH`,
   `rp01.watchdog=false`; the propagation CSV says `HANG_WATCHDOG`; raw shows
   a deliberate in-simulator `CHAOS_RP01_WATCHDOG_EXPIRED` fatal. The CSV is
   right, the summary is wrong.
3. **RP01 Activation column (5 rows).** The propagation CSV fills
   `Activation` with `RP01_ELIGIBLE ordinal=1 … in_instsToReplay_post=1`, the
   *baseline* eligibility event, not the fault activation at ordinal
   26/77/128/179/230 (the skip where `in_instsToReplay_post` goes 1→0).
4. **A01 R02 SQUASHED.** Raw squash: `squash_cause=unrelated; fault_caused=0`;
   the table presents SQUASHED as if the fault caused the elimination.
5. **A01 R03 UNRESOLVED.** Raw `a01_ea_discarded applied_to_request=0`;
   terminal reason excludes this positive evidence.
6. **`Trace=COMPLETE` for A01 R03.** The chain has only
   injection/address_formed/memory_response (+discard/golden) and no
   writeback/commit, yet the structural completeness profile
   `(A01, UNRESOLVED) → ("injection",)` passes and `Trace=COMPLETE`. The
   meaningful `fault_effect_propagation_coverage=UNRESOLVED` is not surfaced
   in the readiness or causal tables.
7. **`Activation` column for the 50 non-A03/RP01 rows** is the tautology
   `injection seq=N`; it does not cite the actual activation event (e.g.
   `a01_ea`, `fw02_decision`, `store_writeback`, `sp05_complete`).
8. **`Downstream` column** is derived from same-`dyn_inst_seq` events only.
   For A01 R01 it reports `errant_commit` although 386 `consumer_commit`
   events exist (first at seq 12980, and `a01_consumed` names seq 12980). For
   SQ01 it reports `commit` (the store's own commit) although the reload
   consumer at seq 13330 and `sq01_chain consumer_seq` exist. The raw
   consumer evidence is present but the table does not cite it.
9. **Identity fields.** A01 R01 `addr=78008` is a PA while R02 `addr=493ff0`
   is an EA; `va` is `None` throughout. FW05 `va=None;addr=None` although the
   injection detail carries `true_addr=0x4919c8`. SP05 `pc=None;va=None;
   addr=None;lq=None` although `sp05_stage` carries `store_seq`/`sq_idx` and
   a reload seq. LP01 `lq=24/57/90/12/1` versus raw `lq_entry_id=2407/5735/
   9063/12391/15719` (leading-digit truncation).
10. **SP05 SDC vs RELOAD_UNVERIFIABLE.** The trace record says
    `stage_outcome=RELOAD_UNVERIFIABLE`, `store_data_fnv=null`,
    `masking_mechanism=NOT_APPLICABLE`, and contains no store writeback and
    no commit node; the propagation table nevertheless reports
    `FirstDivergence=SP05_COMPLETE`, `Downstream=n/a`, `CommitSquashReplay=no`,
    `ArchitecturalOrTerminal=SDC`, `EvidenceClass=DIRECT_DATAFLOW_EVIDENCE`.
11. **SQ03 MASKED.** Supported by `sq03_effect`, but the causal table does
    not carry `visible_before_commit`/`effect_outcome`/`effect_reason`, and
    the qualifier `VISIBILITY_TIMING_SHIFT (CHAIN_VISIBILITY_MOVED 4/5)` is
    not repeated in the causal row. (Raw: R01/R03/R04/R05 moved, R02
    `LIFECYCLE_ONLY`.)
12. **LQ04 MASKED.** The `FirstDivergence=MEMORY_RESPONSE / Downstream=
    errant_commit` wording suggests a data divergence; the raw record says
    `data_unchanged=1`, `data_corruption=0`, and the anomaly is
    `entry_valid_at_response=0` (lifetime). Mechanism must be stated.
13. **`ControlProof=INJECTOR_ABSENT` on 60/60.** True for FW02/DA04/MD04/
    LQ04/RP01 controls, false for A01/A03/FW05/SQ01/SQ03/SP05/LP01 controls,
    where the injector is mounted with `--probability 0.0` (A01 control
    stdout: `CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath … injected=0`).
14. **A03 `injection_count=20000`.** This is the `A03_LOG_CAPPED cap=20000`
    line count (line 60002 of the log), while the injector FUNNEL reports
    `injected=113377`. The count is a logging cap, not the injection count.
15. **A03 selected vs first-effective ordinal.** `FaultSource` names the
    selected ordinal, `FirstDivergence` names a different ordinal for R01
    (1059 vs 1060), R03 (1137 vs 1171) and R04 (1176 vs 1177); the selected
    events were `ALREADY_STUCK`. The table does not say so.
16. **A01-R03 `summary.json exit_code=1`.** `pilot_meta.json exit_code=0`
    (gem5) but `accepted=false`, so `run_pilot.py` returned 1. The summary's
    exit code is the wrapper's, not gem5's.
17. **Provisional SampleRunIDs.** ROI mapping/control pair use
    `V332-<MODEL>-R<NN>` instead of the frozen workbook IDs; the ground-truth
    file calls this out. Not a raw-artifact contradiction, but a provenance
    defect.

No contradiction was found in: ordinal↔command mapping for the
trace-bearing runs (A01 1059/1098/1137/1176/1215, FW02 13/25/37/49/61,
FW05 200/600/1000/1400/1800, SQ01 1018/1044/1069/1095/1121, SQ03 1021/1047/
1072/1098/1124, SP05 952/978/1003/1029/1055, DA04 135/340/544/749/954, LP01
2549/5877/9205/12533/15861, MD04 3/5/6/8/10, LQ04 1–5, RP01 26/77/128/179/
230), nor in the 60/60 control oracle PASS.

## 4. Consolidated issue list

Class: **A** code/hook, **B** workload/dynamic-context design, **C**
trace/propagation/oracle evidence, **D** Excel/seed/control/binary/runner.

### D-01 — A03 oracle parser misses the workload's bare-hex checksum
- **Root cause:** `tools/lsu_v332_matrix.py` A03 branch parses
  `checksum=0x([0-9a-fA-F]+)`; `agu_addrmodes.c` ends with `put_hex(acc)`
  (bare 16 hex digits), and `tools/lsu_v332_report.py` hard-codes
  `oracle="NO_CHECKSUM_ON_PARTIAL_TRACE"` for A03.
- **Affected:** A03 R01–R05; `AUD/propagation/…Final.csv`,
  `AUD/LSU_60Context_Final_Readiness_Matrix.csv`,
  `AUD/controls/LSU_Fault_Control_Pair_Final.csv`; `tools/lsu_v332_matrix.py`,
  `tools/lsu_v332_report.py`.
- **Proposed fix:** accept the bare 16-hex final line and compare against
  `agu_addrmodes.golden`; set `oracle=FAIL` and terminal `SDC` when the
  paired control is PASS. Do not infer HANG from exit 124 alone.
- **Validation:** `for r in 1 2 3 4 5; do grep -oE '^[0-9a-f]{16}$'
  AUD/runs/A03-R0$r-fault/stdout.log | tail -1; done` (five non-golden
  values) and `grep -oE '^[0-9a-f]{16}$'
  AUD/runs/A03-R01-control/stdout.log | tail -1` (`728e604ffcec539d`).
- **Approval:** Y (changes 5 terminal labels and headline counts).
- **Regression risk:** low for code, high for reported results (HANG 5 → 0,
  SDC 36 → 41).
- **Class:** D (runner) with C impact.

### D-02 — RP01 raw watchdog vs summary.json terminal
- **Root cause:** `parse_rp01_stdout` reads `stdout.log` only; the marker is
  emitted to the injector log and `stderr.log` (`fatal:`), so
  `rp01.watchdog=false` and `terminal=CRASH` in `summary.json`.
- **Affected:** RP01 R01–R05; `tools/lsu_v332_matrix.py`.
- **Proposed fix:** also scan `stderr.log`/`lsq_fwd_injections.log`; set
  `watchdog=true`, `terminal=HANG_WATCHDOG`; keep the fatal as the terminal
  cause.
- **Validation:** `grep -n CHAOS_RP01_WATCHDOG
  AUD/runs/RP01-R01-fault/stderr.log
  AUD/runs/RP01-R01-fault/lsq_fwd_injections.log`.
- **Approval:** Y. **Risk:** low. **Class:** D/C.

### D-03 — A01 injector discards the fault on saved-request reuse
- **Root cause:** A01 emits `a01_ea_discarded applied_to_request=0;
  discard_reason=saved_request_reuse`; `terminal_rules.adjudicate` ignores
  the discard record and reports `UNRESOLVED_NO_REGISTER_WRITEBACK_EVIDENCE`.
- **Affected:** A01 R03; `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/` (apply site),
  `docs/gem5-fi/lsu/implementation_v3_2/platform/terminal_rules.py`.
- **Proposed fix:** either apply the EA delta to the reused request (source
  fix) or add a terminal rule: `a01_ea_discarded && applied_to_request==0` →
  `INJECTION_NOT_ACTIVATED` with `DISCARDED_SAVED_REQUEST_REUSE`.
- **Validation:** `grep -o '"event_type":"a01_ea_discarded"[^}]*' ...` or
  Python parse of `AUD/runs/A01-R03-fault/trace_v31.jsonl`.
- **Approval:** Y (model semantics). **Risk:** medium (A01 table row and
  acceptance gate `fault_valid`).
- **Class:** A/C.

### D-04 — `summary.json` exit_code conflates wrapper and gem5 exit status
- **Root cause:** `run_pilot.py` returns `0 if accepted else 1`; the matrix
  records that as `exit_code`. For A01-R03, gem5 exited 0
  (`pilot_meta.json exit_code: 0`) but the summary says 1.
- **Affected:** all run_pilot-based contexts whose accepted=false; at least
  A01 R03.
- **Proposed fix:** record `gem5_exit_code` and `runner_exit_code`
  separately; use `accepted` for validity.
- **Validation:** `python3 -c "import json;print(json.load(open(
  'AUD/runs/A01-R03-fault/pilot_meta.json'))['exit_code'])"` (0) vs
  `summary.json` (1).
- **Approval:** N (metadata only). **Risk:** low. **Class:** D.

### D-05 — Causal table Activation/Downstream are not chain-scoped
- **Root cause:** `tools/lsu_v332_report.py: fault_row` builds `evs` by
  `dyn_inst_seq == injection seq`; `activation` is hard-coded as
  `injection seq=N`; the consumer is chosen among `consumer_commit`,
  `errant_commit`, `commit` *within that same-instruction subset*. Consumer
  events carry their own seq, so they are never seen.
- **Affected:** 50 non-A03/RP01 rows (Downstream), 55 rows (Activation).
- **Proposed fix:** chain-scope on `ptag` (plus target seq), then pick the
  first activation event per model, and the first `consumer_commit` /
  reload consumer (with seq and hash) as Downstream.
- **Validation:** compare A01-R01: raw has 386 `consumer_commit` and
  `a01_consumed consumer_seq=12980`; the CSV says `errant_commit`.
- **Approval:** N (table fix). **Risk:** low. **Class:** C.

### D-06 — Injection identity mixes VA/PA and drops chain fields
- **Root cause:** `addr = inj.addr or rich.addr or rich.pa or
  rich.actual_ea or …` picks the first available, mixing PA (A01
  R01/R03/R04/R05, FW02) with EA (A01 R02); FW05/SP05 have keys not read;
  `lq` is `rich.get("lq_entry_id")` and for LP01 yields 24/57/90/12/1 instead
  of 2407/5735/9063/12391/15719.
- **Affected:** A01 R01–R05, FW05 ×5, SP05 ×5, LP01 ×5 (identity/table).
- **Proposed fix:** emit separate `va=`, `pa=`, `ea=`, `lq_entry=`,
  `sq_entry=`, `reload_seq=`; fix the LP01 truncation; use the exact raw
  values.
- **Validation:** `python3` compare each CSV identity with
  `first_injection.detail`/`trace_v31` (`AUD/runs/LP01-R01-fault` raw
  `lq_entry_id=2407`).
- **Approval:** N. **Risk:** low. **Class:** C/D.

### D-07 — A01 R02 SQUASHED ignores `fault_caused=0`
- **Root cause:** `terminal_rules.adjudicate` treats any `squash` event on
  the target as `SQUASHED`, without reading `squash_cause`/`fault_caused`.
- **Affected:** A01 R02 (`AUD/runs/A01-R02-fault`, squash tick 16150750).
- **Proposed fix:** parse the squash detail; when `fault_caused=0`, emit
  `SQUASHED_UNRELATED` (or `MASKED_UNRELATED_SQUASH`) and record the
  triggering seq; do not imply fault causation.
- **Validation:** `grep -o '"event_type":"squash"[^}]*' ...
  A01-R02-fault/trace_v31.jsonl`.
- **Approval:** Y (label semantics). **Risk:** low. **Class:** C.

### D-08 — MASKED rows do not record the masking mechanism
- **Root cause:** `terminal_rules` returns MASKED on value-present + oracle
  PASS; it never records whether the value is value-identical (FW02 R03),
  inert because the load already completed (MD04 R01), or restored
  (LQ04). The causal table has no mechanism column.
- **Affected:** FW02 R03; MD04 R01; LQ04 R01–R05; SQ03 R02 (LIFECYCLE_ONLY).
- **Proposed fix:** add `masking_mechanism` (`VALUE_IDENTITY_ALT_PATH`,
  `INERT_AFTER_COMPLETION`, `LIFETIME_RESTORED`, `VISIBILITY_SHIFT`) to the
  terminal reason and table.
- **Validation:** raw fields already exist (`memory_response data_hex ==
  store_data_hex` for FW02 R03; `load_complete=1` for MD04 R01;
  `entry_valid_at_response=0` + `restore` for LQ04).
- **Approval:** N. **Risk:** low. **Class:** C.

### D-09 — SP05 SDC has no store data / store commit in the trace
- **Root cause:** the SP05 hook runs at `writebackStores_prematureComplete`
  and emits `store_data_fnv=null`, `write_skipped=1`, `drain_tick=0`; no
  `store_writeback` or `commit` node is emitted for the target store.
  `terminal_rules` special-cases SP05 as committed by construction.
- **Affected:** SP05 R01–R05; `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/`,
  `CHAOSPropagation` (SP05 stage), `terminal_rules.py`.
- **Proposed fix:** capture the store's write data FNV at the hook (or at the
  skipped write) and emit the store commit; then compare the reload hash to
  the store hash; relabel to `SDC` only if they differ (else
  RELOAD_UNVERIFIABLE / MASKED).
- **Validation:** `grep -o 'store_data_fnv=[^;]*' AUD/runs/SP05-R0?-fault/
  trace_v31.jsonl` (currently `null` ×5).
- **Approval:** Y (source hook). **Risk:** medium. **Class:** A/C.

### D-10 — ControlProof `INJECTOR_ABSENT` is wrong for 35 controls
- **Root cause:** `tools/lsu_v332_report.py: control_row` decides
  `injector_absent` by string absence of `--chaos_lsqfwd/--chaos_md04/
  --chaos_addrpath`; `--chaos_addrpath` is present in A01/A03 controls,
  `--chaos_lsqfwd` in FW05/SQ01/SQ03/SP05 controls, `--chaos_l1dfwd` in LP01
  controls (not checked at all), all with `--probability 0.0`.
- **Affected:** A01, A03, FW05, SQ01, SQ03, SP05, LP01 controls (35 runs).
- **Proposed fix:** label `INJECTOR_PRESENT_PROBABILITY_ZERO` when the flag
  is present and `injected=0` (verified by the `CHAOS_LSU_TRIGGER` line), and
  `INJECTOR_ABSENT` only when the flag is absent.
- **Validation:** `grep -h 'CHAOS_LSU_TRIGGER' AUD/runs/A01-R01-control/
  stdout.log` (shows `injected=0`).
- **Approval:** N. **Risk:** low. **Class:** D.

### D-11 — `Trace=COMPLETE` is structural and can pass on an injection-only chain
- **Root cause:** `trace_completeness.DEFAULT_PROFILE` maps A01 etc. to
  `("injection",)`, and `(A01, UNRESOLVED)` falls through to it. The separate
  `fault_effect_propagation_coverage` field (UNRESOLVED) is not surfaced in
  the readiness/causal tables.
- **Affected:** A01 R03; all rows (Trace column semantics).
- **Proposed fix:** surface `fault_effect_propagation_coverage` as the
  meaningful field, and tighten the per-terminal profiles to require
  writeback/commit for load-side models.
- **Validation:** `python3 -c` read `pilot_meta.json` classification of
  A01-R03 (`fault_effect_propagation_coverage: UNRESOLVED` while
  `trace_completeness: COMPLETE`).
- **Approval:** N. **Risk:** low. **Class:** C.

### D-12 — A03 harness/trace loss and count inflation
- **Root cause:** the A03 runner bypasses `run_pilot.py`, runs gem5 directly
  with a 30 s wall clock, does not convert `trace_v31.jsonl`, kills during
  trace flush (truncated gzip, 0-byte stats), and reports the log cap
  (`cap=20000`) as `injection_count` although the FUNNEL reports
  `injected=113377`.
- **Affected:** A03 R01–R05; `tools/lsu_v332_matrix.py` (`A03_TIMEOUT`,
  `run_direct`, `parse_addrpath_log`).
- **Proposed fix:** run A03 through the normal conversion path (or convert
  post-hoc from `prop_trace.csv.gz`), preserve stats, and report the FUNNEL
  count plus the cap explicitly.
- **Validation:** `grep 'A03_LOG_CAPPED\|FUNNEL' AUD/runs/A03-R01-fault/
  addrpath_injections.log | tail -2`; `stat -c %s AUD/runs/A03-R01-fault/
  stats.txt` (0).
- **Approval:** Y. **Risk:** medium (runtime; re-running is needed for a
  complete trace). **Class:** B/C/D.

### D-13 — SQ03/LQ04 mechanism fields not carried into the tables
- **Root cause:** `sq03_effect` (`visible_before_commit`, `effect_outcome`,
  `effect_reason`) and the LQ04 `entry_valid_at_response` /
  `data_unchanged` fields exist in the trace but are not columns in the
  propagation table; `MASKED` is decided by the generic store/load rules.
- **Affected:** SQ03 ×5, LQ04 ×5.
- **Proposed fix:** bubble these fields into `TerminalReason`/a new
  `Mechanism` column; assert `data_unchanged==1` for LQ04 MASKED.
- **Validation:** raw fields verified in §2.2.
- **Approval:** N. **Risk:** low. **Class:** C.

### D-14 — A03 selected ordinal vs first effective ordinal
- **Root cause:** A03 `bit3_stuck0` only changes addresses with bit 3 set;
  the selected ordinal can be `ALREADY_STUCK` (`affected=0`), so the first
  effective event is later (R01 1059→1060, R03 1137→1171, R04 1176→1177).
  The table names only one ordinal in each place.
- **Affected:** A03 R01/R03/R04.
- **Proposed fix:** record `selected_ordinal`, `first_effective_ordinal`,
  and the `reason=ALREADY_STUCK` for the selected event.
- **Validation:** `grep 'event_ordinal=1059\|event_ordinal=1060'
  AUD/runs/A03-R01-fault/addrpath_injections.log`.
- **Approval:** N. **Risk:** low. **Class:** C/B.

### D-15 — Provisional SampleRunIDs vs frozen workbook
- **Root cause:** the v3.3.2 tables use `V332-<MODEL>-R<NN>`; the frozen
  sample matrix uses `A01-F0-W1-S01-R01`-style IDs.
- **Affected:** all 60 rows in ROI mapping/control pairs.
- **Proposed fix:** resolve the mapping to the authoritative IDs, keep both
  columns, and validate against `60_SAMPLE_MATRIX.csv`.
- **Validation:** `grep -c 'V332-' AUD/roi/LSU_60Context_ROI_Percentile_
  Mapping.csv` (60).
- **Approval:** Y (identity). **Risk:** low. **Class:** D.

### D-16 — A01 SDC lacks a golden-value counterfactual
- **Root cause:** `a01_golden_resp` is emitted only for the discarded R03
  path; R01/R04/R05 have no read of the golden address to compare.
- **Affected:** A01 R01/R04/R05.
- **Proposed fix:** always emit `a01_golden_resp` (address + data FNV) for
  the target, or a control-run pair read of the same PC/addr.
- **Validation:** `grep -c a01_golden_resp AUD/runs/A01-R0{1,4,5}-fault/
  trace_v31.jsonl` (0/0/0; R03 = 1).
- **Approval:** N (evidence strength). **Risk:** low. **Class:** C.

### D-17 — RP01 watchdog is a fixed deadline and its control pair is unrecorded
- **Root cause:** `schedule(rp01_watchdog_event, clockEdge(cycles))` at
  startup, no progress reset; the terminal is a `fatal()`. The fault row
  records `no_checksum` but not the control's checksum.
- **Affected:** RP01 R01–R05.
- **Proposed fix:** document the deadline semantics; optionally convert to a
  progress-reset watchdog; record the control checksum
  (`f3b1c554273d23f7`) in the pair table.
- **Validation:** `grep -n 'rp01_watchdog_event\|rp01Watchdog' CHAOS/gem5/
  src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc`; `tail -2 AUD/runs/RP01-R01-
  control/stdout.log`; and for the no-progress evidence,
  `awk '/RP01_SKIP_REPLAY/{s=1;next} s' AUD/runs/RP01-R01-fault/stdout.log |
  wc -l` (0).
- **Approval:** Y for the source change, N for the documentation. **Risk:**
  medium (fault model semantics). **Class:** C/D.

### D-18 — MD04 log hard-codes the modification flags
- **Root cause:** `CHAOSMD04.cc:136` prints
  `address_modified=0, size_modified=0, data_modified=0` as string literals.
  The fault is actually a violation suppression, so those fields must not be
  read as measurements.
- **Affected:** MD04 R01–R05; source `CHAOS/gem5/src/cpu/o3/CHAOSMD04/
  CHAOSMD04.cc`.
- **Proposed fix:** report `operand_modified=0 (suppression)` explicitly and
  compute any real fields, or remove the pseudo-fields.
- **Validation:** `grep -n 'address_modified=0' CHAOS/gem5/src/cpu/o3/
  CHAOSMD04/CHAOSMD04.cc` (line 136).
- **Approval:** N. **Risk:** low. **Class:** A/C.

### D-19 — Control traces carry a control-only probe node
- **Root cause:** A01 controls emit `probe` + `a01_ea` + `memory_request`
  with `ptag=0`, `injected=0`, `control_only=1` at the target tick. They are
  not injections, but a naive ptag-agnostic consumer can count them.
- **Affected:** A01/A03 controls (and possibly others).
- **Proposed fix:** document the node in the control evidence and ensure the
  adjudicator only matches `event_type=injection` (it does today).
- **Validation:** raw event dump of `AUD/runs/A01-R01-control/trace_v31.jsonl`
  (`probe` detail `injected=0;control_only=1`).
- **Approval:** N. **Risk:** low. **Class:** C.

## 5. Could not verify

1. **Absolute causal proof of A01 R01/R04/R05 SDC at value level** — no
   golden read of the same load exists in those runs; the oracle FAIL is the
   independent terminal, but the exact "correct value vs faulted value"
   comparison is absent (D-16).
2. **A03's path from the first affected load to the final checksum** — the
   prop_trace is truncated and no `trace_v31.jsonl` exists; the checksum FAIL
   and direct first-load chain are verified, but the full architectural path
   is not.
3. **A03 "hang" semantics** — no in-simulator stall evidence; the guest
   printed its final checksum. I could not determine whether gem5 was killed
   during trace flush or in a post-workload drain, only that the workload's
   final output exists and `stats.txt` is empty.
4. **SP05 store data / store commit** — `store_data_fnv=null` and no store
   writeback event, so data correctness cannot be certified (B4 persists).
5. **MD04 R01 stale-vs-correct value** — no store data record for the paired
   store 125103 and `source_value_hash=null`, so the MASKED claim is
   "no observable data error", not "error produced then overwritten".
6. **FW02 R03 masking mechanism at value level vs control** — the control
   trace does not record `memory_response`/`register_writeback` data, so the
   "value preserved" conclusion is from the fault run's own
   `store_data_fnv == data_fnv` equality, not a fault-vs-control value
   comparison.
7. **SQ03 CHAIN_VISIBILITY_MOVED consumer timing vs control** — the control
   trace records no `sq03_effect` (no injection), so the "visibility moved"
   claim is fault-run-internal (before-commit reload) plus the oracle PASS,
   not a control-paired timing delta.
8. **RP01 true deadlock** — the fixed 20M-cycle deadline and 212× control
   runtime prove non-completion, but I did not observe a progress-counter
   reset, so "hang" is an inferred no-forward-progress, not a proven
   deadlock.
9. **A01 R02 squash causation** — cannot be attributed to the fault; the
   injector itself says `fault_caused=0`.
10. **Every "control PASS" checksum for the RP01 pair** is from the control
    run (`f3b1c554273d23f7`), but the fault run has no checksum; the pair is
    not an oracle-level comparison.

## 6. Bottom line

- The **raw artifacts support 36 pipeline SDC rows**, and the **5 A03 rows
  should also be SDC** (each printed a non-golden final checksum; the paired
  control prints golden). A03 is therefore an **mislabeled SDC block**, not a
  HANG block. This is the single largest discrepancy in the v3.3.2 tables.
- **45/60 rows are chain-closed YES** (A01 R01/R04/R05, FW02 R01/R02/R04/R05,
  FW05 ×5, SQ01 ×5, SQ03 R01/R03/R04/R05, DA04 ×5, LP01 ×5, MD04
  R02–R05, LQ04 ×5, RP01 ×5). **14 rows are QUALIFIED** (A03 ×5 partial
  trace, SP05 ×5 unverifiable data, FW02 R03 value-identity, SQ03 R02
  lifecycle-only, MD04 R01 inert, A01 R02 unrelated squash). **A01 R03 is
  NO** (the injection was discarded and the terminal should be
  INJECTION_NOT_ACTIVATED). 45 + 14 + 1 = 60.
- **All 60 controls pass the oracle**, so the SDC/MASKED split is not
  confounded by a broken control; the control-proof *label* is wrong for 35
  controls (injector present at probability 0, not absent).
- **RP01's in-simulator watchdog is real**; summary.json's `CRASH` /
  `watchdog=false` is a runner-parsing defect. The propagation CSV's
  HANG_WATCHDOG is the defensible label, with the caveat that the watchdog is
  a fixed 20M-cycle deadline and the terminal is a fatal abort without an
  application oracle.
- **No context qualifies as a CRASH** in the raw artifacts; the only CRASH
  labels are RP01's watchdog aborts, which are already counted as
  HANG_WATCHDOG.
- **SQ03's MASKED 5/5 is value-proven.** In all five contexts the reload
  consumer hash equals the store's writeback data hash (e.g. R01
  `13121252959472046825` = `0xb6180e0c195fd2e9` = `reload_data_hash`), so no
  data error was produced; only the store's visibility-before-commit moved
  (4/5) or the lifecycle changed (R02).
- **The analysis tables are directionally right for the 50 trace-bearing,
  non-A03 rows but under-cite the raw chain**: the `Downstream` column misses
  the actual consumer fan-out (hundreds to tens of thousands of
  `consumer_commit` records), the `Activation` column is a tautology, and the
  identity columns mix VA/PA and truncate LP01's LQ id. These are table/
  tooling defects (D-05/D-06), not missing evidence in the runs.
