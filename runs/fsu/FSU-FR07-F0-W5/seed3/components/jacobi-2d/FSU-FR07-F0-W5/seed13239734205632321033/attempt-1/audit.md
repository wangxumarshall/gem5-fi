# FSU-FR07-F0-W5 seed13239734205632321033 审计

- attempt：`attempt-1`
- sample_run_id：`s13239734205632321033`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 8 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '6', 'kind': 'commit', 'outcome': 'errant_commit'} |
| oracle | Masked |
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
- `1` → `3`：✓
- `3` → `4`：✓
- `4` → `5`：✓
- `5` → `6`：✓
- `6` → `7`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR07-F0-W5-seed13239734205632321033.md` | `ee83a662e00ee4dba0fd86772e22ba8c14ede0ddfa77a861e920b5b7d390a26d` |
| `census.err` | `412bdbb81cc5c76efc9bbb5f0948c687f5dfa2c45db12966c536f4bfcddd2797` |
| `census.out` | `a83bf9a08c7f01c1600686f92a34d8f8fa586e8f29b2ef0e41175066b7a8496a` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `236b4c4c108365c268854b1e7ceb44dab5ccef27c470cbf3e67a8d1523dddeaf` |
| `census/config.json` | `7080308051ad1cfe9a5b086267a794fde7fa4f27a6fa33d5915c8d68de2218b6` |
| `census/fpu_injections.log` | `33964eab95896806142951d02ade884b36dc86d6f522eb88d95e02f88caa3d8a` |
| `census/stats.txt` | `b729cf101d7e0424a61c253878fa3b340484863f700c71e8b7965abc30010a24` |
| `chain_report.json` | `a4cf8eb0bf8cc83f5299773c4577ce189f932bfd3effe9d6a7792106b7a3104e` |
| `component_manifest.json` | `019ffedf46fbe57328d45eeca393b36a6df00c44a222026381c5b97457113bf2` |
| `inject/array.bin` | `dad9731239bff9177fd983b961d93b8100afe636f85248b933b86ee4ab31e624` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `52d37444c16053e8649dd575c6834eaa0919b41971983e69b39cd4e28a64578a` |
| `inject/config.json` | `d72ba937f639d7dc64096aef357a2b5c5f9a73b5105e03827cf25b71b41ae44a` |
| `inject/fpu_injections.log` | `a93d46e2f4ec1839dcabe293a083d8153060dad1aa5da411e9aeb3ca34bae770` |
| `inject/prop_evt.txt.gz` | `728504dd9373f0fff6962b58a9395207f866e3849b63c21844a67a18843fad67` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `eecd15ac0c8d030ea83b13768223fa4472b9cf0f5f671a134eefe6a7912cc7c5` |
| `manifest.json` | `d19abd9d87cf24d88ff4a44d961e6f5494f417f6079c257e6d4b77e111eb9639` |
| `oracle.json` | `0c90bde2aadfac723971ea8f58e28264b027ff73103ed5cb3eb0c9cfa6e54960` |
| `oracle_elements.json` | `48f5c636a063c56dbcf91664e30f8993edb014fa132856c890b7cbdd426809f2` |
| `run.err` | `412bdbb81cc5c76efc9bbb5f0948c687f5dfa2c45db12966c536f4bfcddd2797` |
| `run.out` | `96f62aec62f78a0c81a3c17caf4fa54fd56b3df3bb49b8a420e7f652fbcea155` |
| `stats.txt` | `eecd15ac0c8d030ea83b13768223fa4472b9cf0f5f671a134eefe6a7912cc7c5` |

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
| fault 1 F5 计数/去重/守恒校验 | PASS |
| MD event 0 存在于原始流 | PASS |
| MD event 0 kind 一致 | PASS |
| MD event 0 parent 一致 | PASS |
| MD event 1 存在于原始流 | PASS |
| MD event 1 kind 一致 | PASS |
| MD event 1 parent 一致 | PASS |
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
| MD event 7 存在于原始流 | PASS |
| MD event 7 kind 一致 | PASS |
| MD event 7 parent 一致 | PASS |
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
