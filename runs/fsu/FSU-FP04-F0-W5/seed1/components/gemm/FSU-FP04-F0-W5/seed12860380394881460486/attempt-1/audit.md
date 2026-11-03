# FSU-FP04-F0-W5 seed12860380394881460486 审计

- attempt：`attempt-1`
- sample_run_id：`s12860380394881460486`

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
| `FSU-FP04-F0-W5-seed12860380394881460486.md` | `5eee36d933122ceeddd75e66e3d6ffdab27c0ff852e0520a182b4d5a6e124b56` |
| `census.err` | `aab1510bc39780187ded556b781e6fb104354304676b3bc41045a0db1c656efe` |
| `census.out` | `19431cf806c5c901ed6056643fbc9dddca012675a839815127c66c77ac912ca1` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `cd3701e32a7490a9a81af10965d8d780a562fb4327dfd44dc75f0f36e6ffeadd` |
| `census/config.json` | `7fd108380d3ee1d354942da317ea873c85738ff3393371b3f892fde6b7837356` |
| `census/fpu_injections.log` | `c30027422776ed0ad6973238dbba8a29728c808dad3b27ff3dffc5ddd7a906e5` |
| `census/stats.txt` | `e7c5a75b69d2c37da86ccb33bdeb0037667620778a4a29f3ab86de622fb3888d` |
| `chain_report.json` | `69f80b0b8bd9017a54c1bce71de7028ddfa1da6402ddbac8b0c5cdcb0d866d5e` |
| `component_manifest.json` | `c8003e9474beff85f390c2e09e9d7f6a5e2b2ca7082255942b245893db18bbeb` |
| `inject/array.bin` | `b1ce137016ff6dda77cd147c8bd51764cd5de6d9b5b4b74cce6ea6f45c965d07` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `61aa988eaaa046e8194b701b380b0b2dc221d2d5e2fa4a26f95beb706572ef3a` |
| `inject/config.json` | `8403044a38881c894ae8663529d717eb1386cb2750980288c89f6ee7f3dcdb16` |
| `inject/fpu_injections.log` | `7145538c68c45b6f8c2d19ee8727608e57e7d3d00c4295e4883a7426816b2894` |
| `inject/prop_evt.txt.gz` | `4b49101f69154f6ce30329ea894d13f04aca9b3ec8dff8110e2ffe4c83f442e1` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `010adbd220a98c64e2daa21cfc5015cdbfb468c9f32f043ee7047f67c9ec0217` |
| `manifest.json` | `b332252ebc382adab12b37e1baccdc66092071006e5ed9fd396e07c07168bb04` |
| `oracle.json` | `88faba4c2ede052a497815378bec8963e8d4585da1a2d7cf9beccaebc360394f` |
| `oracle_elements.json` | `406b067af289be5b13648a575182a742c8b1b5456da55a6e6baec5baaf96b65d` |
| `run.err` | `aab1510bc39780187ded556b781e6fb104354304676b3bc41045a0db1c656efe` |
| `run.out` | `a10ef450cde2078673de2519df972515560793ad59e670656f0ed6eda9ec9070` |
| `stats.txt` | `010adbd220a98c64e2daa21cfc5015cdbfb468c9f32f043ee7047f67c9ec0217` |

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
