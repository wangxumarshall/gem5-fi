# R6-P Unit continuation (2026-11-05 takeover)

Base: `fix/r6-p-unit-20261104` @ `f502fd19` (20 commits ahead of origin/fi-ding
`f5055a99`, not merged). Scope unchanged: P-F0/P-F5 only (23 RunIDs); the
authoritative P unit has 53. Every plan task = exactly one commit, pushed to
the P branch. No merge into `fi-ding` until the unit is complete.

Authoritative F5 semantics (scheme §F5): permanent stuck fault, from the first
eligible event after warm-up to the end of the run; one bit/field per run;
run-level independent sample. Physical fault identity is distinct from trigger
opportunities, effective changes and propagation instances: one physical
fault may produce many downstream propagation instances and they all keep
the same fault_id. PARTIAL_SUBMODEL stays the unit-level label; no full-model
claim.

## Task 1 — P04-F5 permanent queue-valid fault

- [x] `Queued`: add run-long stuck-valid state + latching API; invalidate
      live ready-queue entries and every later insertion; each birth/skip is
      a propagation instance of the ONE latched fault_id.
- [x] `CHAOSPrefetch` P04QueueValid F5 path: latch once (effective), later
      fires are `noteOutcome(false)` so `fires = injected + no_effect`.
- [x] Behavior test + no-fault control + bounded diagnostic (W2/W8).
- [x] Evidence doc + CENSUS/CLOSEOUT/STATE/PROGRESS + commit/push.
      Result: 6/6 runs terminal L2, Masked, NOT certified (performance-only);
      seeds are deterministic replications; regression 309/10 same set.

## Task 2 — P09-b premature writeback done

- [ ] Implement the done-early submodel at the prefetch-caused dirty
      eviction gate with real storage semantics (not a log-only change).
- [ ] Behavior test + no-fault control; B0 W6/W8 coverage re-checked.
- [ ] Evidence doc + commit/push.

## Task 3 — P09-c dirty premature clear

- [ ] Prematurely clear the dirty state of the prefetch-caused victim at the
      real eviction gate; verify the resulting eviction is a clean evict and
      the dirty data is lost at this level.
- [ ] Behavior test + no-fault control; docs; commit/push.

## Task 4 — P07-a data written to wrong way

- [ ] At the pure-prefetch fill gate write the response data into a distinct
      valid same-set way while the tag stays in the fill way.
- [ ] Behavior test + no-fault control; bounded pilot; docs; commit/push.

## Task 5 — P07-c old tag/valid fill

- [ ] Keep the previous tag/valid combination on a pure-prefetch fill (new
      data lands under the stale tag).
- [ ] Behavior test + no-fault control; bounded pilot; docs; commit/push.

## Task 6 — Remaining blocks and final closeout

- [ ] P07-F0-W8 downstream-consumer evidence gap: investigate, record exact
      block; do not borrow another branch's L5.
- [ ] P03-F0-W9: attempt the real lineage bridge; if impossible, keep the
      local block.
- [ ] P09-F0-W13: search for legal PARSEC assets; if absent, BLOCKED_ASSET.
- [ ] Whole-unit evidence audit, closeout docs, STATE/PROGRESS, push.

## Verification discipline

Per task: build clean (no new warnings), real behavior output quoted, at
least one unaffected regression (`pytest tests -q` failure set compared to the
recorded baseline 309 passed / 10 failed), golden/control run for the
affected workload, then commit and push. Resource cap: <=4 concurrent gem5
processes; disk has ~25 GiB — incremental builds only, no extra full binary
copies without need.
