# FSU-FP04-F0-W5 seed664471552991680598 审计

- attempt：`attempt-1`
- sample_run_id：`s664471552991680598`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 7 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '5', 'kind': 'commit', 'outcome': 'errant_commit'} |
| oracle | Masked |
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
| `FSU-FP04-F0-W5-seed664471552991680598.md` | `6f03b350f61d6769ce5c0a44f56d381e589e3995336487ea23b1ae5497690d6c` |
| `census.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `census.out` | `ebd792f6461d512abb42df564d9864a21c462de74f95e4b3be8c792d316f3851` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `e574954f973ae16128f4ac2ed38967e50b5436b4c8d58e770b0559a58ad406ee` |
| `census/config.json` | `3c5529410823dacffa71d51cb3929d8cf6cf4c782d3e8159b298fe3ea2533286` |
| `census/fpu_injections.log` | `8b66562bae879a94dd4b30dbecea756d9847812eee986c294b925dc0b6f0d968` |
| `census/stats.txt` | `aba23067e888230a38415a28ff7d53cf62cdce7184bd48a369c2efebabcdfa5d` |
| `chain_report.json` | `b17313bb40ae643abeb1f3472fac1641bf54c99ba0491e98b44ef7184743526b` |
| `component_manifest.json` | `1b7dae89a384fac93746b3169c807018ecb240990075b560c3cca38f23782033` |
| `inject/array.bin` | `ad54ba81bc46aa236d3fc8e663dda077853e513721685ba78abe940108879f43` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `5efbe0b7f21584e2e161b4989fee82f6c870ac01c41c345c85c22ddc95c504fa` |
| `inject/config.json` | `53a4b8edde2a302b2c0c855629e045590b063b6dba2215607fd3e65f1db3aaf7` |
| `inject/fpu_injections.log` | `cb0a9d6862c52fa01cc001df3791555c1512f88c6d5c0646b6bb1facff73e84e` |
| `inject/prop_evt.txt.gz` | `9f3c14caea2365d8920a7c7fa819faacea7bf719ea14db17e7ab6c3bb1535bb5` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `ed57ff0c0b9b9ba7568edf265d67b6fefee32c5714e50933135d6da1f38e9c47` |
| `manifest.json` | `802edc9bbbbf782bbc9857faabc807f76018efe70cd192ed94454430df2ba996` |
| `oracle.json` | `118222a7e56b23c5f71a6810b7f49deef93b9d93d81cc5ca99936a2da9406a56` |
| `oracle_elements.json` | `b5f511fd0c9114cea70a24c8a1caf87de46b5505a27600218a53e693b582ec39` |
| `run.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `run.out` | `8807fd69822b35d1e728f59cbc980c9c5667112912d4c5361c359f9e0f50c5bd` |
| `stats.txt` | `ed57ff0c0b9b9ba7568edf265d67b6fefee32c5714e50933135d6da1f38e9c47` |

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
