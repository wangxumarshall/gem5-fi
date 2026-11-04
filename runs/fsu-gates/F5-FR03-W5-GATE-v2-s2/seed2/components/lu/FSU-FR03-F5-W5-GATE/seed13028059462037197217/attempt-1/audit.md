# FSU-FR03-F5-W5-GATE seed13028059462037197217 审计

- attempt：`attempt-1`
- sample_run_id：`s13028059462037197217`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 109 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '106', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `7`：✓
- `7` → `15`：✓
- `15` → `27`：✓
- `27` → `36`：✓
- `36` → `44`：✓
- `44` → `52`：✓
- `52` → `63`：✓
- `63` → `72`：✓
- `72` → `77`：✓
- `77` → `86`：✓
- `86` → `87`：✓
- `87` → `98`：✓
- `98` → `103`：✓
- `103` → `105`：✓
- `105` → `106`：✓
- `106` → `107`：✓
- `107` → `108`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W5-GATE-seed13028059462037197217.md` | `320f9fbb63aa17e8593b5f60c87c3d0aa65593de824c9bb744c3eef298eb265f` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `52aa39a551360a30dc45fd493e8d876b3eaaa90e2f77c526d5168ce317f0cb1e` |
| `component_manifest.json` | `614c3439cb7855ae640b92b39beb93dbf004380348f187aa5c3c9fa11f6ebd6c` |
| `inject/array.bin` | `46eb754c53cf2ecffe653675230b55272073383f69806a3169a45ba35733dd60` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `f126d029667605a871e7f7a06a88a2ea13069058a5df9b0b509a3d6ba02fe5c6` |
| `inject/config.json` | `dc54b4cbe341b6ddcbbbf18e9dce7e546b456ef0f54817a775025d432d12d66e` |
| `inject/fault_injections.log` | `012c84a4c2bd0b02a0197b32fb3c6262e1a065bca0c05a7947edad7fb7c8800f` |
| `inject/prop_evt.txt.gz` | `5249bc2c1f55b9b8c1c0e51dbc4803961975f837224fc5e46b32cab6836fd786` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `73f56e33229406fe77dd39a6d44cbe123665aee4ab6c8c7494c87b13d23933c3` |
| `manifest.json` | `f256590224002cce0b1143e19fd39afefb56e72e65134848abfdf6392e2cf8b1` |
| `oracle.json` | `879b7c8ad572cc622a298a8b2adf8a975ef2317dc79057abf089c59706e84acf` |
| `oracle_elements.json` | `07eef5e6f84e04df4ef481edca90aab39cab9a5f78ae6c518feaccd65ebebad4` |
| `run.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `run.out` | `de11232159a381afdf2250a9b9445c7dc89ae9dc3d92e6947ef79d5b9a67c67e` |
| `stats.txt` | `73f56e33229406fe77dd39a6d44cbe123665aee4ab6c8c7494c87b13d23933c3` |

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
| MD event 7 存在于原始流 | PASS |
| MD event 7 kind 一致 | PASS |
| MD event 7 parent 一致 | PASS |
| MD event 15 存在于原始流 | PASS |
| MD event 15 kind 一致 | PASS |
| MD event 15 parent 一致 | PASS |
| MD event 27 存在于原始流 | PASS |
| MD event 27 kind 一致 | PASS |
| MD event 27 parent 一致 | PASS |
| MD event 36 存在于原始流 | PASS |
| MD event 36 kind 一致 | PASS |
| MD event 36 parent 一致 | PASS |
| MD event 44 存在于原始流 | PASS |
| MD event 44 kind 一致 | PASS |
| MD event 44 parent 一致 | PASS |
| MD event 52 存在于原始流 | PASS |
| MD event 52 kind 一致 | PASS |
| MD event 52 parent 一致 | PASS |
| MD event 63 存在于原始流 | PASS |
| MD event 63 kind 一致 | PASS |
| MD event 63 parent 一致 | PASS |
| MD event 72 存在于原始流 | PASS |
| MD event 72 kind 一致 | PASS |
| MD event 72 parent 一致 | PASS |
| MD event 77 存在于原始流 | PASS |
| MD event 77 kind 一致 | PASS |
| MD event 77 parent 一致 | PASS |
| MD event 86 存在于原始流 | PASS |
| MD event 86 kind 一致 | PASS |
| MD event 86 parent 一致 | PASS |
| MD event 87 存在于原始流 | PASS |
| MD event 87 kind 一致 | PASS |
| MD event 87 parent 一致 | PASS |
| MD event 98 存在于原始流 | PASS |
| MD event 98 kind 一致 | PASS |
| MD event 98 parent 一致 | PASS |
| MD event 103 存在于原始流 | PASS |
| MD event 103 kind 一致 | PASS |
| MD event 103 parent 一致 | PASS |
| MD event 105 存在于原始流 | PASS |
| MD event 105 kind 一致 | PASS |
| MD event 105 parent 一致 | PASS |
| MD event 106 存在于原始流 | PASS |
| MD event 106 kind 一致 | PASS |
| MD event 106 parent 一致 | PASS |
| MD event 107 存在于原始流 | PASS |
| MD event 107 kind 一致 | PASS |
| MD event 107 parent 一致 | PASS |
| MD event 108 存在于原始流 | PASS |
| MD event 108 kind 一致 | PASS |
| MD event 108 parent 一致 | PASS |
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
