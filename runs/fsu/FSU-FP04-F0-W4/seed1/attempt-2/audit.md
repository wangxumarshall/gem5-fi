# FSU-FP04-F0-W4 seed1 审计

- attempt：`attempt-2`
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
| `FSU-FP04-F0-W4-seed1.md` | `838b44b69a97770c2c6b3d10a577d4f8795d76e1449fae524d67c4bf32cf83ba` |
| `census.err` | `89736f20b2030718beca99e4246b7e20e1e59dfcdbda8d07067bff6783a4a5dc` |
| `census.out` | `457c78dcbd899dfa4eb314e9ae7c7e62df07c3b239e4339933dfc0205adae068` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `ddcd1cba6c9365b22d513818b4ae47c7e8dd3fd4f81dfdf2ecd909f763b6843c` |
| `census/config.json` | `fa91cf386d7f3fe87c75776bf01b1e7e3351e14ec1ca24960d56241cc8dc8d8f` |
| `census/fpu_injections.log` | `7bc8726ba761e237b918a253b4aa17afe92f63b6fb33bcdbe3233ab77f314a00` |
| `census/stats.txt` | `226020d07f76ee95c76cff93c7639aa72e1895bb866084d8d3073662ca5adbf3` |
| `chain_report.json` | `be543d6990cdf710d0f6de17f3aed344a2abfd4718149b9ec5a09dd2377b0009` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `1114410a0cb80b69b0d55f6659d7ea4a6e581a3b889f5bfcfc9801199980bada` |
| `inject/config.json` | `defcbacebea208cf6fc8340926d7a659a1ea3f548da8ee9c9eacb94cf7b5814c` |
| `inject/fpu_injections.log` | `0d5775df20677dcf9a9e9ae411d04d96ae5b842f928b419a08f582761a609dcd` |
| `inject/prop_evt.txt.gz` | `18fab2087555ee3260ce76dc9226aebaa9c5089b3a4e28791478514dc536c706` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `e0578a07d69abbc86917951a260c913bd1a30dad9ef2d11478f363c2a2dce8ca` |
| `manifest.json` | `64928159edf575aa63d00267d5941c3e4628c6c315caea36881362fde00e071b` |
| `oracle.json` | `7e3ec8cd111aeaa35bc40bd43218ae1855891bef8cea63c51652df500b849b86` |
| `run.err` | `89736f20b2030718beca99e4246b7e20e1e59dfcdbda8d07067bff6783a4a5dc` |
| `run.out` | `4e6de5b1b6d7f9dad6fa6c2ab0350c14ba85dbcd125768d69f56bcca5a1d07aa` |
| `stats.txt` | `e0578a07d69abbc86917951a260c913bd1a30dad9ef2d11478f363c2a2dce8ca` |

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
