# FSU-FP06-F5-W5 seed2446998533680144132 审计

- attempt：`attempt-1`
- sample_run_id：`s2446998533680144132`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 522 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '263', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `1` → `259`：✓
- `259` → `260`：✓
- `260` → `261`：✓
- `261` → `262`：✓
- `262` → `263`：✓
- `263` → `521`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W5-seed2446998533680144132.md` | `874f6dc4e334899aad856b2c0e194fff68f0bd70e2b2a09929f1d840957fed8d` |
| `census.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `census.out` | `7a55aea8b3bd6b834ffcf1c6fe9cc2ccaedf2a273080432cce8f8a5121ab862c` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `040d6040cabe156189043527728891e28e807e6cbc164f31e36e3267b6d96e87` |
| `census/config.json` | `01694fde119fcea1721818365bfbdfe1f731e7e4ad61c33b06ddd8f3cae08e82` |
| `census/fpu_injections.log` | `96dd284ce70e08ddfab5718292fa8c721c98a1f3df8076d8c4ee693d8aca1670` |
| `census/stats.txt` | `3d66b4643df449b2e8a4ec1f5156ea3f5884550950b46a77224adcdabd80c024` |
| `chain_report.json` | `3355e8ac452a58280ecdc51d7357e7b4197fa579a4a538be7f94578910d0b4a2` |
| `component_manifest.json` | `c24079b106c87ea6fc462e512aa047d652556a0b6e0874d7881adfb46650e61d` |
| `inject/array.bin` | `5d77aa7976437d28f660375fa9a12b1c6a69b5b46737debea23771d9108f4b58` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `c9d40b84419b31e50e4ef0995dec7ba1abb3a102b9a59fa437713853d0eabb41` |
| `inject/config.json` | `3159663c2c42c8106a172803965266f43cc11220eea108ca57ed7104e282074a` |
| `inject/fpu_injections.log.gz` | `3df21f949a9a141b5759c02e6e77dd4f712b84d93ed231aeb3d5ea0c81cfc329` |
| `inject/prop_evt.txt.gz` | `99a1df8e6f8a0363fecd80936edcc0bc75027fc07378bc7a0e10159567e0cee2` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `d5e429f7d55364894dd086c6ee9dbf5e2cb6fa38c8a1637671325688690d6f93` |
| `injection_log_storage.json` | `3e5be56f1df77dde62e68410d868635282b31b48c978824b35016fe7afbfbc97` |
| `manifest.json` | `3443d55f580e8a51f294d12abe8cb755405dec8c14f2ed46c7282d302e077064` |
| `oracle.json` | `a26e1332297f3368214ad789ac615cb95bf2f14b541ec57a618b8905518099d9` |
| `oracle_elements.json` | `e99ac316c0786546b6cd5b62ca25b0bf067c275bae288324e71a1e3edceb0617` |
| `run.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `run.out` | `20887b5eb214bd28176221e86ed3c853eb554752af56383ea3aaa3b88d0cb761` |
| `stats.txt` | `d5e429f7d55364894dd086c6ee9dbf5e2cb6fa38c8a1637671325688690d6f93` |

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
| MD event 259 存在于原始流 | PASS |
| MD event 259 kind 一致 | PASS |
| MD event 259 parent 一致 | PASS |
| MD event 260 存在于原始流 | PASS |
| MD event 260 kind 一致 | PASS |
| MD event 260 parent 一致 | PASS |
| MD event 261 存在于原始流 | PASS |
| MD event 261 kind 一致 | PASS |
| MD event 261 parent 一致 | PASS |
| MD event 262 存在于原始流 | PASS |
| MD event 262 kind 一致 | PASS |
| MD event 262 parent 一致 | PASS |
| MD event 263 存在于原始流 | PASS |
| MD event 263 kind 一致 | PASS |
| MD event 263 parent 一致 | PASS |
| MD event 521 存在于原始流 | PASS |
| MD event 521 kind 一致 | PASS |
| MD event 521 parent 一致 | PASS |
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
