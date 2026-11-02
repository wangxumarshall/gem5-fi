# FSU-FP04-F0-W4 seed3 审计

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
| `FSU-FP04-F0-W4-seed3.md` | `b5d2314e4d861ecd41351303e7547e2fd0d27e478b4436b1b243bad1873ad11d` |
| `census.err` | `89736f20b2030718beca99e4246b7e20e1e59dfcdbda8d07067bff6783a4a5dc` |
| `census.out` | `457c78dcbd899dfa4eb314e9ae7c7e62df07c3b239e4339933dfc0205adae068` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `3d9ea9a5d9e4fa4ea4e39d58ed8b41fb1539c27fad918e34cc9c296ce0851da6` |
| `census/config.json` | `c6751326f2052da1b7cdd153453e4ca42df0e6e65f2a4fe0cccd1e057e5fc3e8` |
| `census/fpu_injections.log` | `7bc8726ba761e237b918a253b4aa17afe92f63b6fb33bcdbe3233ab77f314a00` |
| `census/stats.txt` | `05a1a175047e2730a27b17185cf539d9d6455392edd8b01190ac6c3ba87b5e38` |
| `chain_report.json` | `01d0e8e7cac30a45bcf7e4bc11f5c06c13ecba4a24a18537709abd2cba34c82a` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `41c57e782808cdec011bf0bb7bb91669de1e751ad6772c00954bbe595f37e485` |
| `inject/config.json` | `4ab2c2ded14aad8a2d5d70d9a83a68f83892eb934ab29696239e67e5afd4121c` |
| `inject/fpu_injections.log` | `1e88c805d04c9bb3c7f28b604a122bbf2350b126cfa09e0a363414b808f36b9f` |
| `inject/prop_evt.txt.gz` | `627228f14370648e6fc60c213d1cb839c6f7fe832769b7dddef7d9cf76092d6a` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `4df9de831c5224e17c7916cd503164a621516aaf2b6196699a94ac71e53b7e48` |
| `manifest.json` | `8edac5c4f6aa11f015864f59bd0da58d0c825d3b792c5e63ec7c48dc717075cf` |
| `oracle.json` | `4d3f5a7674aee9fd7c2d0d9dfa312c8b983890daccc3352ed89ca5c9fdfac9bd` |
| `run.err` | `89736f20b2030718beca99e4246b7e20e1e59dfcdbda8d07067bff6783a4a5dc` |
| `run.out` | `d35d8d46b8b0c814bd17dc84c0856e831ba65d4254f02e7214c1839b347d9eb3` |
| `stats.txt` | `4df9de831c5224e17c7916cd503164a621516aaf2b6196699a94ac71e53b7e48` |

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
