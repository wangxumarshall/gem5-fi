# FSU-FP04-F0-W5 seed664471552991680598 审计

- attempt：`attempt-2`
- sample_run_id：`s664471552991680598`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 7 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '5', 'kind': 'commit', 'outcome': 'errant_commit'} |
| oracle | Masked |
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
| `FSU-FP04-F0-W5-seed664471552991680598.md` | `4932d7dce7b23100302bfe663af517d4e32cf5a6216ecea627b3eaca9e70984a` |
| `census.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `census.out` | `ebd792f6461d512abb42df564d9864a21c462de74f95e4b3be8c792d316f3851` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `6ea72718bb78fba0fe8835e425a65352044c435930b402251e23a204270348df` |
| `census/config.json` | `f3a4d19765cae73c3836822de0058a05f277f5a782df63998988ac7bc8eb1da6` |
| `census/fpu_injections.log` | `8b66562bae879a94dd4b30dbecea756d9847812eee986c294b925dc0b6f0d968` |
| `census/stats.txt` | `8ea6fcd94cdc208007032eee92a637b22a0de93dcc09d66d62d449f2483a2c8b` |
| `chain_report.json` | `19123b517e0e91efe34038a3f23d871097d4d179d3f0df5f70ff2dd3c85c5f4c` |
| `component_manifest.json` | `e0f8a064e875df13514c915df540da8449e777c8504000f7427d9472f64f3f72` |
| `inject/array.bin` | `ad54ba81bc46aa236d3fc8e663dda077853e513721685ba78abe940108879f43` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `80918d12481e1f003e089b9911f82aeedfa0af0eb3fdafb916146e43f0f4aff6` |
| `inject/config.json` | `2981b50bdd92fb27dfd16938fe6ac2a772e0e3186baf9e442485965a697926b0` |
| `inject/fpu_injections.log` | `cb0a9d6862c52fa01cc001df3791555c1512f88c6d5c0646b6bb1facff73e84e` |
| `inject/prop_evt.txt.gz` | `fdbf2851c3b38ea20053db2519bb6288f56cb8f698eb4a28796dc6d3bd7e20eb` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `790411d246883f4333a9365c15edc43ee93a0abf81b49f14670fca683ae88d22` |
| `manifest.json` | `cde2035c84a5f5b254a2cf824e80897b5c7ea1e632062c9d1896c7fc422f6a9d` |
| `oracle.json` | `118222a7e56b23c5f71a6810b7f49deef93b9d93d81cc5ca99936a2da9406a56` |
| `oracle_elements.json` | `503f1433da9bbe4f3dde36daaeb49d37be9cfb1e06f0046c234749933678ae96` |
| `run.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `run.out` | `cb755e41f34025fc339e70f5ad316116799f81f8fa6261c673d4cab160dcd5ed` |
| `stats.txt` | `790411d246883f4333a9365c15edc43ee93a0abf81b49f14670fca683ae88d22` |

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
