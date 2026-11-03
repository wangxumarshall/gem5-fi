# FSU-FP04-F0-W6 seed13745869897499398298 审计

- attempt：`attempt-1`
- sample_run_id：`s13745869897499398298`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 7 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '5', 'kind': 'commit', 'outcome': 'errant_commit'} |
| oracle | Masked |
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
| `FSU-FP04-F0-W6-seed13745869897499398298.md` | `1726636022b4be5a6a155c337b34a80bb0ddd189d4326567d00c648c414c5a6f` |
| `census.err` | `ac94070c9fd00342e736472f14f15e1e2f9f917536b7d47fc81b2d472ba7fff3` |
| `census.out` | `c1db93d3f09cac743454aad2722d61f2ff66c24827b03caa7b5506d6b28268a4` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `891c74120ba5d88b144941130972648cb524bd936a6c1451a87716f8cb928f79` |
| `census/config.json` | `b010a1fd254f21c3510593c43d4b245bd330399d8c36309cc4f7921c03212abd` |
| `census/fpu_injections.log` | `3faa7f5a9be0595b5474830742db08f719727710c394a5285dc14a0ae41241b4` |
| `census/stats.txt` | `91199c314d71657728e0dee50c42e87d7e5762b112fbd13c8e78fcffccdd4260` |
| `chain_report.json` | `5a250c5f1ee7e129fd7e1a273f201091fdd37c086864d4b11ff450ec51decdd1` |
| `component_manifest.json` | `90afcf77842a416c98618ba5e2f51f04056e5b0d0a99143a5276e739629c7450` |
| `inject/array.bin` | `76aeb34d0d7f8cec1fc51329381053194ee5a3ac9b83858ff7d18e9ed00dde17` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `f011b8fea5a8aeccc5ee3311c2ad3e69775e1c30d39289f5b96ee588a4cbf0ba` |
| `inject/config.json` | `ddcf69c4e79ce1e03e0cb19fd37bc4550e0434702c7cfd3a20fa6b7af229de28` |
| `inject/fpu_injections.log` | `77ce1abfa98c9ae27490711e40fb20f1651b06d30d9477d415af0f331e291847` |
| `inject/prop_evt.txt.gz` | `ef4a885923b66ac02eb15b62761b6c9cf3fe68330ee672d143644e12919ba2d0` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `f71e3bd42f8d0eafe9a4adaaf10dfc7bc318fcdbf0c0bf97c26ad3d4090e28d7` |
| `manifest.json` | `7d973a20fd145eeb69aa55ad0d3eaf36b0841144087edc673dd37ec2d5d8885e` |
| `oracle.json` | `ef3d0f8edb195e724d5c218cd600afd68dc822eacebd8b3da5a25baca4496b9f` |
| `oracle_elements.json` | `aeb2878f0166875ffc6aa8f039d84f200a7083a5fc639142676c10a02f9cb4b7` |
| `run.err` | `ac94070c9fd00342e736472f14f15e1e2f9f917536b7d47fc81b2d472ba7fff3` |
| `run.out` | `c7ee9a27f8c790783ed0af3420479c3f9fa7f5ef20074753a1baad7404564746` |
| `stats.txt` | `f71e3bd42f8d0eafe9a4adaaf10dfc7bc318fcdbf0c0bf97c26ad3d4090e28d7` |

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
