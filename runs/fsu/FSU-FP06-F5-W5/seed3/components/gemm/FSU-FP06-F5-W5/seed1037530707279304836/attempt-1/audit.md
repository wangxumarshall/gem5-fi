# FSU-FP06-F5-W5 seed1037530707279304836 审计

- attempt：`attempt-1`
- sample_run_id：`s1037530707279304836`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 521 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '12', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `9`：✓
- `9` → `10`：✓
- `10` → `11`：✓
- `11` → `12`：✓
- `12` → `520`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W5-seed1037530707279304836.md` | `80ac4b0d39d6f8699eada2f06eabb53354f174c7d10c87481c6eed44ee23b84c` |
| `census.err` | `aab1510bc39780187ded556b781e6fb104354304676b3bc41045a0db1c656efe` |
| `census.out` | `19431cf806c5c901ed6056643fbc9dddca012675a839815127c66c77ac912ca1` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `06c17f685a7efc6299511cdb279f07d18a0317a289cf4c7d3cfc838465abd61a` |
| `census/config.json` | `f8e73ffbebae374010155d5f0f8b7c97c4f61b5930202639e77909005bb62966` |
| `census/fpu_injections.log` | `c572620f84da4017f4dbf0ecf0779476a9a7aaca7c2c50031dcb18f76c0a0305` |
| `census/stats.txt` | `17dfb797b61e3be0e91f8962e7dfa01ee8344d97d0b20be0fc6204808e370058` |
| `chain_report.json` | `4db82f48bed5f63199a056ebacf5859e40b559a7d0f1a2149257765e3b4fa318` |
| `component_manifest.json` | `84a85d8997627fdd3097140f5975ff8f76594e260244cf52e693002f07498b95` |
| `inject/array.bin` | `a7ced08c62e894bdb8c5e0ef8a47244015c3d4785169e6280c1f0b9d7f809633` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `c887ec16ba481211aa6e7cb54c2923b40459b4b52dafc082271b87395af9e11d` |
| `inject/config.json` | `f216826d9ecb737f264cfcd0cd0d416a2bea12508783d2bb3bc3073bc4f64711` |
| `inject/fpu_injections.log.gz` | `ad42eacebf6445dd07ad599309889749ccafdec6bbfca4da58b3fc2a6cf4d2d5` |
| `inject/prop_evt.txt.gz` | `3cd7807829691f7f98f934d4884c570003f12c8a5dc746bd64495872a678e6b1` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `e51ee63e48118617b846ce78ca08678364cb4604c5cf5dd93b576d18e4fbbe40` |
| `injection_log_storage.json` | `904029aa927582d3dea9c89c89622a8a7daeb09b795f123a4c39e36658f724d6` |
| `manifest.json` | `7e558ff8f11f5267710e44da87490939c597de190fb7c91f93b8d256a6fd9114` |
| `oracle.json` | `a10d99f1b92aa32203fab13ded6f9aaf29cb2fcfd9d25308b57d673046d8c12a` |
| `oracle_elements.json` | `3b3491aa7cfb8102e0e77d14ea3ad0f3fd0091e98daf673320115eeb7f018ccd` |
| `run.err` | `aab1510bc39780187ded556b781e6fb104354304676b3bc41045a0db1c656efe` |
| `run.out` | `173e2fdd848dddebd852c94c4b958f2202ec70e01457cee3b95e90bbf78e4740` |
| `stats.txt` | `e51ee63e48118617b846ce78ca08678364cb4604c5cf5dd93b576d18e4fbbe40` |

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
| MD event 9 存在于原始流 | PASS |
| MD event 9 kind 一致 | PASS |
| MD event 9 parent 一致 | PASS |
| MD event 10 存在于原始流 | PASS |
| MD event 10 kind 一致 | PASS |
| MD event 10 parent 一致 | PASS |
| MD event 11 存在于原始流 | PASS |
| MD event 11 kind 一致 | PASS |
| MD event 11 parent 一致 | PASS |
| MD event 12 存在于原始流 | PASS |
| MD event 12 kind 一致 | PASS |
| MD event 12 parent 一致 | PASS |
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
