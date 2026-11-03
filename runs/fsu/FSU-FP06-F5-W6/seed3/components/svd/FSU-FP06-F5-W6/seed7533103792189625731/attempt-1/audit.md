# FSU-FP06-F5-W6 seed7533103792189625731 审计

- attempt：`attempt-1`
- sample_run_id：`s7533103792189625731`

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
| `FSU-FP06-F5-W6-seed7533103792189625731.md` | `e8f171b5692a9d20aab5a31a669455a76b7bfabd5dddb8c028c268c4ac85cbe3` |
| `census.err` | `ac94070c9fd00342e736472f14f15e1e2f9f917536b7d47fc81b2d472ba7fff3` |
| `census.out` | `c1db93d3f09cac743454aad2722d61f2ff66c24827b03caa7b5506d6b28268a4` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `9de560d37df2aac5cd2d4431365b82161d03ececd0668ba43f37ab3c6a6bfe61` |
| `census/config.json` | `07f1934cea0217b3dd3dcc1144f33438ee804368269029008fe65d5c5705280d` |
| `census/fpu_injections.log` | `3faa7f5a9be0595b5474830742db08f719727710c394a5285dc14a0ae41241b4` |
| `census/stats.txt` | `5e51d84f2bc1c8669f2073695b806db7d2e2857afb44b176d5d95b8bc6944a45` |
| `chain_report.json` | `b70673d3913954b2845173b18e02cceb31f3a90eb3d4664a49dcac787a7c4a6b` |
| `component_manifest.json` | `4ed56b4a4bf6557772ac35accaf95cfe2e6ba7c1aef35bf7620cab665d6a070d` |
| `inject/array.bin` | `35f5c0798d745f94ab8dfcdf143de72b633e9472f3890e8aab56ed540b11dae5` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `cb2c7d05d81b304dde03ba13b0ecaa1ece5a7e52ad81e7f57aa91ae51f5ec495` |
| `inject/config.json` | `57994792bf04595b9b4ec8e724ed70f53252b1a8a2bbc375ec958e6a6aecd29f` |
| `inject/fpu_injections.log` | `8bf1e1f3533e9ca692e0da5321fe0abc948a56474ad4874451427253ef7e8a4e` |
| `inject/prop_evt.txt.gz` | `8c2fc64a7ab3176233d0dba5952903d8babc0ffd6d69eef813035711a7a68942` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `66d90328a9dd816a6a09e46a93c0938595ff69389387f2182fe3e50af2c07956` |
| `manifest.json` | `48d5860d0f86584ba9586a67bda8a0587dd17a2d642124c835c2c2258a1a5ded` |
| `oracle.json` | `a01e3219af4c1e78020ce7ca97bae7ad1881900b1166dd9ff5ee1afc15f105fa` |
| `oracle_elements.json` | `c6b42bb67831cf61bc14e6d3c660015adb6282a6b100254887d075115e2cbb3d` |
| `run.err` | `ac94070c9fd00342e736472f14f15e1e2f9f917536b7d47fc81b2d472ba7fff3` |
| `run.out` | `7111b599a53e3f24e1e2d844ce72aa1df07055de7c5737241c349f3cf1e3270e` |
| `stats.txt` | `66d90328a9dd816a6a09e46a93c0938595ff69389387f2182fe3e50af2c07956` |

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
