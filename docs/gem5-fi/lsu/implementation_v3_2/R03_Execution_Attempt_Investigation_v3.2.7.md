# MD04-R03 execution_attempt_id investigation (v3.2.7)

**Question (v3.2.6 review):** R03 records Injection at attempt 1 but Memory
Response / Register Writeback / Commit at attempt 2, with
`replay_generation=0` everywhere. Is this a replay, another re-execution,
or an attempt-id propagation bug?

**Answer: it is a D-cache-blocked re-execution of the same dynamic
instruction and the same request. It is not a replay, not a squash, and
not an attempt-id reset or propagation bug. The historical trace did not
carry the request id at injection, so its chain is retrospectively
`CROSS_ATTEMPT_UNVERIFIED`; the frozen-definition rerun carries the full
identity and is `CROSS_ATTEMPT_VERIFIED`.**

## 1. What `execution_attempt_id` actually is

`executionAttemptId` is not a gem5-native field. It is a CHAOS-added
counter:

- Declaration: `CHAOS/gem5/src/cpu/o3/dyn_inst.hh:354`
  `uint64_t executionAttemptId = 0;`
- Increment sites:
  `CHAOS/gem5/src/cpu/o3/lsq_unit.cc:700` at the top of
  `LSQUnit::executeLoad`, and `...:772` at the top of
  `LSQUnit::executeStore`.

It therefore counts **LSQ execution invocations**, not squashes,
re-fetches, or branch replays. `replay_generation` is a separate counter
and remains 0 here.

## 2. Real evidence: the same load is executed twice

Command (reproducible):

```bash
build/ARM/gem5.opt --outdir=/tmp/md04r03dbg --debug-flags=LSQUnit \
  --debug-start=17816000 --debug-end=17824000 \
  --debug-file=/tmp/md04r03dbg/dbg.txt configs/se/lsu_proxy.py \
  --cmd=$PWD/docs/gem5-fi/lsu/implementation_v3_2/workloads/replay_dependency \
  --cpu O3 --variant B0 --probability 1.0 --chaos_propagation \
  --prop_trace_file prop_trace.csv.gz --chaos_md04 --md04_first_clock 0 \
  --md04_max_faults 1 --md04_probability 1.0 \
  --md04_rng_seed 2545691512 --md04_event_ordinal 3
```

The captured window (`logs_v3_2_7/r03_lsq_debug_window.txt`) contains:

```
17816260 ... Executing load PC (0x400530=>0x400534).(0=>1), [sn:17443]
17816260 ... Memory request (pkt: ReadReq [76990:76997]) from inst [sn:17443]
           was not sent (cache is blocked: 1, cache_got_blocked: 0)
17816260 ... Executing store PC (0x40052c=>0x400530).(0=>1) [sn:17442]
17816260 ... CHAOSMD04: suppressed violation load [sn:17443] store [sn:17442]
           addr 0x491990
17822035 ... Executing load PC (0x400530=>0x400534).(0=>1), [sn:17443]
17822035 ... Memory request (pkt: ReadResp [76990:76997]) from inst [sn:17443]
           was sent (cache is blocked: 0, cache_got_blocked: 0)
```

Mechanism:

1. At tick 17816260 the load is issued (attempt 1). The D-cache is blocked,
   so `initiateAcc` returns without sending the request.
2. The store 17442 executes in the same tick; `checkViolations` reaches the
   store branch and MD04 suppresses its report. The injection is recorded
   with the load's current `executionAttemptId = 1` and `load_complete=0`.
3. At tick 17822035 the same `DynInst` (same `seqNum=17443`, same LQ entry
   748, same generation 1235, same request 67) is executed again (attempt 2)
   and the request is sent; the response arrives at 17822805.

## 3. Replay? No.

- `replay_generation = 0` in every event.
- No `squash` event exists for seq 17443 in the R03 trace.
- The dynamic sequence number is unchanged (17443); a squash-and-refetch
  would allocate a new `seqNum`, not reuse it.
- The LQ entry identity is unchanged: `lq_entry_id=748`,
  `entry_generation=1235`.
- The memory request identity is unchanged: `request_id=67`
  (`request_tick=9691605`, created at `pushRequest`, sent at 17822035).

This is the normal `executeLoad` retry path after a blocked cache, not an
IQ/IEW replay.

## 4. Attempt-id reset/propagation? No.

The counter is read at event time from the same `DynInst`. The injection
was recorded before the second `executeLoad` call, so it saw 1; the later
response/writeback/commit saw 2. There is no reset and no propagation of a
stale value.

## 5. Re-adjudication under the new validator

The v3.2.7 rule: a chain may cross `execution_attempt_id` values only when
the events share the identity tuple (dyn seq, LQ entry, entry generation,
request id).

| Trace | `execution_attempt_link` | chain | coverage | reason |
|---|---|---|---|---|
| Historical `pilots_v3_2_6/MD04-R03` | `CROSS_ATTEMPT_UNVERIFIED` | FAIL | PARTIAL | injection detail has no `load_request_id`; the old trace cannot prove the response belongs to the same request |
| New frozen-definition rerun (`pilots_v3_2_7/MD04-R03`) | `CROSS_ATTEMPT_VERIFIED` | PASS | COMPLETE | injection `request_id=67`, LQ 748, generation 1235; response matches all four |

The historical v3.2.6 claim of a COMPLETE chain is therefore **downgraded**
to PARTIAL/UNVERIFIED on the available record. The physical mechanism is
established by the debug window; the trace-level claim now rests on the
new run's explicit identity, not on an assumption.

## 6. Consequence

- R03's injection is a real, single, suppressed store→load violation.
- The attempt change is explained and benign (blocked-cache retry).
- The frozen-definition R03 run is the citable R03 evidence; the v3.2.6
  trace is retained untouched as `HISTORICAL_ATTEMPT_UNVERIFIED`.
