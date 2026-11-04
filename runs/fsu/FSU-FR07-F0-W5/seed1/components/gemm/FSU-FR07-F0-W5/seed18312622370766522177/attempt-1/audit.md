# FSU-FR07-F0-W5 seed18312622370766522177 审计

- attempt：`attempt-1`
- sample_run_id：`s18312622370766522177`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 8 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '6', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `1` → `3`：✓
- `3` → `4`：✓
- `4` → `5`：✓
- `5` → `6`：✓
- `6` → `7`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR07-F0-W5-seed18312622370766522177.md` | `299b85e88a4cd0af0f423034d7844ff46ac2675a3442200691a819e00078ebb0` |
| `census.err` | `aab1510bc39780187ded556b781e6fb104354304676b3bc41045a0db1c656efe` |
| `census.out` | `19431cf806c5c901ed6056643fbc9dddca012675a839815127c66c77ac912ca1` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `52e32782da1677b03e9c78e3abeba7a9f01413d753ff950b490b4622ce608cb3` |
| `census/config.json` | `fbb0e36af7d586690f2333368cc680a8bc11882dbf0ee4065cc035bc2d6f439c` |
| `census/fpu_injections.log` | `5739b49e01569c1bc9e80804280bf4c262d35794bd040e86ec638eda6337f532` |
| `census/stats.txt` | `2529174ea760f55df073f068025c6337de0fa4141a58d7d124f0ab55ae8596e0` |
| `chain_report.json` | `80f90e4e6aee00163de119aaeb6e63a6a8884785f1836ca87f331372214dff00` |
| `component_manifest.json` | `a580db1524e1d4706d839f210954635c0b875a3a72ec6c0a8fc76e13c1f56223` |
| `inject/array.bin` | `651f828ce580056b3037473843576871e4cb31bcfb25ec7dbd18cdfc926ef499` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `d46cf25b21df5c2f9b0d2b2d49f7cbc260a030b73fab282aec2f56d735824f68` |
| `inject/config.json` | `ed1586498975d6831e9e3a147c43e4ecb78d49219992e8a6cc6df734f6b85b5d` |
| `inject/fpu_injections.log` | `2c43595cf7c6f56a3dc9d05e03035b43fb598d8b3669e44a9fade1f243d7ecac` |
| `inject/prop_evt.txt.gz` | `14fdd3e1ad62cad7a50f93b7f9150015760265f5f1542ee8c7535184b446748c` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `9ed82f26d4b1412c62d9ec570b2c81584e6b15e1305df5fd642d2be266dd0cc8` |
| `manifest.json` | `a91c6972154f7e3a37923cc9abd48aba5023a7afded193d95a15dce34da10915` |
| `oracle.json` | `674430ed5411e8c4e09c72dbf0c75312ada178f29b8e73b946c3b92586ee1177` |
| `oracle_elements.json` | `0880f4c147b7d2d22732478b02d72b1cc1c54e32946858cfc44b9ef72492648d` |
| `run.err` | `aab1510bc39780187ded556b781e6fb104354304676b3bc41045a0db1c656efe` |
| `run.out` | `524649b3ac29aba5b50fdb09de93be6bb7c9bbbbdcc0061e25b905289ddd38d3` |
| `stats.txt` | `9ed82f26d4b1412c62d9ec570b2c81584e6b15e1305df5fd642d2be266dd0cc8` |

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
| fault 1 F5 计数/去重/守恒校验 | PASS |
| MD event 0 存在于原始流 | PASS |
| MD event 0 kind 一致 | PASS |
| MD event 0 parent 一致 | PASS |
| MD event 1 存在于原始流 | PASS |
| MD event 1 kind 一致 | PASS |
| MD event 1 parent 一致 | PASS |
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
| MD event 7 存在于原始流 | PASS |
| MD event 7 kind 一致 | PASS |
| MD event 7 parent 一致 | PASS |
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
