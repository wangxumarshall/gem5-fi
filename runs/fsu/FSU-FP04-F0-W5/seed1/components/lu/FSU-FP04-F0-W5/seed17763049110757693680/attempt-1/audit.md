# FSU-FP04-F0-W5 seed17763049110757693680 审计

- attempt：`attempt-1`
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
| certified（全 fault 门禁） | False |
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
| `FSU-FP04-F0-W5-seed17763049110757693680.md` | `d7cc3061b280fd5c6eb0dd4d0226246d54f84a3076758d7a4f99c893f958fb07` |
| `census.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `census.out` | `c4ccb56d248c8b86b7a67db218f9a3af219e5b9ad128c6db50e16319b5880c06` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `68bada857c64f0595369b6205c75ca9c1377a2623b8aaa703777a59ac8b961aa` |
| `census/config.json` | `0e0407ff8ef59b5906a44ed8031b36aead69ea0417ae03350c5e7f9e66ad2704` |
| `census/fpu_injections.log` | `1991ad1c71ecf5d5c63adff1d6c2efcc01e04182094378b1ee3fce16d979c097` |
| `census/stats.txt` | `5df63c7d8772049dce0219343b7d9e81495e2f265df1fd37848d1a889db23e70` |
| `chain_report.json` | `e8f9fa26a1a7df725dcb757c2cacdf9c01dd4c35487fa7b5fa15346e64e0bea1` |
| `component_manifest.json` | `b2c113ce92b9d86e19e2e2eba4075ce2b9c2357c722590a6c7154c4e3dccddf5` |
| `inject/array.bin` | `dd8bdd92a184f793287ce71bb5996a3e233ab3ef4d727321735d0cae37a02af4` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `09873157454ffc0a5354c694105001f1cce45b0e555a7ec040fac2884090a5b4` |
| `inject/config.json` | `874a0a1fcdeda191619479f47c3c525dc1f9d2d223f902d96a8c1bb8bdcb003c` |
| `inject/fpu_injections.log` | `1643f025bf998f23fac0ea4f183559e46dfa860cf68874c1ae12e7093c92fff3` |
| `inject/prop_evt.txt.gz` | `a56a183db7e5ce22976d395e280d98ff9b45378c039c9e3b568fc623292dbe9d` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `af00fba208ba6b2d097fac7d14597508735e4008e87553fb5e55cbd48d241811` |
| `manifest.json` | `4d89c0f76d34e4faacc1156ee3674c7715198d27e4b0e5d2c9c4fb1b8b177091` |
| `oracle.json` | `672b90e7843d777b7cfcc04f56c3b95da78ff1c41e1cc8014347a5fa79b99c57` |
| `oracle_elements.json` | `bac9fe2751c656ba5cd5b54ac98154239f94f673bd294a26c0fd73c1449f4ee0` |
| `run.err` | `d5e752c49b48bbf26d3a7f9e60be67d492f4ff2634911bc62085cd677daeab14` |
| `run.out` | `b7d3d24c624fff3074e49eb5c0ba061e8a2962adbc6ebeda4065f21663fbf810` |
| `stats.txt` | `af00fba208ba6b2d097fac7d14597508735e4008e87553fb5e55cbd48d241811` |

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
| fault 1 字段/lane/mask 语义 | FAIL |
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

**结论：FAIL**
