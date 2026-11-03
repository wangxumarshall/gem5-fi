# FSU-FP06-F5-W4 seed1 审计

- attempt：`attempt-1`
- sample_run_id：`s1`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 521 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '11', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `8`：✓
- `8` → `9`：✓
- `9` → `10`：✓
- `10` → `11`：✓
- `11` → `520`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W4-seed1.md` | `9db3236d72cf8794dc1dada14f2c1493cc69684b34cb3db7e61a3c41da9f699e` |
| `census.err` | `279ad18c40c7f2a5d4dc8a3457ee13f80f0a4de3b1539c0601a810b6329e1eab` |
| `census.out` | `815e57e250d9c03afe107be7e1770c8f47a17f1be2331efe41ea3db80d307a00` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `07ea356b8cf7844697de945b8cfc716cd48fb94771b23410c853a9674323d63e` |
| `census/config.json` | `387571bd043af5dac354f2ef796b2c8695d579f93b4b4c7d96f541ba08d343e2` |
| `census/fpu_injections.log` | `bae2f3430d2fe1401d106ccf14c2b63359fe8bd4cd9163da50479c41a706506d` |
| `census/stats.txt` | `61285ef00c4ae60c1e4e97bf881f251e1171473c40e9bc2f5913dd0e62dc7003` |
| `chain_report.json` | `053fb6869d457afdb0283c23669fb2bcfcdd3dcaf4b96f6dea200f72a44e25d1` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `bb67346881cee2bd3bbc730ef0649c6d45190deebbc42bdd5b693981ea98d16b` |
| `inject/config.json` | `3ce2036dad4d38c38764eca0e65ba653bfb2de89d3db98cb4a47416011667296` |
| `inject/fpu_injections.log.gz` | `13b4b64e870504f01d2ab169c3edf839d60e30a932e6fcefb742923ce6610330` |
| `inject/prop_evt.txt.gz` | `3cbd67186bb63ca4af48a9421262d7a28d18b731e539dbf5560e78595881fca8` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `71f5981420b173c2da649326afe96213ce131956a37f3b7e3b030df88f7c583e` |
| `injection_log_storage.json` | `cb92921bdcbf0ae3c8cf60aae4e61b55829e5d24cdbf80f24423e99407ab72dd` |
| `manifest.json` | `8be93ab3f773934222fb5ec2c08721c338001325d505e28bf35f419a04048023` |
| `oracle.json` | `bd1c1410ae8658a892549c6656e7989b3bc7ca8492d9c192975f02b6f8ea1b86` |
| `run.err` | `279ad18c40c7f2a5d4dc8a3457ee13f80f0a4de3b1539c0601a810b6329e1eab` |
| `run.out` | `b78b6806b5ec1f8c66fd5f64c8b46c0a73029a8b2652d11c2d18cf88d061b4da` |
| `stats.txt` | `71f5981420b173c2da649326afe96213ce131956a37f3b7e3b030df88f7c583e` |

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
