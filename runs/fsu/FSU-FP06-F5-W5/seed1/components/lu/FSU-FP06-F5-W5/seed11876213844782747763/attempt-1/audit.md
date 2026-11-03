# FSU-FP06-F5-W5 seed11876213844782747763 审计

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
| `FSU-FP06-F5-W5-seed11876213844782747763.md` | `252e75cd477c956151da123e15478951288c40925aef32b6807797f6840f43d3` |
| `census.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `census.out` | `c4ccb56d248c8b86b7a67db218f9a3af219e5b9ad128c6db50e16319b5880c06` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `01e1dcb2df8e25b1d4e9738f75e50cff926eb7281f6946caf12a230c5f2f6825` |
| `census/config.json` | `b7a16ef673bafdeb40d16af61a94cf204b2ebe98bf98dc2442f4ca7c330e8b23` |
| `census/fpu_injections.log` | `d1d2884aa2699eaa8cd3fe8e5c4f4aafda42e8e12126229c5ffd600c9ad1e806` |
| `census/stats.txt` | `4428fa8601281deb2825757175106f7cf1f1eb21fa8da954bead75119bd24865` |
| `chain_report.json` | `964c53c74aca20b0955f2c082eb70c93dc01ffd42b42b78ee8d35d4aca1c93f3` |
| `component_manifest.json` | `bc77d812b057307d2e8f451de9e949c36f4f15aa3be66977e725a8eaf389d83c` |
| `inject/array.bin` | `d53e9bbad11acbc058662df382691e87408eacafbc982fa3d736cb639808eca2` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `5953eeac5845ab2ebd830b34112d13e8ac5ac0d7d3f8e4c8508ee1b56fcecc14` |
| `inject/config.json` | `49e12341e340cbbd2ec15ab6306b3cba5d112f6ee45ae8fc39c1875758e58f90` |
| `inject/fpu_injections.log.gz` | `13ec1869d6f1bc5844147dd8f692c11fe4bea476bb53dabe171a2eaaf25bedd9` |
| `inject/prop_evt.txt.gz` | `090a2d8992aff419d902aabec5e1c28125c82f49a1e4a47cec3573a239131896` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `6147a4a39a0d40586cffaf31204eb268e1cdd3693a40d8980b7735682b2e341d` |
| `injection_log_storage.json` | `ead1d00a7c7c8f93ec8c66de73151149b35db3dfebca1c37732bb7f9320ef879` |
| `manifest.json` | `d1d82de0ca2c0f10629312dd0541599ef4383cb93534db61340ff85441278279` |
| `oracle.json` | `eb99729022c15d3c41b59e3a3f0ca3b9dc81d4f05f0237c0f372eb4f909ba592` |
| `oracle_elements.json` | `86a8da5ffc569806a83fd3109ac4dfa08c29042f461a83f534e02b12bf5abfe0` |
| `run.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `run.out` | `645d0775821ebe8322eb26a11086c1a32a3968d46a1fa142941767cedabd3b93` |
| `stats.txt` | `6147a4a39a0d40586cffaf31204eb268e1cdd3693a40d8980b7735682b2e341d` |

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
