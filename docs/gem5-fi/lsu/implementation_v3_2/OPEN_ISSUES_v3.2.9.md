# Open issues — LSU v3.2.9

1. **SP05 has no consumer workload.** All five pilots commit the target store
   and stop at `STORE_COMMITTED_LANE_NOT_READ`; `store_path` has no later load
   of the target address. A workload where a later load reads the dropped
   store is required before any SDC claim.
2. **SP05 drops the cache write.** The frozen premature-completion semantic
   completes the store before its send. This is a lost-write fault, not early
   visibility; if the researcher intended "complete early but still write",
   that is a different model and needs a new frozen definition.
3. **SQ03 is timing-only at the application layer.** The probe shows identical
   forwarded data and checksums; early `_canWB` cannot change a load's value
   through SQ forwarding.
4. **Probe control lacks store_mem instrumentation.** Without an injection the
   store is not registered as a fault store, so the control has no
   `store_wb`/`store_mem` nodes; the matched evidence is the identical
   forwarding multiset and checksum, not a control cache-write tick.
5. **Full pytest is not green in this environment.** 39 passed, 2 failed:
   `test_claim_concurrency` d/e are refused by the admission guard because
   disk free 22.9 GiB < red line 70.6 GiB. The five former fixture errors are
   fixed (pytest-check 2.4.0 + the explicit `check` fixture).
6. **SP05 commit node is absent by construction.** The hook fires after
   `commitStores`; the store is committed by definition, so the terminal rule
   treats `writebackStores_prematureComplete` as post-commit. Recorded rather
   than fabricating a commit node.
7. **Excel WorkloadPath is absolute** to this worktree; the archive README
   documents the portable form (`FW05_Workload_Archive/bin/...`).
8. **No 60-sample formal run.** ConfigFrozen stays NO; global Warm-up/ROI
   still need researcher confirmation.
