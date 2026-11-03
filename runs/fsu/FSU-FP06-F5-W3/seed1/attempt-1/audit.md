# FSU-FP06-F5-W3 seed1 审计

- attempt：`attempt-1`
- sample_run_id：`s1`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 522 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '61', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `1` → `55`：✓
- `55` → `58`：✓
- `58` → `59`：✓
- `59` → `60`：✓
- `60` → `61`：✓
- `61` → `521`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W3-seed1.md` | `ad3bfafeb7c409b0c16eb673ca5a3d70103770f722722356cc51da294e433266` |
| `census.err` | `dec72566590bdc5e161de8212087044774786c74f89964911cc196ef6b1ff992` |
| `census.out` | `fac0a1421006952effb359683641278158af2aead4668dbf9f92db82d4b530af` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `dcfe644ec9e5ecb5ce19b3da75fe335c04221035baa4eb7b8ae0dd8cbebc9a8f` |
| `census/config.json` | `a18dd06026ca7137b900ad5d8abc44e51041d7f2e8a77511fb86ca66dd195c77` |
| `census/fpu_injections.log` | `a11af940ae5abd172a9256c3b0d49a82356f9814c3ed2922e7b15ba6f78f4b1a` |
| `census/stats.txt` | `fa0f84ec09e3d9d9f38ae3501fab24d402437e1546357aeab39f14cd4c988b0d` |
| `chain_report.json` | `1acd3a168fd68ac7cb97da6a607939dc0246ed035e894f3fa97c22020c8e8c64` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `6da9ceb53f4fb931b2fbfbb21724f6bedc228748faea3f1a308c09d5a4544465` |
| `inject/config.json` | `801a810fe9f880f7ec8ef07bacdfbf123d5e3aefbdb600d3cc6997f42a47d705` |
| `inject/fpu_injections.log` | `c88a3449553bd48a3d104322aacdbbe971b6f91877d6ad2c4c47e272ef48a8b8` |
| `inject/prop_evt.txt.gz` | `6658d30f0e181f89eadb072398513b64109811baa091d0266f1c3823aec4f1eb` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `cc01892726f4eec93578d3ff4ef0a9fdc03dd201211f23bcee5861698b41006b` |
| `manifest.json` | `340d82788834532b708dfbd17bd10437370094ee6190c9ba01e3c056094bc1f2` |
| `oracle.json` | `df505893b08a706795ea253bb8bf7e1efdaee4977ca3dfcd858be920b943df9f` |
| `run.err` | `dec72566590bdc5e161de8212087044774786c74f89964911cc196ef6b1ff992` |
| `run.out` | `48e0d74000ced26bcd7635dea8460c805a6f48497f6af6d67e68a876e5a5d784` |
| `stats.txt` | `cc01892726f4eec93578d3ff4ef0a9fdc03dd201211f23bcee5861698b41006b` |

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
| MD event 0 存在于原始流 | PASS |
| MD event 0 kind 一致 | PASS |
| MD event 0 parent 一致 | PASS |
| MD event 1 存在于原始流 | PASS |
| MD event 1 kind 一致 | PASS |
| MD event 1 parent 一致 | PASS |
| MD event 55 存在于原始流 | PASS |
| MD event 55 kind 一致 | PASS |
| MD event 55 parent 一致 | PASS |
| MD event 58 存在于原始流 | PASS |
| MD event 58 kind 一致 | PASS |
| MD event 58 parent 一致 | PASS |
| MD event 59 存在于原始流 | PASS |
| MD event 59 kind 一致 | PASS |
| MD event 59 parent 一致 | PASS |
| MD event 60 存在于原始流 | PASS |
| MD event 60 kind 一致 | PASS |
| MD event 60 parent 一致 | PASS |
| MD event 61 存在于原始流 | PASS |
| MD event 61 kind 一致 | PASS |
| MD event 61 parent 一致 | PASS |
| MD event 521 存在于原始流 | PASS |
| MD event 521 kind 一致 | PASS |
| MD event 521 parent 一致 | PASS |
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
