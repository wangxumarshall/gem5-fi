# FSU-FR03-F5-W5-GATE seed15036002611505353583 审计

- attempt：`attempt-1`
- sample_run_id：`s15036002611505353583`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 139 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '135', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `6`：✓
- `6` → `14`：✓
- `14` → `25`：✓
- `25` → `33`：✓
- `33` → `41`：✓
- `41` → `46`：✓
- `46` → `55`：✓
- `55` → `66`：✓
- `66` → `75`：✓
- `75` → `83`：✓
- `83` → `91`：✓
- `91` → `92`：✓
- `92` → `95`：✓
- `95` → `103`：✓
- `103` → `104`：✓
- `104` → `109`：✓
- `109` → `120`：✓
- `120` → `128`：✓
- `128` → `133`：✓
- `133` → `134`：✓
- `134` → `135`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W5-GATE-seed15036002611505353583.md` | `43629f0f2b620a6f5954a76e5b885236c09c03935724bf0b5428984b0b90aca8` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `83adbb39955bac92ba142e4399945ce23d88556477e3030efb658dee9c89dd85` |
| `component_manifest.json` | `aad3cc214b6e39dd700c77a45fad239056d18371df60f401e9032534b7411565` |
| `inject/array.bin` | `23eb863deda56bcbd897823b0fcc0832907661ca0b80980a6aa5acaaa388ed9a` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `8ba61baf7368baae1426a6afb7bd12899ae6df2aafcbdc8189ab94b5aa486fa4` |
| `inject/config.json` | `629fbba4d8eab977d6e9f0fc949f723bc03dcce10fe4ee847ea57b28e6203649` |
| `inject/fault_injections.log` | `99dc267c35d05f47579f652a242ee7fa7826abb7c4573f85748bee886fe495b0` |
| `inject/prop_evt.txt.gz` | `8bdf6b18d4bbc4ba8b1adcf5a2cc99d78ef914cd2b26ca11c1d95980036d8c13` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `a8ab7c36ada9dae1c126e721f6df685f00e26ccdfd8bb0a82d699e9f93484bcc` |
| `manifest.json` | `306450ee81c8aece0835ed65cbe32805557e6218e2339236acd2fa3ddb44226d` |
| `oracle.json` | `b485fe7afe629539e7addc506115e8b99f2a4ff2c7c74c3594c37122254f2c75` |
| `oracle_elements.json` | `29a9cc526bbdeaf4c43dd2604d047e0fd13731462370dc5e1e87dee0ff4e23ef` |
| `run.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `run.out` | `e8ae2a0243b2321c6d63bf5873dfe8a42002627c0e0382cda8041a1d54201df7` |
| `stats.txt` | `a8ab7c36ada9dae1c126e721f6df685f00e26ccdfd8bb0a82d699e9f93484bcc` |

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
| MD event 6 存在于原始流 | PASS |
| MD event 6 kind 一致 | PASS |
| MD event 6 parent 一致 | PASS |
| MD event 14 存在于原始流 | PASS |
| MD event 14 kind 一致 | PASS |
| MD event 14 parent 一致 | PASS |
| MD event 25 存在于原始流 | PASS |
| MD event 25 kind 一致 | PASS |
| MD event 25 parent 一致 | PASS |
| MD event 33 存在于原始流 | PASS |
| MD event 33 kind 一致 | PASS |
| MD event 33 parent 一致 | PASS |
| MD event 41 存在于原始流 | PASS |
| MD event 41 kind 一致 | PASS |
| MD event 41 parent 一致 | PASS |
| MD event 46 存在于原始流 | PASS |
| MD event 46 kind 一致 | PASS |
| MD event 46 parent 一致 | PASS |
| MD event 55 存在于原始流 | PASS |
| MD event 55 kind 一致 | PASS |
| MD event 55 parent 一致 | PASS |
| MD event 66 存在于原始流 | PASS |
| MD event 66 kind 一致 | PASS |
| MD event 66 parent 一致 | PASS |
| MD event 75 存在于原始流 | PASS |
| MD event 75 kind 一致 | PASS |
| MD event 75 parent 一致 | PASS |
| MD event 83 存在于原始流 | PASS |
| MD event 83 kind 一致 | PASS |
| MD event 83 parent 一致 | PASS |
| MD event 91 存在于原始流 | PASS |
| MD event 91 kind 一致 | PASS |
| MD event 91 parent 一致 | PASS |
| MD event 92 存在于原始流 | PASS |
| MD event 92 kind 一致 | PASS |
| MD event 92 parent 一致 | PASS |
| MD event 95 存在于原始流 | PASS |
| MD event 95 kind 一致 | PASS |
| MD event 95 parent 一致 | PASS |
| MD event 103 存在于原始流 | PASS |
| MD event 103 kind 一致 | PASS |
| MD event 103 parent 一致 | PASS |
| MD event 104 存在于原始流 | PASS |
| MD event 104 kind 一致 | PASS |
| MD event 104 parent 一致 | PASS |
| MD event 109 存在于原始流 | PASS |
| MD event 109 kind 一致 | PASS |
| MD event 109 parent 一致 | PASS |
| MD event 120 存在于原始流 | PASS |
| MD event 120 kind 一致 | PASS |
| MD event 120 parent 一致 | PASS |
| MD event 128 存在于原始流 | PASS |
| MD event 128 kind 一致 | PASS |
| MD event 128 parent 一致 | PASS |
| MD event 133 存在于原始流 | PASS |
| MD event 133 kind 一致 | PASS |
| MD event 133 parent 一致 | PASS |
| MD event 134 存在于原始流 | PASS |
| MD event 134 kind 一致 | PASS |
| MD event 134 parent 一致 | PASS |
| MD event 135 存在于原始流 | PASS |
| MD event 135 kind 一致 | PASS |
| MD event 135 parent 一致 | PASS |
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
