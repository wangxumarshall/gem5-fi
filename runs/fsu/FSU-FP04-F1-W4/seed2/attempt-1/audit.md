# FSU-FP04-F1-W4 seed2 审计

- attempt：`attempt-1`
- sample_run_id：`s2`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 14 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '5', 'kind': 'commit', 'outcome': 'errant_commit'} |
| oracle | SDC |
| chain terminal | full |
| stats 非空 | True |
| 无跨 seed 复制 | True |
| admitted（主 fault） | True |
| certified（全 fault 门禁） | True |
| fault 数 | 2 |
| 所有 fault admitted | True |
| 所有 fault certified | True |
| violations（主 fault） | [] |

## 逐 fault 审计

| fault | terminal | admitted | certified | direct parent | tick 单调 | layers | violations |
|---|---|---|---|---|---|---|---|
| 1 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |
| 2 | full | True | True | True | True | L0, L1, L2, L3, L4, L5 | [] |

## 边（主 fault）

- `0` → `1`：✓
- `1` → `2`：✓
- `2` → `3`：✓
- `3` → `4`：✓
- `4` → `5`：✓
- `5` → `12`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP04-F1-W4-seed2.md` | `484b7055769ec0879bc4da6705c5468daf0b920d16709e836c8f633357b08c34` |
| `census.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `census.out` | `0b81fa1b4782b87a4301fb7eface32d15be38f2b8d90facba9a841064b11ede6` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `985c6a9eb2298eac380b665399b6055c0a50e6c935215085a5d8763ff4e3d2ea` |
| `census/config.json` | `6109d409aa337b3e626f2e49c7e220f33ac03d24d702b0f2f247407a7610c564` |
| `census/fpu_injections.log` | `d153ffcef9b24d6300f5e45cc845ff6f57d519c1226cad280a84cfcae023a2c2` |
| `census/stats.txt` | `ab067b673913f292a5acc8f53cc4e3e782ea12fadc002a2e3622a3d8966f6ee7` |
| `chain_report.json` | `7516bcb3a2d14d4901eab84a94adf0118eef6f6aabc8eba2155a46bfc7e728b8` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `9675f360f269e719d57e0afb27162d97637856a61fc27afed4ad906fd19867bb` |
| `inject/config.json` | `d6653fcabfea6e55780db5aef889bd2a9c8f9df165b9159e6b32b85e738724f7` |
| `inject/fpu_injections.log` | `b36c84a18420548aab3f6a8cc8e6550ff3f561cbf77954eae72a2d6e7f08f940` |
| `inject/prop_evt.txt.gz` | `d4afd32159856e396ee887ce490c83c1791d750dceab651f4d29505d58867459` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `b468fa4df061801d30bac18b501a9a93c6569f51fb8b792c7c67f1d9dde002a9` |
| `manifest.json` | `3377f07dd1643ee0857d595db557b8d4e73ed085bc721e060ad00dba782a1adb` |
| `oracle.json` | `472f534c079cb09ba510e237db8f0c34d02acafceb57e624ab6d1aaf53cbdc50` |
| `ordinals.json` | `b751d246742d462a57fed2e6f8f897783babdbe153761aae87bba2691b10e2dc` |
| `run.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `run.out` | `9a62dbea004c512bac88d344726142cd1077aed2d18fe427b8984e376d202067` |
| `stats.txt` | `b468fa4df061801d30bac18b501a9a93c6569f51fb8b792c7c67f1d9dde002a9` |

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
| 重算 admitted_faults 一致 | PASS |
| 重算 truncated 一致 | PASS |
| 事件流 fault 数 = 注入数 | PASS |
| 所有 fault 均 admitted | PASS |
| 所有 fault 均 certified | PASS |
| fault 1 terminal 一致 | PASS |
| fault 1 violations 一致 | PASS |
| fault 1 admitted 一致 | PASS |
| fault 1 certified 一致 | PASS |
| fault 2 terminal 一致 | PASS |
| fault 2 violations 一致 | PASS |
| fault 2 admitted 一致 | PASS |
| fault 2 certified 一致 | PASS |
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
| MD event 12 存在于原始流 | PASS |
| MD event 12 kind 一致 | PASS |
| MD event 12 parent 一致 | PASS |
| MD event 6 存在于原始流 | PASS |
| MD event 6 kind 一致 | PASS |
| MD event 6 parent 一致 | PASS |
| MD event 7 存在于原始流 | PASS |
| MD event 7 kind 一致 | PASS |
| MD event 7 parent 一致 | PASS |
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
| MD event 13 存在于原始流 | PASS |
| MD event 13 kind 一致 | PASS |
| MD event 13 parent 一致 | PASS |
| 链 admitted=True | PASS |
| 链 certified=True | PASS |
| 链 violations=[] | PASS |
| 存在 admitted fault | PASS |
| MD 逐 fault 终局表存在 | PASS |
| fault 1 MD 覆盖主链全部事件 | PASS |
| fault 1 MD/原始流 direct parent | PASS |
| fault 1 MD 逐 fault 终局行存在 | PASS |
| fault 1 MD terminal 一致 | PASS |
| fault 1 MD admitted 一致 | PASS |
| fault 1 MD certified 一致 | PASS |
| fault 2 MD 覆盖主链全部事件 | PASS |
| fault 2 MD/原始流 direct parent | PASS |
| fault 2 MD 逐 fault 终局行存在 | PASS |
| fault 2 MD terminal 一致 | PASS |
| fault 2 MD admitted 一致 | PASS |
| fault 2 MD certified 一致 | PASS |
| MD terminal 与 chain_report 一致 | PASS |
| MD admitted/certified 与 chain_report 一致 | PASS |
| evidence_sha256.json 存在 | PASS |
| 证据 SHA-256 全部匹配（失配 0） | PASS |
| stats.txt 非空 | PASS |
| admitted=True | PASS |
| violations=[] | PASS |

**结论：PASS**
