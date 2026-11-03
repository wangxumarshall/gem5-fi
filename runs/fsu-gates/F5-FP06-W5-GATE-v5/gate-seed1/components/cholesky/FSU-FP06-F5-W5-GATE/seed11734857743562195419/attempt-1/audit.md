# FSU-FP06-F5-W5-GATE seed11734857743562195419 审计

- attempt：`attempt-1`
- sample_run_id：`s11734857743562195419`

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
| `FSU-FP06-F5-W5-GATE-seed11734857743562195419.md` | `85d6aaa5aeb9f18bcd1e4833afc2a3c098856e3c10f0605cce6d83e745560a3e` |
| `census.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `census.out` | `ebd792f6461d512abb42df564d9864a21c462de74f95e4b3be8c792d316f3851` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `8079afe16c94ae9e1ba04249cf0ef2ee70e3008b3626e55d9b25a1361e4cd9ea` |
| `census/config.json` | `ddb96c3f40ac82d652758a95829eb640647c1d90ce810630aaa5c0215b31eeb6` |
| `census/fpu_injections.log` | `6888b5f440be65818781c1e962672d465a94da01be8d84aea2d5b24ec3abc9aa` |
| `census/stats.txt` | `33905732a763d7de621acc6d521cb8fb94f7f41678345ba4f879cabff0e3d856` |
| `chain_report.json` | `46f14f0a2437dda6a3563e7dab95168911429b60c9fc8a4fe05d3ed4c42e2884` |
| `component_manifest.json` | `050afe322c6f3f7c46785daa6df891b733c3142bcb62ce3b06392e89f6e44c2b` |
| `inject/array.bin` | `51ce8e215036381118ffbee3b946f9093677c42964c46d6abcedb81197391844` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `418540411c7774c1af8466a785f6c32dfe823bb421a856c9ff0c11261b0cfbdc` |
| `inject/config.json` | `a75a9af53c0c8a330037ade1b38592ef12ae5ebb7aeff9e92102283ea1291d26` |
| `inject/fpu_injections.log` | `77ade4b1f4e8e404c123b9cf5cb9b414f4908286a2ba38c41a04cea42ad12318` |
| `inject/prop_evt.txt.gz` | `0454b0c71e8eb5fbab0439a4efbfc69dca5aa513bea4f5074818f6fc84dbf8ed` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `a29048fcc64a76b5c91c204e67d731cd9a2e4fa235643173f4229dd7c76d71a9` |
| `manifest.json` | `55e084280e07a2471c6ae14030d7ba5fd82a34078a79b90cc9cfccd0ebb73876` |
| `oracle.json` | `472811f60448943e60ecb5cd0dea590ed20711da786be12e5c222a416614d710` |
| `oracle_elements.json` | `b9fff3545494f399544ef1b5e2036858105c981a8a8d2c87c56322271d2b0cf7` |
| `run.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `run.out` | `4225fa7d59d995271e703fcdc97e315bde219238154088ac76c552610617f8a5` |
| `stats.txt` | `a29048fcc64a76b5c91c204e67d731cd9a2e4fa235643173f4229dd7c76d71a9` |

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
