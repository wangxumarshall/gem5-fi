# FSU-FP04-F0-W5 seed17763049110757693680 审计

- attempt：`attempt-2`
- sample_run_id：`s17763049110757693680`

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
| `FSU-FP04-F0-W5-seed17763049110757693680.md` | `6b0b96ac2fe8061f058ab3156082b1232c3f09709cc821ee888b4de562ea9f6f` |
| `census.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `census.out` | `c4ccb56d248c8b86b7a67db218f9a3af219e5b9ad128c6db50e16319b5880c06` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `57e77310542d8fa86b934913c0594d618b93b63f96db8833a4c57ecbfe17fbca` |
| `census/config.json` | `2bd81b04b55e7239d7273ea100dfa792f9ef763f2f723f0826bad4df081d81db` |
| `census/fpu_injections.log` | `1991ad1c71ecf5d5c63adff1d6c2efcc01e04182094378b1ee3fce16d979c097` |
| `census/stats.txt` | `fa445239ae7ab83fbd1b9e5d9af763cf82cde6312f7770cc1e674010fc670df4` |
| `chain_report.json` | `c9a004b954039b632c87e8ace677d3abc7ee7eed74019034439085b70a97191d` |
| `component_manifest.json` | `c01247b848f34915025241b9493cb77f34526ef810e4968254ea5cdfac6b9297` |
| `inject/array.bin` | `dd8bdd92a184f793287ce71bb5996a3e233ab3ef4d727321735d0cae37a02af4` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `912ef858a7229a303fc6652053bd2b16dba3273050fa61062046ef6c55af65c0` |
| `inject/config.json` | `c9c5c2ce01b884c9b7899d6382ae87d6439dd24b96ca8e9f1606219956f30e2b` |
| `inject/fpu_injections.log` | `1643f025bf998f23fac0ea4f183559e46dfa860cf68874c1ae12e7093c92fff3` |
| `inject/prop_evt.txt.gz` | `7c4bfb4065b8924dac63699f1422bcff58ff2397c2e7275817d95f0e159ed1b4` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `b29b1774a888b24d2ddd08cfcc75c076ed42b6f8fc86c7d7aa033a398d4030b5` |
| `manifest.json` | `74a191438b595ec486e47c5633eba7fd26ca4c18731541f5142a105708a91a51` |
| `oracle.json` | `672b90e7843d777b7cfcc04f56c3b95da78ff1c41e1cc8014347a5fa79b99c57` |
| `oracle_elements.json` | `de024da00ffbf7471e5d58da10dfefcfed3f4eefa6993288602f549fa6e320da` |
| `run.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `run.out` | `846568482f75ecfda4069963a2e9848640056b279f643ae546f7861439bf9c4e` |
| `stats.txt` | `b29b1774a888b24d2ddd08cfcc75c076ed42b6f8fc86c7d7aa033a398d4030b5` |

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
