# FSU-FP04-F0-W5 seed10590959326789771992 审计

- attempt：`attempt-1`
- sample_run_id：`s10590959326789771992`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 7 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '5', 'kind': 'commit', 'outcome': 'errant_commit'} |
| oracle | SDC |
| chain terminal | full |
| stats 非空 | True |
| 无跨 seed 复制 | True |
| decode_guard | True |
| decoded / legacy roots | 1 / 0 |
| admitted（主 fault） | True |
| certified（全 fault 门禁） | True |
| fault 数 | 1 |
| 所有 fault admitted | True |
| 所有 fault certified | True |
| violations（主 fault） | [] |

## 逐 fault 审计

| fault | terminal | admitted | certified | direct parent | tick 单调 | layers | violations |
|---|---|---|---|---|---|---|---|
| 1 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |

## 边（主 fault）

- `0` → `1`：✓
- `1` → `2`：✓
- `2` → `3`：✓
- `3` → `4`：✓
- `4` → `5`：✓
- `5` → `6`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP04-F0-W5-seed10590959326789771992.md` | `75ccced25489628075c2919dc00cfe60039d8dd91991fed4b5587ba16673c0bf` |
| `census.err` | `412bdbb81cc5c76efc9bbb5f0948c687f5dfa2c45db12966c536f4bfcddd2797` |
| `census.out` | `a83bf9a08c7f01c1600686f92a34d8f8fa586e8f29b2ef0e41175066b7a8496a` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `62de99ae95c26a3b134dece10eca231382efaef05135e67206a33d680643fa94` |
| `census/config.json` | `594f1f1944afaa8f7000a9214aac51f36f35394bec0533249a35245465e68c6f` |
| `census/fpu_injections.log` | `a05a9807a610db15416c1398f34e24fecba5944ff6c9c3a1bfc37cfedf1db11a` |
| `census/stats.txt` | `b7a055186968df53ed1e0dffb169b00ce34016946205345776598a0332cd167f` |
| `chain_report.json` | `cffd442c838855f08adff3a213f54cd1b79c1f0a4f3b5953b6c21d890aa89ba6` |
| `component_manifest.json` | `845ee506f98bce2fcb32c2f013b734bbfd1de1cf17b32fda210e80930069417e` |
| `inject/array.bin` | `f27c6f638c8467fb1c8b14857e874d871b3c5fcb54827f9c78b6df3ac113868c` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `36136a877be5fd21f9dc636e8c79d84e9772c28160978edc579b95ad5df2f983` |
| `inject/config.json` | `ffe57baac97294c7df561ca7030ba87dc251691134e399f96e08dbf9c365ebcd` |
| `inject/fpu_injections.log` | `4b71903057b5528fd35a1636fc51799518f8d4fe00d091588edbe386b503a625` |
| `inject/prop_evt.txt.gz` | `93ae50bd420bb8b9bec673fde42547a74454109a9e862bc3cb3b58f0540f093f` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `69d8aba4bf9738194914fe23953bc02ce830e182d2f5b5b05c701fabde0359b4` |
| `manifest.json` | `1cb12ee2e80f22168b6275345a5192fa73f3066b30df317788dc28d3656189e4` |
| `oracle.json` | `9be710533c3788f41f4f9457af40b56fba02d29c8726493586e2ba21a6f6e69b` |
| `oracle_elements.json` | `ed7d98c162c7cf2b0d252c0fabdb3ad7c2653c4389d5f7bb862b00122560da03` |
| `run.err` | `412bdbb81cc5c76efc9bbb5f0948c687f5dfa2c45db12966c536f4bfcddd2797` |
| `run.out` | `7cbf7598334b1572bcd278e6bba6b94457ffe1c69f4570ddaf0730fda2424e3f` |
| `stats.txt` | `69d8aba4bf9738194914fe23953bc02ce830e182d2f5b5b05c701fabde0359b4` |

## 审计检查

| 检查 | 结果 |
|---|---|
| seed Markdown 存在 | PASS |
| RunID 一致 | PASS |
| seed/sample_run_id 一致 | PASS |
| workload 二进制身份一致 | PASS |
| gem5 二进制身份一致 | PASS |
| 源码 HEAD 一致 | PASS |
| prop_evt 存在 | PASS |
| prop_evt 未截断（reason=ok） | PASS |
| 事件身份全为本 seed（越界 0） | PASS |
| scheduled(1) = fault_roots(1) | PASS |
| 每个 injected fault 均真实激活 | PASS |
| fault 1 字段/lane/mask 语义 | PASS |
| fault 1 真实指令解码匹配 | PASS |
| decode_guard: 所有 root 含真实解码字段 | PASS |
| 事件 model_id 与 manifest 一致 | PASS |
| 事件 submodel 与 manifest 一致 | PASS |
| 事件 freq 与 manifest 一致 | PASS |
| 事件 load_id 与 manifest 一致 | PASS |
| fault 1 全链 field 一致 | PASS |
| 重算 admitted_faults 一致 | PASS |
| 重算 truncated 一致 | PASS |
| 事件流 fault 数 = 注入数 | PASS |
| 所有 fault 均 admitted | PASS |
| 所有 fault 均 certified | PASS |
| fault 1 terminal 一致 | PASS |
| fault 1 violations 一致 | PASS |
| fault 1 admitted 一致 | PASS |
| fault 1 certified 一致 | PASS |
| MD event 0 存在于原始流 | PASS |
| MD event 0 kind 一致 | PASS |
| MD event 0 parent 一致 | PASS |
| MD event 1 存在于原始流 | PASS |
| MD event 1 kind 一致 | PASS |
| MD event 1 parent 一致 | PASS |
| MD event 2 存在于原始流 | PASS |
| MD event 2 kind 一致 | PASS |
| MD event 2 parent 一致 | PASS |
| MD event 3 存在于原始流 | PASS |
| MD event 3 kind 一致 | PASS |
| MD event 3 parent 一致 | PASS |
| MD event 4 存在于原始流 | PASS |
| MD event 4 kind 一致 | PASS |
| MD event 4 parent 一致 | PASS |
| MD event 5 存在于原始流 | PASS |
| MD event 5 kind 一致 | PASS |
| MD event 5 parent 一致 | PASS |
| MD event 6 存在于原始流 | PASS |
| MD event 6 kind 一致 | PASS |
| MD event 6 parent 一致 | PASS |
| 链 admitted=True | PASS |
| 链 certified=True | PASS |
| 链 violations=[] | PASS |
| 存在 admitted fault | PASS |
| MD 逐 fault 终局表存在（legacy 单 fault 行） | PASS |
| fault 1 MD 覆盖主链全部事件 | PASS |
| fault 1 MD/原始流 direct parent | PASS |
| fault 1 MD 逐 fault 终局行存在 | PASS |
| fault 1 MD terminal 一致 | PASS |
| fault 1 MD admitted 一致 | PASS |
| fault 1 MD certified 一致 | PASS |
| MD terminal 与 chain_report 一致 | PASS |
| MD admitted/certified 与 chain_report 一致 | PASS |
| evidence_sha256.json 存在 | PASS |
| 证据 SHA-256 全部匹配（失配 0） | PASS |
| stats.txt 非空 | PASS |
| B0 运行态配置匹配（census） | PASS |
| B0 运行态配置匹配（inject） | PASS |
| admitted=True | PASS |
| violations=[] | PASS |

**结论：PASS**
