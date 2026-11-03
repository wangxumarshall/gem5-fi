# FSU-FP04-F0-W5 seed11459609017687405773 审计

- attempt：`attempt-2`
- sample_run_id：`s11459609017687405773`

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
| `FSU-FP04-F0-W5-seed11459609017687405773.md` | `51f8bd589d509f705d3bb378b36e7e3ff3a22f35f0e1b2503379d5898569ce79` |
| `census.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `census.out` | `7a55aea8b3bd6b834ffcf1c6fe9cc2ccaedf2a273080432cce8f8a5121ab862c` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `a4167b7b77c964eb1dec133e33fe17ecfc6c925bf9a62370147616a353ec94b7` |
| `census/config.json` | `cae14d371ad8da6e72bf909b4dc53dfee087c5458789e7f5ab0176c5e49de05f` |
| `census/fpu_injections.log` | `d746b3ec116cf49efdb3e04d2366b7df009b532a601be892e2970b0a73e7013d` |
| `census/stats.txt` | `b02a2786e05623b4c8b61a3416fe1cc10a2b792020cff6bbc1e920f58860dfc3` |
| `chain_report.json` | `aeecacd14c7c369023b0ba4f558f9299fc8207d42667b3d9a0953b07cf464aca` |
| `component_manifest.json` | `2672dda7d8dcc3778654d768b0f4564310b308d26f249fcf53f8e6b3eda8f726` |
| `inject/array.bin` | `6ace7539d69bc06cd6b4f1bdc10d1d2f35f585ab4647b3b06e13e5e24b4724c1` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `538606ab3d114a838b48b96b3259c848877a571e5f1e9e06f0bd8fbe80dc1a9a` |
| `inject/config.json` | `fd5a708e875347fe67cde294b81916f570d9ff2782880c0bc276920d568d5b72` |
| `inject/fpu_injections.log` | `e0da46ce8c11b0a9e711a5b04ad795f8326fd327f3831b50819c400e0056f8a3` |
| `inject/prop_evt.txt.gz` | `3fd9f25a75fc0692a12fcc4b2beb32590222a8cc1fbfa4f6fbebe2baf78fade3` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `bdd955037dddfdab59ffe6e42e9a9fe4ed800b83319330500210883ee8a1c1d0` |
| `manifest.json` | `a3c746c1462c3b4839eba5c66a283d1d26e8df80b1e13c660025bfd0cd6a74f3` |
| `oracle.json` | `5c1b159a7033ac5aba51d5c5bd1523d5672c5c7b536980772eff20e5589cff86` |
| `oracle_elements.json` | `8e7eca54851cf5f8d28746a7f2cdbe681ac98d4006250e8568b3e14ecbb137f0` |
| `run.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `run.out` | `a90f17aa6da0342675c5c7e25345138a51c7dfc31344dfea39c50646a2615e8a` |
| `stats.txt` | `bdd955037dddfdab59ffe6e42e9a9fe4ed800b83319330500210883ee8a1c1d0` |

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
