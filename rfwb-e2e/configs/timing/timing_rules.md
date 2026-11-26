# RF/WB dynamic-timing rules

## Eligible events

The injector counts eligible events at the exact point where a fault could be
applied.  Count-only (`RFWB_MODE=count`) and fault (`RFWB_MODE=fault`) runs use
the same event definition.

| Model | Eligible event | Meaning |
|---|---|---|
| M001 | `M001_MARKER_READ` | consumer-side marker read of the producer PhysRegId |
| M002 | `M002_VEC_ELIGIBLE` | one per vector instruction seq; destination byte is writable |
| M003 | `M003_CONSUMER_READ` | read-port consumer read selected by consumer PC |
| M004 | `M004_ELIGIBLE` | executed, non-squashed, non-memory, non-control completion event |
| M005 | `M005_WB` with a matching `M005_CONSUMER_RENAME` | same PhysRegId + generation, Rename AFTER WB |

For M005, a Producer WB whose consumer Rename happened **before** the WB is not
eligible.  This is the corrected definition; the historical Batch02 M005 scan
counted all 8 WBs and is invalid for timing selection.

## Ordinal selection

For eligible count `N`:

```text
T01 = ceil(0.10 * N)
T02 = ceil(0.50 * N)
T03 = ceil(0.90 * N)
```

A condition is runnable only if `N >= 3` and the three ordinals are distinct.
Otherwise the timing plan marks it `BLOCKED` and no fault is injected.

## How the run selects the event

- M001–M004: `RFWB_ORDINAL=<Txx>`; the injector fires on the `Txx`-th eligible
  event (1-based).
- M005: `RFWB_TARGET_SEQ=<producer seq>`; the injector fires on the WB with that
  sequence.  This is required because the raw WB counter also counts ineligible
  (Rename-before-WB) events; the corrected ordinal cannot be used as a raw
  counter.
- Every sample is a separate gem5 process, so all model state is reset.
- If the selected event never occurs, no injection event is written; the run is
  classified `NOT_ACTIVATED` and is never converted to a fake fault.

## Authoritative values

`frozen_timing_plan.tsv` records the 25 authoritative (model, context) rows.
`corrected_prescan_summary.tsv` is the frozen M005 correction table.
`evidence_sample_ids.tsv` maps each condition to the exact historical sample
ID (six M005 T02/T03 samples use the `-A3` rerun ID) and M005 target sequence.

M005 corrected N and ordinals:

| Context | N | T01/T02/T03 |
|---|---:|---|
| C01 | 6 | 1 / 3 / 6 |
| C02 | 6 | 1 / 3 / 6 |
| C03 | 8 | 1 / 4 / 8 |
| C04 | 6 | 1 / 3 / 6 |
| C05 | 8 | 1 / 4 / 8 |

M001–M004 must use their own scan N; do not copy M005 values.

## Producer sequences are run-specific

`target_seq` is a guest dynamic instruction sequence number, not a static PC.  It
shifts with the guest initial stack layout (notably the workload path string).
The reproducible design invariant is **N and the ordinal position**; the producer
sequence is the identity of the selected WB in that particular run.

The runner uses the canonical 51-byte workload path when the project is at the
frozen path, otherwise a stable 51-byte symlink path under `/tmp`.  This keeps N
and the T01/T02/T03 ordinals identical across checkout locations.  On the frozen
path the absolute sequences also match; elsewhere they may differ by a constant.

`--strict-target-seq` is available for canonical-path byte-level review.  The
default validation compares N, ordinals, status, and sample IDs, and warns on
M005 producer-sequence shifts.
