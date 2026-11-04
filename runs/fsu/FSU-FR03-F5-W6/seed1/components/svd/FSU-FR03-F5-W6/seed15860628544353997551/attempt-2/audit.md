# FSU-FR03-F5-W6 seed15860628544353997551 审计

- attempt：`attempt-2`
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
| `FSU-FR03-F5-W6-seed15860628544353997551.md` | `f8fbf755a19db19e2f7d598676ad39a21d6f7ff870e94171f712f5b0dd658935` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `0eb877cc35ab543105cbb29509c2a38fd3b5c66dd74f5215a911ea3188fa7634` |
| `component_manifest.json` | `d68478db396cad83767a7effbdd087a1904054f0cb962cee28cc5c7d8c2e7bf1` |
| `inject/array.bin` | `c057a7f60984974ab4db131468dbf4f078432f69112593eec44701a207fb531c` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `2db7e1ebb9a357ad2438717197c453b1bf03f31f0791a066cededc97ac97e0a9` |
| `inject/config.json` | `b6684eefc1b0d0e948fb629edecdf6c057a10e951bb6be093c551985e66c377a` |
| `inject/fault_injections.log` | `07977de83998a1161e02b88a903c5b1ee8c3d62e01086431980b2b07036ff074` |
| `inject/prop_evt.txt.gz` | `73990e5f568525b66405dd5217e0a277ca7ad15d93cc7eb2c58af23b5d0f47d5` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `da649097f604892ac67745a80cd6fd829b4ee76d928d7469b4de7382ec821ce6` |
| `manifest.json` | `ffbc7851ba1973951b2b48f512b49a6956df8782087d53563c4d6ff8017c9d4d` |
| `oracle.json` | `afcf71725b0c3ac30b00f007fefd31c2947e28cf9f479b9649e00ee10fb0efe6` |
| `oracle_elements.json` | `da47e22b4932e50ace975e3c9419fb7a41fc9bdbf0d6fd9f2a1562259d3b91c7` |
| `run.err` | `ac94070c9fd00342e736472f14f15e1e2f9f917536b7d47fc81b2d472ba7fff3` |
| `run.out` | `73882ce1c5a0815b30ac673327c97e84fec467aa42de036a564bcf38ff994b57` |
| `stats.txt` | `da649097f604892ac67745a80cd6fd829b4ee76d928d7469b4de7382ec821ce6` |

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
