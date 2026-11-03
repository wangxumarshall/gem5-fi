# FSU-FP04-F0-W5 seed5536446555532653464 审计

- attempt：`attempt-1`
- sample_run_id：`s5536446555532653464`

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
| `FSU-FP04-F0-W5-seed5536446555532653464.md` | `b3248054620c07c3f962ad2f8e979f8d65879f2ea4ea087c8ab12faf5499de50` |
| `census.err` | `aab1510bc39780187ded556b781e6fb104354304676b3bc41045a0db1c656efe` |
| `census.out` | `19431cf806c5c901ed6056643fbc9dddca012675a839815127c66c77ac912ca1` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `089d96adf2ca7dc8d81285f8163cd0f81f35548d4908c3a94849f81e40840105` |
| `census/config.json` | `c1ec8451049d1e56a8341471a601cd2fbdd2525938ff4f6b16f90cb2cee5561c` |
| `census/fpu_injections.log` | `c30027422776ed0ad6973238dbba8a29728c808dad3b27ff3dffc5ddd7a906e5` |
| `census/stats.txt` | `1ead698a8740f04b5b7266457ce51b6e50b0ab3cf2d79560879b85eb015e0af0` |
| `chain_report.json` | `ad0e995822eb17a5a41e1a27dc127fdddb57a1ee6a4090cda295808df063a942` |
| `component_manifest.json` | `80c1bf3120ec21dc80bf5700c7d2b1c33e6966ced642e8d4667bba747dc9d337` |
| `inject/array.bin` | `f88fbd91ffabe6ba83e348c40b2907468db52260cbbf9a44eadd9b3a72ef3f6c` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `6c220a159be855637eaab0105ff95df45de7008339b3a4f9021b86ef0dd65b84` |
| `inject/config.json` | `ddec840104c137e7fc9bc7ce4bb73a7e60f45b698ab426b2f435da95cb653971` |
| `inject/fpu_injections.log` | `90a5923a6e8be5ac383ebb5f6ae6020b54fe10a8df16ac038494d5b5016d1c48` |
| `inject/prop_evt.txt.gz` | `2e514d912d344459c5f1d9ad6a60a9f57361fb2ce95ec00cf86c6fa31da0c2dd` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `6f5e466f49dd519ec9fe6fc397d8ec27b17f32aea00bced03081af57336b5641` |
| `manifest.json` | `1037d890039309295f6833be881fa220eb5c11c138c18aa0caba6cf43940fdb1` |
| `oracle.json` | `90de01ff163cf3365d9118df980e0ae5814083b114126a8bf9b160fe884cf118` |
| `oracle_elements.json` | `c6bd7c419a0762684a0857dacbf8e18c1d2a1ed5ad6e6e943c2cdcfe419f24e2` |
| `run.err` | `aab1510bc39780187ded556b781e6fb104354304676b3bc41045a0db1c656efe` |
| `run.out` | `b98d19115d51a85bf23314d86f4e3aa938daca0fff799c0c5e3b18b92ca526c8` |
| `stats.txt` | `6f5e466f49dd519ec9fe6fc397d8ec27b17f32aea00bced03081af57336b5641` |

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
