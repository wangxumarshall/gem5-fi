# FSU-FP04-F3-W4-GATE seed1 审计

- attempt：`attempt-1`
- sample_run_id：`s1`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 28 |
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
| fault 数 | 4 |
| 所有 fault admitted | True |
| 所有 fault certified | True |
| violations（主 fault） | [] |

## 逐 fault 审计

| fault | terminal | admitted | certified | direct parent | tick 单调 | layers | violations |
|---|---|---|---|---|---|---|---|
| 1 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 2 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 3 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 4 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |

## 边（主 fault）

- `0` → `1`：✓
- `1` → `2`：✓
- `2` → `3`：✓
- `3` → `4`：✓
- `4` → `5`：✓
- `5` → `24`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP04-F3-W4-GATE-seed1.md` | `e8f6d8e7f3360da1ebe0bc92b704251a72bbfb67c71d16b2f337d6661cad5ea1` |
| `census.err` | `89736f20b2030718beca99e4246b7e20e1e59dfcdbda8d07067bff6783a4a5dc` |
| `census.out` | `457c78dcbd899dfa4eb314e9ae7c7e62df07c3b239e4339933dfc0205adae068` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `7f28f9b6023b53f40ddef6122de8a887dbaa1969baf03b1e3a55d1c34f709714` |
| `census/config.json` | `32a9699d32ccce05ac993e4fb8b2a5473c8ecb1ddbfea1dad6c3a799941021e0` |
| `census/fpu_injections.log` | `7bc8726ba761e237b918a253b4aa17afe92f63b6fb33bcdbe3233ab77f314a00` |
| `census/stats.txt` | `f4a6ecc2818a54959006ed18b0272ec6706366ec1f0412bd1f1df3594c220d9f` |
| `chain_report.json` | `57aabc59766cb1737cf16399aabea0a625f244072b072e0648fa5b9edcfc3e21` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `3ea71148d1cf0200f3ce8c8637b04ea8ed53a2dbd50690e46d3d3869e59c5f3d` |
| `inject/config.json` | `dfb7cdd5b76089461533073855d579b350aed2ca8c5308558a2e5977c39beb53` |
| `inject/fpu_injections.log` | `fffbc5da680dd958176a126d744702d746737f376f95337677756d7ed94d915c` |
| `inject/prop_evt.txt.gz` | `80e855a72e6bcc52f8943c13212e872a64af3bba94a0967110674c0007332063` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `d5890184d75166599738e3763bb64cdf533b81e3d069152d2f4470ad0447eecf` |
| `manifest.json` | `c28e3768c5d5f48e54cbde15c2f090c788441cfaca1b2eaf8a259e8ca024d3d4` |
| `oracle.json` | `c6a156b55f0b02f6445c5941a0b8a47c8b0ddcb8ff220831e4550a425c431c59` |
| `ordinals.json` | `2e5b7546da9616a5d99b0160a483607bcf172bfd580ccd6ecb630b988f1ae122` |
| `run.err` | `89736f20b2030718beca99e4246b7e20e1e59dfcdbda8d07067bff6783a4a5dc` |
| `run.out` | `f0381346ac62cd0f57698ebcaf8603fc1dc025ea9b9c84166b69c9eedfedae0b` |
| `stats.txt` | `d5890184d75166599738e3763bb64cdf533b81e3d069152d2f4470ad0447eecf` |

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
| fault 2 terminal 一致 | PASS |
| fault 2 violations 一致 | PASS |
| fault 2 admitted 一致 | PASS |
| fault 2 certified 一致 | PASS |
| fault 3 terminal 一致 | PASS |
| fault 3 violations 一致 | PASS |
| fault 3 admitted 一致 | PASS |
| fault 3 certified 一致 | PASS |
| fault 4 terminal 一致 | PASS |
| fault 4 violations 一致 | PASS |
| fault 4 admitted 一致 | PASS |
| fault 4 certified 一致 | PASS |
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
| MD event 24 存在于原始流 | PASS |
| MD event 24 kind 一致 | PASS |
| MD event 24 parent 一致 | PASS |
| MD event 6 存在于原始流 | PASS |
| MD event 6 kind 一致 | PASS |
| MD event 6 parent 一致 | PASS |
| MD event 7 存在于原始流 | PASS |
| MD event 7 kind 一致 | PASS |
| MD event 7 parent 一致 | PASS |
| MD event 8 存在于原始流 | PASS |
| MD event 8 kind 一致 | PASS |
| MD event 8 parent 一致 | PASS |
| MD event 9 存在于原始流 | PASS |
| MD event 9 kind 一致 | PASS |
| MD event 9 parent 一致 | PASS |
| MD event 10 存在于原始流 | PASS |
| MD event 10 kind 一致 | PASS |
| MD event 10 parent 一致 | PASS |
| MD event 11 存在于原始流 | PASS |
| MD event 11 kind 一致 | PASS |
| MD event 11 parent 一致 | PASS |
| MD event 25 存在于原始流 | PASS |
| MD event 25 kind 一致 | PASS |
| MD event 25 parent 一致 | PASS |
| MD event 12 存在于原始流 | PASS |
| MD event 12 kind 一致 | PASS |
| MD event 12 parent 一致 | PASS |
| MD event 13 存在于原始流 | PASS |
| MD event 13 kind 一致 | PASS |
| MD event 13 parent 一致 | PASS |
| MD event 14 存在于原始流 | PASS |
| MD event 14 kind 一致 | PASS |
| MD event 14 parent 一致 | PASS |
| MD event 15 存在于原始流 | PASS |
| MD event 15 kind 一致 | PASS |
| MD event 15 parent 一致 | PASS |
| MD event 16 存在于原始流 | PASS |
| MD event 16 kind 一致 | PASS |
| MD event 16 parent 一致 | PASS |
| MD event 17 存在于原始流 | PASS |
| MD event 17 kind 一致 | PASS |
| MD event 17 parent 一致 | PASS |
| MD event 26 存在于原始流 | PASS |
| MD event 26 kind 一致 | PASS |
| MD event 26 parent 一致 | PASS |
| MD event 18 存在于原始流 | PASS |
| MD event 18 kind 一致 | PASS |
| MD event 18 parent 一致 | PASS |
| MD event 19 存在于原始流 | PASS |
| MD event 19 kind 一致 | PASS |
| MD event 19 parent 一致 | PASS |
| MD event 20 存在于原始流 | PASS |
| MD event 20 kind 一致 | PASS |
| MD event 20 parent 一致 | PASS |
| MD event 21 存在于原始流 | PASS |
| MD event 21 kind 一致 | PASS |
| MD event 21 parent 一致 | PASS |
| MD event 22 存在于原始流 | PASS |
| MD event 22 kind 一致 | PASS |
| MD event 22 parent 一致 | PASS |
| MD event 23 存在于原始流 | PASS |
| MD event 23 kind 一致 | PASS |
| MD event 23 parent 一致 | PASS |
| MD event 27 存在于原始流 | PASS |
| MD event 27 kind 一致 | PASS |
| MD event 27 parent 一致 | PASS |
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
| fault 2 MD 覆盖主链全部事件 | PASS |
| fault 2 MD/原始流 direct parent | PASS |
| fault 2 MD 逐 fault 终局行存在 | PASS |
| fault 2 MD terminal 一致 | PASS |
| fault 2 MD admitted 一致 | PASS |
| fault 2 MD certified 一致 | PASS |
| fault 3 MD 覆盖主链全部事件 | PASS |
| fault 3 MD/原始流 direct parent | PASS |
| fault 3 MD 逐 fault 终局行存在 | PASS |
| fault 3 MD terminal 一致 | PASS |
| fault 3 MD admitted 一致 | PASS |
| fault 3 MD certified 一致 | PASS |
| fault 4 MD 覆盖主链全部事件 | PASS |
| fault 4 MD/原始流 direct parent | PASS |
| fault 4 MD 逐 fault 终局行存在 | PASS |
| fault 4 MD terminal 一致 | PASS |
| fault 4 MD admitted 一致 | PASS |
| fault 4 MD certified 一致 | PASS |
| MD terminal 与 chain_report 一致 | PASS |
| MD admitted/certified 与 chain_report 一致 | PASS |
| evidence_sha256.json 存在 | PASS |
| 证据 SHA-256 全部匹配（失配 0） | PASS |
| stats.txt 非空 | PASS |
| admitted=True | PASS |
| violations=[] | PASS |

**结论：PASS**
