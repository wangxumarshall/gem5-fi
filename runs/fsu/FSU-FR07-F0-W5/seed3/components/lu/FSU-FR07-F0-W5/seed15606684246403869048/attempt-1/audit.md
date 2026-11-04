# FSU-FR07-F0-W5 seed15606684246403869048 审计

- attempt：`attempt-1`
- sample_run_id：`s15606684246403869048`

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
| `FSU-FR07-F0-W5-seed15606684246403869048.md` | `c19a4f33d80214e159d3c3e7f3bca3e932bf35491a379c54bdc28326ac5cdae6` |
| `census.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `census.out` | `c4ccb56d248c8b86b7a67db218f9a3af219e5b9ad128c6db50e16319b5880c06` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `ccc09753786972ed36418fa0132d9167bf8d8a9eca61b6b5cd28019c58ef8df4` |
| `census/config.json` | `0dde31046761db285b3b927eddbdb7243eb53bdaefb4910637a1c442c0dc1bb0` |
| `census/fpu_injections.log` | `cd18798cacbd198a4aac41821d50f3f553124f905faf8da29028d785004480ca` |
| `census/stats.txt` | `aefc2a9654ca827f37ade54ca951709108b9af564ef2569dd8ecc4bb7200519e` |
| `chain_report.json` | `9984fb866602e45049e6850c262c1e9dcb62bdb76978bed7fbdde9878cc0c318` |
| `component_manifest.json` | `4eeb782e50f875b168e25dc36e3ab158d3425e4602385158ac841b789879a3e5` |
| `inject/array.bin` | `2e36b1ba0468b2560b7ec909380c4bf1f1b3e582c809d2b06038fccb5313cb8a` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `93db03fe819622c14c2d386875103a33f2caf7cfc57b611e9bde66d241a9f2f3` |
| `inject/config.json` | `a59f60c936a1f97721ec9280fc2a315f74fd52830d48aff2f2fd68ac2af4b45b` |
| `inject/fpu_injections.log` | `03e94c211f4f22ace6fa9ab66afdbe9ff35fa9ca5341f01eca5746b450d03c96` |
| `inject/prop_evt.txt.gz` | `77d68e3107012413ed69638aaeca836fbf0059543c901ef3c4e6f5eac0a78313` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `14012af0d9eb0ed1b02f2495f403002f0a17b97688aa7b27c028d0c7519a06fc` |
| `manifest.json` | `4d222c3e85ebdb80fa0b0322bdfdc99c09d6e3cee20ed5e0a23fb1b0403eef9c` |
| `oracle.json` | `95f8292683458613213093efc5f8fb1027049ddb9d0b58d1b3aa33a027bc65d9` |
| `oracle_elements.json` | `910503550e722015a028d00594af065159b2959dccac8699b47cc1ba5950144b` |
| `run.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `run.out` | `92d102c66fdb3556c827fc0924c7f8009719d51bab19041e584649eddccbbfbc` |
| `stats.txt` | `14012af0d9eb0ed1b02f2495f403002f0a17b97688aa7b27c028d0c7519a06fc` |

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
