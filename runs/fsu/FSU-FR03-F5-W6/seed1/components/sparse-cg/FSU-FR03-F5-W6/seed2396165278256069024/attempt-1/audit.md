# FSU-FR03-F5-W6 seed2396165278256069024 审计

- attempt：`attempt-1`
- sample_run_id：`s2396165278256069024`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 152 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '149', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `3`：✓
- `3` → `11`：✓
- `11` → `16`：✓
- `16` → `19`：✓
- `19` → `27`：✓
- `27` → `35`：✓
- `35` → `36`：✓
- `36` → `37`：✓
- `37` → `45`：✓
- `45` → `55`：✓
- `55` → `63`：✓
- `63` → `72`：✓
- `72` → `80`：✓
- `80` → `83`：✓
- `83` → `88`：✓
- `88` → `96`：✓
- `96` → `105`：✓
- `105` → `114`：✓
- `114` → `125`：✓
- `125` → `134`：✓
- `134` → `142`：✓
- `142` → `147`：✓
- `147` → `148`：✓
- `148` → `149`：✓
- `149` → `150`：✓
- `150` → `151`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W6-seed2396165278256069024.md` | `36939ccd47d842a2e5559a91543e57839dd49d7f6877ad6cd87ebca99caeba1f` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `20e1f85da26fd852affd5c23d4472fbc89764e5173d4595585e1b112caca23c5` |
| `component_manifest.json` | `0270c5c890ca73ba9b30f6236938cfa6629e308416a8846ff596954568a9a28f` |
| `inject/array.bin` | `ea5b57c3795f5b56f2f4c0c374555bd542056f2aad70cf224eabe6abe14bc8f8` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `bfe02314f275d3b0562b8dfe871049cbf754eaf7150e5ce8e0c340003e8e27d0` |
| `inject/config.json` | `cc586376b32269fc27a108bf3d6a6aa49e7b8804b8b6a94bf1fafcc9e5a2e8b3` |
| `inject/fault_injections.log` | `e2da102f9f29b5d5c692bd98c26886d0c72a2ccb0e82315fbd9fc6bbfa7f7de6` |
| `inject/prop_evt.txt.gz` | `3d780c204581df53820d6772dd682de48ea48b0605670b6ff79ebd7f7331daee` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `6cb3d219200fbee06ddff5ebb318c9bc3942a4e7b03b684402f9847885f43973` |
| `manifest.json` | `39c259e6897f20b8c4be62feaf40329440e2ced4adb394d7a3501ee286c89021` |
| `oracle.json` | `6e0115a1752f11049b32da1ef89a2b8f8bff41dd9fabba49770786f016798f63` |
| `oracle_elements.json` | `e7de39871fd709b11148e509a43ace4f31044a648bcc38b0d06e649c4ea6308f` |
| `run.err` | `c0d7ed0b8024da977ee10538dcd63845e4793271dc417a5badeb0978e48fbec2` |
| `run.out` | `b9d23bf0347583f4f5e6a4ad43c0ad7aa2af66828ecf5c89ab35695d70bbcf61` |
| `stats.txt` | `6cb3d219200fbee06ddff5ebb318c9bc3942a4e7b03b684402f9847885f43973` |

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
| MD event 3 存在于原始流 | PASS |
| MD event 3 kind 一致 | PASS |
| MD event 3 parent 一致 | PASS |
| MD event 11 存在于原始流 | PASS |
| MD event 11 kind 一致 | PASS |
| MD event 11 parent 一致 | PASS |
| MD event 16 存在于原始流 | PASS |
| MD event 16 kind 一致 | PASS |
| MD event 16 parent 一致 | PASS |
| MD event 19 存在于原始流 | PASS |
| MD event 19 kind 一致 | PASS |
| MD event 19 parent 一致 | PASS |
| MD event 27 存在于原始流 | PASS |
| MD event 27 kind 一致 | PASS |
| MD event 27 parent 一致 | PASS |
| MD event 35 存在于原始流 | PASS |
| MD event 35 kind 一致 | PASS |
| MD event 35 parent 一致 | PASS |
| MD event 36 存在于原始流 | PASS |
| MD event 36 kind 一致 | PASS |
| MD event 36 parent 一致 | PASS |
| MD event 37 存在于原始流 | PASS |
| MD event 37 kind 一致 | PASS |
| MD event 37 parent 一致 | PASS |
| MD event 45 存在于原始流 | PASS |
| MD event 45 kind 一致 | PASS |
| MD event 45 parent 一致 | PASS |
| MD event 55 存在于原始流 | PASS |
| MD event 55 kind 一致 | PASS |
| MD event 55 parent 一致 | PASS |
| MD event 63 存在于原始流 | PASS |
| MD event 63 kind 一致 | PASS |
| MD event 63 parent 一致 | PASS |
| MD event 72 存在于原始流 | PASS |
| MD event 72 kind 一致 | PASS |
| MD event 72 parent 一致 | PASS |
| MD event 80 存在于原始流 | PASS |
| MD event 80 kind 一致 | PASS |
| MD event 80 parent 一致 | PASS |
| MD event 83 存在于原始流 | PASS |
| MD event 83 kind 一致 | PASS |
| MD event 83 parent 一致 | PASS |
| MD event 88 存在于原始流 | PASS |
| MD event 88 kind 一致 | PASS |
| MD event 88 parent 一致 | PASS |
| MD event 96 存在于原始流 | PASS |
| MD event 96 kind 一致 | PASS |
| MD event 96 parent 一致 | PASS |
| MD event 105 存在于原始流 | PASS |
| MD event 105 kind 一致 | PASS |
| MD event 105 parent 一致 | PASS |
| MD event 114 存在于原始流 | PASS |
| MD event 114 kind 一致 | PASS |
| MD event 114 parent 一致 | PASS |
| MD event 125 存在于原始流 | PASS |
| MD event 125 kind 一致 | PASS |
| MD event 125 parent 一致 | PASS |
| MD event 134 存在于原始流 | PASS |
| MD event 134 kind 一致 | PASS |
| MD event 134 parent 一致 | PASS |
| MD event 142 存在于原始流 | PASS |
| MD event 142 kind 一致 | PASS |
| MD event 142 parent 一致 | PASS |
| MD event 147 存在于原始流 | PASS |
| MD event 147 kind 一致 | PASS |
| MD event 147 parent 一致 | PASS |
| MD event 148 存在于原始流 | PASS |
| MD event 148 kind 一致 | PASS |
| MD event 148 parent 一致 | PASS |
| MD event 149 存在于原始流 | PASS |
| MD event 149 kind 一致 | PASS |
| MD event 149 parent 一致 | PASS |
| MD event 150 存在于原始流 | PASS |
| MD event 150 kind 一致 | PASS |
| MD event 150 parent 一致 | PASS |
| MD event 151 存在于原始流 | PASS |
| MD event 151 kind 一致 | PASS |
| MD event 151 parent 一致 | PASS |
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
