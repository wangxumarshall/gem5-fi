# FSU-FP04-F2-W4 seed3 审计

- attempt：`attempt-1`
- sample_run_id：`s3`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 133 |
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
| fault 数 | 19 |
| 所有 fault admitted | True |
| 所有 fault certified | True |
| violations（主 fault） | [] |

## 逐 fault 审计

| fault | terminal | admitted | certified | direct parent | tick 单调 | layers | violations |
|---|---|---|---|---|---|---|---|
| 1 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 10 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 11 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 12 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 13 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 14 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 15 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 16 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 17 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 18 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 19 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 2 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 3 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 4 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 5 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 6 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 7 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 8 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 9 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |

## 边（主 fault）

- `0` → `1`：✓
- `1` → `2`：✓
- `2` → `3`：✓
- `3` → `4`：✓
- `4` → `5`：✓
- `5` → `114`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP04-F2-W4-seed3.md` | `94516741402b1796b0c7a283a81fcf96ee2a61b6aaa1e38401d6df2780ebba5a` |
| `census.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `census.out` | `0b81fa1b4782b87a4301fb7eface32d15be38f2b8d90facba9a841064b11ede6` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `1ba8c219d4db30d38dd12f8609e23c329f77a2438c06f8ced1c48bf5da6afc4c` |
| `census/config.json` | `d2737252d76d6f23f980068892ec7137f7838519c82b8ca4d4b422ecf95b3c7f` |
| `census/fpu_injections.log` | `d153ffcef9b24d6300f5e45cc845ff6f57d519c1226cad280a84cfcae023a2c2` |
| `census/stats.txt` | `1c52ec88700e60f517c5eebcb9bff26fa8b4ba3d46e5ccfb41f71f7d26c61b75` |
| `chain_report.json` | `c5c920b5583878dd881f13e11db8ec82d91342113bf4f21bc84736c5d96df0c2` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `b66859af226cc6c4ae380cdb38dbf01a45037b0de51495581538c6217013da06` |
| `inject/config.json` | `b7f7b969b022b397708df90123c5e00fccf765744f673f827fdea76f61be1532` |
| `inject/fpu_injections.log` | `b89f1cd605d635b92e9c2c7509e58579797a0725ce557468ce2902dd0ddd2a63` |
| `inject/prop_evt.txt.gz` | `ba06e2f5480dee1898c514bcc08fecaa92b657592460cb0fbebb094a22b4c685` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `ec5393f3a6bc6d67db857d8a975dbe44c79d3d3e4eb0f066f27e611d992ca870` |
| `manifest.json` | `d30f58db1afc0ebd563843569542ebd25c68428ae9a33273a4e3102ff84f2a93` |
| `oracle.json` | `25fe582adac336903a17d6e2c120dc3feb10f096a1bf3942b8ae2d73c6e7fc98` |
| `ordinals.json` | `097afed3c24e7d8d23913ed61faa968d3628fa76b6c4bedb41a3f774456629f3` |
| `run.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `run.out` | `d0107a905ad26489e4f73e526e2c16c19e7d8376cb873147a1e79048056b2718` |
| `stats.txt` | `ec5393f3a6bc6d67db857d8a975dbe44c79d3d3e4eb0f066f27e611d992ca870` |

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
| fault 10 terminal 一致 | PASS |
| fault 10 violations 一致 | PASS |
| fault 10 admitted 一致 | PASS |
| fault 10 certified 一致 | PASS |
| fault 11 terminal 一致 | PASS |
| fault 11 violations 一致 | PASS |
| fault 11 admitted 一致 | PASS |
| fault 11 certified 一致 | PASS |
| fault 12 terminal 一致 | PASS |
| fault 12 violations 一致 | PASS |
| fault 12 admitted 一致 | PASS |
| fault 12 certified 一致 | PASS |
| fault 13 terminal 一致 | PASS |
| fault 13 violations 一致 | PASS |
| fault 13 admitted 一致 | PASS |
| fault 13 certified 一致 | PASS |
| fault 14 terminal 一致 | PASS |
| fault 14 violations 一致 | PASS |
| fault 14 admitted 一致 | PASS |
| fault 14 certified 一致 | PASS |
| fault 15 terminal 一致 | PASS |
| fault 15 violations 一致 | PASS |
| fault 15 admitted 一致 | PASS |
| fault 15 certified 一致 | PASS |
| fault 16 terminal 一致 | PASS |
| fault 16 violations 一致 | PASS |
| fault 16 admitted 一致 | PASS |
| fault 16 certified 一致 | PASS |
| fault 17 terminal 一致 | PASS |
| fault 17 violations 一致 | PASS |
| fault 17 admitted 一致 | PASS |
| fault 17 certified 一致 | PASS |
| fault 18 terminal 一致 | PASS |
| fault 18 violations 一致 | PASS |
| fault 18 admitted 一致 | PASS |
| fault 18 certified 一致 | PASS |
| fault 19 terminal 一致 | PASS |
| fault 19 violations 一致 | PASS |
| fault 19 admitted 一致 | PASS |
| fault 19 certified 一致 | PASS |
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
| fault 5 terminal 一致 | PASS |
| fault 5 violations 一致 | PASS |
| fault 5 admitted 一致 | PASS |
| fault 5 certified 一致 | PASS |
| fault 6 terminal 一致 | PASS |
| fault 6 violations 一致 | PASS |
| fault 6 admitted 一致 | PASS |
| fault 6 certified 一致 | PASS |
| fault 7 terminal 一致 | PASS |
| fault 7 violations 一致 | PASS |
| fault 7 admitted 一致 | PASS |
| fault 7 certified 一致 | PASS |
| fault 8 terminal 一致 | PASS |
| fault 8 violations 一致 | PASS |
| fault 8 admitted 一致 | PASS |
| fault 8 certified 一致 | PASS |
| fault 9 terminal 一致 | PASS |
| fault 9 violations 一致 | PASS |
| fault 9 admitted 一致 | PASS |
| fault 9 certified 一致 | PASS |
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
| MD event 114 存在于原始流 | PASS |
| MD event 114 kind 一致 | PASS |
| MD event 114 parent 一致 | PASS |
| MD event 54 存在于原始流 | PASS |
| MD event 54 kind 一致 | PASS |
| MD event 54 parent 一致 | PASS |
| MD event 55 存在于原始流 | PASS |
| MD event 55 kind 一致 | PASS |
| MD event 55 parent 一致 | PASS |
| MD event 56 存在于原始流 | PASS |
| MD event 56 kind 一致 | PASS |
| MD event 56 parent 一致 | PASS |
| MD event 57 存在于原始流 | PASS |
| MD event 57 kind 一致 | PASS |
| MD event 57 parent 一致 | PASS |
| MD event 58 存在于原始流 | PASS |
| MD event 58 kind 一致 | PASS |
| MD event 58 parent 一致 | PASS |
| MD event 59 存在于原始流 | PASS |
| MD event 59 kind 一致 | PASS |
| MD event 59 parent 一致 | PASS |
| MD event 123 存在于原始流 | PASS |
| MD event 123 kind 一致 | PASS |
| MD event 123 parent 一致 | PASS |
| MD event 60 存在于原始流 | PASS |
| MD event 60 kind 一致 | PASS |
| MD event 60 parent 一致 | PASS |
| MD event 61 存在于原始流 | PASS |
| MD event 61 kind 一致 | PASS |
| MD event 61 parent 一致 | PASS |
| MD event 62 存在于原始流 | PASS |
| MD event 62 kind 一致 | PASS |
| MD event 62 parent 一致 | PASS |
| MD event 63 存在于原始流 | PASS |
| MD event 63 kind 一致 | PASS |
| MD event 63 parent 一致 | PASS |
| MD event 64 存在于原始流 | PASS |
| MD event 64 kind 一致 | PASS |
| MD event 64 parent 一致 | PASS |
| MD event 65 存在于原始流 | PASS |
| MD event 65 kind 一致 | PASS |
| MD event 65 parent 一致 | PASS |
| MD event 124 存在于原始流 | PASS |
| MD event 124 kind 一致 | PASS |
| MD event 124 parent 一致 | PASS |
| MD event 66 存在于原始流 | PASS |
| MD event 66 kind 一致 | PASS |
| MD event 66 parent 一致 | PASS |
| MD event 67 存在于原始流 | PASS |
| MD event 67 kind 一致 | PASS |
| MD event 67 parent 一致 | PASS |
| MD event 68 存在于原始流 | PASS |
| MD event 68 kind 一致 | PASS |
| MD event 68 parent 一致 | PASS |
| MD event 69 存在于原始流 | PASS |
| MD event 69 kind 一致 | PASS |
| MD event 69 parent 一致 | PASS |
| MD event 70 存在于原始流 | PASS |
| MD event 70 kind 一致 | PASS |
| MD event 70 parent 一致 | PASS |
| MD event 71 存在于原始流 | PASS |
| MD event 71 kind 一致 | PASS |
| MD event 71 parent 一致 | PASS |
| MD event 125 存在于原始流 | PASS |
| MD event 125 kind 一致 | PASS |
| MD event 125 parent 一致 | PASS |
| MD event 72 存在于原始流 | PASS |
| MD event 72 kind 一致 | PASS |
| MD event 72 parent 一致 | PASS |
| MD event 73 存在于原始流 | PASS |
| MD event 73 kind 一致 | PASS |
| MD event 73 parent 一致 | PASS |
| MD event 74 存在于原始流 | PASS |
| MD event 74 kind 一致 | PASS |
| MD event 74 parent 一致 | PASS |
| MD event 75 存在于原始流 | PASS |
| MD event 75 kind 一致 | PASS |
| MD event 75 parent 一致 | PASS |
| MD event 76 存在于原始流 | PASS |
| MD event 76 kind 一致 | PASS |
| MD event 76 parent 一致 | PASS |
| MD event 77 存在于原始流 | PASS |
| MD event 77 kind 一致 | PASS |
| MD event 77 parent 一致 | PASS |
| MD event 126 存在于原始流 | PASS |
| MD event 126 kind 一致 | PASS |
| MD event 126 parent 一致 | PASS |
| MD event 78 存在于原始流 | PASS |
| MD event 78 kind 一致 | PASS |
| MD event 78 parent 一致 | PASS |
| MD event 79 存在于原始流 | PASS |
| MD event 79 kind 一致 | PASS |
| MD event 79 parent 一致 | PASS |
| MD event 80 存在于原始流 | PASS |
| MD event 80 kind 一致 | PASS |
| MD event 80 parent 一致 | PASS |
| MD event 81 存在于原始流 | PASS |
| MD event 81 kind 一致 | PASS |
| MD event 81 parent 一致 | PASS |
| MD event 82 存在于原始流 | PASS |
| MD event 82 kind 一致 | PASS |
| MD event 82 parent 一致 | PASS |
| MD event 83 存在于原始流 | PASS |
| MD event 83 kind 一致 | PASS |
| MD event 83 parent 一致 | PASS |
| MD event 127 存在于原始流 | PASS |
| MD event 127 kind 一致 | PASS |
| MD event 127 parent 一致 | PASS |
| MD event 84 存在于原始流 | PASS |
| MD event 84 kind 一致 | PASS |
| MD event 84 parent 一致 | PASS |
| MD event 85 存在于原始流 | PASS |
| MD event 85 kind 一致 | PASS |
| MD event 85 parent 一致 | PASS |
| MD event 86 存在于原始流 | PASS |
| MD event 86 kind 一致 | PASS |
| MD event 86 parent 一致 | PASS |
| MD event 87 存在于原始流 | PASS |
| MD event 87 kind 一致 | PASS |
| MD event 87 parent 一致 | PASS |
| MD event 88 存在于原始流 | PASS |
| MD event 88 kind 一致 | PASS |
| MD event 88 parent 一致 | PASS |
| MD event 89 存在于原始流 | PASS |
| MD event 89 kind 一致 | PASS |
| MD event 89 parent 一致 | PASS |
| MD event 128 存在于原始流 | PASS |
| MD event 128 kind 一致 | PASS |
| MD event 128 parent 一致 | PASS |
| MD event 90 存在于原始流 | PASS |
| MD event 90 kind 一致 | PASS |
| MD event 90 parent 一致 | PASS |
| MD event 91 存在于原始流 | PASS |
| MD event 91 kind 一致 | PASS |
| MD event 91 parent 一致 | PASS |
| MD event 92 存在于原始流 | PASS |
| MD event 92 kind 一致 | PASS |
| MD event 92 parent 一致 | PASS |
| MD event 93 存在于原始流 | PASS |
| MD event 93 kind 一致 | PASS |
| MD event 93 parent 一致 | PASS |
| MD event 94 存在于原始流 | PASS |
| MD event 94 kind 一致 | PASS |
| MD event 94 parent 一致 | PASS |
| MD event 95 存在于原始流 | PASS |
| MD event 95 kind 一致 | PASS |
| MD event 95 parent 一致 | PASS |
| MD event 129 存在于原始流 | PASS |
| MD event 129 kind 一致 | PASS |
| MD event 129 parent 一致 | PASS |
| MD event 96 存在于原始流 | PASS |
| MD event 96 kind 一致 | PASS |
| MD event 96 parent 一致 | PASS |
| MD event 97 存在于原始流 | PASS |
| MD event 97 kind 一致 | PASS |
| MD event 97 parent 一致 | PASS |
| MD event 98 存在于原始流 | PASS |
| MD event 98 kind 一致 | PASS |
| MD event 98 parent 一致 | PASS |
| MD event 99 存在于原始流 | PASS |
| MD event 99 kind 一致 | PASS |
| MD event 99 parent 一致 | PASS |
| MD event 100 存在于原始流 | PASS |
| MD event 100 kind 一致 | PASS |
| MD event 100 parent 一致 | PASS |
| MD event 101 存在于原始流 | PASS |
| MD event 101 kind 一致 | PASS |
| MD event 101 parent 一致 | PASS |
| MD event 130 存在于原始流 | PASS |
| MD event 130 kind 一致 | PASS |
| MD event 130 parent 一致 | PASS |
| MD event 102 存在于原始流 | PASS |
| MD event 102 kind 一致 | PASS |
| MD event 102 parent 一致 | PASS |
| MD event 103 存在于原始流 | PASS |
| MD event 103 kind 一致 | PASS |
| MD event 103 parent 一致 | PASS |
| MD event 104 存在于原始流 | PASS |
| MD event 104 kind 一致 | PASS |
| MD event 104 parent 一致 | PASS |
| MD event 105 存在于原始流 | PASS |
| MD event 105 kind 一致 | PASS |
| MD event 105 parent 一致 | PASS |
| MD event 106 存在于原始流 | PASS |
| MD event 106 kind 一致 | PASS |
| MD event 106 parent 一致 | PASS |
| MD event 107 存在于原始流 | PASS |
| MD event 107 kind 一致 | PASS |
| MD event 107 parent 一致 | PASS |
| MD event 131 存在于原始流 | PASS |
| MD event 131 kind 一致 | PASS |
| MD event 131 parent 一致 | PASS |
| MD event 108 存在于原始流 | PASS |
| MD event 108 kind 一致 | PASS |
| MD event 108 parent 一致 | PASS |
| MD event 109 存在于原始流 | PASS |
| MD event 109 kind 一致 | PASS |
| MD event 109 parent 一致 | PASS |
| MD event 110 存在于原始流 | PASS |
| MD event 110 kind 一致 | PASS |
| MD event 110 parent 一致 | PASS |
| MD event 111 存在于原始流 | PASS |
| MD event 111 kind 一致 | PASS |
| MD event 111 parent 一致 | PASS |
| MD event 112 存在于原始流 | PASS |
| MD event 112 kind 一致 | PASS |
| MD event 112 parent 一致 | PASS |
| MD event 113 存在于原始流 | PASS |
| MD event 113 kind 一致 | PASS |
| MD event 113 parent 一致 | PASS |
| MD event 132 存在于原始流 | PASS |
| MD event 132 kind 一致 | PASS |
| MD event 132 parent 一致 | PASS |
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
| MD event 115 存在于原始流 | PASS |
| MD event 115 kind 一致 | PASS |
| MD event 115 parent 一致 | PASS |
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
| MD event 116 存在于原始流 | PASS |
| MD event 116 kind 一致 | PASS |
| MD event 116 parent 一致 | PASS |
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
| MD event 117 存在于原始流 | PASS |
| MD event 117 kind 一致 | PASS |
| MD event 117 parent 一致 | PASS |
| MD event 24 存在于原始流 | PASS |
| MD event 24 kind 一致 | PASS |
| MD event 24 parent 一致 | PASS |
| MD event 25 存在于原始流 | PASS |
| MD event 25 kind 一致 | PASS |
| MD event 25 parent 一致 | PASS |
| MD event 26 存在于原始流 | PASS |
| MD event 26 kind 一致 | PASS |
| MD event 26 parent 一致 | PASS |
| MD event 27 存在于原始流 | PASS |
| MD event 27 kind 一致 | PASS |
| MD event 27 parent 一致 | PASS |
| MD event 28 存在于原始流 | PASS |
| MD event 28 kind 一致 | PASS |
| MD event 28 parent 一致 | PASS |
| MD event 29 存在于原始流 | PASS |
| MD event 29 kind 一致 | PASS |
| MD event 29 parent 一致 | PASS |
| MD event 118 存在于原始流 | PASS |
| MD event 118 kind 一致 | PASS |
| MD event 118 parent 一致 | PASS |
| MD event 30 存在于原始流 | PASS |
| MD event 30 kind 一致 | PASS |
| MD event 30 parent 一致 | PASS |
| MD event 31 存在于原始流 | PASS |
| MD event 31 kind 一致 | PASS |
| MD event 31 parent 一致 | PASS |
| MD event 32 存在于原始流 | PASS |
| MD event 32 kind 一致 | PASS |
| MD event 32 parent 一致 | PASS |
| MD event 33 存在于原始流 | PASS |
| MD event 33 kind 一致 | PASS |
| MD event 33 parent 一致 | PASS |
| MD event 34 存在于原始流 | PASS |
| MD event 34 kind 一致 | PASS |
| MD event 34 parent 一致 | PASS |
| MD event 35 存在于原始流 | PASS |
| MD event 35 kind 一致 | PASS |
| MD event 35 parent 一致 | PASS |
| MD event 119 存在于原始流 | PASS |
| MD event 119 kind 一致 | PASS |
| MD event 119 parent 一致 | PASS |
| MD event 36 存在于原始流 | PASS |
| MD event 36 kind 一致 | PASS |
| MD event 36 parent 一致 | PASS |
| MD event 37 存在于原始流 | PASS |
| MD event 37 kind 一致 | PASS |
| MD event 37 parent 一致 | PASS |
| MD event 38 存在于原始流 | PASS |
| MD event 38 kind 一致 | PASS |
| MD event 38 parent 一致 | PASS |
| MD event 39 存在于原始流 | PASS |
| MD event 39 kind 一致 | PASS |
| MD event 39 parent 一致 | PASS |
| MD event 40 存在于原始流 | PASS |
| MD event 40 kind 一致 | PASS |
| MD event 40 parent 一致 | PASS |
| MD event 41 存在于原始流 | PASS |
| MD event 41 kind 一致 | PASS |
| MD event 41 parent 一致 | PASS |
| MD event 120 存在于原始流 | PASS |
| MD event 120 kind 一致 | PASS |
| MD event 120 parent 一致 | PASS |
| MD event 42 存在于原始流 | PASS |
| MD event 42 kind 一致 | PASS |
| MD event 42 parent 一致 | PASS |
| MD event 43 存在于原始流 | PASS |
| MD event 43 kind 一致 | PASS |
| MD event 43 parent 一致 | PASS |
| MD event 44 存在于原始流 | PASS |
| MD event 44 kind 一致 | PASS |
| MD event 44 parent 一致 | PASS |
| MD event 45 存在于原始流 | PASS |
| MD event 45 kind 一致 | PASS |
| MD event 45 parent 一致 | PASS |
| MD event 46 存在于原始流 | PASS |
| MD event 46 kind 一致 | PASS |
| MD event 46 parent 一致 | PASS |
| MD event 47 存在于原始流 | PASS |
| MD event 47 kind 一致 | PASS |
| MD event 47 parent 一致 | PASS |
| MD event 121 存在于原始流 | PASS |
| MD event 121 kind 一致 | PASS |
| MD event 121 parent 一致 | PASS |
| MD event 48 存在于原始流 | PASS |
| MD event 48 kind 一致 | PASS |
| MD event 48 parent 一致 | PASS |
| MD event 49 存在于原始流 | PASS |
| MD event 49 kind 一致 | PASS |
| MD event 49 parent 一致 | PASS |
| MD event 50 存在于原始流 | PASS |
| MD event 50 kind 一致 | PASS |
| MD event 50 parent 一致 | PASS |
| MD event 51 存在于原始流 | PASS |
| MD event 51 kind 一致 | PASS |
| MD event 51 parent 一致 | PASS |
| MD event 52 存在于原始流 | PASS |
| MD event 52 kind 一致 | PASS |
| MD event 52 parent 一致 | PASS |
| MD event 53 存在于原始流 | PASS |
| MD event 53 kind 一致 | PASS |
| MD event 53 parent 一致 | PASS |
| MD event 122 存在于原始流 | PASS |
| MD event 122 kind 一致 | PASS |
| MD event 122 parent 一致 | PASS |
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
| fault 10 MD 覆盖主链全部事件 | PASS |
| fault 10 MD/原始流 direct parent | PASS |
| fault 10 MD 逐 fault 终局行存在 | PASS |
| fault 10 MD terminal 一致 | PASS |
| fault 10 MD admitted 一致 | PASS |
| fault 10 MD certified 一致 | PASS |
| fault 11 MD 覆盖主链全部事件 | PASS |
| fault 11 MD/原始流 direct parent | PASS |
| fault 11 MD 逐 fault 终局行存在 | PASS |
| fault 11 MD terminal 一致 | PASS |
| fault 11 MD admitted 一致 | PASS |
| fault 11 MD certified 一致 | PASS |
| fault 12 MD 覆盖主链全部事件 | PASS |
| fault 12 MD/原始流 direct parent | PASS |
| fault 12 MD 逐 fault 终局行存在 | PASS |
| fault 12 MD terminal 一致 | PASS |
| fault 12 MD admitted 一致 | PASS |
| fault 12 MD certified 一致 | PASS |
| fault 13 MD 覆盖主链全部事件 | PASS |
| fault 13 MD/原始流 direct parent | PASS |
| fault 13 MD 逐 fault 终局行存在 | PASS |
| fault 13 MD terminal 一致 | PASS |
| fault 13 MD admitted 一致 | PASS |
| fault 13 MD certified 一致 | PASS |
| fault 14 MD 覆盖主链全部事件 | PASS |
| fault 14 MD/原始流 direct parent | PASS |
| fault 14 MD 逐 fault 终局行存在 | PASS |
| fault 14 MD terminal 一致 | PASS |
| fault 14 MD admitted 一致 | PASS |
| fault 14 MD certified 一致 | PASS |
| fault 15 MD 覆盖主链全部事件 | PASS |
| fault 15 MD/原始流 direct parent | PASS |
| fault 15 MD 逐 fault 终局行存在 | PASS |
| fault 15 MD terminal 一致 | PASS |
| fault 15 MD admitted 一致 | PASS |
| fault 15 MD certified 一致 | PASS |
| fault 16 MD 覆盖主链全部事件 | PASS |
| fault 16 MD/原始流 direct parent | PASS |
| fault 16 MD 逐 fault 终局行存在 | PASS |
| fault 16 MD terminal 一致 | PASS |
| fault 16 MD admitted 一致 | PASS |
| fault 16 MD certified 一致 | PASS |
| fault 17 MD 覆盖主链全部事件 | PASS |
| fault 17 MD/原始流 direct parent | PASS |
| fault 17 MD 逐 fault 终局行存在 | PASS |
| fault 17 MD terminal 一致 | PASS |
| fault 17 MD admitted 一致 | PASS |
| fault 17 MD certified 一致 | PASS |
| fault 18 MD 覆盖主链全部事件 | PASS |
| fault 18 MD/原始流 direct parent | PASS |
| fault 18 MD 逐 fault 终局行存在 | PASS |
| fault 18 MD terminal 一致 | PASS |
| fault 18 MD admitted 一致 | PASS |
| fault 18 MD certified 一致 | PASS |
| fault 19 MD 覆盖主链全部事件 | PASS |
| fault 19 MD/原始流 direct parent | PASS |
| fault 19 MD 逐 fault 终局行存在 | PASS |
| fault 19 MD terminal 一致 | PASS |
| fault 19 MD admitted 一致 | PASS |
| fault 19 MD certified 一致 | PASS |
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
| fault 5 MD 覆盖主链全部事件 | PASS |
| fault 5 MD/原始流 direct parent | PASS |
| fault 5 MD 逐 fault 终局行存在 | PASS |
| fault 5 MD terminal 一致 | PASS |
| fault 5 MD admitted 一致 | PASS |
| fault 5 MD certified 一致 | PASS |
| fault 6 MD 覆盖主链全部事件 | PASS |
| fault 6 MD/原始流 direct parent | PASS |
| fault 6 MD 逐 fault 终局行存在 | PASS |
| fault 6 MD terminal 一致 | PASS |
| fault 6 MD admitted 一致 | PASS |
| fault 6 MD certified 一致 | PASS |
| fault 7 MD 覆盖主链全部事件 | PASS |
| fault 7 MD/原始流 direct parent | PASS |
| fault 7 MD 逐 fault 终局行存在 | PASS |
| fault 7 MD terminal 一致 | PASS |
| fault 7 MD admitted 一致 | PASS |
| fault 7 MD certified 一致 | PASS |
| fault 8 MD 覆盖主链全部事件 | PASS |
| fault 8 MD/原始流 direct parent | PASS |
| fault 8 MD 逐 fault 终局行存在 | PASS |
| fault 8 MD terminal 一致 | PASS |
| fault 8 MD admitted 一致 | PASS |
| fault 8 MD certified 一致 | PASS |
| fault 9 MD 覆盖主链全部事件 | PASS |
| fault 9 MD/原始流 direct parent | PASS |
| fault 9 MD 逐 fault 终局行存在 | PASS |
| fault 9 MD terminal 一致 | PASS |
| fault 9 MD admitted 一致 | PASS |
| fault 9 MD certified 一致 | PASS |
| MD terminal 与 chain_report 一致 | PASS |
| MD admitted/certified 与 chain_report 一致 | PASS |
| evidence_sha256.json 存在 | PASS |
| 证据 SHA-256 全部匹配（失配 0） | PASS |
| stats.txt 非空 | PASS |
| admitted=True | PASS |
| violations=[] | PASS |

**结论：PASS**
