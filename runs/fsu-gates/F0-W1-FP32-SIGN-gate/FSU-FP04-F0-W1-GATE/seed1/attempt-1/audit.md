# FSU-FP04-F0-W1-GATE seed1 审计

- attempt：`attempt-1`
- sample_run_id：`s1`

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
| `FSU-FP04-F0-W1-GATE-seed1.md` | `1f0f19752d904d0b451727989a87f96586f37b85a80c738037c6b7bec0e2e64a` |
| `census.err` | `0417ff9982266f3b600e35fbd8fe02d81e37399ffa90930ea5d638b8a649c218` |
| `census.out` | `2e31ec2e224c57bcd7709e39eeefd092b0230670f67d8cc80917423f7fdb0b67` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `1de21d5e209d5a1898b56fca4e60a9021649ecc53bab5aa3620a7b3a26677ed6` |
| `census/config.json` | `bfe47d5976092023a7d4893b833e268bbf63788c6965653ef7fde5201b459a30` |
| `census/fpu_injections.log` | `79b6fba93055242c4fcaebb79021ed59efdaf7b1d80bb5425945394d0edad996` |
| `census/stats.txt` | `e976274d8ca4f70f9b146d1e91a18d8ed5ec4da978f468ce493e70afb2b1e8a5` |
| `chain_report.json` | `d9f410c7a5fd05bd36fe50a3db8b93d02d0454b56342bfc52790f95ef49ac41f` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `b646503f966549f06ffe1101ca6216badf99bd6212c0fcfe1cf29d76fea38270` |
| `inject/config.json` | `488be8f7ab0dfa755abc61d5e26fb0cc47153535dfe7ec9d72c9fec5a80e0fea` |
| `inject/fpu_injections.log` | `c7109d5b6ab75c3f8906237307d1da3e11344379b026b1a6a684f0d7804bfd8c` |
| `inject/prop_evt.txt.gz` | `2c4ce53c0133fd6b3d77fd61c9897d2a0e77ae5b4448f5f8cdf407c0ef502fbe` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `28ddce7305c3f51319200bb92aa8eef7681c1c739bf9ea6a37c8673765e3d00e` |
| `manifest.json` | `41a52f6ec921a81e41c7beeb61a32dcfbe2585094713075ff0aa5b189df64f8b` |
| `oracle.json` | `da885e2066b0eba0669c9cd49ca698c45896e9956118cccbf52200b312b94707` |
| `run.err` | `0417ff9982266f3b600e35fbd8fe02d81e37399ffa90930ea5d638b8a649c218` |
| `run.out` | `6666f1d7258d037c473590e92c639056152f6811bf206fced4eedf9c4de48b67` |
| `stats.txt` | `28ddce7305c3f51319200bb92aa8eef7681c1c739bf9ea6a37c8673765e3d00e` |

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
| scheduled(1) = fault_applied(1) | PASS |
| 每个 injected fault 均真实激活 | PASS |
| fault 1 字段/lane/mask 语义 | PASS |
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
| MD 逐 fault 终局表存在 | PASS |
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
| admitted=True | PASS |
| violations=[] | PASS |

**结论：PASS**
