# FSU-FP06-F5-W6 seed2750522184732370354 审计

- attempt：`attempt-1`
- sample_run_id：`s2750522184732370354`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 521 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '7', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `1` → `2`：✓
- `2` → `4`：✓
- `4` → `5`：✓
- `5` → `6`：✓
- `6` → `7`：✓
- `7` → `520`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W6-seed2750522184732370354.md` | `870d9c8502c209a1787682f8e52b500304eae0959abbbc063e4b624599f836db` |
| `census.err` | `c0d7ed0b8024da977ee10538dcd63845e4793271dc417a5badeb0978e48fbec2` |
| `census.out` | `aaa3ad592bed190d0c07bea5f2eff404f94545e4d4749bebe8a33e53046b0eec` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `3774525e84e4a33c2116eaf9693fb713176c086cdf50ae26139fe46a0c0f8826` |
| `census/config.json` | `3219d6f46d03af0faed066ba38f07d3e13e4261b880497c3bbc0a9a8af5fd00d` |
| `census/fpu_injections.log` | `7d4a2321eb81215bafc86524bac039b3535e5a09895fc42f5bbe3d1f14e430b2` |
| `census/stats.txt` | `dac57d3a720eb2416048a437465c6838816aaf15d24d1867e869b1378d4dcb81` |
| `chain_report.json` | `b363851614db7972bef010d0fda7dc3539851883bafa59964609c14177d29335` |
| `component_manifest.json` | `f19ea4bd21e0a8a54cc6b8012c68be1acd9012df99021b540188af01e4cc7e27` |
| `inject/array.bin` | `5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `b6f4467865fbc962eab8540fe3ccd3fe85efb7cdef35f54681818c249f00ad9c` |
| `inject/config.json` | `e5e64874c09581cee43c4bea08b02e8a8bd897121f90dd2d9e67b0814fadd4d2` |
| `inject/fpu_injections.log` | `21fe9bc1f901f69537f5ec392d47849525db7319fa29b8e11ec1ad724a9d3054` |
| `inject/prop_evt.txt.gz` | `7c581e0a80844f308c67996c5a11c703ab0c3d777eade293142ebc0993b3ef88` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `c1bfcf2f6177f44614d3ae0755413536d38b509d016b2981ddaddb983edb11d6` |
| `manifest.json` | `5da064e357d48075ad085c24b71d467ed12bcc38baeedd3d0ec3d406e6181c35` |
| `oracle.json` | `df797ef64cb3882d2ae5eda33d69557b9fcd3c2adf20c5e57e9dca69bdda3dcb` |
| `oracle_elements.json` | `6d1af28ecd088c494477e62bd45991518d3d8ac63702aac7cb4d4d17909fbbc2` |
| `run.err` | `c0d7ed0b8024da977ee10538dcd63845e4793271dc417a5badeb0978e48fbec2` |
| `run.out` | `d0bfd264cc56fb29a6651221bd94b73a970a06ba2924fb11d49d318ad1a47a2b` |
| `stats.txt` | `c1bfcf2f6177f44614d3ae0755413536d38b509d016b2981ddaddb983edb11d6` |

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
| MD event 2 存在于原始流 | PASS |
| MD event 2 kind 一致 | PASS |
| MD event 2 parent 一致 | PASS |
| MD event 4 存在于原始流 | PASS |
| MD event 4 kind 一致 | PASS |
| MD event 4 parent 一致 | PASS |
| MD event 5 存在于原始流 | PASS |
| MD event 5 kind 一致 | PASS |
| MD event 5 parent 一致 | PASS |
| MD event 6 存在于原始流 | PASS |
| MD event 6 kind 一致 | PASS |
| MD event 6 parent 一致 | PASS |
| MD event 7 存在于原始流 | PASS |
| MD event 7 kind 一致 | PASS |
| MD event 7 parent 一致 | PASS |
| MD event 520 存在于原始流 | PASS |
| MD event 520 kind 一致 | PASS |
| MD event 520 parent 一致 | PASS |
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
