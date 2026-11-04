# FSU-FR03-F5-W5-GATE seed8444189732774129999 审计

- attempt：`attempt-1`
- sample_run_id：`s8444189732774129999`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 81 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '77', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `13`：✓
- `13` → `21`：✓
- `21` → `33`：✓
- `33` → `42`：✓
- `42` → `50`：✓
- `50` → `58`：✓
- `58` → `69`：✓
- `69` → `74`：✓
- `74` → `76`：✓
- `76` → `77`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W5-GATE-seed8444189732774129999.md` | `7c455e698d46e03a12b80ca85796dbb8b4299f289595aaba152db72c7998dc91` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `ec93b0d35397bd1cfdbb7d3e6384acd8c361d98372d5741ab807217d36a2707a` |
| `component_manifest.json` | `2a83725c424a17fbb6032e924d33b33ab397e08ed12e32f9c28de3385cf860ac` |
| `inject/array.bin` | `46eb754c53cf2ecffe653675230b55272073383f69806a3169a45ba35733dd60` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `9250b898bae3602f218f2e0af2753e8d57c0faafa6581b5a1537e28f9b3cdbcc` |
| `inject/config.json` | `33d53e514ea6ef22e97024c12d452ac321fe47e92b9accd283c792fe437f05f5` |
| `inject/fault_injections.log` | `4f0f330acb832d0fac8eddbc1ad623239e56f886bd0f92407aef66260dee5f22` |
| `inject/prop_evt.txt.gz` | `ee29638ec0b3a17246a8037787b1bf6569d446b35f237f28f419fd75b3a769e5` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `0de40d8a74582774a7dc2383641d4f2f7c6220a05e1da047f2c772dcd8869ed4` |
| `manifest.json` | `7bc263b3bccc394759dfdc4e21485944faefaf27e2faa33a4e567ef958bfd9fa` |
| `oracle.json` | `757ed252c689adc7455611072b9f4f019d08f47c2d0cb8e03da77503cf61447c` |
| `oracle_elements.json` | `42be3976f675ce62b78f692e33f62a5c4c2a0bd4f4ae6873432b0e0c3e1c7492` |
| `run.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `run.out` | `0691c37ff2697411840743fa2ef570ffd1b86c1bbdeb01a6c92254735ea350b2` |
| `stats.txt` | `0de40d8a74582774a7dc2383641d4f2f7c6220a05e1da047f2c772dcd8869ed4` |

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
| MD event 13 存在于原始流 | PASS |
| MD event 13 kind 一致 | PASS |
| MD event 13 parent 一致 | PASS |
| MD event 21 存在于原始流 | PASS |
| MD event 21 kind 一致 | PASS |
| MD event 21 parent 一致 | PASS |
| MD event 33 存在于原始流 | PASS |
| MD event 33 kind 一致 | PASS |
| MD event 33 parent 一致 | PASS |
| MD event 42 存在于原始流 | PASS |
| MD event 42 kind 一致 | PASS |
| MD event 42 parent 一致 | PASS |
| MD event 50 存在于原始流 | PASS |
| MD event 50 kind 一致 | PASS |
| MD event 50 parent 一致 | PASS |
| MD event 58 存在于原始流 | PASS |
| MD event 58 kind 一致 | PASS |
| MD event 58 parent 一致 | PASS |
| MD event 69 存在于原始流 | PASS |
| MD event 69 kind 一致 | PASS |
| MD event 69 parent 一致 | PASS |
| MD event 74 存在于原始流 | PASS |
| MD event 74 kind 一致 | PASS |
| MD event 74 parent 一致 | PASS |
| MD event 76 存在于原始流 | PASS |
| MD event 76 kind 一致 | PASS |
| MD event 76 parent 一致 | PASS |
| MD event 77 存在于原始流 | PASS |
| MD event 77 kind 一致 | PASS |
| MD event 77 parent 一致 | PASS |
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
