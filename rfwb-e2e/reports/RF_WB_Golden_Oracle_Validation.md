# RF/WB Golden Oracle Validation

Native AArch64 `gcc -O2 -static` executions of rfwb_01..05 C01–C05 were used as
the independent golden (25 files under `golden/`). The 25 Control runs were
compared line-by-line on `OUT` records.

Result: 25/25 Controls match golden; 0 mismatches.

Golden is generated only from workload binary execution, never from Fault stdout.
