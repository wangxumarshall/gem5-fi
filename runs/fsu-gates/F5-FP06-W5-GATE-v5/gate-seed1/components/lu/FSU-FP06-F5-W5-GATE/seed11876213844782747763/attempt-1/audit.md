# FSU-FP06-F5-W5-GATE seed11876213844782747763 审计

- attempt：`attempt-1`
- sample_run_id：`s11876213844782747763`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 522 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '50', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `1` → `3`：✓
- `3` → `47`：✓
- `47` → `48`：✓
- `48` → `49`：✓
- `49` → `50`：✓
- `50` → `521`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W5-GATE-seed11876213844782747763.md` | `ae2dbdda0aeed52e359ad165ce9b8bd2e4ce9e9d35dd661b0e33e3374d8cb142` |
| `census.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `census.out` | `c4ccb56d248c8b86b7a67db218f9a3af219e5b9ad128c6db50e16319b5880c06` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `01e1dcb2df8e25b1d4e9738f75e50cff926eb7281f6946caf12a230c5f2f6825` |
| `census/config.json` | `b7a16ef673bafdeb40d16af61a94cf204b2ebe98bf98dc2442f4ca7c330e8b23` |
| `census/fpu_injections.log` | `d1d2884aa2699eaa8cd3fe8e5c4f4aafda42e8e12126229c5ffd600c9ad1e806` |
| `census/stats.txt` | `781003b7a42711ddc09347e58d288d7acc7feae117edaedd006f7360b9606c59` |
| `chain_report.json` | `99399696ce9244daf1ad596902dfcbab080e9766f9c516ed4fa95f5d1a989b04` |
| `component_manifest.json` | `1d23bc90b4f387e92a178caa34712716b1bbd35d91ad0255acd505ac85b8c57a` |
| `inject/array.bin` | `d53e9bbad11acbc058662df382691e87408eacafbc982fa3d736cb639808eca2` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `1d561518f3773d202159ff935ddec77024e220ff78b4d348f7a4b0a1828b70d1` |
| `inject/config.json` | `a261d68c748af04521e9a4f05504817c07cc4776db594b9cb2bfae75b7f725fe` |
| `inject/fpu_injections.log` | `a9f6af08c67b40368987b28fcd791a27ff4b4ca47706e33455472a0627db73c7` |
| `inject/prop_evt.txt.gz` | `0d70ee37d9178cbda30063835f0851529cd53fe4aa57d5bcc9ac7de04d6a71db` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `27b2cc7d520404074481212bf59a93be932ce5c6b9f83c7970407c69da402f37` |
| `manifest.json` | `df68ab924ea523d94b0a1f091e5e5d07880da17c02dc3da71cef7937e7e75a91` |
| `oracle.json` | `eb99729022c15d3c41b59e3a3f0ca3b9dc81d4f05f0237c0f372eb4f909ba592` |
| `oracle_elements.json` | `0fe0c749b09e09f3a61b8f8dd4f72c648d38f1ab3869d12bacf7f7d527f5250c` |
| `run.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `run.out` | `2b3318a527c1453e1f29e3440dc078b86d96207022ab9205cc92420ef3d33e7e` |
| `stats.txt` | `27b2cc7d520404074481212bf59a93be932ce5c6b9f83c7970407c69da402f37` |

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
| MD event 3 存在于原始流 | PASS |
| MD event 3 kind 一致 | PASS |
| MD event 3 parent 一致 | PASS |
| MD event 47 存在于原始流 | PASS |
| MD event 47 kind 一致 | PASS |
| MD event 47 parent 一致 | PASS |
| MD event 48 存在于原始流 | PASS |
| MD event 48 kind 一致 | PASS |
| MD event 48 parent 一致 | PASS |
| MD event 49 存在于原始流 | PASS |
| MD event 49 kind 一致 | PASS |
| MD event 49 parent 一致 | PASS |
| MD event 50 存在于原始流 | PASS |
| MD event 50 kind 一致 | PASS |
| MD event 50 parent 一致 | PASS |
| MD event 521 存在于原始流 | PASS |
| MD event 521 kind 一致 | PASS |
| MD event 521 parent 一致 | PASS |
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
