# FSU-FP06-F5-W5 seed9731202158273511969 审计

- attempt：`attempt-1`
- sample_run_id：`s9731202158273511969`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 521 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '42', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `39`：✓
- `39` → `40`：✓
- `40` → `41`：✓
- `41` → `42`：✓
- `42` → `520`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W5-seed9731202158273511969.md` | `9e1233a792ec54b970f4f95d1dd90e1dc6bbb5e4753c53d1b5b6557993f929de` |
| `census.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `census.out` | `ebd792f6461d512abb42df564d9864a21c462de74f95e4b3be8c792d316f3851` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `e4083a195cc5a4d2513a3639a4a3fd774d07463e10922448e801d4585d660dec` |
| `census/config.json` | `64e8175fdee26e766bdcf57413b8392540316ccf71b59f31322ca1af305311f8` |
| `census/fpu_injections.log` | `6888b5f440be65818781c1e962672d465a94da01be8d84aea2d5b24ec3abc9aa` |
| `census/stats.txt` | `3d16f4d5815751f8946487ef6a6d2e154b108be31b6041ee679163c516d391bc` |
| `chain_report.json` | `73342b05be3952a4478cc8953d61d3cf63c91c3cd5aea3b6415eccdbdd2a179f` |
| `component_manifest.json` | `b5b62d6ba22471fd40362a45b33d7713078bd4a42c92284a078e415f1ec609c0` |
| `inject/array.bin` | `cea015ea4b56c860775b00a44736494cef4d4217463ce40d73b6bc2bea57c182` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `8b3d9242b619150bc31e87e84f3cc28de39d76fe5432c7d5cfc6d87598bed28a` |
| `inject/config.json` | `2216f2843dfa1b194c1032dd6bdaa7609cc7b0793d3e71dc0e740b3dee56921d` |
| `inject/fpu_injections.log.gz` | `bb801b870319ef6a092b058fa60cf88d01a36584251e8be827e863cd1a90d302` |
| `inject/prop_evt.txt.gz` | `018dd1d3fd58d7fe46914fca83485a326aa21a04f0bccca41d8c316bd42d175f` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `92661d09424dc03556d0aeb784bd6afcf6f2f36ebc72e6649c6f85a74bf99524` |
| `injection_log_storage.json` | `ca0ddc7b73ee02b3c07ad05932a9acaa69fc93e7433fed97491d59ac353a2af0` |
| `manifest.json` | `d59915178efa330f6260caa4eaa57d9152ae13e63d9c4c973459f725d413f102` |
| `oracle.json` | `85ae2d492c08a0c519cf2c074b7a67eec351642ec868daac2caa88dcee4cda81` |
| `oracle_elements.json` | `d87ff77d65b24af73f95eb58055fb2a855c251a0007333bfb5d25c2c38f2d35c` |
| `run.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `run.out` | `dc8060bd64409c1ccd0c2814009f39fab469eabff195e7c823ca5aed438f041a` |
| `stats.txt` | `92661d09424dc03556d0aeb784bd6afcf6f2f36ebc72e6649c6f85a74bf99524` |

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
| MD event 39 存在于原始流 | PASS |
| MD event 39 kind 一致 | PASS |
| MD event 39 parent 一致 | PASS |
| MD event 40 存在于原始流 | PASS |
| MD event 40 kind 一致 | PASS |
| MD event 40 parent 一致 | PASS |
| MD event 41 存在于原始流 | PASS |
| MD event 41 kind 一致 | PASS |
| MD event 41 parent 一致 | PASS |
| MD event 42 存在于原始流 | PASS |
| MD event 42 kind 一致 | PASS |
| MD event 42 parent 一致 | PASS |
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
