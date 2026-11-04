# FSU-FR03-F5-W5-GATE seed6976623493032354155 审计

- attempt：`attempt-1`
- sample_run_id：`s6976623493032354155`

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
| `FSU-FR03-F5-W5-GATE-seed6976623493032354155.md` | `310d5977bca05293a0836fd16a99adfd3e733b608adcf38e00ba8a3f0723d5c3` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `690dce5438b9ce23dd820912f7d7fed4339265bdebb67554309304facd88e985` |
| `component_manifest.json` | `be49552a36a2b87ad74ff30f18a163aba7717d89940de0ab7f2bac3936133a35` |
| `inject/array.bin` | `ad54ba81bc46aa236d3fc8e663dda077853e513721685ba78abe940108879f43` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `5ccc43b63f1015d2d7dc9a9cdbf123df774d55baf8e3753ab29a418205bd944c` |
| `inject/config.json` | `023ab85e9140ce71228b85c08dc2afe4a864a137a2761bf8cc58b883459fe3f3` |
| `inject/fault_injections.log` | `cc52f3cb737c73ffbc564c36e08dbbc6d09ab39e07e6b77212309ec760c4fecf` |
| `inject/prop_evt.txt.gz` | `262e14e97d3227aeb484209c10ecf39291dcb44f06f7879e412e4c6ad63b20a7` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `b7878f5bcb4b0db11687af79176282d1ad9d6477872fee190b6836753496dcda` |
| `manifest.json` | `2c5351d08c2cbff938e72213d52d4a2ceda79c9ed0abbc443d0efad3bf59fe02` |
| `oracle.json` | `016459a86826d6430f5963440b4f9ef0520d8536671e425b513cb16ef080b068` |
| `oracle_elements.json` | `979c7b6953c9d6ed63779be9bdefd6acb89fac933841cff2ff768c43d21cdd3f` |
| `run.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `run.out` | `f42cd25026ad0a51fbbce837e3f53dc8fbc8b29c415cdf9033eae974b412f25d` |
| `stats.txt` | `b7878f5bcb4b0db11687af79176282d1ad9d6477872fee190b6836753496dcda` |

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
