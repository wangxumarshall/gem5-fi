# FSU-FP06-F5-W5-GATE seed1898146363856152889 审计

- attempt：`attempt-1`
- sample_run_id：`s1898146363856152889`

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
| `FSU-FP06-F5-W5-GATE-seed1898146363856152889.md` | `91877bd12bc4aedde62143eabcbbffe0954a94cae25a565dfe10422d901c43fa` |
| `census.err` | `412bdbb81cc5c76efc9bbb5f0948c687f5dfa2c45db12966c536f4bfcddd2797` |
| `census.out` | `a83bf9a08c7f01c1600686f92a34d8f8fa586e8f29b2ef0e41175066b7a8496a` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `76f2733aa932ec51cf2ad00be046a48560859a2233412ca34d5598ff0b3e60ce` |
| `census/config.json` | `f1d8e94e9ac0fe3824387f2eab6906d9a77afc0dc9e672889bcec69ceb362428` |
| `census/fpu_injections.log` | `5364c25fa30df322a51a8f82a182e02d8e6a1179076e680a7e746bfc21d7e84f` |
| `census/stats.txt` | `11811276faf7dd51bb69dd715eab14d3a1f1bcdf50ecf50a10a82563a5fb2ef3` |
| `chain_report.json` | `17d71c07be51e864d217a9c4e763020e3be1f8d1c3a38c4c45b5c3244a8c26aa` |
| `component_manifest.json` | `c6751352299a2e58983aea7e80752fb51b88cc90051d27025bae10d8e24a9a02` |
| `inject/array.bin` | `d48a373361f5e241f4bbc59602e8cdc2006a67fd480be90a062a2d425988cf0b` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `b14d4733c1969794d5075addd146caea51ff3b7c151adf32a3826ff6bfe8a607` |
| `inject/config.json` | `aea5176b12b9c48dccc36063f730635335c304c3a709397cf0e885cd9bca110a` |
| `inject/fpu_injections.log` | `3698401afc0c88d351859870faf7841f5ae8c9b1045e65c84f7aed100dca4baa` |
| `inject/prop_evt.txt.gz` | `03392329645b5cdb523895b20373d62902e29b192847e6857994daaf1adad860` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `17b3a3c4ff51fd503e4589acfd6f90781f9faf95048097c476fa84a89208f95b` |
| `manifest.json` | `82acbbda35d36277b5cf7e99719422990d5aea77ebd8aa4f1c89d1aef88924c2` |
| `oracle.json` | `e7d917e0c9593fa7e112bcf1b38b6a332c7fa9ef136afdfe80d9932d7d52fd4b` |
| `oracle_elements.json` | `c12971bc8c8d4837ad2ba2d6fcc40a47dea1ff1f7cdebfb2cae307783dee93e1` |
| `run.err` | `412bdbb81cc5c76efc9bbb5f0948c687f5dfa2c45db12966c536f4bfcddd2797` |
| `run.out` | `90dbcc8bb4f786c02461dfb37b4733b9f85878931ae735d661a9eedc7d32eaf3` |
| `stats.txt` | `17b3a3c4ff51fd503e4589acfd6f90781f9faf95048097c476fa84a89208f95b` |

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
