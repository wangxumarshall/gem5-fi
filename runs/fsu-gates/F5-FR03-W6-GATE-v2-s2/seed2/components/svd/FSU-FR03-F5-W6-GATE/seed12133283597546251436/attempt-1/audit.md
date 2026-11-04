# FSU-FR03-F5-W6-GATE seed12133283597546251436 审计

- attempt：`attempt-1`
- sample_run_id：`s12133283597546251436`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 101 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '98', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `27` → `30`：✓
- `30` → `38`：✓
- `38` → `41`：✓
- `41` → `49`：✓
- `49` → `57`：✓
- `57` → `65`：✓
- `65` → `73`：✓
- `73` → `75`：✓
- `75` → `83`：✓
- `83` → `91`：✓
- `91` → `96`：✓
- `96` → `97`：✓
- `97` → `98`：✓
- `98` → `99`：✓
- `99` → `100`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W6-GATE-seed12133283597546251436.md` | `fa8e1bb9c3aa13cbeb89c77805b987dfd88869e14438bbe602df1069d109409a` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `fe486bdbcc628c125d1d90004808d9817c8e3ff38d6fff0c4e85cc180a56a3cf` |
| `component_manifest.json` | `6a2085cec4cb392a5799b6560609b559e8926ff42d3632690aa5a7ba655da242` |
| `inject/array.bin` | `c057a7f60984974ab4db131468dbf4f078432f69112593eec44701a207fb531c` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `319f9ead81e2b87a2a1f19d712cad76dabf5d2a77bad0e28cc0ade84d3d34ec7` |
| `inject/config.json` | `e7ae888f23403c1b1c0b5a86346bca60b9e35eec0630426540ee049bd3398492` |
| `inject/fault_injections.log` | `37f683dc3ec3a0b34493936bff06d63b98708886c334b0371448f136c915d61d` |
| `inject/prop_evt.txt.gz` | `372e18dacba42ac35076d41222c1ba0eea16907e2560710f6415244c6e6f8ec2` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `2fc2708b5c750d84f6f236fd8f8331d775c9b67ec446e748d1dfa64dce721a4d` |
| `manifest.json` | `b9364636feeb2c981c533f642aad20988d18aec5fe396bafe97bd8967a05b69b` |
| `oracle.json` | `4b4664c8cd42cb9892fd91945c1e8ad44242e2bb8883d73200b8bdb34cec243c` |
| `oracle_elements.json` | `72097fdbf53462197af71119106346070da670e3512b05d5e34d766d5e1586cf` |
| `run.err` | `ac94070c9fd00342e736472f14f15e1e2f9f917536b7d47fc81b2d472ba7fff3` |
| `run.out` | `38c3150d23336461b288840ff58264fb47d5bb108a7e164f2574fe58d4b06968` |
| `stats.txt` | `2fc2708b5c750d84f6f236fd8f8331d775c9b67ec446e748d1dfa64dce721a4d` |

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
| MD event 30 存在于原始流 | PASS |
| MD event 30 kind 一致 | PASS |
| MD event 30 parent 一致 | PASS |
| MD event 38 存在于原始流 | PASS |
| MD event 38 kind 一致 | PASS |
| MD event 38 parent 一致 | PASS |
| MD event 41 存在于原始流 | PASS |
| MD event 41 kind 一致 | PASS |
| MD event 41 parent 一致 | PASS |
| MD event 49 存在于原始流 | PASS |
| MD event 49 kind 一致 | PASS |
| MD event 49 parent 一致 | PASS |
| MD event 57 存在于原始流 | PASS |
| MD event 57 kind 一致 | PASS |
| MD event 57 parent 一致 | PASS |
| MD event 65 存在于原始流 | PASS |
| MD event 65 kind 一致 | PASS |
| MD event 65 parent 一致 | PASS |
| MD event 73 存在于原始流 | PASS |
| MD event 73 kind 一致 | PASS |
| MD event 73 parent 一致 | PASS |
| MD event 75 存在于原始流 | PASS |
| MD event 75 kind 一致 | PASS |
| MD event 75 parent 一致 | PASS |
| MD event 83 存在于原始流 | PASS |
| MD event 83 kind 一致 | PASS |
| MD event 83 parent 一致 | PASS |
| MD event 91 存在于原始流 | PASS |
| MD event 91 kind 一致 | PASS |
| MD event 91 parent 一致 | PASS |
| MD event 96 存在于原始流 | PASS |
| MD event 96 kind 一致 | PASS |
| MD event 96 parent 一致 | PASS |
| MD event 97 存在于原始流 | PASS |
| MD event 97 kind 一致 | PASS |
| MD event 97 parent 一致 | PASS |
| MD event 98 存在于原始流 | PASS |
| MD event 98 kind 一致 | PASS |
| MD event 98 parent 一致 | PASS |
| MD event 99 存在于原始流 | PASS |
| MD event 99 kind 一致 | PASS |
| MD event 99 parent 一致 | PASS |
| MD event 100 存在于原始流 | PASS |
| MD event 100 kind 一致 | PASS |
| MD event 100 parent 一致 | PASS |
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
