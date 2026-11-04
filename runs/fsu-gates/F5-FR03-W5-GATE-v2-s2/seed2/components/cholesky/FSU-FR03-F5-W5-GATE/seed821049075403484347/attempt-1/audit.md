# FSU-FR03-F5-W5-GATE seed821049075403484347 审计

- attempt：`attempt-1`
- sample_run_id：`s821049075403484347`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 113 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '110', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `72` → `81`：✓
- `81` → `86`：✓
- `86` → `95`：✓
- `95` → `103`：✓
- `103` → `108`：✓
- `108` → `109`：✓
- `109` → `110`：✓
- `110` → `111`：✓
- `111` → `112`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W5-GATE-seed821049075403484347.md` | `d70dde0794276aeb01fd461f56fc6b6342208349b091f738b168e77a9adf7338` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `8821d7f9894c4596e30a62f80bd2a73525b40df0ac13412df91a28d34fe2d591` |
| `component_manifest.json` | `a71cc6bf167d1785e61054207bd2812c5c8e9ca53060e5f9615ef2ddfea48820` |
| `inject/array.bin` | `ad54ba81bc46aa236d3fc8e663dda077853e513721685ba78abe940108879f43` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `7b71b750efa1b76e1674e98543d3baa84939822272633650cc8f2a096a7aeef3` |
| `inject/config.json` | `b08304263856072fd20feb7c1c1e402c05feb82c87ac7cb62984349d98a02ae5` |
| `inject/fault_injections.log` | `780fb9b94d1c70d1a30827be15ae77ec35dc53d77ffe26a96476c8f545bafb5b` |
| `inject/prop_evt.txt.gz` | `2f9b633aa8d25a743f1cd62168754c3f5f2f21b70dc5ad2fa5ac968e7d8c00f8` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `bb778b4232e7896a9c2b8cf6134a3f379c97320c4e7c9bc40287544808b5cd79` |
| `manifest.json` | `b955e728439a9ad07884f6e6e06016aa9495300634b47a1d3e7f5de0a2910e66` |
| `oracle.json` | `d2a52949f2c89404332a0b3de2fd672184b311eaf3f38b745e51c3bb0934cedf` |
| `oracle_elements.json` | `c830ad82b94951ac3f35befd081939edf51b0dea75b877ee5406732c186bbcba` |
| `run.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `run.out` | `b972620a0ca82bf4cc7d3dbca38d70ee28261e2082648831dce52e6f1f4415de` |
| `stats.txt` | `bb778b4232e7896a9c2b8cf6134a3f379c97320c4e7c9bc40287544808b5cd79` |

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
| MD event 81 存在于原始流 | PASS |
| MD event 81 kind 一致 | PASS |
| MD event 81 parent 一致 | PASS |
| MD event 86 存在于原始流 | PASS |
| MD event 86 kind 一致 | PASS |
| MD event 86 parent 一致 | PASS |
| MD event 95 存在于原始流 | PASS |
| MD event 95 kind 一致 | PASS |
| MD event 95 parent 一致 | PASS |
| MD event 103 存在于原始流 | PASS |
| MD event 103 kind 一致 | PASS |
| MD event 103 parent 一致 | PASS |
| MD event 108 存在于原始流 | PASS |
| MD event 108 kind 一致 | PASS |
| MD event 108 parent 一致 | PASS |
| MD event 109 存在于原始流 | PASS |
| MD event 109 kind 一致 | PASS |
| MD event 109 parent 一致 | PASS |
| MD event 110 存在于原始流 | PASS |
| MD event 110 kind 一致 | PASS |
| MD event 110 parent 一致 | PASS |
| MD event 111 存在于原始流 | PASS |
| MD event 111 kind 一致 | PASS |
| MD event 111 parent 一致 | PASS |
| MD event 112 存在于原始流 | PASS |
| MD event 112 kind 一致 | PASS |
| MD event 112 parent 一致 | PASS |
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
