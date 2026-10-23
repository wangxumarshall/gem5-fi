# R6-CENSUS — S01/S02 (Store-Queue data, LSQFwd family) F0 span census on W1

Lane L23 (pilots + evidence). Branch `r6-census` off `lsu-mdspec-20261019`.
Read-only w.r.t. the contract tooling: `tools/lsu_campaign.py`,
`tools/lsu_chain_check.py`, `tools/lsu_ready_contract.py` and all C++ are
untouched by this lane.

## 1. What the "census" is

`tools/lsu_campaign.resolve_cell` routes every cell through a per-`(model,
workload-binary)` **F0 span**. The trigger is event-normalized: with
`warmup=1` + `span=N` the first fire is `next_fire = 1 + lcg(seed) % N`, i.e.
**truly F0-uniform over the N eligible events** (see the `LSQFWD_F0_SPAN`
comment block in `tools/lsu_campaign.py`). `N` must therefore equal the
**measured length of that model's eligible stream on that exact carrier**; an
unmeasured pair is refused LOUDLY (`BLOCKED(F0-span-unmeasured)`) instead of
silently reusing another pair's span.

The **census** is the measurement of that stream: run the resolved lsqfwd F0
command for the model on the carrier with the draw pinned so it can never land
(`span=INT64_MAX`, and `--max_faults 0` for a hard control), then read the
injector teardown line, whose `eligible=` IS the whole stream:

```
CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=<N> eligible=<N> injected=0 ...
```

`SPAN_UNREACHABLE` / `EARLY_BIAS` alarms are part of the census shape, not a
defect: `SPAN_UNREACHABLE` is the *intent* on short carriers, `EARLY_BIAS` is
exactly what an **injected** run produces on a long one (and is why an injected
run can never be used as the census — R5 §4 below).

## 2. The blocked cells and the exact unblock condition

Quoted verbatim from `docs/gem5-fi/lsu/mdspec/ready_contract.json`:

| RunID | category | `why` / `resolve_reason` |
|---|---|---|
| S01-F0-W1 | UNRESOLVED | `BLOCKED(F0-span-unmeasured: model S01 on workload mibench/bin/w1_all — measure its eligible stream with a real run and set LSQFWD_F0_SPAN[('S01', 'mibench/bin/w1_all')] in tools/lsu_campaign.py; refusing rather than silently reusing another pair's span)` |
| S02-F0-W1 | UNRESOLVED | same text with model `S02` and key `('S02', 'mibench/bin/w1_all')` |

Both are `coverage: PASS`, `status_reasons` absent → per
`tools/lsu_ready_contract._classify` they land in UNRESOLVED only because
`resolve_cell` returns `flags=None`. **The unblock condition is exactly: obtain
the uninjected measured `eligible` for `(S01, mibench/bin/w1_all)` and
`(S02, mibench/bin/w1_all)`, add the two rows to `LSQFWD_F0_SPAN`, regenerate
the contract.** No other evidence (pilot, chain) is required for these two —
unlike the other 2 UNRESOLVED cells (S10-F2-W5 / S10-F2-W9, structurally
unreachable, a spec-level decision).

Confirmed: `LSQFWD_F0_SPAN` today contains only `("S01","sq_forward"): 7`,
`("S02","sq_forward"): 7` (+ S03/S08/S09/L03/L04/S10 rows). There is **no**
`mibench/bin/w1_all` row for either model.

## 3. Existing evidence found (preserved, quoted — none of it is the census)

### 3a. W1 carrier golden runs (SE, uninjected) — the *carrier*, not the span

`runs/lsu/golden/w1_all/{g1,g2,g3}/` (2026-10-10/11), `w1_full1/2/3.done` all
`EXIT_RC=0`; each log ends `[w1] suite done: 14/14 ok` with identical output
hashes, e.g. `[w1] edge out susan_edge.pgm fnv1a64=090bc05c2150bfec`,
`[w1] smooth out susan_smooth.pgm fnv1a64=e2ab1a593b7b03b5`.
This proves the carrier is deterministic and terminates — it measures no
LSQFwd stream.

### 3b. W1 lsqfwd-family count runs (2026-10-11) — **not** the S01/S02 stream

* `runs/lsu/engineering/w1_cnt_lsqfwd.out` (rc 0):
  `CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=515917150 eligible=515917150 injected=0 (activated=W3-L0-layer)`
* `runs/lsu/engineering/w1_ac_lsqfwd.out` (rc 0):
  `CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=498300231 eligible=498300231 injected=0 first_eligible_tick=207900 last_eligible_tick=1270908389135`

Command shape (from the `.out` header, binary built **2026-10-11**):
`lsu_proxy.py --cmd workloads/mibench/bin/w1_all --cpu O3 --variant B0
--chaos_lsqfwd --lsqfwd_lsu_tier F0 --lsqfwd_warmup_events 0
--lsqfwd_span_events 9223372036854775807 --lsqfwd_l03 --rng_seed 10762886349909418557`
— i.e. the **generic family** stream (`--lsqfwd_l03` enabled, which adds the
L03 violation-check stream). It is uninjected and is the largest preserved
number, but it is **not** the `(S01, w1_all)` span. Do not reuse it.

### 3c. R5 §4 — the injected trial, and the census that was started

`docs/gem5-fi/lsu/mdspec/R5-FS-PILOT-EVIDENCE.md` §4 ("S01-F0-W1 span census
结果（真机）") quotes the **injected** trial:

```
CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=17663390 eligible=17663390
                   injected=1 first_eligible_tick=3340645 last_eligible_tick=1271365657485
CHAOS_LSU_TRIGGER_ALARM: mode=EARLY_BIAS fired_at=756413 span=1000000 warmup=1
```

and states the tool's own alarm requires the **uninjected golden** measurement,
so 17,663,390 was deliberately NOT written into `LSQFWD_F0_SPAN`, and that a
no-injection golden census (`--max_faults 0`, ~7.5 h) was started.

**That census (PID 2133313, launched ~2026-10-22 17:44) is no longer alive
(`ps -p 2133313` → not running) and left no output on disk** — a filesystem-wide
scan found no `EARLY_BIAS`, no `3340645`, no `--max_faults 0` run, and no
census outdir. It was killed before writeback or ran in a worktree since
reclaimed. **Verdict: no valid completed census exists.**

## 4. What this lane did

Launched the census properly (see `tools/lsu_census_w1_span.py`), on the frozen
integration binary `lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
sha256 `f4dbfb9a66e0df80…` (the R4-10 build R5 §1 records), carrier
`workloads/mibench/bin/w1_all` (sha256 `adf23d2cd1257fed…`, identical in all
three trees):

```
<gem5.opt> --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_census_S01 \
  configs/se/lsu_proxy.py --cmd workloads/mibench/bin/w1_all \
  --cpu O3 --variant B0 --chaos_lsqfwd --lsq_struct_mode byte_flip \
  --lsqfwd_lsu_tier F0 --lsqfwd_warmup_events 1 \
  --lsqfwd_span_events 9223372036854775807 --max_faults 0 --rng_seed 1
```

Budget note: this is an **SE** carrier, not FS, so `--fs-timeout` does not
apply; the W1 suite simulates ~1270 s of simulated time in ~7.5 h wall
(the 2026-10-11 census ran 27042 s). The census must be allowed to run to
natural termination; the 600 s figure truncates **FS** runs only.

S02 is the same SQ-forward eligibility gate as S01 (only `--bits_to_change 2`
differs — a fault-time parameter), so the stream is structurally identical; a
second run with `--bits_to_change 2` is still required to have a measured value
for the `('S02', 'mibench/bin/w1_all')` key rather than a reasoned reuse.

**Outcome is recorded in `runs/lsu/r6_reports/L23.md` (status at lane exit).**
