# FSU-FR03-F5-W6-GATE seed17527292261993683735 审计

- attempt：`attempt-1`
- sample_run_id：`s17527292261993683735`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 149 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '141', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `80` → `81`：✓
- `81` → `92`：✓
- `92` → `100`：✓
- `100` → `108`：✓
- `108` → `117`：✓
- `117` → `120`：✓
- `120` → `125`：✓
- `125` → `133`：✓
- `133` → `138`：✓
- `138` → `140`：✓
- `140` → `141`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W6-GATE-seed17527292261993683735.md` | `bb35f86aa4972df7564ca5df424d57b173b92a028eec5059445160871f659bda` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `ecef1d6dd15e8762c97ce0f309744bb02773ab2bee6a4d35ddf0fc0f6f8a070c` |
| `component_manifest.json` | `b4fc97040506f43230686fffbd4a5a9f751b27e945277f7a1fe50d66eaa96180` |
| `inject/array.bin` | `ea5b57c3795f5b56f2f4c0c374555bd542056f2aad70cf224eabe6abe14bc8f8` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `58e4b962c6a6a704477261abdc2661ee61f992b2d6578e452955a65ebf4ce1c8` |
| `inject/config.json` | `dce2c32cdf99131f246a225a05c4c3e04bb4b9cc61c82e06dc0d5576871e5ca7` |
| `inject/fault_injections.log` | `f32f53f19fada80fedcb905e1a9810bf9c635cd99a00bddf216f678e243929e3` |
| `inject/prop_evt.txt.gz` | `0e0a1e5f0c54d71752c1243650cebffefc1364d35190bfb7f4a8ce5b0315c32c` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `9afd79251738072dd64016397ab651965e84d58990dd35b2fa89f29df5bf9b9f` |
| `manifest.json` | `4367f1b8712e3d6726606dcde5f246e9e01157155be880b04b799fd290e75113` |
| `oracle.json` | `f2adc6abc03e13643b2e9b07782ada68ac66816851109e154f1565a884cc2b7b` |
| `oracle_elements.json` | `e49a7f40050e3cb06ec3e281ff22d765aa97a714e55f9e7ea5f28da267d3e294` |
| `run.err` | `c0d7ed0b8024da977ee10538dcd63845e4793271dc417a5badeb0978e48fbec2` |
| `run.out` | `ff9fe4222a3421ed80e9230c1b3c72f2fc002105cd6fc4222226154b97c81b57` |
| `stats.txt` | `9afd79251738072dd64016397ab651965e84d58990dd35b2fa89f29df5bf9b9f` |

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
| MD event 81 存在于原始流 | PASS |
| MD event 81 kind 一致 | PASS |
| MD event 81 parent 一致 | PASS |
| MD event 92 存在于原始流 | PASS |
| MD event 92 kind 一致 | PASS |
| MD event 92 parent 一致 | PASS |
| MD event 100 存在于原始流 | PASS |
| MD event 100 kind 一致 | PASS |
| MD event 100 parent 一致 | PASS |
| MD event 108 存在于原始流 | PASS |
| MD event 108 kind 一致 | PASS |
| MD event 108 parent 一致 | PASS |
| MD event 117 存在于原始流 | PASS |
| MD event 117 kind 一致 | PASS |
| MD event 117 parent 一致 | PASS |
| MD event 120 存在于原始流 | PASS |
| MD event 120 kind 一致 | PASS |
| MD event 120 parent 一致 | PASS |
| MD event 125 存在于原始流 | PASS |
| MD event 125 kind 一致 | PASS |
| MD event 125 parent 一致 | PASS |
| MD event 133 存在于原始流 | PASS |
| MD event 133 kind 一致 | PASS |
| MD event 133 parent 一致 | PASS |
| MD event 138 存在于原始流 | PASS |
| MD event 138 kind 一致 | PASS |
| MD event 138 parent 一致 | PASS |
| MD event 140 存在于原始流 | PASS |
| MD event 140 kind 一致 | PASS |
| MD event 140 parent 一致 | PASS |
| MD event 141 存在于原始流 | PASS |
| MD event 141 kind 一致 | PASS |
| MD event 141 parent 一致 | PASS |
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
