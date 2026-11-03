# FSU-FP06-F5-W5 seed9890028866439031825 审计

- attempt：`attempt-1`
- sample_run_id：`s9890028866439031825`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 522 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '158', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `1` → `151`：✓
- `151` → `155`：✓
- `155` → `156`：✓
- `156` → `157`：✓
- `157` → `158`：✓
- `158` → `521`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W5-seed9890028866439031825.md` | `d207bf4b8709e1c6197c139d10c0d3a084ee3a19f748aaf9c87c84c8a89b8c62` |
| `census.err` | `aab1510bc39780187ded556b781e6fb104354304676b3bc41045a0db1c656efe` |
| `census.out` | `19431cf806c5c901ed6056643fbc9dddca012675a839815127c66c77ac912ca1` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `2080016e23335b772043e0cbb3c5d7d0e06c1eb0aef8b6ac28d1de753c79a9d0` |
| `census/config.json` | `2b6823e5cafb23ccb3c7f08d1c8f5aa1223e94ef49c2acff8a4ecc9d89e55afd` |
| `census/fpu_injections.log` | `c572620f84da4017f4dbf0ecf0779476a9a7aaca7c2c50031dcb18f76c0a0305` |
| `census/stats.txt` | `a44d431987cd856af10bde4cd75dfa606181bb3df8a327dc83d47c48b9a9709e` |
| `chain_report.json` | `56b733a61c6d4bedad664caa9637dcc1cafd384f844190c5b3595c86a58aa84f` |
| `component_manifest.json` | `72030e081949ce7bde06d33dfa32e9f019d22622a16a0b4c40d86161037e513a` |
| `inject/array.bin` | `9c7a21d0a02f1d38759a97689e19c314f6876715d3a59ede2e151f15d38db9a3` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `244e3d3be43bea657ef24f75aba6b5fef1ea623b648ae89c5b87c2df687fd368` |
| `inject/config.json` | `569ccbf4fbe4f461dcd864b4681fb5845b393841bb9c370ab0c5ab0690d88757` |
| `inject/fpu_injections.log.gz` | `5e1c36621288dde9bce9e9d56462caca5e79dee2e3a73bf4d202e1b951bd7ecb` |
| `inject/prop_evt.txt.gz` | `400ccd7f460c442fd40a24a797904ac89bc45935786ba727f1f7d84341d065aa` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `e4c0c7375a122f0c55c4947c12d6c7c646f94ef1e7257e374c1dc10acffcccc0` |
| `injection_log_storage.json` | `a0f9f7d50a66c5f088c8ceb054f8f03f719c8455a86a02cc93d2d1032bfe84aa` |
| `manifest.json` | `0161f835d2d38c40258dd3f08223f4a26c7d40002e28b96dd71fc389025a49e1` |
| `oracle.json` | `90f14903cae3cec59d2b0dfafb7490c4e60be9ab45065862d6a71f38fa032e78` |
| `oracle_elements.json` | `e11190bfd16174c8a8583cbeee13f2e16dc80ad6249b5e62bd9a11e47c561ffe` |
| `run.err` | `aab1510bc39780187ded556b781e6fb104354304676b3bc41045a0db1c656efe` |
| `run.out` | `932ab01efd08326bf5922059eff1955d71e9e95cf3908ca8799ce30088821a11` |
| `stats.txt` | `e4c0c7375a122f0c55c4947c12d6c7c646f94ef1e7257e374c1dc10acffcccc0` |

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
| MD event 151 存在于原始流 | PASS |
| MD event 151 kind 一致 | PASS |
| MD event 151 parent 一致 | PASS |
| MD event 155 存在于原始流 | PASS |
| MD event 155 kind 一致 | PASS |
| MD event 155 parent 一致 | PASS |
| MD event 156 存在于原始流 | PASS |
| MD event 156 kind 一致 | PASS |
| MD event 156 parent 一致 | PASS |
| MD event 157 存在于原始流 | PASS |
| MD event 157 kind 一致 | PASS |
| MD event 157 parent 一致 | PASS |
| MD event 158 存在于原始流 | PASS |
| MD event 158 kind 一致 | PASS |
| MD event 158 parent 一致 | PASS |
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
