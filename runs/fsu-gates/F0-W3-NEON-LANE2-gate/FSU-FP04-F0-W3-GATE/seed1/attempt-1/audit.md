# FSU-FP04-F0-W3-GATE seed1 审计

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
| `FSU-FP04-F0-W3-GATE-seed1.md` | `55fae404d2da8b31bb9194b8434363aa831f5b57194d38ebab54e424b347eacf` |
| `census.err` | `3b94bc39600d81ebe273ced2f04543d363c1f8965959df54c0ee05789173dbaf` |
| `census.out` | `c700ade0802ee2163fbd21cc6974ca492622677e84322b994eb446a0f8b96be9` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `73503eb61837067ba0842b00766bec503c0bfe79d477f2b8a88f99029570adc6` |
| `census/config.json` | `b497a2901998267495b4629072fbf7af3641d3a62c9b949fef2e74097aedf7c4` |
| `census/fpu_injections.log` | `d00d38340db51de7c1c6fb62f1bb636a1d50ee3b76ed17e3e40a2db17bb3130f` |
| `census/stats.txt` | `8b5d2db7bc893d92bee0f688000785041dc9fb5e0189eb2ac3c1aada20341ee0` |
| `chain_report.json` | `6fac7c0ec0c6f50fae667184bf3c4132debb9bee2f25e2cd8a3fcade9b38fcc9` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `27d73daed4d4ec885ec5376961319e1436a43138c0bbc8f3c8ed643f8f7de559` |
| `inject/config.json` | `c44bc2cb94472df0c9e48ffdfcf68d7667606cb9f86b99e9ac01c515b6a5d893` |
| `inject/fpu_injections.log` | `df89ade630d47dd9085481753014c2d73b2991b499e83ec78379bb540714d6b8` |
| `inject/prop_evt.txt.gz` | `12812c4ad9caff68e1992d0a6730059d3778b3ff8f4c925a56936c0ffb750787` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `aa2081ed50e4716918ca7696c5c74fecca763acab2a08f556b5394ed2a93660a` |
| `manifest.json` | `b954edcdda35adcf4a87b50a0fb09cb4b3e81167fa24e8d1701460c9e46be33e` |
| `oracle.json` | `a933ca4d8001ccc015348a3d9873aa0d0ad36f1ad52bb625176f4f66ad99a19c` |
| `run.err` | `3b94bc39600d81ebe273ced2f04543d363c1f8965959df54c0ee05789173dbaf` |
| `run.out` | `4a3d59063693ccfa8981168908c5f1ff750c6e6efea1535f2803abc3b70ea84c` |
| `stats.txt` | `aa2081ed50e4716918ca7696c5c74fecca763acab2a08f556b5394ed2a93660a` |

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
