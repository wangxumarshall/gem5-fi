# FSU-FR03-F5-W5 seed13028059462037197217 审计

- attempt：`attempt-1`
- sample_run_id：`s13028059462037197217`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 115 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '112', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `69` → `78`：✓
- `78` → `83`：✓
- `83` → `92`：✓
- `92` → `93`：✓
- `93` → `104`：✓
- `104` → `109`：✓
- `109` → `111`：✓
- `111` → `112`：✓
- `112` → `113`：✓
- `113` → `114`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W5-seed13028059462037197217.md` | `ef757c399cbd002ec8cd11b4616cb2956783df99f6f700ed5102ad897eaa42d6` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `09f14139312b4fe091a1d53dfa12859448223a8bf02c74e2ddce7940683c6085` |
| `component_manifest.json` | `9c827c9c5047dab1dca5cf5aaa64f6c5b0db9f4d442a205092d0f40e3f0a0f21` |
| `inject/array.bin` | `46eb754c53cf2ecffe653675230b55272073383f69806a3169a45ba35733dd60` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `646c19bc4d131734bbc7c895bfb8a47b959fbd761c810b475cea4fcb3a8f6ef8` |
| `inject/config.json` | `212954341c5711e8c41c6dbbbf142404a03006ce290f1ab7bed62136f5f5b1ab` |
| `inject/fault_injections.log` | `cff0bb858637479d551baef865f7942ea382f20420235d2ddcfe4bd3900c3c46` |
| `inject/prop_evt.txt.gz` | `d9351ec76a31323bc776918570a8956eebeb112c8caf39ec9d92539794f3063b` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `1cb113f4b16312b2dc4bfc0716c12cb4b3c3bb1be5991cfbdbcb25a9e257bda3` |
| `manifest.json` | `436f2acfb1eddedcc187e6419deb329f20abd5ff4501b863cf215e2f8967cca3` |
| `oracle.json` | `879b7c8ad572cc622a298a8b2adf8a975ef2317dc79057abf089c59706e84acf` |
| `oracle_elements.json` | `e3b4eba0a21aaa819f1ed135e6462b12d04ae61809ab57b76bb47d9cd97f60be` |
| `run.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `run.out` | `602d4f085f717456a7354f35b408f3e909f5ad204f1b3af1134120e4177d3abc` |
| `stats.txt` | `1cb113f4b16312b2dc4bfc0716c12cb4b3c3bb1be5991cfbdbcb25a9e257bda3` |

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
| MD event 78 存在于原始流 | PASS |
| MD event 78 kind 一致 | PASS |
| MD event 78 parent 一致 | PASS |
| MD event 83 存在于原始流 | PASS |
| MD event 83 kind 一致 | PASS |
| MD event 83 parent 一致 | PASS |
| MD event 92 存在于原始流 | PASS |
| MD event 92 kind 一致 | PASS |
| MD event 92 parent 一致 | PASS |
| MD event 93 存在于原始流 | PASS |
| MD event 93 kind 一致 | PASS |
| MD event 93 parent 一致 | PASS |
| MD event 104 存在于原始流 | PASS |
| MD event 104 kind 一致 | PASS |
| MD event 104 parent 一致 | PASS |
| MD event 109 存在于原始流 | PASS |
| MD event 109 kind 一致 | PASS |
| MD event 109 parent 一致 | PASS |
| MD event 111 存在于原始流 | PASS |
| MD event 111 kind 一致 | PASS |
| MD event 111 parent 一致 | PASS |
| MD event 112 存在于原始流 | PASS |
| MD event 112 kind 一致 | PASS |
| MD event 112 parent 一致 | PASS |
| MD event 113 存在于原始流 | PASS |
| MD event 113 kind 一致 | PASS |
| MD event 113 parent 一致 | PASS |
| MD event 114 存在于原始流 | PASS |
| MD event 114 kind 一致 | PASS |
| MD event 114 parent 一致 | PASS |
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
