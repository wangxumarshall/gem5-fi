# FSU-FP06-F5-W6-GATE seed4348244394395585333 审计

- attempt：`attempt-1`
- sample_run_id：`s4348244394395585333`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 522 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '10', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `3` → `7`：✓
- `7` → `8`：✓
- `8` → `9`：✓
- `9` → `10`：✓
- `10` → `521`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W6-GATE-seed4348244394395585333.md` | `058b9fbfe785b5897b9f40f7bbe1c45a2d271ce03e2942470a20405a9299b756` |
| `census.err` | `c0d7ed0b8024da977ee10538dcd63845e4793271dc417a5badeb0978e48fbec2` |
| `census.out` | `aaa3ad592bed190d0c07bea5f2eff404f94545e4d4749bebe8a33e53046b0eec` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `7f93c1cd05b9431106a4b4b07b40acb4d2895f48a9b63ec6d9655dc06c7440e6` |
| `census/config.json` | `a9f83e2d00fa5f65f27a0e5d0e9556b5576e1d7b83836208ac7a1f6263bb11ff` |
| `census/fpu_injections.log` | `7d4a2321eb81215bafc86524bac039b3535e5a09895fc42f5bbe3d1f14e430b2` |
| `census/stats.txt` | `e73692a9461934f2bf00b8d850015456c6108073a347a232839591f36b502c79` |
| `chain_report.json` | `3e705fc2bbf4a1699f76a7b0de0c638542b555368b315fe228d88ebce3f30b6b` |
| `component_manifest.json` | `ee846083e70cf1a861a89ee387513a3b1c12fa9d7bef08272b8629b85a2463eb` |
| `inject/array.bin` | `2ee14262951168f09faa9d755485e02f3017f99f5cc2b33de8cf9223de512b5c` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `f1c8a07871e478524f74036a992aba584a0a97e829f1a70c7e3306567886b6d1` |
| `inject/config.json` | `96bb71bf46ef00699d1729f4f5de9a64ed909b874257b908a17ac8e674ff1dfc` |
| `inject/fpu_injections.log` | `8b85db7f01069d18ba47a433bba76a99f111553bc3c74c8e970819cee040a394` |
| `inject/prop_evt.txt.gz` | `cda64e985548b494c5ddc5785025008adb9ddaf1182d2c4574d3ce0c88142302` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `34af1bafeb73e6cde24e9b3cbe53c07e5f623e3c3d51cf8b14b82dd50a37064c` |
| `manifest.json` | `0476f34a45ce117f4dfc2faeb89570d57552808a7df7d5be561614df2bb53bd8` |
| `oracle.json` | `b2c103d75b0f5c229df834c4dd6c995ad29ea0b3b1a601a2904453549bb84fc6` |
| `oracle_elements.json` | `50955a17d79eac174023b2ca148a16b8ec929f3e70e5cbe417d9c80c1fe48f26` |
| `run.err` | `c0d7ed0b8024da977ee10538dcd63845e4793271dc417a5badeb0978e48fbec2` |
| `run.out` | `4343bd3536d45de723d7fe19106ac69cf44ec404b2dcf0ebc473d06f226994bb` |
| `stats.txt` | `34af1bafeb73e6cde24e9b3cbe53c07e5f623e3c3d51cf8b14b82dd50a37064c` |

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
| MD event 7 存在于原始流 | PASS |
| MD event 7 kind 一致 | PASS |
| MD event 7 parent 一致 | PASS |
| MD event 8 存在于原始流 | PASS |
| MD event 8 kind 一致 | PASS |
| MD event 8 parent 一致 | PASS |
| MD event 9 存在于原始流 | PASS |
| MD event 9 kind 一致 | PASS |
| MD event 9 parent 一致 | PASS |
| MD event 10 存在于原始流 | PASS |
| MD event 10 kind 一致 | PASS |
| MD event 10 parent 一致 | PASS |
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
