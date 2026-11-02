# FSU-FP04-F1-W4 seed3 审计

- attempt：`attempt-1`
- sample_run_id：`s3`

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
| `FSU-FP04-F1-W4-seed3.md` | `ef47ecced8db43e984c25972c72e31eed2585eca07f2246ec910f09a304ba5a6` |
| `census.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `census.out` | `0b81fa1b4782b87a4301fb7eface32d15be38f2b8d90facba9a841064b11ede6` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `d4cfe33d92c99513612b72a4166653744d192db9bf57bd6f1257defebc1a7b9f` |
| `census/config.json` | `3bba46101ad9ec4f834efbec05627f75d8cf2492de668592d20ebee8ac97c1c2` |
| `census/fpu_injections.log` | `d153ffcef9b24d6300f5e45cc845ff6f57d519c1226cad280a84cfcae023a2c2` |
| `census/stats.txt` | `d9befee0220a28c4d38c076590a579dae7ef701c46e14211a2df64ce5bccf77e` |
| `chain_report.json` | `272afc76827fca77b2e9ebabcacaaabd1763fa1f9457b8a8bf61b242ea47db22` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `1a1145499d0fccffe162d71f4087f23a5872545e7fa709034e765c1db96ca46d` |
| `inject/config.json` | `59b8025c1dec600feb6ad1bf0854e37c84837cbe6bf7fbd3a12f020284e45485` |
| `inject/fpu_injections.log` | `35e1fa08e8a487397fbc7c4e9a86bc65caa2dd1c2ef0494afbee3c19c9832cf7` |
| `inject/prop_evt.txt.gz` | `acaf6707576b7b0f13b9d96947d5d4c57ce77443b59c3c1f3acd610037af3f25` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `06318bb50a52b05328a6ddeb0d770c41db5aba9c2f4da11791602906f98bead3` |
| `manifest.json` | `ed8b17f5ec63f2c911acee30c7d308b209dfcfc252dd04c0730e59f114bc9892` |
| `oracle.json` | `c3d31e16ba05e490a32b98b8dbd1a5519b12567ef73a02d8ea8407b5b7651550` |
| `ordinals.json` | `39e0b89571c30645f0ee14a5f53a3a59230f2422480007513230a67de8e2ccaa` |
| `run.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `run.out` | `61c0840dfaf1845ef9ef6816baf3a2b3e4a41b19b1284d474aca2871184e90d1` |
| `stats.txt` | `06318bb50a52b05328a6ddeb0d770c41db5aba9c2f4da11791602906f98bead3` |

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
