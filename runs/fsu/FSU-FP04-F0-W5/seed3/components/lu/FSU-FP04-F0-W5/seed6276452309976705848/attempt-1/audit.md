# FSU-FP04-F0-W5 seed6276452309976705848 审计

- attempt：`attempt-1`
- sample_run_id：`s6276452309976705848`

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
| `FSU-FP04-F0-W5-seed6276452309976705848.md` | `2f586afebc8df8f052b219efbf80e6dc6c57a15357c08eead7a2c106718573f2` |
| `census.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `census.out` | `c4ccb56d248c8b86b7a67db218f9a3af219e5b9ad128c6db50e16319b5880c06` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `26aff2a406f631c81b5a9abea8b8660f348d3f2887579111f07b9d2e263dd402` |
| `census/config.json` | `69eb782bb0f19b3676124d441adce3df4757d030c6c164592753ae9defe89c12` |
| `census/fpu_injections.log` | `1991ad1c71ecf5d5c63adff1d6c2efcc01e04182094378b1ee3fce16d979c097` |
| `census/stats.txt` | `80eb6ae0e58bb8e5e6fde3b3057e349fc5c68b95c77b9a9fe84e572a70718268` |
| `chain_report.json` | `7a16ad4be7243bcf31da0f7962881020f187fde7cec0be3fd47d574eb300f1c1` |
| `component_manifest.json` | `b62ec29c3fe3a36254637ca319914e12e522ac31d62da202badc23c1a6e74f64` |
| `inject/array.bin` | `99b983c84773bfda7463959498deb86717cf16db91bad7faa067ffc0bef81fd3` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `5c8031861bf4c84425f2ca5ad5e79b132e78ecd8b05394548892294b7c112e40` |
| `inject/config.json` | `c1a6be22d9a2fe66d3dcf70a5e6fdffb113082dfa8eb4f7cbd207abd200b9213` |
| `inject/fpu_injections.log` | `b8e285ed88221a09efc37be81d54b59bf5db703e626d337e346cdc0622d41d70` |
| `inject/prop_evt.txt.gz` | `cdfe69ed9543a2888486e24fb8eb96b47c9d55054200443ca6aa5d7140718263` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `4848183f104233a801361dd95164f6bb3993e38b40ee2652cb513c96ce663fbb` |
| `manifest.json` | `07e06706a3e787719aa15e19b9e7fbf5884d28e2e01a570dc20864222002bf0a` |
| `oracle.json` | `efd4ed2f53bab04f8394877e400fe56a1f3405d9712b6e8a33f1a9a3b1f23085` |
| `oracle_elements.json` | `dcd8666a5e8eb85600c43834a159ea4e378f03ca37e5499156928bf46ec3144f` |
| `run.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `run.out` | `cd2d45f6e699b95065cccecd756f8eccc20a087c2c6b5122fbaaa1ea88445c18` |
| `stats.txt` | `4848183f104233a801361dd95164f6bb3993e38b40ee2652cb513c96ce663fbb` |

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
