# FSU-FP04-F0-W6 seed10230542913907129042 审计

- attempt：`attempt-3`
- sample_run_id：`s10230542913907129042`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 7 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '5', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `3`：✓
- `3` → `4`：✓
- `4` → `5`：✓
- `5` → `6`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP04-F0-W6-seed10230542913907129042.md` | `9bf13b67f4659c2a26ccbf450e8d73bb978cfab01db0a6ff2029a36651b43c5a` |
| `census.err` | `e798c107ac5ec23672815724a64d0efaab3e9a7a5c4a78f21880c7252f78fe80` |
| `census.out` | `71b0fec718fc3877f1b9d14881b902f6a946569c8e349e47508f127b566107e9` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `e666c838beb8d332c74a2fbe4ad17a119f83edde05c27c937ba97a6722039eec` |
| `census/config.json` | `2da1963330c604f00d82bf074c7a8e0c6ea00688855f7e31a3aef4ba6c834055` |
| `census/fpu_injections.log` | `087bc3ceedd301bd607f7361e9afb309f73a49379488262b1a933d1238a5d32f` |
| `census/stats.txt` | `0b5770e062e8f25e7c48ad718b7a7a5105e1a9d6595f5dbfe9080a1e2b511936` |
| `chain_report.json` | `a2e4b6c27d55254628ea16f5c09fa7ca06842dc97cade2fd40e6e04fe2e2ebb3` |
| `component_manifest.json` | `947d9a6e0ac369234c29e6a6dcdea4a3ea37f068b7a32dbd34e1a46519f99d1f` |
| `inject/array.bin` | `324171cf1a2f8a1d5e4ca9e7465cb57b5b0ecdb56f7005ebb7973f4f4e61b369` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `c94c1f235dc00269c4f5c4fe2633f0a05147d4151aa7fae087da40849053c1f5` |
| `inject/config.json` | `ca84b080cf5c74e2c4091e500ef7e0057e0315c8d35f0c53c8922498cb6da68e` |
| `inject/fpu_injections.log` | `822ced56baab254fccf35e6d30e7890d195bb1870671bfd7cf5134955dc594f7` |
| `inject/prop_evt.txt.gz` | `85332a44af1ce7d3019f6c43b1e91de4ebfe959630f0d222e72965a3784859b7` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `47435ca1f8465b9349b56c5221788fb9e335362d23f8cfb58eb1ab6a698682ab` |
| `manifest.json` | `7bc8799e9f229b2af41d1c90359596db26ac62cc8c4a718c8afcb3b1f673eb2d` |
| `oracle.json` | `82a035b44fff31050312615e083945e20ac28972323148b9ded01c79c5acf64a` |
| `oracle_elements.json` | `3f9f98ae82aa901d3e5e32043f44d5de6fb9dbf935652e41b8da311ffd3a1d32` |
| `run.err` | `e798c107ac5ec23672815724a64d0efaab3e9a7a5c4a78f21880c7252f78fe80` |
| `run.out` | `e12768bf7fc9ebfd10bc558ad4b699423003babf5c4b7feb4da89b57e6063c34` |
| `stats.txt` | `47435ca1f8465b9349b56c5221788fb9e335362d23f8cfb58eb1ab6a698682ab` |

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
