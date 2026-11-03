# FSU-FP04-F0-W5 seed933615570083433162 审计

- attempt：`attempt-2`
- sample_run_id：`s933615570083433162`

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
| `FSU-FP04-F0-W5-seed933615570083433162.md` | `df4de93ef215bc052796ba40e3c0aad309dae2d2304ff83f233b316ba2fae850` |
| `census.err` | `412bdbb81cc5c76efc9bbb5f0948c687f5dfa2c45db12966c536f4bfcddd2797` |
| `census.out` | `a83bf9a08c7f01c1600686f92a34d8f8fa586e8f29b2ef0e41175066b7a8496a` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `48a0902007d7bd11a0a7af3e02b1be3b79c1ec6a29dc99be18e45d3c44b93f0c` |
| `census/config.json` | `63dcc036c5298e8c28aadcda18c31938c38033eefe6c2bd95f291e78b303c517` |
| `census/fpu_injections.log` | `a05a9807a610db15416c1398f34e24fecba5944ff6c9c3a1bfc37cfedf1db11a` |
| `census/stats.txt` | `e640140f8d565b65f6bfcbd44def8ccd0bc6bf0bd7ee1c2bf31ab36713ffd8fd` |
| `chain_report.json` | `3b6e0714429206f55792e46f1cfdd7dd35a6ed0f5be4f2780a62c55e1e878294` |
| `component_manifest.json` | `8d626f4bd043d748880140520c8feb280ff811a35b34856634ab7039514d426d` |
| `inject/array.bin` | `4ccbcfd50274c6dc288d0eef424ff3ee71ba9cbdc26c0aea49cb36c59f683b24` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `c34223eecda30cab16838832ff0bf189187d036c1335841cfdb4cab365f3a7dd` |
| `inject/config.json` | `cf2306384b2c5344aa12e72ca54f9d466826c46e2b69f825871aae61fd83f7c6` |
| `inject/fpu_injections.log` | `1a6ae1216021a531aed3814e6eab40273415f737d2b5e884fba62baea45143f8` |
| `inject/prop_evt.txt.gz` | `b07d13c323a395ecce1a2e5db525139c99e575c2a6877d4df94097d41c225211` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `59c0ee38a690e354999102f4c4bdc6622ee597f0d47470c3e84ca014400e21c5` |
| `manifest.json` | `d40c318d7fc98aa20c7457ce510f4f78b8d81e49a0095611949fdb28e8bd180e` |
| `oracle.json` | `ac8d63e497e26741863418d85194c19cad553bc3921993666444f28c4489eeda` |
| `oracle_elements.json` | `3df1a05ce2f36787d706a8c3b0135f5c794afc6ee93cad828ada1952e994313e` |
| `run.err` | `412bdbb81cc5c76efc9bbb5f0948c687f5dfa2c45db12966c536f4bfcddd2797` |
| `run.out` | `af0a97319bef055703116dd2438df38cd8454d5706d1e59adb46454098c74ef1` |
| `stats.txt` | `59c0ee38a690e354999102f4c4bdc6622ee597f0d47470c3e84ca014400e21c5` |

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
