# FSU-FP06-F5-W1-FP32-SIGN-GATE seed1 审计

- attempt：`attempt-1`
- sample_run_id：`s1`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 26 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '15', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `1` → `11`：✓
- `11` → `12`：✓
- `12` → `13`：✓
- `13` → `14`：✓
- `14` → `15`：✓
- `15` → `25`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W1-FP32-SIGN-GATE-seed1.md` | `3b061164784df4c36929cad59390d5fc7bdef7619e1718b9a1b726a63b8af5b4` |
| `census.err` | `70c903c6b501403db8b5162ced9bbf43f40b13e120d7c1df4354edaa225c9f68` |
| `census.out` | `2db6a778ec445a146baf8a47b0bde89307c65e23d3f13f150b2466ce50b251e5` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `dab90c3acdbb9a0977cbf0908c70fd21df5f1bb88a3dbef8c6d5a359587c5d54` |
| `census/config.json` | `e3f38db559e30e5a1a12f623e60144c705e578932c8d0a43605b0192b5556844` |
| `census/fpu_injections.log` | `2b19dc8502ca5832c97dc669a6441c91dbe3fdddd1e53b729d2e449b6b86c45d` |
| `census/stats.txt` | `0342cb70c79b820fc2ba625283781bd4eb5bdd5f982a73dc7101a4801d2cb072` |
| `chain_report.json` | `7b99f8ffb372fc798da55f763d4be0266d9108296c22339e4f8fd2a74faa321f` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `5dc7b16af51ad390cc161c816cb0167f28dd2e6a399a6250999a5ca3ebe64308` |
| `inject/config.json` | `0b3e96f3bd226b566bee5f7d2673165d985a7d45caf62d5cb9d1487ad7ddfc59` |
| `inject/fpu_injections.log` | `0fa8f39f93a55e906b4e10e45ee983dedf13de55d24ec0311888e06a58bb7b41` |
| `inject/prop_evt.txt.gz` | `b0ff0771b2c2d7ce7d9010314b9a94c4a2f5e1519432aa9e26658f3a7ba8100b` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `045f7803698ca535258ee6b044d6bfa35a2ffe1c564bcd34af00301b1086706b` |
| `manifest.json` | `88a775844516dcf6939c08c32755b1c56e5b42bb9a9f801a288875b2d542e55b` |
| `oracle.json` | `24dd13876f8447adb8253b16c3242a0842c1ebba74876d4924f7daa0dc415923` |
| `run.err` | `70c903c6b501403db8b5162ced9bbf43f40b13e120d7c1df4354edaa225c9f68` |
| `run.out` | `a676242956dc5180846930f4a5b4cea61498bb0717da5adefe92ca1dc97e3e25` |
| `stats.txt` | `045f7803698ca535258ee6b044d6bfa35a2ffe1c564bcd34af00301b1086706b` |

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
| MD event 0 存在于原始流 | PASS |
| MD event 0 kind 一致 | PASS |
| MD event 0 parent 一致 | PASS |
| MD event 1 存在于原始流 | PASS |
| MD event 1 kind 一致 | PASS |
| MD event 1 parent 一致 | PASS |
| MD event 11 存在于原始流 | PASS |
| MD event 11 kind 一致 | PASS |
| MD event 11 parent 一致 | PASS |
| MD event 12 存在于原始流 | PASS |
| MD event 12 kind 一致 | PASS |
| MD event 12 parent 一致 | PASS |
| MD event 13 存在于原始流 | PASS |
| MD event 13 kind 一致 | PASS |
| MD event 13 parent 一致 | PASS |
| MD event 14 存在于原始流 | PASS |
| MD event 14 kind 一致 | PASS |
| MD event 14 parent 一致 | PASS |
| MD event 15 存在于原始流 | PASS |
| MD event 15 kind 一致 | PASS |
| MD event 15 parent 一致 | PASS |
| MD event 25 存在于原始流 | PASS |
| MD event 25 kind 一致 | PASS |
| MD event 25 parent 一致 | PASS |
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
