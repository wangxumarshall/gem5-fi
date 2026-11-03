# FSU-FP06-F5-W6 seed13519425898416439123 审计

- attempt：`attempt-1`
- sample_run_id：`s13519425898416439123`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 521 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '7', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `4`：✓
- `4` → `5`：✓
- `5` → `6`：✓
- `6` → `7`：✓
- `7` → `520`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W6-seed13519425898416439123.md` | `0e8e7d98ab6c10518afb23b57410f952cc1b9235c9b0b1a3fdc394086e2aa317` |
| `census.err` | `c0d7ed0b8024da977ee10538dcd63845e4793271dc417a5badeb0978e48fbec2` |
| `census.out` | `aaa3ad592bed190d0c07bea5f2eff404f94545e4d4749bebe8a33e53046b0eec` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `84d7807d727803690278bac6ab11f7a4498b237ea286a8712f7f62093f1e81ce` |
| `census/config.json` | `a4b9d25d50c0332bab66b53434ded37a97f6cc71e6191660246fea2b2d2490ad` |
| `census/fpu_injections.log` | `7d4a2321eb81215bafc86524bac039b3535e5a09895fc42f5bbe3d1f14e430b2` |
| `census/stats.txt` | `390b7637536757b9adbd7a9990ed3f76fc59b137a2e00f90a88cfdf010d50778` |
| `chain_report.json` | `0a4affe46ab867b06ffb2b5c7ee4cb382d0e52ea34fc5f82ea625cabb2bd6450` |
| `component_manifest.json` | `c86424777fb1d33622795517a1d025e85bc3c789a1b2e85d6de8f71166e42820` |
| `inject/array.bin` | `5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `2499c21c398d9aa5a02536e77c21827cbed02ffdf7a0e2c3db43811133e01ba3` |
| `inject/config.json` | `3f26f86e01b13d978fedcb21716906b0a816e860e013f9a0b3727f1faea9f9b7` |
| `inject/fpu_injections.log` | `3073e0a13e5568a8a8955218ee99a47791431b1fa33d32e6cfa825b01616ee05` |
| `inject/prop_evt.txt.gz` | `886dc149502237c076e923cd834d0631c5afd6f0b26833090e516fd2e85854d9` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `5513078a0843558544a2e2a693ef15caa50e4dd3b5b8292544c857ed38bda674` |
| `manifest.json` | `c20c2ee6eb81cd8fa24ec27ac47177b7c212f594d34b7b0d27a2060eae4231f8` |
| `oracle.json` | `db7ecdfd8f7c824cc3177b42d99f6e62c9c4042ffe1983b9a5092516aaae882a` |
| `oracle_elements.json` | `6a7964f37f0bbb591f5a12a01b289bef578fe685fdb20b7d42528510026d60aa` |
| `run.err` | `c0d7ed0b8024da977ee10538dcd63845e4793271dc417a5badeb0978e48fbec2` |
| `run.out` | `d510a56bbb15cf7e2c6f1de82dcee05581ec0d88e7475a074c33dd91f259e7e7` |
| `stats.txt` | `5513078a0843558544a2e2a693ef15caa50e4dd3b5b8292544c857ed38bda674` |

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
| MD event 4 存在于原始流 | PASS |
| MD event 4 kind 一致 | PASS |
| MD event 4 parent 一致 | PASS |
| MD event 5 存在于原始流 | PASS |
| MD event 5 kind 一致 | PASS |
| MD event 5 parent 一致 | PASS |
| MD event 6 存在于原始流 | PASS |
| MD event 6 kind 一致 | PASS |
| MD event 6 parent 一致 | PASS |
| MD event 7 存在于原始流 | PASS |
| MD event 7 kind 一致 | PASS |
| MD event 7 parent 一致 | PASS |
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
