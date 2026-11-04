# FSU-FR03-F5-W5-GATE seed16065008133739276579 审计

- attempt：`attempt-1`
- sample_run_id：`s16065008133739276579`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 88 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '85', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `42` → `47`：✓
- `47` → `56`：✓
- `56` → `61`：✓
- `61` → `70`：✓
- `70` → `78`：✓
- `78` → `83`：✓
- `83` → `84`：✓
- `84` → `85`：✓
- `85` → `86`：✓
- `86` → `87`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W5-GATE-seed16065008133739276579.md` | `184a920e37a1746cb947397953a9e0c04096c8ded769c5d10c92c577ecfc3c7f` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `1e0bbd79149ddf60457d68a6fd7be73129c74893a57132e2705d310836ea684f` |
| `component_manifest.json` | `531ab33f02af2c15c2db60bad439a0e6c56318259f8e534aec984c60e371231e` |
| `inject/array.bin` | `46eb754c53cf2ecffe653675230b55272073383f69806a3169a45ba35733dd60` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `fd711210a3e62c9997e1b2891a37657bdba1dcbfb727b6f495e6f70613a276d2` |
| `inject/config.json` | `7150acd7725538dd16b3f422cc29800f93475f213a34ed5cf29f23aaa9451ce4` |
| `inject/fault_injections.log` | `92b1ed0b4640c104c37a25a119cf1b66ba2485dcbc1cf1b99dd5f7b2d8ea1a88` |
| `inject/prop_evt.txt.gz` | `fcba689b2c77b9bef39a9001a3be502338db83fa9f66dec9fe09d2b55e0c8915` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `fb8a8a31d3d891810a2e6c30c64cef92a3deb2039dcb0dee2277621c6cb9f722` |
| `manifest.json` | `c02d313d9576bb9ef20c1e7f77bf1cf494994f2aac33d55687442f703498ec2d` |
| `oracle.json` | `8b9ce4b1f1f40fb123573117b1b93d00f745a2e4c7cd96c7610a58debd577041` |
| `oracle_elements.json` | `a3ee26399b9a2a2a00882413b38d4893ccf46aff5794d2e062b69cb491f6cb30` |
| `run.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `run.out` | `7b9188383170707112c3d6fe1e1e640c4130ae63ac172c9e0bf4356b5577e8eb` |
| `stats.txt` | `fb8a8a31d3d891810a2e6c30c64cef92a3deb2039dcb0dee2277621c6cb9f722` |

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
| MD event 47 存在于原始流 | PASS |
| MD event 47 kind 一致 | PASS |
| MD event 47 parent 一致 | PASS |
| MD event 56 存在于原始流 | PASS |
| MD event 56 kind 一致 | PASS |
| MD event 56 parent 一致 | PASS |
| MD event 61 存在于原始流 | PASS |
| MD event 61 kind 一致 | PASS |
| MD event 61 parent 一致 | PASS |
| MD event 70 存在于原始流 | PASS |
| MD event 70 kind 一致 | PASS |
| MD event 70 parent 一致 | PASS |
| MD event 78 存在于原始流 | PASS |
| MD event 78 kind 一致 | PASS |
| MD event 78 parent 一致 | PASS |
| MD event 83 存在于原始流 | PASS |
| MD event 83 kind 一致 | PASS |
| MD event 83 parent 一致 | PASS |
| MD event 84 存在于原始流 | PASS |
| MD event 84 kind 一致 | PASS |
| MD event 84 parent 一致 | PASS |
| MD event 85 存在于原始流 | PASS |
| MD event 85 kind 一致 | PASS |
| MD event 85 parent 一致 | PASS |
| MD event 86 存在于原始流 | PASS |
| MD event 86 kind 一致 | PASS |
| MD event 86 parent 一致 | PASS |
| MD event 87 存在于原始流 | PASS |
| MD event 87 kind 一致 | PASS |
| MD event 87 parent 一致 | PASS |
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
