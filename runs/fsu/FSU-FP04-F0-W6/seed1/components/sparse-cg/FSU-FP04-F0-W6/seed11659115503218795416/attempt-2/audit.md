# FSU-FP04-F0-W6 seed11659115503218795416 审计

- attempt：`attempt-2`
- sample_run_id：`s11659115503218795416`

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
| `FSU-FP04-F0-W6-seed11659115503218795416.md` | `bb133efb4f83960217100304d866e0b2682225240851ec7b695fdda57337e531` |
| `census.err` | `c0d7ed0b8024da977ee10538dcd63845e4793271dc417a5badeb0978e48fbec2` |
| `census.out` | `aaa3ad592bed190d0c07bea5f2eff404f94545e4d4749bebe8a33e53046b0eec` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `12c85bd2006390567fc8db7c274f11bafd4082826260b8f39202ccac78386d91` |
| `census/config.json` | `420bdba76808394df8def7fc3e727dab272a733773be0b875654993c709ca030` |
| `census/fpu_injections.log` | `7d4a2321eb81215bafc86524bac039b3535e5a09895fc42f5bbe3d1f14e430b2` |
| `census/stats.txt` | `b45e9d54123eb16f6ef3d90b2dde8216524820a40a0fa8b399296ab10b14ae48` |
| `chain_report.json` | `10d44d6201f6a410f77f80cb9e2e5bf71ddb698e32f9515429d5ab6e9b6dcf11` |
| `component_manifest.json` | `a7230583050bd63fc142e2cc0aaf642270cb1371a7c726288fea4c11849531d4` |
| `inject/array.bin` | `1ab3a10ca31fd7304dddd44145de1840293180aa1b09de04594b0eb6e7b8e51c` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `164ebf6ffddf932330bbff12abdfd708c7ab725d2f4659b0a6d3414a48bb766d` |
| `inject/config.json` | `6b4a7f99d1340fe913a3fd4f3ae0dd414ba96bebb7190c2bcdf3a4d6c91c0c42` |
| `inject/fpu_injections.log` | `fccce7584f96e3a01dd32e8dad31e62a51c0b2893a5af524d9bcd2ea44dcba00` |
| `inject/prop_evt.txt.gz` | `3d1779b133da36082033f88d2ca0fb1662a5ad6f3b0206e87800e8b4ec7daf1b` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `1fac8f168f59f0dd7e269be14b55404ae152ff028dc8e022e9cb07b48352d160` |
| `manifest.json` | `f8b8bea987bd8e0644dfae2ca403a55a3c7e4f8544bd6cf5fdb6efef5f2fb27e` |
| `oracle.json` | `b3dd197c39c68fceb412a49f512ab64b721f0c6f09a04e2f3db664084fd31fc4` |
| `oracle_elements.json` | `dfe5d3e0ac22d1a8d8a15bdbba4b1bd4d67954625a40d56b8a8e3e397eb0a55a` |
| `run.err` | `c0d7ed0b8024da977ee10538dcd63845e4793271dc417a5badeb0978e48fbec2` |
| `run.out` | `6ba5ba8da0d9085adcd47e1bc7c3bb39b6c6a4ad3657072ddd48c70d6b96e74e` |
| `stats.txt` | `1fac8f168f59f0dd7e269be14b55404ae152ff028dc8e022e9cb07b48352d160` |

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
