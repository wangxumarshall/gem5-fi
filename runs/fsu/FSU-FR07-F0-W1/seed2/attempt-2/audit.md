# FSU-FR07-F0-W1 seed2 审计

- attempt：`attempt-2`
- sample_run_id：`s2`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 8 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '6', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `1` → `3`：✓
- `3` → `4`：✓
- `4` → `5`：✓
- `5` → `6`：✓
- `6` → `7`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR07-F0-W1-seed2.md` | `4cb7fa18d2016a493096e91ed4110f2fc19240a637f9bcfeab9c7e197c6a5862` |
| `census.err` | `d0903335a494a11f367331e8ebf85f0386bced2f2cc85a825bb6415899e45a03` |
| `census.out` | `2db6a778ec445a146baf8a47b0bde89307c65e23d3f13f150b2466ce50b251e5` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `681d6c05c6a4b019b7d716c34a9225551f4d731b62d2fbeea4485e27e0cb03fe` |
| `census/config.json` | `9b459841e40a3371c3e131b3add1d937091a8d97139b50279960a5fd0a43ae7f` |
| `census/fpu_injections.log` | `2b19dc8502ca5832c97dc669a6441c91dbe3fdddd1e53b729d2e449b6b86c45d` |
| `census/stats.txt` | `cb4b27b21c92a9b3de94c197fe3dc89df4fc406db79558bda6be361ca872f7a0` |
| `chain_report.json` | `8ab9001635f04f9dcd1c589a919035a565d7813f1ecc5c0f88120ea0638b4dc3` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `706ccbe6a11c168271a29b0b3200474522388b5fa7a6d5a74d9ddedce5b1a0f9` |
| `inject/config.json` | `b2a5d89bfcf0abc54b1d5f83acea434df1803b364b08712e36087adcdbba767c` |
| `inject/fpu_injections.log` | `c9335e0442836011f29864e698f2564736282a4e5f31e82dc7910119c4d23419` |
| `inject/prop_evt.txt.gz` | `9889b6164027d60e976c810e06d0265e94c4defaa04d6c0df0f40f58b283b64d` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `5c7cf6969f3369c0b07a7cf528f4ec8771dc8c8af4d8099624d9fa554a351170` |
| `manifest.json` | `62dbbe3c73e81ce79fcf629ec3ea2c117829aad1fe498f9a800e40bf814ff59c` |
| `oracle.json` | `bc03209953ab7da773fd5a28c7463bc7ee2c713665dd7ba9143610414d62d933` |
| `run.err` | `d0903335a494a11f367331e8ebf85f0386bced2f2cc85a825bb6415899e45a03` |
| `run.out` | `ed69d9bfc79376718aa0384a8cbbbb31d5cdd514e60c380d62eabfbff034b1d5` |
| `stats.txt` | `5c7cf6969f3369c0b07a7cf528f4ec8771dc8c8af4d8099624d9fa554a351170` |

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
| MD event 7 存在于原始流 | PASS |
| MD event 7 kind 一致 | PASS |
| MD event 7 parent 一致 | PASS |
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
