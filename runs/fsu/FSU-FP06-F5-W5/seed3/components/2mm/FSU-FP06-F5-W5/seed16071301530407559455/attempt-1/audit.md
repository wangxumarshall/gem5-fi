# FSU-FP06-F5-W5 seed16071301530407559455 审计

- attempt：`attempt-1`
- sample_run_id：`s16071301530407559455`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 521 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '12', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `9`：✓
- `9` → `10`：✓
- `10` → `11`：✓
- `11` → `12`：✓
- `12` → `520`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W5-seed16071301530407559455.md` | `4fef4d71b8044c5bdd36f04b743eefc1d3b154481ab3495201fc8ae3c01146a5` |
| `census.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `census.out` | `7a55aea8b3bd6b834ffcf1c6fe9cc2ccaedf2a273080432cce8f8a5121ab862c` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `64eee45367947304f46aedb70fc3ca7ffa320811017e61541134be38333572a1` |
| `census/config.json` | `67edffa43591cb79962009be7c393795f4fa52fa01ecae52684c5bf869428550` |
| `census/fpu_injections.log` | `96dd284ce70e08ddfab5718292fa8c721c98a1f3df8076d8c4ee693d8aca1670` |
| `census/stats.txt` | `dc2e15399c1f1714817bd098581e91602f015934b8254c61a3dbf2724bf51584` |
| `chain_report.json` | `0a9dc00e0308db703a77c265389c0334a61d88cec0468000457db150ceab3b29` |
| `component_manifest.json` | `28913435eacf8a9c92cdeadcfd1e2c4d08643b70f84040ec4ed67990b76be89e` |
| `inject/array.bin` | `f594ddd94f8103286558c335b0dfcca9a909adddcafa5c89c35f604ed6a006c3` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `59033a08bbe0c5ac2c4da59a65eafb0398bfcdac923055706f05e85f915300b1` |
| `inject/config.json` | `105d23fa6f338f167513b97b64e6f687d0176b469a25c01f231af32cddc734ec` |
| `inject/fpu_injections.log.gz` | `80a5e77b22a5facc2127d279030b5b62fce7523ef27dffe7a1b19af541e17f93` |
| `inject/prop_evt.txt.gz` | `26a35994f9c4418d6f8804d10f21ec0068cf78126a3732fc9148a6c26aadad07` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `104d3f65ba152c1c8e7af5cb463866fb9ed0174787f2a9df583a911ff64fa360` |
| `injection_log_storage.json` | `dc10d6427b18b2ecf71b2bebd906fec595f694afc8f3654837a1d219549692c0` |
| `manifest.json` | `792990d2d47d9775e0b1a7bbd2f829f2a98b8327352dd8ea35aafe1af7fb56ad` |
| `oracle.json` | `3e6ee2080754164a856d3fa0160093ffae66b56ea46e642878ffce850e169f53` |
| `oracle_elements.json` | `f9272c49f2e14716dde627f8f47e038ccab43a41666f88d3617198f2ad4c5c13` |
| `run.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `run.out` | `4af1a86a94d11a229b3293f4e089eaa80815f25016de8f60b869c6991b0e803e` |
| `stats.txt` | `104d3f65ba152c1c8e7af5cb463866fb9ed0174787f2a9df583a911ff64fa360` |

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
| MD event 9 存在于原始流 | PASS |
| MD event 9 kind 一致 | PASS |
| MD event 9 parent 一致 | PASS |
| MD event 10 存在于原始流 | PASS |
| MD event 10 kind 一致 | PASS |
| MD event 10 parent 一致 | PASS |
| MD event 11 存在于原始流 | PASS |
| MD event 11 kind 一致 | PASS |
| MD event 11 parent 一致 | PASS |
| MD event 12 存在于原始流 | PASS |
| MD event 12 kind 一致 | PASS |
| MD event 12 parent 一致 | PASS |
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
