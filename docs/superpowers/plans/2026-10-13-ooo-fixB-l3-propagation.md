# Plan — OOO FIX-B: real L3 propagation chain for the decode fault family

> Task owner: Subagent-B (worktree `.claude/worktrees/ooo-fixB`, branch
> `ooo/l0l5-fixB`, base 2a25073). Central mandate: replace
> `L3=unsupported` for the decode family with a REAL source-consumer
> propagation chain built from (L0 injection event ↔ committed-instruction
> trace) joins — no ref-vs-empty-run proxies, no PRF-write-liveness
> proxies, no fabricated hops.

## Facts established by code reading (2026-10-13)

- `DynInst::seqNum` (`dyn_inst.hh:124`, public `InstSeqNum`) is the
  pipeline sequence number assigned in `Fetch::buildInst`
  (`fetch.cc:1011`, `cpu->getAndIncrementInstSeq()`). The task calls it
  `seqencNum`; there is no separate `seqencNum` member in gem5 v25.1.
  v2 ctrace column `seqencNum` = `head_inst->seqNum`; decode log field
  `sn=` = the injected DynInst's `seqNum` (same convention the legacy
  dest_reg_sub line already uses, CHAOSDecode.cc:414).
- The decode hook (`fetch.cc:1257 maybeCorruptEncoding`) runs BEFORE
  `buildInst` (`fetch.cc:1293`) in the SAME do-while iteration, with no
  break in between (plain inst: buildInst same iteration; macroop
  replacement: first microop built same iteration with
  `macroop == replacement`). So the injected DynInst's seqNum is knowable
  one tick later via a build-join, NOT at injection time — the sn join is
  implemented as a deferred log line completed at `noteBuildInst`.
- Commit trace row (v1, pinned): `seq,tid,tick,pc,op,ndest[,c,a,p,v]*`,
  producer CHAOSCommitTrace (commit.cc:1286 hook, AFTER the commit
  renameMap setEntry loop), consumer tools/commit_diff.py.
  `ooo_observation.py:298 tick_from_ctrace_raw` reads CSV col 2 as tick
  (v1 assumption) — that file is NOT mine to change; v2 is therefore
  strictly opt-in (`--ctrace_v2`, default off = byte-identical v1) and
  the caveat is documented for the observation-chain owner.
- Squashed instructions retire from the ROB via commit.cc:965 WITHOUT
  passing commitHead → they never appear in the ctrace; a squash event
  line is genuinely additive. ALL squash paths (trap/TC/squashAfter/
  mispredict) converge on `ROB::squash` → `ROB::doSquash` (rob.cc:325,
  per-inst loop at :355) — one hook point covers everything.
- Squash-line refinement: doSquash has the DynInst (post-rename), so the
  squashed inst's src triples ARE readable there. Line format
  `# squash <sn> <tick> [<class> <arch> <phys>]...` keeps the pinned
  `# squash seqencNum tick` prefix and makes squashed-consumer matching
  actually provable (sn-only would be unprovable — no src info).
- L0 parse (`ooo_observation.parse_injection_log`) keys events on the
  `faults_injected: N` line-final marker; extra `k=v` tokens are parsed
  into the event dict (`sn=123` becomes `rec["sn"]=123`). The deferred
  decode line keeps the marker as its FINAL field, so the contract holds.

## Units (one commit each, `[OOO][FIX-B]` prefix, no push)

### Unit 1 — CHAOSCommitTrace v2 rows (seqencNum + source triples)
Files: `CHAOS/gem5/src/cpu/o3/CHAOSCommitTrace/CHAOSCommitTrace.{hh,cc,py}`,
`configs/se/ooo_proxy.py` (new `--ctrace_v2`, default False).
- New param `v2` (Bool, default False). v2=false → byte-identical v1
  output (hard requirement).
- v2 file layout: first line `# ctrace v2 <format>`, then rows
  `seq,seqencNum,tid,tick,pc,op,ndest[,c,a,p,v]*,nsrc[,c,a,p]*`
  (seqencNum = DynInst::seqNum; per-src class/arch/phys from
  renamedSrcIdx/srcRegIdx, null phys → `-1` like the dest convention).
- src value columns: NOT written (pinned format has no src val; reading
  them back from the phys regfile at commit would give the CURRENT
  value, not the value the inst read — honest omission).
- Verification: clean build -j16 (zero new warnings); old binary
  `/home/sdc/gem5-fi-ding/build/ARM/gem5.opt` (sha 1a618953…) vs new
  binary on `workloads/ooo/smoke` × {no-injection, decode injection}:
  FINAL checksums identical all 4 runs; v1-default ctrace gunzipped
  byte-identical old-vs-new; v2 ctrace parses, seqencNum column
  non-empty, src triples not all-zero. Record new binary sha256.
- [x] implemented  [x] built clean  [x] FINAL identical (no-inj + inj:
      45737cc9a76c0dce all 4 runs; decode log byte-identical)
- [x] v1 trace byte-identical (no-inj + inj, 309399 rows)
- [x] v2 trace sane (marker + 309399 rows, 0 empty seqenc, 308674 rows
      with srcs, 615408 nonzero src triples; FINAL unchanged)
- [x] committed

### Unit 2 — squash observation (`# squash` events)
Files: `CHAOSCommitTrace.{hh,cc}` (`traceSquash`), `cpu.hh` (pointer +
setter, CHAOSDecode pattern), `rob.cc` (one-line hook in doSquash).
- `traceSquash(const o3::DynInst*)` writes
  `# squash <seqNum> <tick> [<class> <arch> <phys>]...` (srcs of the
  squashed inst; nsrc=0 → bare line). Only when v2 && writeLog. Read-only.
- ROB hook: `if (cpu->chaosCommitTraceV2) cpu->chaosCommitTraceV2->traceSquash((*squashIt[tid]).get());` — hmm, DynInstPtr; pass raw ptr.
- Verification: incremental build; branch_mispred workload (guaranteed
  squashes) with --ctrace_v2: `# squash` lines present, count>0, sn
  values absent from the committed rows; FINAL checksum identical to
  no-tracer run (read-only proof). smoke no-inj FINAL unchanged.
- [x] implemented  [x] built (incremental, clean link)
- [x] squash lines observed on branch_mispred: 5,091,434 events
      (e.g. `# squash 93 343420 0 4 82 7 0 0 7 523 523 2 0 44`)
- [x] squashed sn ∉ committed rows: awk hash-set overlap of
      {squash sn} x {row seqencNum} = 0 / 5,091,434 x 8,612,690
- [x] FINAL unchanged: smoke no-inj + inj both 45737cc9a76c0dce; v1
      traces still byte-identical to old binary; v2 ROWS identical to
      unit-1's v2 output (squash lines purely additive)
- [x] committed

### Unit 3 — CHAOSDecode sn join (deferred injection line + build join)
Files: `CHAOSDecode.{hh,cc}`, `fetch.cc` (one-line hook after buildInst).
- CHAOSDecode: `pending` buffer (std::ostringstream + pending_repl
  StaticInstPtr + pending_count). All 8 fetch_decode success paths write
  into `deferLogLine(repl)` instead of the stream, WITHOUT the marker;
  `noteBuildInst(const DynInstPtr&)` (called from fetch.cc right after
  buildInst) matches `staticInst == pending_repl || macroop ==
  pending_repl`, appends `, sn=<seqNum>, faults_injected: <count>` and
  writes the line. Defensive flushes (sn=na) on next-injection and in an
  exit callback. RNG draws untouched.
- Honest-skip lines: unchanged (written directly; they carry no marker
  increase).
- Verification: incremental build; decode injection run
  (mode=opcode_bitflip, fixed seed) with --chaos_ctrace --ctrace_v2:
  decode log line ends with `, sn=N, faults_injected: 1` and N appears
  as seqencNum of a v2 ctrace row (join proof); FINAL identical to the
  same run on the old binary (RNG stream untouched).
- [ ] implemented  [ ] built  [ ] sn join proven against real ctrace
- [ ] FINAL identical  [ ] committed

### Unit 4 — commit_diff.py v2-aware parsing (backward compatible)
Files: `tools/commit_diff.py`.
- `iter_records`: skip known `#` annotations (`# ctrace v2 …` header,
  `# squash …` events — grammar-validated, anything else `#`-prefixed is
  a loud TraceError). Row version detection: file-level marker if seen;
  otherwise per-line exactly-one-fit (v1: len==6+4*ndest; v2: len==
  8+4*ndest+3*nsrc with nsrc at col 7+4*ndest); both-fit → loud error,
  neither-fit → loud error.
- Rec gains seqenc/nsrc/srcs (None for v1 rows). Comparison semantics
  unchanged (v2 extra fields never classified); JSON gains
  ref_format/run_format ("v1"/"v2") keys only.
- Verification: real v1 pair (regression: byte-identical report vs
  pre-change tool output on same inputs); real v2 pair from smoke
  no-inj vs inj; tools/tests/test_commit_diff_seqrange.py still passes.
- [ ] implemented  [ ] v1 regression identical  [ ] v2 pair parses
- [ ] seqrange test passes  [ ] committed

### Unit 5 — tools/ooo_l3.py (offline L3 builder) + tools/tests/test_ooo_l3.py
- API: `build_l3(component, l0_events, run_ctrace_path, coverage,
  first_divergent_commit) -> dict` (pinned schema: status ok/unsupported/
  error, method "source_read", injected{seqencNum,pc,tick,field,bit,
  orig,new}, hops[{seqencNum,seq,pc,op,via_src{c,a,p},dest{…},
  committed}], squashed_consumers or n/a, first_divergent_commit
  passthrough, caveat).
- Chain rule (no fabrication): join L0 event sn → v2 ctrace row
  (seqencNum). BFS over subsequent rows: consumer = row with a src
  triple equal to a chain node's dest triple (class+phys dataflow key,
  arch as pinned consistency). Kill rule: a later row whose DEST phys ==
  P (redefinition) ends P's match window (commit order = program order).
  Squash events with matching src triples → squashed_consumers
  (committed=false). Window end: first_divergent_commit (if given) else
  trace end, with a bounded scan budget and honest truncation notes.
  Unprovable links → counted `unresolved`, never silently dropped.
  v1 trace (no seqencNum) → status unsupported with reason. Missing sn
  in L0 events → unsupported with reason (pre-FIX-B logs).
- Tests (real assertions, hand-built fixtures): v2 row parse, version
  auto-detect old/new, L0 join, single-hop chain, multi-hop BFS with
  kill rule, squashed consumer via `# squash` line, v1 incompat →
  unsupported, no-sn → unsupported, first_divergent_commit windowing.
- End-to-end: real smoke v2 trace + real decode_injections.log →
  build_l3 returns ok with a real chain; every hop's via_src triple is
  grep-verifiable in the trace file.
- [ ] tool  [ ] tests green  [ ] end-to-end on real smoke trace  [ ] committed

## Cross-unit honesty gates
- Every C++ change is read-only w.r.t. simulation state; proof = FINAL
  checksum identity on smoke (no-inj and inj) between old binary
  (1a618953…) and the new binary, re-run after each unit.
- v1 default behavior byte-identical (trace bytes + JSON of commit_diff).
- No push (central owner integrates); commits carry `[OOO][FIX-B]`.
