# FSU-FR07-F0-W5 seed8347509638432206262 审计

- attempt：`attempt-1`
- sample_run_id：`s8347509638432206262`

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
| `FSU-FR07-F0-W5-seed8347509638432206262.md` | `53cb2354d291fda496cf758def3df0147230d39d075eacec585e5e6f6991eeb4` |
| `census.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `census.out` | `ebd792f6461d512abb42df564d9864a21c462de74f95e4b3be8c792d316f3851` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `b73dc1fd0b08e46fc541e1c3711607ba95d264066753a327ac7308e38dc16ee1` |
| `census/config.json` | `9476bdfdb578a7d7088503b4e382491f19e6a1da9847c3f4f12af68bc79d1030` |
| `census/fpu_injections.log` | `c9116a76ae73b161bb541b8dc59355881f9ff80d9c5d6f512e36e94acba2210b` |
| `census/stats.txt` | `802b05cff6ad723f46fd540ca2026964c38feb3924277a68d6f68ee5b949a249` |
| `chain_report.json` | `5d8e7bdbd795f5c3c09076c8f3ffe5262934a5f4db4c2b2b32abb870b3d7ba38` |
| `component_manifest.json` | `efbc0c0909d4a530bebbb58b23e27679329485d5b764d3f5dc8adb6359f4ecae` |
| `inject/array.bin` | `b083110d93b37a5378a8fd761d79ca6fd35d6d2c85c3d6040db9fff611b7461c` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `d6f40ee3c3c0f24e182058a6182f34223173007fc7d5ff477cf9c4f99d1923a0` |
| `inject/config.json` | `a20bd13961ec55296e11f4474271ab658adc832e6459a76c96e50e48c040171f` |
| `inject/fpu_injections.log` | `4cee201fdab319ae0714a1a745c6da181ab71d157630f1edcb76cf59e08e56f9` |
| `inject/prop_evt.txt.gz` | `1cde0805a3013c69843f7607bd0febe8ae32933669ab4d02c5b32fd3f35c73a5` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `2c1a8fcd0026411f5d53fb87ba33524659065b4536d58f96cbeeb80d22a31feb` |
| `manifest.json` | `c24d38eec27dca8560c3ec5ce485e9751adb66edc34a52b4de0cb1a7ec5ca3fd` |
| `oracle.json` | `61904c6ce15441190476952ceb2cb82f5dab401622c282e3378e8ea97f5a4727` |
| `oracle_elements.json` | `061c079a3bffe4c49cd32d302a9992f8630d419774813b80e518477728470008` |
| `run.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `run.out` | `d45493085d2f864a15ca48fd6d1a3de1e8b84ba6e8656ba48299e33f59739176` |
| `stats.txt` | `2c1a8fcd0026411f5d53fb87ba33524659065b4536d58f96cbeeb80d22a31feb` |

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
