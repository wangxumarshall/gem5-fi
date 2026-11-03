# FSU-FP04-F0-W5 seed933615570083433162 审计

- attempt：`attempt-1`
- sample_run_id：`s933615570083433162`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 7 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '5', 'kind': 'commit', 'outcome': 'errant_commit'} |
| oracle | SDC |
| chain terminal | full |
| stats 非空 | True |
| 无跨 seed 复制 | True |
| decode_guard | True |
| decoded / legacy roots | 1 / 0 |
| admitted（主 fault） | True |
| certified（全 fault 门禁） | False |
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
| `FSU-FP04-F0-W5-seed933615570083433162.md` | `75d10f87a2ffc811e4e8f8f47a1b029c86b3f97bbcaaec26ff8d07ba961974f7` |
| `census.err` | `412bdbb81cc5c76efc9bbb5f0948c687f5dfa2c45db12966c536f4bfcddd2797` |
| `census.out` | `a83bf9a08c7f01c1600686f92a34d8f8fa586e8f29b2ef0e41175066b7a8496a` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `62e76e17d52ede5fea7ce4bebe45285a13a2dbde3a2d992286fdc73d6bfec124` |
| `census/config.json` | `2be9ef6326ea6662edc2b7ad3abddcd9693705f65e66c937b59676e3b4469d0f` |
| `census/fpu_injections.log` | `a05a9807a610db15416c1398f34e24fecba5944ff6c9c3a1bfc37cfedf1db11a` |
| `census/stats.txt` | `145834a7b71c79dc8a2440ee0b9b4ba8b8304406ea15e66cebe9c22e918499b6` |
| `chain_report.json` | `f70860e64960377eb62734d0b86d41e2ee102127f36aaa939a53332e4ff0ba2d` |
| `component_manifest.json` | `f90dffb6f538f93a0fbf8587d43cd5b7788a3df2522ead2dfe8d7bb557af249a` |
| `inject/array.bin` | `4ccbcfd50274c6dc288d0eef424ff3ee71ba9cbdc26c0aea49cb36c59f683b24` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `025014de6137c9f46d1ea41cf717508021e83e147a819378bec8409ad6c53cef` |
| `inject/config.json` | `5887b9b413cd47ba5814fdbc8042722e93620f6fd4350bb7afbb49e308ecb9fb` |
| `inject/fpu_injections.log` | `1a6ae1216021a531aed3814e6eab40273415f737d2b5e884fba62baea45143f8` |
| `inject/prop_evt.txt.gz` | `653493dabf3c0baa50db00e876a685c73d519573a36db3dc1996da6a729940e3` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `3a9305a0e5d82cff55b41ccbbdb92713f2441f6970fa03e351923fd14025a186` |
| `manifest.json` | `49704c314c2fef7ca7f7493901a488b845fd948726390ca8cb316f52d34e7045` |
| `oracle.json` | `ac8d63e497e26741863418d85194c19cad553bc3921993666444f28c4489eeda` |
| `oracle_elements.json` | `6161e23fedac84636874326910193cac28d64aa2b90a0e9b29c3be17e45da867` |
| `run.err` | `412bdbb81cc5c76efc9bbb5f0948c687f5dfa2c45db12966c536f4bfcddd2797` |
| `run.out` | `8e96f2cb303fcc7e797d9694979a28222d4cb1c2434a8ce74845ee9a6c529c3f` |
| `stats.txt` | `3a9305a0e5d82cff55b41ccbbdb92713f2441f6970fa03e351923fd14025a186` |

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
| fault 1 字段/lane/mask 语义 | FAIL |
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

**结论：FAIL**
