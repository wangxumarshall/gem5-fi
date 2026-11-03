# FSU-FP04-F0-W6 seed9543147912694745727 审计

- attempt：`attempt-1`
- sample_run_id：`s9543147912694745727`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 7 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '5', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `3`：✓
- `3` → `4`：✓
- `4` → `5`：✓
- `5` → `6`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP04-F0-W6-seed9543147912694745727.md` | `0b40dada785fda021fb101bc9e7c133ef4d41abb104fdf38ade4155aa18315cd` |
| `census.err` | `ac94070c9fd00342e736472f14f15e1e2f9f917536b7d47fc81b2d472ba7fff3` |
| `census.out` | `c1db93d3f09cac743454aad2722d61f2ff66c24827b03caa7b5506d6b28268a4` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `7c221c6dcb399ed78f694f3e28adf119fd9cfef3b821a2f6714112016fefcafc` |
| `census/config.json` | `2e62de5b7d22c93522b416e6b3afbaf824fc11c290b2a36a7993b0f3bd419206` |
| `census/fpu_injections.log` | `3faa7f5a9be0595b5474830742db08f719727710c394a5285dc14a0ae41241b4` |
| `census/stats.txt` | `cf758b1cb984341b63bb3a2d95840e081f2ff3d9434a62fbf32a30d87216bd42` |
| `chain_report.json` | `6a2782de4a72d16531e390b1ddcfeeb6032e7a22f23216495dffe4b505981bb8` |
| `component_manifest.json` | `be5939e452c86c2680eddf1855fc5129e14ccb0b53aba1ab34e75650392d8705` |
| `inject/array.bin` | `c39769bd4bff2a92d0522ca27ac4256dcf1e0727edc70bc42f993e8c5db2e2ed` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `b9119df41086a7950ad010f6d094dbed15134f57ae7dc9c90fafb151e4a9d5e8` |
| `inject/config.json` | `d6a801b077c02c954755ea544e2e42f9b245c5bee6e5495f80d46cc30be10b0a` |
| `inject/fpu_injections.log` | `d5e92acd65a215bbcca0f13139bc915cb99062247c6c516f279bb6f26e1344c7` |
| `inject/prop_evt.txt.gz` | `ec8d6c84afdc1c1d56c191a6de974f48ce3b7ac9127a9670f9b758c73378490a` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `d5207d9e3afd4163f8d8c63c274e72551bee5256d6093d368e7f07b968a58a69` |
| `manifest.json` | `6adaf27fe8ffb5737f5150a3db1fa30daf9489413d9577addb07d66985ee0da3` |
| `oracle.json` | `863f4b0086907c016fd45a8970cc1e7af08afd7baf6af18c8af52216924c299d` |
| `oracle_elements.json` | `2242324b336c787edc9bb1b3fab37db5dfa63d03705de15362584215ce428083` |
| `run.err` | `ac94070c9fd00342e736472f14f15e1e2f9f917536b7d47fc81b2d472ba7fff3` |
| `run.out` | `c32027f3ea7ad63fba5dcc34ce2510b92e3320bdac3ddf6a4b569f447124bb19` |
| `stats.txt` | `d5207d9e3afd4163f8d8c63c274e72551bee5256d6093d368e7f07b968a58a69` |

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
| MD event 3 存在于原始流 | PASS |
| MD event 3 kind 一致 | PASS |
| MD event 3 parent 一致 | PASS |
| MD event 4 存在于原始流 | PASS |
| MD event 4 kind 一致 | PASS |
| MD event 4 parent 一致 | PASS |
| MD event 5 存在于原始流 | PASS |
| MD event 5 kind 一致 | PASS |
| MD event 5 parent 一致 | PASS |
| MD event 6 存在于原始流 | PASS |
| MD event 6 kind 一致 | PASS |
| MD event 6 parent 一致 | PASS |
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
