# MMU Repeatability Research Analysis

## 1. Activation stability

Across the 10 repeats, activation comparison is {"MATCH": 10}. 10/10 are exact MATCH; no model/fault parameter was changed.

## 2. Key propagation nodes

Propagation comparison is {"MATCH": 10}; 10/10 are exact event-level MATCH. The normalized signature uses event kinds, causal order and key state/address semantics; run IDs/ticks are compared only when they are actually stable.

## 3. Why contexts differ

The formal design deliberately uses different access modes and consumer paths. M03 R01-R04 are data-side reads squashed before architectural update; M03 R05 is an Execute consumer that commits the wrong code page. M07 R01 is a write bypass; R05 is an indirect-branch Execute bypass. These are context differences, not model instability.

## 4. Squash and detection repeatability

M03 R01 and M06 R02 are included in the repeat set. Their terminal and propagation status are compared separately; squash is not reported as detection and detection is not reported as generic masking.

## 5. Trace differences

For M01 R01 the repeat trace is event-for-event identical to the formal trace after normalizing only run_id/sample_run_id; the guest terminal file is byte-identical. For other samples the per-sample comparison records whether this identity holds, or reports the actual differing events. No differing event is deleted.

## 6. Stable diagnostic signals

At the simulator-assisted level, fault site, state delta, TLB/PTW path and downstream consumer are directly comparable. At the blinded level, only event-kind/guest-symptom features are used; the earlier GT-derived UpstreamPathClass is not used.

## 7. Simulator-only signals

TLB entry identity/generation, modified PFN, PTW partial-entry internals, permission-grant intermediate decisions and exact request PA remain SIMULATOR_INSTRUMENTATION_ONLY or UNKNOWN for production hardware.

## 8. Where/When/How narrative

Where: fault site and state owner. When: activation/consumption ordering. How: translation/permission/PA effect and downstream consumer. The repeat comparison preserves all three axes rather than collapsing them into a single success flag.

## 9. Real ARM case correspondence

M01 remains the functional match for a stale DTLB translation after correct maintenance, but the gem5 target is l2_shared, not the DTB. The correspondence is functional/propagation-level, not a claim of identical microarchitecture.

## 10. Limits

There are only two observations per context (formal + one repeat). This cannot establish statistical stability, cross-workload generalization or classifier accuracy. No such claim is made.
