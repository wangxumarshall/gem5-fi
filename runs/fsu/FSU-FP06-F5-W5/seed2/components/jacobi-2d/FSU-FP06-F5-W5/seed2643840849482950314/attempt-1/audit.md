# FSU-FP06-F5-W5 seed2643840849482950314 审计

- attempt：`attempt-1`
- sample_run_id：`s2643840849482950314`

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
| `FSU-FP06-F5-W5-seed2643840849482950314.md` | `a9b48118efc11d34f6f59795982e434b740b596af72958041ebb5503b8b8c43f` |
| `census.err` | `412bdbb81cc5c76efc9bbb5f0948c687f5dfa2c45db12966c536f4bfcddd2797` |
| `census.out` | `a83bf9a08c7f01c1600686f92a34d8f8fa586e8f29b2ef0e41175066b7a8496a` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `1e478714b1a6b8d7e52d026a19da91346dcacf461faf3bd965c9841d3b779904` |
| `census/config.json` | `05f4921fa43ea92841a7f540b7d7ca1e0c8ce21caca488fac393fb6df7e9b06e` |
| `census/fpu_injections.log` | `5364c25fa30df322a51a8f82a182e02d8e6a1179076e680a7e746bfc21d7e84f` |
| `census/stats.txt` | `191de1608ad61f1d9cedffaa73030e0c8f3d4b78992a4c17ce0227dacb610753` |
| `chain_report.json` | `9b412f2440c4283bf70b4842a87dfe5d076ab58b6f856c51d6f2ec41bdfc6172` |
| `component_manifest.json` | `304fbb9e2cfcfe30e5459797edddb2b4dd4d13687f0eebd8d0c73772d50b2fe8` |
| `inject/array.bin` | `0f02b744082edccb0cb804d6d6fe4d27ab1e079855cbea2ec577a3db74786974` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `3d123bd84c213db0995338b0713119ea153971cc2aa27b19c6abb343f01cacbf` |
| `inject/config.json` | `42ed1407c8d71a00f08997f34e9277239baa60693b60c414c78d6a1ae95759b8` |
| `inject/fpu_injections.log.gz` | `bf27bc38d5db4963648dd32fd96ccb22b4256fa2adee7c3ef609c94817299420` |
| `inject/prop_evt.txt.gz` | `003b2a73c64ba18def27c42827a523742c75c7e193b20399b8fa1deecc4d56e2` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `fc8b5248d31d0b738000a41c8cce065a3ad3e7cc4dae8bf372bc8f3c4b65dda8` |
| `injection_log_storage.json` | `b59188a5ceaa05aeb8c0ca5eb3770ee66f4e3d7bd796a7370b4caff2073dc3df` |
| `manifest.json` | `343f4975d69ab15181de82f5bed55b4157376386897cd88ab1d5e7eef30ff49b` |
| `oracle.json` | `3f12504c4e4f4220e2425bfe4861eca58dd4476ed15f958967f2e03df7f7a122` |
| `oracle_elements.json` | `f807b1c6817defa055ebdab2627dfe5acc5933ecc283d0ddc434cf1df6565fd5` |
| `run.err` | `412bdbb81cc5c76efc9bbb5f0948c687f5dfa2c45db12966c536f4bfcddd2797` |
| `run.out` | `011645f1718f0dd83e3de0395f744fbe6f181ddbb3985d3029735f9289405a17` |
| `stats.txt` | `fc8b5248d31d0b738000a41c8cce065a3ad3e7cc4dae8bf372bc8f3c4b65dda8` |

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
