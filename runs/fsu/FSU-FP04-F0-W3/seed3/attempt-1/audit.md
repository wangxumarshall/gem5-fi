# FSU-FP04-F0-W3 seed3 审计

- attempt：`attempt-1`
- sample_run_id：`s3`

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
| `FSU-FP04-F0-W3-seed3.md` | `caee21ca6f909a1059abc428b4f0a43b7a8ca6452d4e4c82ba3f159a090f7535` |
| `census.err` | `3b94bc39600d81ebe273ced2f04543d363c1f8965959df54c0ee05789173dbaf` |
| `census.out` | `c700ade0802ee2163fbd21cc6974ca492622677e84322b994eb446a0f8b96be9` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `1c7572544378752e989775ef3c30e767894fea38b7a3420039d029f1921b6f79` |
| `census/config.json` | `49989b9d9df63c4eb3b3105ace214e05e9a4d669ed0474a6b7e8869a8caccd7f` |
| `census/fpu_injections.log` | `d00d38340db51de7c1c6fb62f1bb636a1d50ee3b76ed17e3e40a2db17bb3130f` |
| `census/stats.txt` | `476a7f163483fd4da7c33050f3aff46247d5643f72416b255fd615dd4738be8d` |
| `chain_report.json` | `c1799e47a75791133742d43fd82a9e13d0ec27a5aebcc6c9430990104184e6b6` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `f0655d93ec397292d3b8da133d1eb96196cfde514d74dfd78c9d7e9aeb09415d` |
| `inject/config.json` | `2f8d4bb71a80d72622d2a1689f487cff14a64c33ff7b07329c02e008febae3be` |
| `inject/fpu_injections.log` | `5f55f8f8d2f12738f6d5ef672016a62d52a84114afb25eaee5ebf9dadd520d2d` |
| `inject/prop_evt.txt.gz` | `ce373aa84090ec3c993a4bfea6ab75c9b0f001e1e1ee90cc9f18a342a4d4c8c3` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `6b4b23020929d34d13e209fd1626a7107a42d911b6ed3d21a6b9dfa7623e87a9` |
| `manifest.json` | `6de164434d470e3d93a26ac84a01bb1652d71301eb72de56ff76f7a77be0a5f2` |
| `oracle.json` | `c573b91d2988451bbfeb34f774a667fc1b060c4ae832198acde0712582931014` |
| `run.err` | `3b94bc39600d81ebe273ced2f04543d363c1f8965959df54c0ee05789173dbaf` |
| `run.out` | `ad9a4001092b2d6813833c2d7fa18b0dbebbdd0cd1690d551e4fbf70fc2ac4a4` |
| `stats.txt` | `6b4b23020929d34d13e209fd1626a7107a42d911b6ed3d21a6b9dfa7623e87a9` |

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
| scheduled(1) = fault_applied(1) | PASS |
| 每个 injected fault 均真实激活 | PASS |
| fault 1 字段/lane/mask 语义 | PASS |
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
| MD 逐 fault 终局表存在 | PASS |
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
| admitted=True | PASS |
| violations=[] | PASS |

**结论：PASS**
