# FSU-FP06-F5-W5 seed9842723862644389253 审计

- attempt：`attempt-1`
- sample_run_id：`s9842723862644389253`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 521 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '8', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `5`：✓
- `5` → `6`：✓
- `6` → `7`：✓
- `7` → `8`：✓
- `8` → `520`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W5-seed9842723862644389253.md` | `9e58d3a60f8129aedf607f6f245de0aa09b907f8f89c9fdd5c8a8e943b269c18` |
| `census.err` | `412bdbb81cc5c76efc9bbb5f0948c687f5dfa2c45db12966c536f4bfcddd2797` |
| `census.out` | `a83bf9a08c7f01c1600686f92a34d8f8fa586e8f29b2ef0e41175066b7a8496a` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `03fc23c6dc2e1fada3f06059bc60a4ada8e3664509eefcd0fe025ed62021351c` |
| `census/config.json` | `770efc4c8ed4c03f4bcc91a250a8ec388a40384acdbafa45e570c3fbf2e7232a` |
| `census/fpu_injections.log` | `5364c25fa30df322a51a8f82a182e02d8e6a1179076e680a7e746bfc21d7e84f` |
| `census/stats.txt` | `38b10b8ad1d1d89e2e2c59855ceb8e29010790793a8d6937cb443fb2d91963e3` |
| `chain_report.json` | `692dbb4c52a47f83ad28ae3ef1f4dedad33cc5cbd548eff9fa450e6e78cfee81` |
| `component_manifest.json` | `ac7a9a9a30adfde0e95f77c6a569b5f70c9ec9201a8a4de5bf984f81c82ea8a0` |
| `inject/array.bin` | `d1aabaf7f77b908747595340520d1773c05d7019811f5d24d742e208fe14f21f` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `0b9f732ed196a4d64882c6365da2a1dc9066661f1b1523f6c45577d0f47fa5ad` |
| `inject/config.json` | `f7f24b9d20e5479241900abdece7926f37622d0ecb9d07a8ac1acef7417ccb7a` |
| `inject/fpu_injections.log.gz` | `756593f8119078d33c40ddf183ccd206e80bcf2ca7f706b694411771144bf5ef` |
| `inject/prop_evt.txt.gz` | `d9035007a37613390fcdca447fb5858ecaf93fa034841460cbf670abca13ba07` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `39eba401b73e820c93ce46269177446f3e448c4849a02af25fca3beef2a01d16` |
| `injection_log_storage.json` | `8286443290aa3d7fd907f76f1124e4399c18c1024d6ba82ff88072ff5805e171` |
| `manifest.json` | `2f4e2692ae64e0aa656adcd09ca00a4adb8f770da3d757459cc525995ee52984` |
| `oracle.json` | `0f33891d054d0912cd378b082413e4372381c8fb726e68bbe710a66cb6e6549a` |
| `oracle_elements.json` | `a0b46ad7e69379e5ecfc90658828ac23dcf0795fc552c8acec2375bdf7f7e919` |
| `run.err` | `412bdbb81cc5c76efc9bbb5f0948c687f5dfa2c45db12966c536f4bfcddd2797` |
| `run.out` | `209f5cd3f2ea8b3f46b2e614d239b7944692e14b596a48b31ea162b9445bf4d1` |
| `stats.txt` | `39eba401b73e820c93ce46269177446f3e448c4849a02af25fca3beef2a01d16` |

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
| fault 1 sampled_unique = 唯一 exposure_id 数 | PASS |
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
| MD event 5 存在于原始流 | PASS |
| MD event 5 kind 一致 | PASS |
| MD event 5 parent 一致 | PASS |
| MD event 6 存在于原始流 | PASS |
| MD event 6 kind 一致 | PASS |
| MD event 6 parent 一致 | PASS |
| MD event 7 存在于原始流 | PASS |
| MD event 7 kind 一致 | PASS |
| MD event 7 parent 一致 | PASS |
| MD event 8 存在于原始流 | PASS |
| MD event 8 kind 一致 | PASS |
| MD event 8 parent 一致 | PASS |
| MD event 520 存在于原始流 | PASS |
| MD event 520 kind 一致 | PASS |
| MD event 520 parent 一致 | PASS |
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
