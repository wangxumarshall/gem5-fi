# FSU-FR03-F5-W5 seed6976623493032354155 审计

- attempt：`attempt-1`
- sample_run_id：`s6976623493032354155`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 91 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '88', 'kind': 'commit', 'outcome': 'errant_commit'} |
| oracle | Masked |
| chain terminal | full |
| stats 非空 | True |
| 无跨 seed 复制 | True |
| decode_guard | False |
| decoded / legacy roots | 0 / 1 |
| admitted（主 fault） | True |
| certified（全 fault 门禁） | True |
| fault 数 | 1 |
| 所有 fault admitted | True |
| 所有 fault certified | True |
| violations（主 fault） | [] |

## 逐 fault 审计

| fault | terminal | admitted | certified | direct parent | tick 单调 | layers | violations |
|---|---|---|---|---|---|---|---|
| 1 | full | True | True | True | True | L0, L1, L1, L2, L5 | [] |

## 边（主 fault）

- `0` → `1`：✓
- `1` → `2`：✓
- `2` → `16`：✓
- `16` → `24`：✓
- `24` → `36`：✓
- `36` → `45`：✓
- `45` → `50`：✓
- `50` → `59`：✓
- `59` → `64`：✓
- `64` → `73`：✓
- `73` → `81`：✓
- `81` → `86`：✓
- `86` → `87`：✓
- `87` → `88`：✓
- `88` → `89`：✓
- `89` → `90`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W5-seed6976623493032354155.md` | `e6db74f687dd6c0c473190286041aec8ab1dddc5bc70801a9bd45e46498a6d6b` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `3928363ae50375714a725642df0371fb4c18425e9504bcbc7f035acf68aeb6f8` |
| `component_manifest.json` | `0e65039ff9d6a6cf767f06a6eff5df957e7f82b75bb31d09e55ded56a46f947b` |
| `inject/array.bin` | `ad54ba81bc46aa236d3fc8e663dda077853e513721685ba78abe940108879f43` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `e1e1c2fc547b55ea25dc39d2f195652137ba78043e423e4863ae7bc7b0da524e` |
| `inject/config.json` | `620dd33c3ab814705d74594090abb5081d956c64c0e0fb5d85ad04c1007686c3` |
| `inject/fault_injections.log` | `162afffecdd2a6c45f27c695aaf67ee091de7d418b20b586459291408e9412ad` |
| `inject/prop_evt.txt.gz` | `6a4629514a9099a298f8fea8390f39f2665ef562760c01b41d86a4d9f7f175c7` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `efc90cc95508ade430447e7ad4a71780293f3d1155a85540783c1d95c186ba50` |
| `manifest.json` | `c73e48e778040e55d611bebf64a32782291c3c42b932a74a92f83df264a38eb4` |
| `oracle.json` | `016459a86826d6430f5963440b4f9ef0520d8536671e425b513cb16ef080b068` |
| `oracle_elements.json` | `6670747ee06586da7e615554fa006e686ea330a467786017dcc83b616e5531fe` |
| `run.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `run.out` | `df635ee7057860e4ec38ac8da5f29fd52d1aafb87afed4c9766b0c4673233914` |
| `stats.txt` | `efc90cc95508ade430447e7ad4a71780293f3d1155a85540783c1d95c186ba50` |

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
| fault 1 永久故障至少一次 activated exposure | PASS |
| fault 1 字段/lane/mask 语义 | PASS |
| fault 1 真实指令解码匹配 | PASS |
| 事件 model_id 与 manifest 一致 | PASS |
| 事件 submodel 与 manifest 一致 | PASS |
| 事件 freq 与 manifest 一致 | PASS |
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
| fault 1 F5 计数/去重/守恒校验 | PASS |
| MD event 0 存在于原始流 | PASS |
| MD event 0 kind 一致 | PASS |
| MD event 0 parent 一致 | PASS |
| MD event 1 存在于原始流 | PASS |
| MD event 1 kind 一致 | PASS |
| MD event 1 parent 一致 | PASS |
| MD event 2 存在于原始流 | PASS |
| MD event 2 kind 一致 | PASS |
| MD event 2 parent 一致 | PASS |
| MD event 16 存在于原始流 | PASS |
| MD event 16 kind 一致 | PASS |
| MD event 16 parent 一致 | PASS |
| MD event 24 存在于原始流 | PASS |
| MD event 24 kind 一致 | PASS |
| MD event 24 parent 一致 | PASS |
| MD event 36 存在于原始流 | PASS |
| MD event 36 kind 一致 | PASS |
| MD event 36 parent 一致 | PASS |
| MD event 45 存在于原始流 | PASS |
| MD event 45 kind 一致 | PASS |
| MD event 45 parent 一致 | PASS |
| MD event 50 存在于原始流 | PASS |
| MD event 50 kind 一致 | PASS |
| MD event 50 parent 一致 | PASS |
| MD event 59 存在于原始流 | PASS |
| MD event 59 kind 一致 | PASS |
| MD event 59 parent 一致 | PASS |
| MD event 64 存在于原始流 | PASS |
| MD event 64 kind 一致 | PASS |
| MD event 64 parent 一致 | PASS |
| MD event 73 存在于原始流 | PASS |
| MD event 73 kind 一致 | PASS |
| MD event 73 parent 一致 | PASS |
| MD event 81 存在于原始流 | PASS |
| MD event 81 kind 一致 | PASS |
| MD event 81 parent 一致 | PASS |
| MD event 86 存在于原始流 | PASS |
| MD event 86 kind 一致 | PASS |
| MD event 86 parent 一致 | PASS |
| MD event 87 存在于原始流 | PASS |
| MD event 87 kind 一致 | PASS |
| MD event 87 parent 一致 | PASS |
| MD event 88 存在于原始流 | PASS |
| MD event 88 kind 一致 | PASS |
| MD event 88 parent 一致 | PASS |
| MD event 89 存在于原始流 | PASS |
| MD event 89 kind 一致 | PASS |
| MD event 89 parent 一致 | PASS |
| MD event 90 存在于原始流 | PASS |
| MD event 90 kind 一致 | PASS |
| MD event 90 parent 一致 | PASS |
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
| physreg census explicitly skipped | PASS |
| B0 运行态配置匹配（inject） | PASS |
| admitted=True | PASS |
| violations=[] | PASS |

**结论：PASS**
