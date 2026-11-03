# FSU-FP04-F0-W3-GATE seed3 审计

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
| `FSU-FP04-F0-W3-GATE-seed3.md` | `54e2ae59c69072670c0f8874025926064105925bba6bb9169a45a64f51a084fd` |
| `census.err` | `3b94bc39600d81ebe273ced2f04543d363c1f8965959df54c0ee05789173dbaf` |
| `census.out` | `c700ade0802ee2163fbd21cc6974ca492622677e84322b994eb446a0f8b96be9` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `1c7572544378752e989775ef3c30e767894fea38b7a3420039d029f1921b6f79` |
| `census/config.json` | `49989b9d9df63c4eb3b3105ace214e05e9a4d669ed0474a6b7e8869a8caccd7f` |
| `census/fpu_injections.log` | `d00d38340db51de7c1c6fb62f1bb636a1d50ee3b76ed17e3e40a2db17bb3130f` |
| `census/stats.txt` | `63e6afe7d110eb88a82e399658af55e5fa56c53749668ed4494e1c7f3108c0a0` |
| `chain_report.json` | `f85fe6a1bcd58d7a0836287468b771c0d81fe23c060097f44dbbbf64a39c0244` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `e52e8f2a9a34b6fb38b73951920bcf957ee958fa398016ae7857fde176b0893c` |
| `inject/config.json` | `79892555148d7118be62966ed1b5014ccbba9e0d80b0231c06c2eae9b4e46f9f` |
| `inject/fpu_injections.log` | `5f55f8f8d2f12738f6d5ef672016a62d52a84114afb25eaee5ebf9dadd520d2d` |
| `inject/prop_evt.txt.gz` | `a85f3d52e43e0615f61f3d58d695481c2ab4f73e3125555d4038e6bc4017047a` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `748cbfbfa0e5fe642d990e4f11c59ab992248583d1c30191faf2e0b9a2b718a0` |
| `manifest.json` | `2f71362ef722fb96e577dc98d46f4e6811636736a325cb3cf5c187d320a6fa7c` |
| `oracle.json` | `c573b91d2988451bbfeb34f774a667fc1b060c4ae832198acde0712582931014` |
| `run.err` | `3b94bc39600d81ebe273ced2f04543d363c1f8965959df54c0ee05789173dbaf` |
| `run.out` | `c8c9f5bbb151e9037a3ea49ed9f9e761d06343d373dbe76ea0f748cb2861b8ff` |
| `stats.txt` | `748cbfbfa0e5fe642d990e4f11c59ab992248583d1c30191faf2e0b9a2b718a0` |

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
