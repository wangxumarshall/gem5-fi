# FSU-FR03-F5-W5 seed16497714004944453208 审计

- attempt：`attempt-1`
- sample_run_id：`s16497714004944453208`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 84 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '80', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `16`：✓
- `16` → `24`：✓
- `24` → `36`：✓
- `36` → `45`：✓
- `45` → `53`：✓
- `53` → `61`：✓
- `61` → `72`：✓
- `72` → `77`：✓
- `77` → `79`：✓
- `79` → `80`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W5-seed16497714004944453208.md` | `b540e9ce25b21e667b6eb00ca019a1d56af4127f92cb5b086a276eaf374ec743` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `1c2f1ca9d56fb8a1e09a48729c942880544b0a581fb9beff5cb4919b355996f0` |
| `component_manifest.json` | `f37dac6108c4feb05bdf442cc6615303fa3280592ef12e42cc7d6eaf21b4af42` |
| `inject/array.bin` | `ad54ba81bc46aa236d3fc8e663dda077853e513721685ba78abe940108879f43` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `9a146ba105916cc0254577357c37222bd6033c30af65328e80db74ab5eb40a27` |
| `inject/config.json` | `9ed4fd03c6c743bed8d42290ab33d100b11dbbc87bdda31258bfc704ea1f377e` |
| `inject/fault_injections.log` | `6fd43715e212fa081cb18a9f571700bf9f83a48571944622bffa35df2466d88d` |
| `inject/prop_evt.txt.gz` | `b2df4e2e461b11b034ad9ee5f35c3f924a95164994bb89b50e59f20b87265147` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `f7f7eb0ba1d6c231e867b1b212459d096bd3a51e5de5a02e34d4165e1caa1ce4` |
| `manifest.json` | `41972dd82fd9d23f4dd0b0264d7808a762fb52af62999e46ed82a43648344bc0` |
| `oracle.json` | `784354c3044e4f879f1455790e72d27382cfb118e7ef3b846904b9f4b4b77ace` |
| `oracle_elements.json` | `ff933edcff9ae2fe198b1ef182796a0a089035b50fcf1cb90c42c10e083278d5` |
| `run.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `run.out` | `f8352821e673e394b669a1bf9e454707c84900282a3612ac4a43022dbc85a3d1` |
| `stats.txt` | `f7f7eb0ba1d6c231e867b1b212459d096bd3a51e5de5a02e34d4165e1caa1ce4` |

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
| MD event 16 存在于原始流 | PASS |
| MD event 16 kind 一致 | PASS |
| MD event 16 parent 一致 | PASS |
| MD event 24 存在于原始流 | PASS |
| MD event 24 kind 一致 | PASS |
| MD event 24 parent 一致 | PASS |
| MD event 36 存在于原始流 | PASS |
| MD event 36 kind 一致 | PASS |
| MD event 36 parent 一致 | PASS |
| MD event 45 存在于原始流 | PASS |
| MD event 45 kind 一致 | PASS |
| MD event 45 parent 一致 | PASS |
| MD event 53 存在于原始流 | PASS |
| MD event 53 kind 一致 | PASS |
| MD event 53 parent 一致 | PASS |
| MD event 61 存在于原始流 | PASS |
| MD event 61 kind 一致 | PASS |
| MD event 61 parent 一致 | PASS |
| MD event 72 存在于原始流 | PASS |
| MD event 72 kind 一致 | PASS |
| MD event 72 parent 一致 | PASS |
| MD event 77 存在于原始流 | PASS |
| MD event 77 kind 一致 | PASS |
| MD event 77 parent 一致 | PASS |
| MD event 79 存在于原始流 | PASS |
| MD event 79 kind 一致 | PASS |
| MD event 79 parent 一致 | PASS |
| MD event 80 存在于原始流 | PASS |
| MD event 80 kind 一致 | PASS |
| MD event 80 parent 一致 | PASS |
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
