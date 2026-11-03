# FSU-FP06-F5-W5 seed11619651366395148639 审计

- attempt：`attempt-1`
- sample_run_id：`s11619651366395148639`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 521 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '12', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `9`：✓
- `9` → `10`：✓
- `10` → `11`：✓
- `11` → `12`：✓
- `12` → `520`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W5-seed11619651366395148639.md` | `87b992bf37259ba2310b458cff04010c503a4f4e32a1928af3692fe9932a31ed` |
| `census.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `census.out` | `7a55aea8b3bd6b834ffcf1c6fe9cc2ccaedf2a273080432cce8f8a5121ab862c` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `59173406ee069481d3f729d5c1ce15416507b5545714f0edff884881cd4fc17a` |
| `census/config.json` | `16f67b8b9a96bbf5d5be115e05a9042237d631bea030a0b524a534ca066d4afb` |
| `census/fpu_injections.log` | `96dd284ce70e08ddfab5718292fa8c721c98a1f3df8076d8c4ee693d8aca1670` |
| `census/stats.txt` | `1a77d66cabec00d128ae5aa0d03f41b8907542846126367edc73e9bda2e9555d` |
| `chain_report.json` | `1dbe88e0de9c7091ddbe342fcf86cc579e9e92caaad078857d6df10ce6c14d9f` |
| `component_manifest.json` | `30f5f8a524ffa0860b5394bebd21af2992a8980e37efa0671c4534b8f3d66842` |
| `inject/array.bin` | `b355a68e243751ac1e37341a9c0c1b3b9ac03c53624b81445f3d0c48f1f02648` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `71b866a2f2198604c51f29b380d38a26b1aae243712748fa8927ddc9674665d7` |
| `inject/config.json` | `d80408775c19307b397c35a867b0d092d12ff2118c66d3c2adeb7b68357c51d8` |
| `inject/fpu_injections.log.gz` | `f1f9dde15909f9592be9e63ab4e0e983a40c58423d1672096367d25a465e72bc` |
| `inject/prop_evt.txt.gz` | `64a3f5c0e9b8c90fb8a8a1a5d946200189381d7bce24a69942ad8866c287600a` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `1ae8c923a831aa9e330b3801f82a70316c2ef16be39a42d96b2cd45dd1be850f` |
| `injection_log_storage.json` | `f3f7f7b7d3352f5313d83192932b314d01160a5cf5c6c878faca7091764cfa11` |
| `manifest.json` | `03bbac3e76eeee7d315b0466ae0813b4b4a61f92c0c1f9a59d705bb7cbac36da` |
| `oracle.json` | `483283d9ac4f173287039affbc0e232f65238d2053c97718eb8a7ff7df0a8a72` |
| `oracle_elements.json` | `1368bce5467578511981ceb368ae7ba409cf4f3f48bc73b9070b6d9c9a5810d7` |
| `run.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `run.out` | `6d607a6dfdb0d1c5361a4b1033487ca3d167fdcfb7edf1cbd2450d7bd2d461a1` |
| `stats.txt` | `1ae8c923a831aa9e330b3801f82a70316c2ef16be39a42d96b2cd45dd1be850f` |

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
| fault 1 永久故障至少一次 activated exposure | PASS |
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
| fault 1 sampled_unique = 唯一 exposure_id 数 | PASS |
| fault 1 F5 计数/去重/守恒校验 | PASS |
| MD event 0 存在于原始流 | PASS |
| MD event 0 kind 一致 | PASS |
| MD event 0 parent 一致 | PASS |
| MD event 1 存在于原始流 | PASS |
| MD event 1 kind 一致 | PASS |
| MD event 1 parent 一致 | PASS |
| MD event 2 存在于原始流 | PASS |
| MD event 2 kind 一致 | PASS |
| MD event 2 parent 一致 | PASS |
| MD event 9 存在于原始流 | PASS |
| MD event 9 kind 一致 | PASS |
| MD event 9 parent 一致 | PASS |
| MD event 10 存在于原始流 | PASS |
| MD event 10 kind 一致 | PASS |
| MD event 10 parent 一致 | PASS |
| MD event 11 存在于原始流 | PASS |
| MD event 11 kind 一致 | PASS |
| MD event 11 parent 一致 | PASS |
| MD event 12 存在于原始流 | PASS |
| MD event 12 kind 一致 | PASS |
| MD event 12 parent 一致 | PASS |
| MD event 520 存在于原始流 | PASS |
| MD event 520 kind 一致 | PASS |
| MD event 520 parent 一致 | PASS |
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
