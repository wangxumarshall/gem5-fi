# FSU-FP04-F0-W5 seed7449357199526526885 审计

- attempt：`attempt-1`
- sample_run_id：`s7449357199526526885`

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
| `FSU-FP04-F0-W5-seed7449357199526526885.md` | `fa8deebd2f2632b2b92f806f5c82f63bfbb133625e59ae3d1e7b9a0884e01cdc` |
| `census.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `census.out` | `7a55aea8b3bd6b834ffcf1c6fe9cc2ccaedf2a273080432cce8f8a5121ab862c` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `0ede7d9bf7390c4f508ee72ac93c0ba96bf1fac1856172439dfcfc79b80a43ac` |
| `census/config.json` | `127a9f45f7396bddb6884d1ad2957baecb6948b69fe9f69adf71af3740a28246` |
| `census/fpu_injections.log` | `d746b3ec116cf49efdb3e04d2366b7df009b532a601be892e2970b0a73e7013d` |
| `census/stats.txt` | `a5b914b0364c9a9ae32a3655d63646d73f72b54a7e2fc7abbebd0e9604bd12df` |
| `chain_report.json` | `9c21b8943ff958ec3aa5906c313e3bd86da2610920bb888bf38f606d18e133f0` |
| `component_manifest.json` | `0dede2681411c6cce92822133153a524c3945b23117671e336a4be8ca6496634` |
| `inject/array.bin` | `5884271c5494f2d566f57f341d7be12543efa05eebc7d3ebaeb2999fa915c877` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `fd9479e47c57900579563526d3cb1107a1e1f603b7fa6ee553df89d4000d2268` |
| `inject/config.json` | `825d3f3ad08e4b67419d6902dbb6a0321c4ac8f2f29393cd9d853b485b2e9c75` |
| `inject/fpu_injections.log` | `4dd4ca1271f93a21bf3de4a6cc6f736c4397f04f6b5d2fd8af3ecbf6e22fa610` |
| `inject/prop_evt.txt.gz` | `3cda756ba44c1bbfb155904b76ed12a4450152902e6d4efc570ff7510fb0080e` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `2f2a6446204ac541b70de917bc056c8e56f4878cc8c5834de22c0090fc02d625` |
| `manifest.json` | `72ecadc2a732543561e75bb639c41abf083e7e7f11b1dcf83ee4a5a59d1fac05` |
| `oracle.json` | `3f9047da9d621491555e8358a57fe563e3bc29ed2ae2a8d49550b14ec6a79dc7` |
| `oracle_elements.json` | `990fc1eabf9ef67660c71330013853bd3b92d3d4121a4dc344db1126f4989b1a` |
| `run.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `run.out` | `f9868d34e4bcab96d0292314150b02c14b301e1b215ca1df452fae3655b35cc4` |
| `stats.txt` | `2f2a6446204ac541b70de917bc056c8e56f4878cc8c5834de22c0090fc02d625` |

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
