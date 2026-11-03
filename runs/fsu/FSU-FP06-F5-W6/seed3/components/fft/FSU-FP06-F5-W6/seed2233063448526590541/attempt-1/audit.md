# FSU-FP06-F5-W6 seed2233063448526590541 审计

- attempt：`attempt-1`
- sample_run_id：`s2233063448526590541`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 521 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '10', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `7`：✓
- `7` → `8`：✓
- `8` → `9`：✓
- `9` → `10`：✓
- `10` → `520`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W6-seed2233063448526590541.md` | `41157d44389f25cd54e29dcd73197ae1f4c17c4eb530033e145bde04b3f05942` |
| `census.err` | `e798c107ac5ec23672815724a64d0efaab3e9a7a5c4a78f21880c7252f78fe80` |
| `census.out` | `71b0fec718fc3877f1b9d14881b902f6a946569c8e349e47508f127b566107e9` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `f599bb02f413665d4d6c4d520ab372e5f9cef05d41cba01692f80aa1dfa8310b` |
| `census/config.json` | `543edd004c413966132f402a5291decd5420d3a23b0322daf35b9b169ee86b4a` |
| `census/fpu_injections.log` | `087bc3ceedd301bd607f7361e9afb309f73a49379488262b1a933d1238a5d32f` |
| `census/stats.txt` | `ec8a1657e56ae161f3c1ff6c105b7238ef6eb232e7d7d55b9a7669fe765bda42` |
| `chain_report.json` | `d43b5970c22a53ddaa9f2537a8006cb0dbd4038880207ec1c52cee92b9883a71` |
| `component_manifest.json` | `e0a00f2f191fa672818e8dd86cbca2fc0bbcb744450c70dc6e1d7d7818552b3e` |
| `inject/array.bin` | `623d684c1b7596ff0653dc745deaa74ebc970e5be7ba28414265ccfbd50201e2` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `99f5fc978dc6cc42645a32c4b1c03499713d910b675cee6b2a79447b7d21dd47` |
| `inject/config.json` | `b245c362a9f12ae01b8f70e493bb8c1b464f8d3cb36bad1a56bbd378c0c55e36` |
| `inject/fpu_injections.log` | `cb7458c36e77433142c736d6552ffcd02877788489bf0f1ce34b43d448d45dc5` |
| `inject/prop_evt.txt.gz` | `593c9b39de850887b34b9f4a754dd959be1a70deccee9f211335ff44fe2d81e7` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `606fa4e06ec89b0106a943b239a2fe9d068158a0f4b7f49b8368c8111ca4f03f` |
| `manifest.json` | `98966d2589b571c9cb03a0885254ee45c785cf00301994ef618fccd52595cf13` |
| `oracle.json` | `17d5cd2fac7041d2e00525fa397a943787fa0d5be1e209f5fd5bf3c9c51569c3` |
| `oracle_elements.json` | `692fb14a385e82b7293ab22cc288e648fdebc18b775f793cf7ee04d5c3a6f2d4` |
| `run.err` | `e798c107ac5ec23672815724a64d0efaab3e9a7a5c4a78f21880c7252f78fe80` |
| `run.out` | `a799328742d3037c3f6901652c0e95991e0a51fe791d3001c420cd23754cb36b` |
| `stats.txt` | `606fa4e06ec89b0106a943b239a2fe9d068158a0f4b7f49b8368c8111ca4f03f` |

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
