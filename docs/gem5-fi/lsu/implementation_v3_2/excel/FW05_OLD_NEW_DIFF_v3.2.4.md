# FW05 diff v3.2.3 → v3.2.4

| Field | v3.2.3 | v3.2.4 | Reason |
|---|---|---|---|
| WorkloadPath | `.../workloads/fw05_forward` | `.../FW05_Workload_Archive/bin/fw05_forward` | Archive script repaired; the archive binary is the single runnable input. |
| WorkloadSHA256 | `0cf40509…` | unchanged | Exact pilot binary, SHA unchanged. |
| Oracle | `67afad307642983e` | unchanged | Golden. |
| FaultModel | Wrong-Source Store-to-Load Forwarding | unchanged | Frozen definition. |
| Baselines | byte_flip/prob 0 | fw05_older_src/prob 0 added (v3.2.9 evidence) | Strict matched control; fault side rerun on the same final binary. |
| History | W8 alignment retained | retained | No historical row deleted. |
