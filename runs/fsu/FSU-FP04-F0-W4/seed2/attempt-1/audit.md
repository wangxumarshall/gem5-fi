# FSU-FP04-F0-W4 seed2 审计

- attempt：`attempt-1`
- sample_run_id：`s2`

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
| admitted | True |
| certified | True |
| violations | [] |

## 边

- `0` → `1`：✓
- `1` → `2`：✓
- `2` → `3`：✓
- `3` → `4`：✓
- `4` → `5`：✓
- `5` → `6`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP04-F0-W4-seed2.md` | `ed2a26b991c232665e7138bc12ee24987909b3c9aa211be116a515df19a9927b` |
| `census.err` | `89736f20b2030718beca99e4246b7e20e1e59dfcdbda8d07067bff6783a4a5dc` |
| `census.out` | `457c78dcbd899dfa4eb314e9ae7c7e62df07c3b239e4339933dfc0205adae068` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `ce0c622180b356eae8de22467e3686403d4b751029c95caee502477fef9a592c` |
| `census/config.json` | `7c541575d1fcb63b81127c0f7b991015900410f51cbc68b585fe0b880752e89a` |
| `census/fpu_injections.log` | `7bc8726ba761e237b918a253b4aa17afe92f63b6fb33bcdbe3233ab77f314a00` |
| `census/stats.txt` | `c4df7c04d18fa6cc9142bec42f28c4d2d6206afcdc4f69d2728731dbb986f263` |
| `chain_report.json` | `ff67f863c998f720a1c7077eb5c977c97e4ed8f81d2ba5214ea384352404af4b` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `78f906d40c44ad25910266c096a07180b4ac09732226fbe58de16d95875b2cd6` |
| `inject/config.json` | `51dc2503d4a5d76c2c4b8483c2fba1814d7a4184f7e02b7922e1081b216af78a` |
| `inject/fpu_injections.log` | `e2721c7e734e1f732b7dd664a2e31b85e7df3a389480be2b9d1e87ee882edcde` |
| `inject/prop_evt.txt.gz` | `fc5ca226fac390fde8425e87dbb9abf78b164f94c344a5ea4586c56180eb8cb7` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `511e09115e4e7bcf7bc2e608cbf6cc07af250e35e283ba626dcfa764c70a99b6` |
| `manifest.json` | `85049d4a94f1869c92dd597db0912c08bde37b50947bc25b18aac00107221e4f` |
| `oracle.json` | `456ee36c9aa9b5184195f4bb174620929e723542cf4f47d1b1c21056be754cbe` |
| `run.err` | `89736f20b2030718beca99e4246b7e20e1e59dfcdbda8d07067bff6783a4a5dc` |
| `run.out` | `c9d3ea631060f5d036a7a6972c7777f9e12b5cbb98182bdf72c3055ebbadcca9` |
| `stats.txt` | `511e09115e4e7bcf7bc2e608cbf6cc07af250e35e283ba626dcfa764c70a99b6` |

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
| fault 1 terminal 一致 | PASS |
| fault 1 violations 一致 | PASS |
| fault 1 admitted 一致 | PASS |
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
| MD 覆盖原始主链全部事件 | PASS |
| MD terminal 与 chain_report 一致 | PASS |
| MD admitted/certified 与 chain_report 一致 | PASS |
| evidence_sha256.json 存在 | PASS |
| 证据 SHA-256 全部匹配（失配 0） | PASS |
| stats.txt 非空 | PASS |
| admitted=True | PASS |
| violations=[] | PASS |

**结论：PASS**
