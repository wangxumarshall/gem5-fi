# FSU-FP06-F5-W3 seed2 审计

- attempt：`attempt-1`
- sample_run_id：`s2`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 521 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '8', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `5`：✓
- `5` → `6`：✓
- `6` → `7`：✓
- `7` → `8`：✓
- `8` → `520`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W3-seed2.md` | `99678e26a1f2ea10ae7681beff6cd50be670bf3a870cb28bfa5be5e722772c4f` |
| `census.err` | `dec72566590bdc5e161de8212087044774786c74f89964911cc196ef6b1ff992` |
| `census.out` | `fac0a1421006952effb359683641278158af2aead4668dbf9f92db82d4b530af` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `13b0ba8ab1aabb80d0b8a751e45951c94db3b6a4ebf44dbef09e5484391eecd0` |
| `census/config.json` | `02187b8e571e57630476890570027341bbc3886e2dbd5d14422febdbe212659a` |
| `census/fpu_injections.log` | `a11af940ae5abd172a9256c3b0d49a82356f9814c3ed2922e7b15ba6f78f4b1a` |
| `census/stats.txt` | `146f9a9c23a85abe52433b1eaffbdc985d4867d2f46e082f73a188eff654156c` |
| `chain_report.json` | `628f421f834283c664a5828ea5266a9c5c1f2c8f73f8617b6ffbe92c90602d98` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `58ad7c603aff7172c0abe9ce54490b445646870d57b63e03b32d88884945471c` |
| `inject/config.json` | `ae6cf6dcec5dfb66ad1f25b4881d13ba98f1154032b9787205aeb0bfe36ee971` |
| `inject/fpu_injections.log` | `8578f0b8e5bbacd8151e4125b47a76e7543769d854588eed0965bb78b08aa169` |
| `inject/prop_evt.txt.gz` | `b36b8697ff9faaa328cb2bb543f125e3e9ba890bb61ba46aeae081dc5f7f8986` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `e5b0090c54c43a8654cae49f2c5f59ab88184224556f8311e6ad0d4fb4abbb4c` |
| `manifest.json` | `c173b5717d5482ddb428120a5fa7a829cb0776c79d1cdbbd2e757a015ec20318` |
| `oracle.json` | `f078e21488a18687bf037015f5d03628f8b3e331c1f488afba2f43827cfc4d20` |
| `run.err` | `dec72566590bdc5e161de8212087044774786c74f89964911cc196ef6b1ff992` |
| `run.out` | `39d3d25ddedcba466b2d87ca583b8d34d4343679774172041ca325f3e5c21792` |
| `stats.txt` | `e5b0090c54c43a8654cae49f2c5f59ab88184224556f8311e6ad0d4fb4abbb4c` |

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
| MD event 0 存在于原始流 | PASS |
| MD event 0 kind 一致 | PASS |
| MD event 0 parent 一致 | PASS |
| MD event 1 存在于原始流 | PASS |
| MD event 1 kind 一致 | PASS |
| MD event 1 parent 一致 | PASS |
| MD event 2 存在于原始流 | PASS |
| MD event 2 kind 一致 | PASS |
| MD event 2 parent 一致 | PASS |
| MD event 5 存在于原始流 | PASS |
| MD event 5 kind 一致 | PASS |
| MD event 5 parent 一致 | PASS |
| MD event 6 存在于原始流 | PASS |
| MD event 6 kind 一致 | PASS |
| MD event 6 parent 一致 | PASS |
| MD event 7 存在于原始流 | PASS |
| MD event 7 kind 一致 | PASS |
| MD event 7 parent 一致 | PASS |
| MD event 8 存在于原始流 | PASS |
| MD event 8 kind 一致 | PASS |
| MD event 8 parent 一致 | PASS |
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
