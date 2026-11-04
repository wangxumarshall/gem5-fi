# FSU-FR03-F5-W5 seed15036002611505353583 审计

- attempt：`attempt-1`
- sample_run_id：`s15036002611505353583`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 137 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L1, L2, L5；N/A=['L3', 'L4'] |
| L5 witness | {'event_id': '134', 'kind': 'commit', 'outcome': 'errant_commit'} |
| oracle | Masked |
| chain terminal | full |
| stats 非空 | True |
| 无跨 seed 复制 | True |
| decode_guard | False |
| decoded / legacy roots | 0 / 1 |
| admitted（主 fault） | True |
| certified（全 fault 门禁） | True |
| fault 数 | 1 |
| 所有 fault admitted | True |
| 所有 fault certified | True |
| violations（主 fault） | [] |

## 逐 fault 审计

| fault | terminal | admitted | certified | direct parent | tick 单调 | layers | violations |
|---|---|---|---|---|---|---|---|
| 1 | full | True | True | True | True | L0, L1, L1, L2, L5 | [] |

## 边（主 fault）

- `0` → `1`：✓
- `1` → `2`：✓
- `2` → `9`：✓
- `9` → `17`：✓
- `17` → `28`：✓
- `28` → `36`：✓
- `36` → `44`：✓
- `44` → `45`：✓
- `45` → `54`：✓
- `54` → `65`：✓
- `65` → `74`：✓
- `74` → `82`：✓
- `82` → `90`：✓
- `90` → `91`：✓
- `91` → `96`：✓
- `96` → `105`：✓
- `105` → `110`：✓
- `110` → `119`：✓
- `119` → `127`：✓
- `127` → `132`：✓
- `132` → `133`：✓
- `133` → `134`：✓
- `134` → `135`：✓
- `135` → `136`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR03-F5-W5-seed15036002611505353583.md` | `336eac0d10c85eda1207f7c9b3da53056603f5004727ca83cf8ff3a46fb19493` |
| `census_skipped.json` | `b9b84111618105c0b4743af95b5d7f74e02edb7ed546178279f14008747f0c94` |
| `chain_report.json` | `e268e2daf6c114129483b311a6908bed4739215c0089d9fb4d8f0407d372627f` |
| `component_manifest.json` | `0ad073b404aaa38ea7995f80503ca9a3289916a780d8ddbb74745fbdfd41009c` |
| `inject/array.bin` | `23eb863deda56bcbd897823b0fcc0832907661ca0b80980a6aa5acaaa388ed9a` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `5936b4df9f0ebcd55c5108d3eeef5ce6acd9ecd0dabbcc758f4c57d693bd29e7` |
| `inject/config.json` | `83ea04b2a2d3bcf05b450482b957697c6747cc5630472ff1fb400f209658321b` |
| `inject/fault_injections.log` | `d3143045ff5f7fcfd89e9cf50ba6fc79c63a38c02e1e468d4ba4539b3ac230ee` |
| `inject/prop_evt.txt.gz` | `d338ad718373da0295eeccb87fd2c6c67edad324f1eb4aef6fe22901c305ddb6` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `74c04ce8b5ec1dcc56c140b04d1bc373d7f175a8245e7463f482937538ae7ea7` |
| `manifest.json` | `69b1f1f56a792f5a1d8be2db01b4409244b6a5b665741b87d02079bab294f19d` |
| `oracle.json` | `b485fe7afe629539e7addc506115e8b99f2a4ff2c7c74c3594c37122254f2c75` |
| `oracle_elements.json` | `dfc44d2b28eba237b860c05166a9c21d10ce403bf418fe5b170ee2afc1a9bf45` |
| `run.err` | `34be856a34c5b83967fba3dc4dc9bf29f70b5508c4d27c42439d2ae7c6bfe6e8` |
| `run.out` | `a7e6eeb6005dcf81b47d41a68d9a470f549d0241aa17d52a3ff56c0883fb0e50` |
| `stats.txt` | `74c04ce8b5ec1dcc56c140b04d1bc373d7f175a8245e7463f482937538ae7ea7` |

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
| 事件 model_id 与 manifest 一致 | PASS |
| 事件 submodel 与 manifest 一致 | PASS |
| 事件 freq 与 manifest 一致 | PASS |
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
| MD event 9 存在于原始流 | PASS |
| MD event 9 kind 一致 | PASS |
| MD event 9 parent 一致 | PASS |
| MD event 17 存在于原始流 | PASS |
| MD event 17 kind 一致 | PASS |
| MD event 17 parent 一致 | PASS |
| MD event 28 存在于原始流 | PASS |
| MD event 28 kind 一致 | PASS |
| MD event 28 parent 一致 | PASS |
| MD event 36 存在于原始流 | PASS |
| MD event 36 kind 一致 | PASS |
| MD event 36 parent 一致 | PASS |
| MD event 44 存在于原始流 | PASS |
| MD event 44 kind 一致 | PASS |
| MD event 44 parent 一致 | PASS |
| MD event 45 存在于原始流 | PASS |
| MD event 45 kind 一致 | PASS |
| MD event 45 parent 一致 | PASS |
| MD event 54 存在于原始流 | PASS |
| MD event 54 kind 一致 | PASS |
| MD event 54 parent 一致 | PASS |
| MD event 65 存在于原始流 | PASS |
| MD event 65 kind 一致 | PASS |
| MD event 65 parent 一致 | PASS |
| MD event 74 存在于原始流 | PASS |
| MD event 74 kind 一致 | PASS |
| MD event 74 parent 一致 | PASS |
| MD event 82 存在于原始流 | PASS |
| MD event 82 kind 一致 | PASS |
| MD event 82 parent 一致 | PASS |
| MD event 90 存在于原始流 | PASS |
| MD event 90 kind 一致 | PASS |
| MD event 90 parent 一致 | PASS |
| MD event 91 存在于原始流 | PASS |
| MD event 91 kind 一致 | PASS |
| MD event 91 parent 一致 | PASS |
| MD event 96 存在于原始流 | PASS |
| MD event 96 kind 一致 | PASS |
| MD event 96 parent 一致 | PASS |
| MD event 105 存在于原始流 | PASS |
| MD event 105 kind 一致 | PASS |
| MD event 105 parent 一致 | PASS |
| MD event 110 存在于原始流 | PASS |
| MD event 110 kind 一致 | PASS |
| MD event 110 parent 一致 | PASS |
| MD event 119 存在于原始流 | PASS |
| MD event 119 kind 一致 | PASS |
| MD event 119 parent 一致 | PASS |
| MD event 127 存在于原始流 | PASS |
| MD event 127 kind 一致 | PASS |
| MD event 127 parent 一致 | PASS |
| MD event 132 存在于原始流 | PASS |
| MD event 132 kind 一致 | PASS |
| MD event 132 parent 一致 | PASS |
| MD event 133 存在于原始流 | PASS |
| MD event 133 kind 一致 | PASS |
| MD event 133 parent 一致 | PASS |
| MD event 134 存在于原始流 | PASS |
| MD event 134 kind 一致 | PASS |
| MD event 134 parent 一致 | PASS |
| MD event 135 存在于原始流 | PASS |
| MD event 135 kind 一致 | PASS |
| MD event 135 parent 一致 | PASS |
| MD event 136 存在于原始流 | PASS |
| MD event 136 kind 一致 | PASS |
| MD event 136 parent 一致 | PASS |
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
| physreg census explicitly skipped | PASS |
| B0 运行态配置匹配（inject） | PASS |
| admitted=True | PASS |
| violations=[] | PASS |

**结论：PASS**
