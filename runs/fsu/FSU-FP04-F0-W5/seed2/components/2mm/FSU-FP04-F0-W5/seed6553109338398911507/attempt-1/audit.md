# FSU-FP04-F0-W5 seed6553109338398911507 审计

- attempt：`attempt-1`
- sample_run_id：`s6553109338398911507`

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
| `FSU-FP04-F0-W5-seed6553109338398911507.md` | `3401eb2e390796dfed50e3e46790f66628165711a048f1e23724c114c8010f0a` |
| `census.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `census.out` | `7a55aea8b3bd6b834ffcf1c6fe9cc2ccaedf2a273080432cce8f8a5121ab862c` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `e5f6166949b29d52663481fd5f0f62e6220dda7b0fcaf9beed822a9e4bca7e68` |
| `census/config.json` | `7f8a1e74b929375dfd65747a3d0721eea725069198ddba19bd2c77cc0ad87f8f` |
| `census/fpu_injections.log` | `d746b3ec116cf49efdb3e04d2366b7df009b532a601be892e2970b0a73e7013d` |
| `census/stats.txt` | `c6406b98aa8eb2f6818ce96f8233e5ffe856ac27eee844c71171c18b5acc9823` |
| `chain_report.json` | `de3be3a2f78e1dfbc4d43002135f36c517b63426d3299d8cf02f7c61f096a789` |
| `component_manifest.json` | `6fa4be94c344cbff4d99f5afbfae42372863424bbbfe189f747ee122c30e8c81` |
| `inject/array.bin` | `06d33a5bda1efdf38e5dd2891f51cd6ba077d8f4b652f98cd161a92e86b1fce0` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `a445ba910f36265ea1926685a6ea68d4ecda9a2266767b527d99094bce42ec18` |
| `inject/config.json` | `69207e71fc51708f3953fd16b617996a232876e2a91c820e9aa9436c6ca83eb3` |
| `inject/fpu_injections.log` | `b000522ba331251d38fced43f6db6b088e82ed763667c0e79107de73ab432ff8` |
| `inject/prop_evt.txt.gz` | `0ecbf6fc5f108a3dcd512acd675de1c9f98bdde035213f86cba921a551b8086c` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `575b4fd4cf12d4f4ecaff0062cc5d0d60913fee63bce953bcfbec05ccbd3b845` |
| `manifest.json` | `102f86f3474172de7b4a522e7bbd9bef670b0b6bcaddd186a8ec149ca7d4a3db` |
| `oracle.json` | `617eb29bf96a31f83b2d16cfb1bba8b5001b9ad0997a2d21afe153088023586f` |
| `oracle_elements.json` | `81a8d999f428c2ea06432ffcae7681dcd810bbb9874eb218a03808adc74d0539` |
| `run.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `run.out` | `d8df7e6728b782e30b8fc9b44fa3638765b4b133301ffc40076ef0ef34555325` |
| `stats.txt` | `575b4fd4cf12d4f4ecaff0062cc5d0d60913fee63bce953bcfbec05ccbd3b845` |

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
