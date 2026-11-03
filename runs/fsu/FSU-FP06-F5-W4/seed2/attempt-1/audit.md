# FSU-FP06-F5-W4 seed2 审计

- attempt：`attempt-1`
- sample_run_id：`s2`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 522 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '14', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `3` → `11`：✓
- `11` → `12`：✓
- `12` → `13`：✓
- `13` → `14`：✓
- `14` → `521`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W4-seed2.md` | `08b3f776a4ebcf8c07710facce45a18e357ad31d1fa896a46a2e9c81126e403c` |
| `census.err` | `279ad18c40c7f2a5d4dc8a3457ee13f80f0a4de3b1539c0601a810b6329e1eab` |
| `census.out` | `815e57e250d9c03afe107be7e1770c8f47a17f1be2331efe41ea3db80d307a00` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `6003d6b59518cabaf854d1935fde97c86abba106832e32896bd462fe0519c1f1` |
| `census/config.json` | `b94f149005922f54536270f164867fa424dfe19019e9c8a3e42590f5b3465293` |
| `census/fpu_injections.log` | `bae2f3430d2fe1401d106ccf14c2b63359fe8bd4cd9163da50479c41a706506d` |
| `census/stats.txt` | `57d32d6c8a644967aa67c3d65cfef02b993a0dad34cbd0edc70a93c0a860776b` |
| `chain_report.json` | `738dd427cec62a110f1b34cdcb912c1090d95f5f638d6a1adb1dde1167da187f` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `2e295303fcab84648b86c22e6f44771fa4bd1f3296f3956270339797e7d3ac6e` |
| `inject/config.json` | `1fdded84b6adba6a63906a1edb4633b73ca465e268be7e782ed4d41251f8bc38` |
| `inject/fpu_injections.log.gz` | `7de136f4895140087724c132fae6c0556231f45e10a31a8b87a095b34f2cb551` |
| `inject/prop_evt.txt.gz` | `18b7c386bc185ea2e7a32d9b24808d9470d10d407a84b755d2b1361143161102` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `6ec38e4c71382b0ab6f7ae90e196dafac33081cd5ea2907b88c0967f89522b2e` |
| `injection_log_storage.json` | `ccb6f973fbbdf1c32c8a22095a260d2916eccbccb3bc96ed310c0feaa1c940ce` |
| `manifest.json` | `1a5cfbcdd1e7014c59764a9d5cf4da1daac50c3349c73250c83289fa1cd849c9` |
| `oracle.json` | `fc6e1107b0a5cacd6568bda73dfed5cfc35be8fa87dae067415f9f68c9bbf7c6` |
| `run.err` | `279ad18c40c7f2a5d4dc8a3457ee13f80f0a4de3b1539c0601a810b6329e1eab` |
| `run.out` | `4c0aa5e0f2c57dac1847b8bb02613835ef0b0d616220c0528c5dea70563a77d7` |
| `stats.txt` | `6ec38e4c71382b0ab6f7ae90e196dafac33081cd5ea2907b88c0967f89522b2e` |

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
| MD event 3 存在于原始流 | PASS |
| MD event 3 kind 一致 | PASS |
| MD event 3 parent 一致 | PASS |
| MD event 11 存在于原始流 | PASS |
| MD event 11 kind 一致 | PASS |
| MD event 11 parent 一致 | PASS |
| MD event 12 存在于原始流 | PASS |
| MD event 12 kind 一致 | PASS |
| MD event 12 parent 一致 | PASS |
| MD event 13 存在于原始流 | PASS |
| MD event 13 kind 一致 | PASS |
| MD event 13 parent 一致 | PASS |
| MD event 14 存在于原始流 | PASS |
| MD event 14 kind 一致 | PASS |
| MD event 14 parent 一致 | PASS |
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
