# FSU-FR03-F5-W6 seed10044515714169597802 审计

- attempt：`attempt-1`
- sample_run_id：`s10044515714169597802`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 84 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '81', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `16` → `20`：✓
- `20` → `28`：✓
- `28` → `31`：✓
- `31` → `39`：✓
- `39` → `42`：✓
- `42` → `50`：✓
- `50` → `58`：✓
- `58` → `66`：✓
- `66` → `74`：✓
- `74` → `79`：✓
- `79` → `80`：✓
- `80` → `81`：✓
- `81` → `82`：✓
- `82` → `83`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W6-seed10044515714169597802.md` | `036c10a7532e2ed0eee6c69bf5890919bf047022b9455f275305ef24622b2c96` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `acf08bc7bf2557efcd7f9bfa86aa11e06e2502c3f943123f09d7a1c7723361d0` |
| `component_manifest.json` | `b6ba42b2f3c1f940bf716588de512e164483fd6feafe4f840559844853a9d2f3` |
| `inject/array.bin` | `c057a7f60984974ab4db131468dbf4f078432f69112593eec44701a207fb531c` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `3832f3aa855d7862f90330a307fda33ca578f64c3457e5d3758001ab8e10fa99` |
| `inject/config.json` | `22b549f8a9f32501a05840564096d64672897f0bbad295d0b15b68d7653bb4cd` |
| `inject/fault_injections.log` | `f155fe2db45e387cd30ee70d98bd20aeed7827f30611071d53c0ba1705b32c0a` |
| `inject/prop_evt.txt.gz` | `0afaeb88cab3ba259c94550f13731e3d2d0d7c69602bba34a493546ab1b31fb4` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `7559cf05d7aa2a0c1b0d7fa5b752bf1efd4a2d145e638bc129ef4522014c0fa7` |
| `manifest.json` | `d141196d6c775fc4abb1556627ffa682cbf318206beeca92d57be9fa07eaf1aa` |
| `oracle.json` | `76996312f384efd1831863ed80c9e1fdf429851408670fd093cd671a6bb36be8` |
| `oracle_elements.json` | `e08f7734802b6e4ad55cd4f46a06e13383091f82478279f77f9999c641ec37f0` |
| `run.err` | `ac94070c9fd00342e736472f14f15e1e2f9f917536b7d47fc81b2d472ba7fff3` |
| `run.out` | `bddee1e0b9147ab6d805915932a78c1fb78e3ca5b096385cf891817e90b7a6bb` |
| `stats.txt` | `7559cf05d7aa2a0c1b0d7fa5b752bf1efd4a2d145e638bc129ef4522014c0fa7` |

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
| MD event 20 存在于原始流 | PASS |
| MD event 20 kind 一致 | PASS |
| MD event 20 parent 一致 | PASS |
| MD event 28 存在于原始流 | PASS |
| MD event 28 kind 一致 | PASS |
| MD event 28 parent 一致 | PASS |
| MD event 31 存在于原始流 | PASS |
| MD event 31 kind 一致 | PASS |
| MD event 31 parent 一致 | PASS |
| MD event 39 存在于原始流 | PASS |
| MD event 39 kind 一致 | PASS |
| MD event 39 parent 一致 | PASS |
| MD event 42 存在于原始流 | PASS |
| MD event 42 kind 一致 | PASS |
| MD event 42 parent 一致 | PASS |
| MD event 50 存在于原始流 | PASS |
| MD event 50 kind 一致 | PASS |
| MD event 50 parent 一致 | PASS |
| MD event 58 存在于原始流 | PASS |
| MD event 58 kind 一致 | PASS |
| MD event 58 parent 一致 | PASS |
| MD event 66 存在于原始流 | PASS |
| MD event 66 kind 一致 | PASS |
| MD event 66 parent 一致 | PASS |
| MD event 74 存在于原始流 | PASS |
| MD event 74 kind 一致 | PASS |
| MD event 74 parent 一致 | PASS |
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
| MD event 83 存在于原始流 | PASS |
| MD event 83 kind 一致 | PASS |
| MD event 83 parent 一致 | PASS |
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
