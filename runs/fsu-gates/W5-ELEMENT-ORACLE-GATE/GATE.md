# W5 element-oracle no-fault gate

- suite：`polybench-fp-v1` v1
- suite_hash：`7282decf461243a8fdff38b6f99f66112c18027ee9a9b0a7dd057c4e2a0a7493`
- native reps：3；gem5 B0 reps：3
- 结论：PASS

| program | native SHA-256 | gem5 SHA-256 | mismatch | FINAL | ok |
|---|---|---|---|---|---|
| gemm | `babce53409efc22e…` | `babce53409efc22e…` | 0 | 116849d3adf3227b | PASS |
| 2mm | `23eb863deda56bcb…` | `23eb863deda56bcb…` | 0 | 41ebd3d0a77ab3d2 | PASS |
| lu | `46eb754c53cf2ecf…` | `46eb754c53cf2ecf…` | 0 | 74ffe5eb77ea9257 | PASS |
| cholesky | `ad54ba81bc46aa23…` | `ad54ba81bc46aa23…` | 0 | ea7e0d0e7c86582d | PASS |
| jacobi-2d | `dad9731239bff917…` | `dad9731239bff917…` | 0 | dc867b5f02998c1e | PASS |
