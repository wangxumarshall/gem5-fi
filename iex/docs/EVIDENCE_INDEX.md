# IEX final experiment evidence index

Spec: `IEX_WHEN_5x3_v3_2026-11-23` — 105 Fault conditions, 35 paired Controls.

Authoritative on-disk results: `/home/sdc/gem5-fi-IEX/when_5x3_v3/results/IEX_WHEN_5x3_v3_2026-11-23` (105 run dirs, 35 control dirs, raw traces retained).

Accepted portable archives (retained outside Git):

| Artifact | SHA256 | Bytes | Purpose | Git path |
|---|---|---:|---|---|
| `fault_runs.csv` | `a65369cee0fa8779961f092185abb53b4b726635fc3028d3e23eadb0782839bc` | 50966 | Authority rows for all 105 Fault conditions | `iex/evidence/fault_runs.csv` |
| `controls.csv` | `8c3f633d376d89ac0e08dbc08d061586c153d4bd0b2b4dd65ade15c3eacadbf2` | 35514 | 35 paired Control records (N, ordinals, census) | `iex/evidence/controls.csv` |
| `injections.csv` | `053a378a503b5b40c04e190375bd3cd29c47f8307b65da48c4c43f7297d335d0` | 30774 | Exact hook/PC/SeqNum/before-after/guard state | `iex/evidence/injections.csv` |
| `propagation_edges.csv` | `79e837913ed44c2b2cea069e592450a09839257754633edf8ca40a92be4f51d5` | 159804 | Dynamic producer→consumer edges and read values | `iex/evidence/propagation_edges.csv` |
| `lifecycle.csv` | `6ca714979faeecb096e82cba684aa0785e5a75f3adcb1e83d24c52656784f169` | 10217 | Issue/execute/writeback/commit/squash ticks | `iex/evidence/lifecycle.csv` |
| `oracle_comparison.csv` | `e01340e4fc5a360acf38e721c6afb53174a0731b30a233103dc82df765883f4b` | 12075 | Selected-slot actual vs independent bigint oracle | `iex/evidence/oracle_comparison.csv` |
| `attempt_history.csv` | `03b4bbdc8f144974de42b25072e755b4629645cb4edff50a5c5f46d1c4f77013` | 100827 | Every attempt, including anomalous attempts | `iex/evidence/attempt_history.csv` |
| `evidence_index.json` | `26f48976cffe6a1c6dd753618b6efa63801de05a53a72a45d03e910ff6d87cee` | 88284 | CaseID → trace/meta path + SHA256 | `iex/evidence/evidence_index.json` |
| `closure.json` | `a8755b93ef83f34b46465aa715535b8affb689608aa9ea5758d539bddcedf979` | 1758 | G13 closure counts and artifact paths | `iex/evidence/closure.json` |
| `gate_status.json` | `b8050b41e88b82ada83bb11363e8f758b962cb15d37fa932ec91c52dbf23b5b2` | 1600 | G01–G13 gate status (all PASS) | `iex/evidence/gate_status.json` |
| `verification_report.json` | `a1d74093bfe843d0b971ac7c427802b2b7f2688aba25a29349b0340f91df234b` | 153 | Independent 105/35 verification (0 failures) | `iex/evidence/verification_report.json` |
| `source.diff` | `36e57b9a4fcacb9272a67cd083fa17a64b53595c90936b029d906ca6f0f1aa53` | 18025 | Exact git diff 1aa61d5..1e8214e | `iex/source/source.diff` |
| `environment.json` | `db96dec748632a3f1805f6eaa5311f19828134d807b1c806fbf27836841285e7` | 1944 | Original experiment environment record | `iex/configs/environment.json` |
| `IEX_WHEN_5x3_v3_Evidence.tar.zst` | `b31f41122bb3a5e492a3f8f3cab2736b00a8ec8a2db08692b439fb2409742523` | 482537 | Accepted core evidence archive (35 files) | `iex/evidence/IEX_WHEN_5x3_v3_Evidence.tar.zst` |
| `IEX_Final_Core_Evidence.zip` | `30685ab3c4923b1d9374bc0bf702053c380fb699124080753aac55e1c9ef3fc9` | 2974874 | 105 CASE_SUMMARY + 35 CONTROL_SUMMARY + integrity | `iex/evidence/final_package/IEX_Final_Core_Evidence.zip` |
| `IEX_Final_Raw_Traces.tar.zst` | MISSING | 0 | Authoritative raw traces: 105 faults + 35 controls | `iex/evidence/final_package/IEX_Final_Raw_Traces.tar.zst` |
| `IEX_Final_Experiment_Results.xlsx` | `a0ab768a4252d03850a0ddba62553cc37bf648b291e7da5a99ba076822cd5ae1` | 59970 | Final results workbook | `iex/evidence/final_package/IEX_Final_Experiment_Results.xlsx` |
| `IEX_Final_Reproduction_Info.zip` | `da4690a65af19a0f865c7dde8451db3d154e19779b9cecf81b1e60d155a8c143` | 257187 | Reproduction metadata, diffs, scripts | `iex/evidence/final_package/IEX_Final_Reproduction_Info.zip` |
| `IEX_Final_Workloads.zip` | `6340aadb0e94d0b49165a0377df5cf296dcedc10f29d650a54d4278292017160` | 142777 | 35 workload sources/ELFs/manifests | `iex/evidence/final_package/IEX_Final_Workloads.zip` |

## External archives (not stored in Git)

| Artifact | SHA256 | Bytes | Purpose |
|---|---|---:|---|
| `when_5x3_v3/delivery/IEX_WHEN_5x3_v3_2026-11-23/All_Raw_Traces.tar.zst` | `d0a800b0707cff6c28e73e0f8843456d4e540b7723480c192d8116f08b7e1f08` | 695193753 | All attempts (6,306 entries; restorable by CaseID) |
| `when_5x3_v3/delivery/IEX_WHEN_5x3_v3_2026-11-23/IEX_WHEN_5x3_v3_Source_and_Workloads.tar.zst` | `434a3adf06edaa89e3b3a00fbc8d5ceb8ea5660bbd4e44caa8ac56cf370e9046` | 150859 | Accepted source/workload archive |
| `when_5x3_v3/delivery/IEX_WHEN_5x3_v3_2026-11-23/SHA256SUMS_ALL` | `4da7d02801ae41c370f966689ccdc7a05bde7737be438908f4acf57d9cf6a828` | 3173 | Original accepted hash list |

## Completeness notes

- `INCOMPLETE_CASES.txt` in the core evidence package says: "None. All 105 Fault cases have a complete causal chain."
- The final raw-trace archive contains 105 fault cases and 35 control cases, one authoritative attempt per case.
- `All_Raw_Traces.tar.zst` additionally preserves every historical attempt, including the one anomalous attempt retained by policy.
- Hash verification was performed with `sha256sum -c` against `final_package/FILES_SHA256.txt`; all five files passed.
