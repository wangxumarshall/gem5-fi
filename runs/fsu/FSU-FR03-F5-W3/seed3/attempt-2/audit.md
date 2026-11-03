# FSU-FR03-F5-W3 seed3 审计

- attempt：`attempt-2`
- sample_run_id：`s3`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 6167 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '6162', 'kind': 'commit', 'outcome': 'errant_commit'} |
| oracle | SDC |
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
- `3` → `8`：✓
- `8` → `23`：✓
- `23` → `35`：✓
- `35` → `6160`：✓
- `6160` → `6161`：✓
- `6161` → `6162`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W3-seed3.md` | `787e65370e753580855a111c5784e81e7522b40d675657431343f8f24a1d8ee6` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `f9b5c81320cc19a98fa1bf5f9c4a2f090ea37cbbc0d0ba7ce444b44d3df2e038` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `2feb9f6afa84ab6d265cfa95cd33d99c60a2e5f9b1750693f97d9cc3f9ef804a` |
| `inject/config.json` | `68c9753c29fa414b235de64614fc614d81393d3efae521e140f6694d8dd8dddc` |
| `inject/fault_injections.log` | `e9ffd745daab4b39362fdb474a2f12c247bec7bde31b5b78e9c2e7a3fda86b41` |
| `inject/prop_evt.txt.gz` | `1bf5bd61a96124fc2fe9730fc1fcacf76f8c3890428934aae739438e0c25fb21` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `bb3a31ca0e0d7d72b3ebaf63cca6205630a3bcfca2c101de9bf0b8ae60c14ea7` |
| `manifest.json` | `1942f1aa49ebc281b1379cd6accf6a2b397e7880b047808621f8933191ef6484` |
| `oracle.json` | `63b19c9e971867ef4f1400e14a99f4860835735d3838ad8e90a533abcbefecb7` |
| `run.err` | `dec72566590bdc5e161de8212087044774786c74f89964911cc196ef6b1ff992` |
| `run.out` | `6bdef35c85971e3f754ba3d8f2b631c34a6b7eb8857d8175348bbcf12614a0ef` |
| `stats.txt` | `bb3a31ca0e0d7d72b3ebaf63cca6205630a3bcfca2c101de9bf0b8ae60c14ea7` |

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
| MD event 8 存在于原始流 | PASS |
| MD event 8 kind 一致 | PASS |
| MD event 8 parent 一致 | PASS |
| MD event 23 存在于原始流 | PASS |
| MD event 23 kind 一致 | PASS |
| MD event 23 parent 一致 | PASS |
| MD event 35 存在于原始流 | PASS |
| MD event 35 kind 一致 | PASS |
| MD event 35 parent 一致 | PASS |
| MD event 6160 存在于原始流 | PASS |
| MD event 6160 kind 一致 | PASS |
| MD event 6160 parent 一致 | PASS |
| MD event 6161 存在于原始流 | PASS |
| MD event 6161 kind 一致 | PASS |
| MD event 6161 parent 一致 | PASS |
| MD event 6162 存在于原始流 | PASS |
| MD event 6162 kind 一致 | PASS |
| MD event 6162 parent 一致 | PASS |
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
