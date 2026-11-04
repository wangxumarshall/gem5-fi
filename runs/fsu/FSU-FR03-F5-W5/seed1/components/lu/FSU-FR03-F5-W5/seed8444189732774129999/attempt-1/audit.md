# FSU-FR03-F5-W5 seed8444189732774129999 审计

- attempt：`attempt-1`
- sample_run_id：`s8444189732774129999`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 84 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '80', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `72` → `77`：✓
- `77` → `79`：✓
- `79` → `80`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W5-seed8444189732774129999.md` | `75fdf7a9113f29449e69123b9f701337f6f711a84b0e29d190b8a94c2bcf56c4` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `636c3df40a9b31cfde09cddac7aa2ea32e3dbd64b9d76de4a004d6d470f63e97` |
| `component_manifest.json` | `d7fe4e7d30def4470fe94b8f30cf82176b260e075332e09d6219452aba805c51` |
| `inject/array.bin` | `46eb754c53cf2ecffe653675230b55272073383f69806a3169a45ba35733dd60` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `cb9690dc5871fbd8bed3414d29101cabf6ca0e48955a1884df2ba3e52308d2fb` |
| `inject/config.json` | `8234edab290aa4cac208e9add881496677c97b5a1297b487fd3560b2b3fca051` |
| `inject/fault_injections.log` | `301932aa5b3461eaf96d31119cbdb97a1b9713ffc2bbd9c1591ca51cef88e84e` |
| `inject/prop_evt.txt.gz` | `a489382e17b3d8e53925b5b0b505518fb63da97881faec57a6ba4c801bb5b60d` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `a1b9ae1b4410447d7a32e8a012f7b71b23ee215485d44352bdfa478ed0f03d56` |
| `manifest.json` | `aec691b82cc69b150ba9912c73d8f439c4aff60484180602b626818257f0f2b5` |
| `oracle.json` | `757ed252c689adc7455611072b9f4f019d08f47c2d0cb8e03da77503cf61447c` |
| `oracle_elements.json` | `cd9057f734a9ebde4bc5404d55ba54e7058e2dab4b948a2b607f348f361a3bf0` |
| `run.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `run.out` | `f867ea72866e88615f5b5617a87407c122b376e72a93c8b81f10c335de2e4b9a` |
| `stats.txt` | `a1b9ae1b4410447d7a32e8a012f7b71b23ee215485d44352bdfa478ed0f03d56` |

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
| MD event 77 存在于原始流 | PASS |
| MD event 77 kind 一致 | PASS |
| MD event 77 parent 一致 | PASS |
| MD event 79 存在于原始流 | PASS |
| MD event 79 kind 一致 | PASS |
| MD event 79 parent 一致 | PASS |
| MD event 80 存在于原始流 | PASS |
| MD event 80 kind 一致 | PASS |
| MD event 80 parent 一致 | PASS |
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
