# FSU-FR03-F5-W5 seed18144183937250453399 审计

- attempt：`attempt-1`
- sample_run_id：`s18144183937250453399`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 155 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '152', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `6`：✓
- `6` → `14`：✓
- `14` → `25`：✓
- `25` → `33`：✓
- `33` → `41`：✓
- `41` → `46`：✓
- `46` → `55`：✓
- `55` → `66`：✓
- `66` → `75`：✓
- `75` → `83`：✓
- `83` → `91`：✓
- `91` → `92`：✓
- `92` → `101`：✓
- `101` → `112`：✓
- `112` → `121`：✓
- `121` → `122`：✓
- `122` → `133`：✓
- `133` → `144`：✓
- `144` → `149`：✓
- `149` → `151`：✓
- `151` → `152`：✓
- `152` → `153`：✓
- `153` → `154`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W5-seed18144183937250453399.md` | `dec22a0ad1086c0c415e590010a782cd5bce403b1df6e276892cae3f994a8691` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `fe0d0040c3aca9e2cb4fe4e647a02cb01508641b354077bbc1dd6e0e503f9e20` |
| `component_manifest.json` | `8fd8dfdbc49b9fde789d0add12ed9619b162dc0dd5055c41bf7f7d6bafa12d79` |
| `inject/array.bin` | `23eb863deda56bcbd897823b0fcc0832907661ca0b80980a6aa5acaaa388ed9a` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `e14eec922ae356c937e251abdc5b9eedd9fcfa062be7fbd058d3ee3e92cd5140` |
| `inject/config.json` | `6a40af579f412ae82711693ce3961f7de07d4b1b29053aaedf2666d777090d4c` |
| `inject/fault_injections.log` | `3e0688b15af51fd2ffb376ae1dd6a5716553ed091ecb178f25508d35f0080ad6` |
| `inject/prop_evt.txt.gz` | `4ac0e1e6ce4448ddbdf560a24e71e7e339200e3157241725eee6071272532cbc` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `cd0be6f658283d882dad4f15aaa4e5405d3e93f32d1443c583ba6245ea2dd36e` |
| `manifest.json` | `843a4b54da42b874b3573797662b7bd2e1ede99c4388cfaa260f83ed49a0a8ce` |
| `oracle.json` | `dd40335360e8e879a627cdc815a486576c96735795f35f0e45e699ac55accf9b` |
| `oracle_elements.json` | `434a7c3a0d4fa40c81ab25a7633cd77801d7cfb6081b2ec0f99b0a04416fa0d9` |
| `run.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `run.out` | `84cf3573dc79cd5e2962eaa55d57af464513e2b2d40b37af654342730bdd201c` |
| `stats.txt` | `cd0be6f658283d882dad4f15aaa4e5405d3e93f32d1443c583ba6245ea2dd36e` |

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
| MD event 6 存在于原始流 | PASS |
| MD event 6 kind 一致 | PASS |
| MD event 6 parent 一致 | PASS |
| MD event 14 存在于原始流 | PASS |
| MD event 14 kind 一致 | PASS |
| MD event 14 parent 一致 | PASS |
| MD event 25 存在于原始流 | PASS |
| MD event 25 kind 一致 | PASS |
| MD event 25 parent 一致 | PASS |
| MD event 33 存在于原始流 | PASS |
| MD event 33 kind 一致 | PASS |
| MD event 33 parent 一致 | PASS |
| MD event 41 存在于原始流 | PASS |
| MD event 41 kind 一致 | PASS |
| MD event 41 parent 一致 | PASS |
| MD event 46 存在于原始流 | PASS |
| MD event 46 kind 一致 | PASS |
| MD event 46 parent 一致 | PASS |
| MD event 55 存在于原始流 | PASS |
| MD event 55 kind 一致 | PASS |
| MD event 55 parent 一致 | PASS |
| MD event 66 存在于原始流 | PASS |
| MD event 66 kind 一致 | PASS |
| MD event 66 parent 一致 | PASS |
| MD event 75 存在于原始流 | PASS |
| MD event 75 kind 一致 | PASS |
| MD event 75 parent 一致 | PASS |
| MD event 83 存在于原始流 | PASS |
| MD event 83 kind 一致 | PASS |
| MD event 83 parent 一致 | PASS |
| MD event 91 存在于原始流 | PASS |
| MD event 91 kind 一致 | PASS |
| MD event 91 parent 一致 | PASS |
| MD event 92 存在于原始流 | PASS |
| MD event 92 kind 一致 | PASS |
| MD event 92 parent 一致 | PASS |
| MD event 101 存在于原始流 | PASS |
| MD event 101 kind 一致 | PASS |
| MD event 101 parent 一致 | PASS |
| MD event 112 存在于原始流 | PASS |
| MD event 112 kind 一致 | PASS |
| MD event 112 parent 一致 | PASS |
| MD event 121 存在于原始流 | PASS |
| MD event 121 kind 一致 | PASS |
| MD event 121 parent 一致 | PASS |
| MD event 122 存在于原始流 | PASS |
| MD event 122 kind 一致 | PASS |
| MD event 122 parent 一致 | PASS |
| MD event 133 存在于原始流 | PASS |
| MD event 133 kind 一致 | PASS |
| MD event 133 parent 一致 | PASS |
| MD event 144 存在于原始流 | PASS |
| MD event 144 kind 一致 | PASS |
| MD event 144 parent 一致 | PASS |
| MD event 149 存在于原始流 | PASS |
| MD event 149 kind 一致 | PASS |
| MD event 149 parent 一致 | PASS |
| MD event 151 存在于原始流 | PASS |
| MD event 151 kind 一致 | PASS |
| MD event 151 parent 一致 | PASS |
| MD event 152 存在于原始流 | PASS |
| MD event 152 kind 一致 | PASS |
| MD event 152 parent 一致 | PASS |
| MD event 153 存在于原始流 | PASS |
| MD event 153 kind 一致 | PASS |
| MD event 153 parent 一致 | PASS |
| MD event 154 存在于原始流 | PASS |
| MD event 154 kind 一致 | PASS |
| MD event 154 parent 一致 | PASS |
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
