# Inputs and initialization

This workload has no external input or initialization file. All state is:

- `static uint64_t buf[64];` — zero-initialized by the C runtime.
- `static uint64_t slow[1 << 20];` — zero-initialized by the C runtime.
- Loop index `i` drives addresses, stored values and the cold-load index.

The archive therefore contains no binary input blob; the source completely
determines the initialization.
