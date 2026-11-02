# FSU-FP04-F1-W4 seed1 审计

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
| `FSU-FP04-F1-W4-seed1.md` | `152454c157a9262990d8c9f6ed574ff2ad72b968949daa20eba3f99b665c9c8b` |
| `census.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `census.out` | `0b81fa1b4782b87a4301fb7eface32d15be38f2b8d90facba9a841064b11ede6` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `e6e3a796572dc93e6066ba853fed04ce6ece68d22bbad21c317575037ad14373` |
| `census/config.json` | `24b40ecc21e89a11bf887131cdd106e0054cfa650ab03b61ed766bdfb86d40a6` |
| `census/fpu_injections.log` | `d153ffcef9b24d6300f5e45cc845ff6f57d519c1226cad280a84cfcae023a2c2` |
| `census/stats.txt` | `ec5fcf0ea2e202ad61be380f0618aa303232f0c637d8adcdc8c103d75dffb229` |
| `chain_report.json` | `e388bd6b2982e750022ef227d670f9d685c1d619667e1903cc5b8b1817406f55` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `33823347a9dad827edb2623be8ed511d9128b43f5ca151b97ec3af7bf4aea351` |
| `inject/config.json` | `fbf69e3e6e0228ac1ed07787fcd47ff6aa0718c5b3cffaf3f05bfbbd9c25cd55` |
| `inject/fpu_injections.log` | `5198600acf12a013616c7c6dddb47d11801a04125c3ced50d9af0cae4d71a0fa` |
| `inject/prop_evt.txt.gz` | `45b0de25c72ace63d6160d8b6aac823d6b26793232ef54ef60153351c2a85056` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `43ee881bfac6ce88b0dfc397f39ef9993828cdd5ef6fafaf1f54f73f90f0e871` |
| `manifest.json` | `80a90826f33401fe254557be266749288c1fb99cd96bb09ba6f99fb775981cc1` |
| `oracle.json` | `748817ade9d580d2f51504c8899e6df14db71a40a5ef126d017095d5cc752e2a` |
| `ordinals.json` | `b8e80e065b4cbe2352f85fc0ca092e625ddb190aa44e5b1d0e2f67f7fc3ef892` |
| `run.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `run.out` | `fddadba105b0f167f3c7eb9d22e1352745d9d6259df0a6ef641545dbc5270b23` |
| `stats.txt` | `43ee881bfac6ce88b0dfc397f39ef9993828cdd5ef6fafaf1f54f73f90f0e871` |

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
