# MMU authority change log v3.0.2

Supersedes v3.0.1 (preserved unchanged in the sibling directory).

## Added

- `07_Sample_Matrix.TargetVAExact`: exact instruction VA for M07 R01-R05
  (M07 R04 `0x400d400100`, R05 `0x400d600180`).
- `07_Sample_Matrix.M05DecoyVA`: `0x4010200000` for M05 R01-R05.
- `07_Sample_Matrix.M05DecoyTableBase`: `0` for M05 R01-R05.
- `18_Parameter_Authority_v3.0.2`: per-value source and pilot SHA256.
- `MMU_Parameter_Authority_v3.0.2.json`: machine-readable parity authority
  with W13/W14 source and final F1 pilot provenance.

## Unchanged

All original 40 SampleRunIDs, model/workload/context triples, Seeds
(`N/A_DETERMINISTIC`), controls, pilots, binaries and fault semantics.

## Evidence

- `workloads/mmu/W13/mmu_w13.c` `W13_DECOY_VA 0x4010200000`.
- `workloads/mmu/W14/mmu_w14.c` `CODE_OFF 0x100`, `R05_CODE_OFF 0x180`.
- Final F1 pilots M05 R01-R05 and M07 R01-R05 (SHA256 in the JSON and sheet).
- The older closure pilot TEST-M07-R05 (`0x400d600100`) is superseded by the
  final F1 pilot (`0x400d600180`).
