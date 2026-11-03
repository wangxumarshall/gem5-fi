# FSU-FP06-F5-W6 seed8737153417061090794 审计

- attempt：`attempt-1`
- sample_run_id：`s8737153417061090794`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 520 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L4, L5；N/A=['L3'] |
| L5 witness | {'event_id': '20', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
| 1 | full | True | True | True | True | L0, L1, L2, L4, L5 | [] |

## 边（主 fault）

- `0` → `1`：✓
- `1` → `2`：✓
- `2` → `16`：✓
- `16` → `19`：✓
- `19` → `20`：✓
- `20` → `519`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W6-seed8737153417061090794.md` | `bb55f1b7861d329401c6574e35e71d10b5eed356b02e41797bb3003d634dc53d` |
| `census.err` | `ac94070c9fd00342e736472f14f15e1e2f9f917536b7d47fc81b2d472ba7fff3` |
| `census.out` | `c1db93d3f09cac743454aad2722d61f2ff66c24827b03caa7b5506d6b28268a4` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `94de1a39067fe9442e33e79bffaa5ecf3c1f68e65fee53e36c908dd34eea5239` |
| `census/config.json` | `84edce690959965839b1528707ccf109037ed0b91242ea213fb1df0053c22598` |
| `census/fpu_injections.log` | `3faa7f5a9be0595b5474830742db08f719727710c394a5285dc14a0ae41241b4` |
| `census/stats.txt` | `e96580c75ce5d8cfbd543145c07fcc1301d5c6b09d99ef042f1ab10371d82274` |
| `chain_report.json` | `d406f293c2cda8d2209fc33b27951edd0bccc2d08f49b5acfa471d628656a859` |
| `component_manifest.json` | `2403d94fbd7850d07bc1624af3525424b4680c1a6c0e75b14aa796cbe7781d62` |
| `inject/array.bin` | `957ac57ea5e29d25471cf81f665f6cd2b39c267f20ce322510aec919e8b34dec` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `a5078cac2402df19b11f4559807e35e03a61793b3a85c2b46df5ac74f56a8d8a` |
| `inject/config.json` | `7b776f3f96e912e233890cfb9706c67e8821e2be897f7513aa1959fce42b0e90` |
| `inject/fpu_injections.log` | `8e8d88cee02baa1d4b69e4098a82ff36e24f4999d102076daa8a56356eb95031` |
| `inject/prop_evt.txt.gz` | `a8c9836594cfd9165ec334f3f02fe808f2e9258c0ab50bef00b34a151e42d3dc` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `452a538f04172a447f882af83550c417988215367da76a436a8f7e9588f75af2` |
| `manifest.json` | `c633bf50d8b9e0e5553f1f6d81a16d99ad7320c41b305748f78c86868abefeae` |
| `oracle.json` | `4f9940d09583926ff7de7da30028c8b2124d8e991636bae74d77fc13ad817ea7` |
| `oracle_elements.json` | `f15570d03c51de4547028b386c2d39c786ed7234e7765d97c5ea98ec6b9d5271` |
| `run.err` | `ac94070c9fd00342e736472f14f15e1e2f9f917536b7d47fc81b2d472ba7fff3` |
| `run.out` | `1b6acb59f12a393813a3b8d55e6ff4a4b6aaaeb16f403cac58b65b3ac5770b6e` |
| `stats.txt` | `452a538f04172a447f882af83550c417988215367da76a436a8f7e9588f75af2` |

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
| MD event 16 存在于原始流 | PASS |
| MD event 16 kind 一致 | PASS |
| MD event 16 parent 一致 | PASS |
| MD event 19 存在于原始流 | PASS |
| MD event 19 kind 一致 | PASS |
| MD event 19 parent 一致 | PASS |
| MD event 20 存在于原始流 | PASS |
| MD event 20 kind 一致 | PASS |
| MD event 20 parent 一致 | PASS |
| MD event 519 存在于原始流 | PASS |
| MD event 519 kind 一致 | PASS |
| MD event 519 parent 一致 | PASS |
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
