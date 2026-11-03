# FSU-FP06-F5-W6-GATE seed8737153417061090794 审计

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
| `FSU-FP06-F5-W6-GATE-seed8737153417061090794.md` | `c41885385e1fa4ef5d0f5622db6e39279173577e711f0dd417b12b7e2ed11056` |
| `census.err` | `ac94070c9fd00342e736472f14f15e1e2f9f917536b7d47fc81b2d472ba7fff3` |
| `census.out` | `c1db93d3f09cac743454aad2722d61f2ff66c24827b03caa7b5506d6b28268a4` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `94de1a39067fe9442e33e79bffaa5ecf3c1f68e65fee53e36c908dd34eea5239` |
| `census/config.json` | `84edce690959965839b1528707ccf109037ed0b91242ea213fb1df0053c22598` |
| `census/fpu_injections.log` | `3faa7f5a9be0595b5474830742db08f719727710c394a5285dc14a0ae41241b4` |
| `census/stats.txt` | `083a0ada74a55be1e4ec9132a6e071b47f96d8d352c3279879653c153ea0de83` |
| `chain_report.json` | `393551e99f0a1556527f0001220f8fe0ad7122c107f6e1d03621322d05f258ad` |
| `component_manifest.json` | `b88f70f3b74dd9106b7009cbc3d80903094455f6f83c42d450dd31e7bcdfe71f` |
| `inject/array.bin` | `957ac57ea5e29d25471cf81f665f6cd2b39c267f20ce322510aec919e8b34dec` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `98315377d1f2d8a575002ce3f0010f7f9b5ae495afeb279c73c0a9e24d0e9eed` |
| `inject/config.json` | `d079cd2276a71901fcbc8ae94694b73b44fe598ca1bf496fc326ec33fab3decb` |
| `inject/fpu_injections.log` | `c06998f97729b0219367bcceba10cc16c22a90eea3379fbf88ad94e088d5e829` |
| `inject/prop_evt.txt.gz` | `54340b67d718f9b5b4d5aea61aeaff93bdfe59bfa094be5b29cb9c8f922d66e9` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `61893d682338f7ae0cfd5d3ff9601ee357624dcb008d837d3a486bfb9614b766` |
| `manifest.json` | `f0114c8df2b868cf4ffcfb72e8af1b4f31a757599672359b0f49845b9d3c6790` |
| `oracle.json` | `4f9940d09583926ff7de7da30028c8b2124d8e991636bae74d77fc13ad817ea7` |
| `oracle_elements.json` | `8350db1bb0e3dc574a6bda8c865fb97dde4c98fed09aa1adf59d35eb1d3eb76d` |
| `run.err` | `ac94070c9fd00342e736472f14f15e1e2f9f917536b7d47fc81b2d472ba7fff3` |
| `run.out` | `a1deb4243f3e5b8d1bb20edd2735317089739ca6155cf635a24ef071eb72e6f5` |
| `stats.txt` | `61893d682338f7ae0cfd5d3ff9601ee357624dcb008d837d3a486bfb9614b766` |

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
