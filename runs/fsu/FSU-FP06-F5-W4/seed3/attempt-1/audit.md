# FSU-FP06-F5-W4 seed3 审计

- attempt：`attempt-1`
- sample_run_id：`s3`

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
| `FSU-FP06-F5-W4-seed3.md` | `cb360ffde4b77c08dafc4e2f087dae386b3ef7347963fccadf0b6e5786737790` |
| `census.err` | `279ad18c40c7f2a5d4dc8a3457ee13f80f0a4de3b1539c0601a810b6329e1eab` |
| `census.out` | `815e57e250d9c03afe107be7e1770c8f47a17f1be2331efe41ea3db80d307a00` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `ea584cec8adbc6478e2f578ebc9b993d15169662dfcf98b34c256b1bf7697bd5` |
| `census/config.json` | `2c534a04bc7d661eda962358e8217abe857ff4b2541c2ea94797157acc21ad9f` |
| `census/fpu_injections.log` | `bae2f3430d2fe1401d106ccf14c2b63359fe8bd4cd9163da50479c41a706506d` |
| `census/stats.txt` | `5a8bab5b3be0b4071b7215e00f93249780286efef2c07d0da6aa3483f5e6e4e3` |
| `chain_report.json` | `cc0683b54a263f6129707e5a5ecbdf0ff952567d24ebb2ad50050e093370ebdc` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `93c1919242f7d05e0c7686f4f4535c32d06ef822e2fd0a9144b2907bf8284aa4` |
| `inject/config.json` | `421cc8190bf5f393a16cc3c1281d3fdb0fdb854ef3d6de4a5801e683642d6d21` |
| `inject/fpu_injections.log.gz` | `236961b4e280a42423d63407870a2abc1861656cee4d06108713704e8f958cc0` |
| `inject/prop_evt.txt.gz` | `ea61c245ccd67b165ac1411f995727be9d0d9ee8c5e206ba60f371248d591da5` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `e1371a87399b1d8dbe2a4281f7cd11ec64473c2724d69533d3ad22d628aae624` |
| `injection_log_storage.json` | `19d1a18c5341a7d66f723886384d60cef50237f684ddc3657e3960af0171ff62` |
| `manifest.json` | `cee95ff825bc1c01389cc1378ed4f03d07098616c1ac2ff050fde96222ceb6e3` |
| `oracle.json` | `c0ef08328f02c29d7e46471dbbc10657407ff4bf9d420f611baa1c9d52d3b907` |
| `run.err` | `279ad18c40c7f2a5d4dc8a3457ee13f80f0a4de3b1539c0601a810b6329e1eab` |
| `run.out` | `9f64713d06509e3f7ff4d971a9cd34c3f2fd2f3339aee6fb7e495fc012131324` |
| `stats.txt` | `e1371a87399b1d8dbe2a4281f7cd11ec64473c2724d69533d3ad22d628aae624` |

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
