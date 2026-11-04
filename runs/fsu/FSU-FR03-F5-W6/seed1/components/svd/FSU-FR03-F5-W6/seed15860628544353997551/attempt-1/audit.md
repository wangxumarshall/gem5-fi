# FSU-FR03-F5-W6 seed15860628544353997551 审计

- attempt：`attempt-1`
- sample_run_id：`s15860628544353997551`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 83 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '80', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `73` → `78`：✓
- `78` → `79`：✓
- `79` → `80`：✓
- `80` → `81`：✓
- `81` → `82`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W6-seed15860628544353997551.md` | `b17602a703b7334b0a04b5bc92870d59a576a63006b4fa173f43cfaa5bae1ab9` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `216ae5cbfcde19762f9e88620cdad68a75bf50ceb1fe651988fc0a771d571cf8` |
| `component_manifest.json` | `f9270afecd87b2b3b1d6b7e74d8c564ca114d46a6a25deea19443799c75c1189` |
| `inject/array.bin` | `c057a7f60984974ab4db131468dbf4f078432f69112593eec44701a207fb531c` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `6b75a8cae5e54e91fb2f84ff0289428d9fe76171562236256902b26baed460dd` |
| `inject/config.json` | `cdcb4a11ffa56ce93bdc98966b1c7a494f70d8b9ec5632f75b9df4c1cc2a932b` |
| `inject/fault_injections.log` | `ca1ce5339b674562a82adefcdf8aa2f92e930ff9f53a4a2e5dd2b95b0441023f` |
| `inject/prop_evt.txt.gz` | `566ee1a00ab7a3f9a1b2ce6461a581f3b9383b15f2dd4b2b4931435954902d8d` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `59817781aa723c0f08e4310b16d741621ec955fa8b15f685e4c2a7edbb060884` |
| `manifest.json` | `f3189fa0871cd882d360a805c9d712900103824a8ab537e60919c5028218a978` |
| `oracle.json` | `afcf71725b0c3ac30b00f007fefd31c2947e28cf9f479b9649e00ee10fb0efe6` |
| `oracle_elements.json` | `13191125a415cd5ae5146256d4a9cf8dce571928f3585899bc1a3e88d55399f5` |
| `run.err` | `ac94070c9fd00342e736472f14f15e1e2f9f917536b7d47fc81b2d472ba7fff3` |
| `run.out` | `532c75aad8fcab6ab83739859a10b51c49cf956c800a880dc4c24642cdb34e44` |
| `stats.txt` | `59817781aa723c0f08e4310b16d741621ec955fa8b15f685e4c2a7edbb060884` |

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
| MD event 78 存在于原始流 | PASS |
| MD event 78 kind 一致 | PASS |
| MD event 78 parent 一致 | PASS |
| MD event 79 存在于原始流 | PASS |
| MD event 79 kind 一致 | PASS |
| MD event 79 parent 一致 | PASS |
| MD event 80 存在于原始流 | PASS |
| MD event 80 kind 一致 | PASS |
| MD event 80 parent 一致 | PASS |
| MD event 81 存在于原始流 | PASS |
| MD event 81 kind 一致 | PASS |
| MD event 81 parent 一致 | PASS |
| MD event 82 存在于原始流 | PASS |
| MD event 82 kind 一致 | PASS |
| MD event 82 parent 一致 | PASS |
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
