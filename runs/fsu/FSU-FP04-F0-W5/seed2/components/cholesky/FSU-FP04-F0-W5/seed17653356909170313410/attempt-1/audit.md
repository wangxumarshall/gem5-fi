# FSU-FP04-F0-W5 seed17653356909170313410 审计

- attempt：`attempt-1`
- sample_run_id：`s17653356909170313410`

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
| `FSU-FP04-F0-W5-seed17653356909170313410.md` | `2af1b5b446c5104273bd05d72124a72932d2c119168e76f3f6a8bfd0afe7e736` |
| `census.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `census.out` | `ebd792f6461d512abb42df564d9864a21c462de74f95e4b3be8c792d316f3851` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `2de6c4b2b943aa3c91284fc18fd68d1d048a2d5e803534953e742146a2f0681d` |
| `census/config.json` | `dbb86fdd16608f0c1e406d99bc10a83b399f49fcfd892599e71277a0b411372b` |
| `census/fpu_injections.log` | `8b66562bae879a94dd4b30dbecea756d9847812eee986c294b925dc0b6f0d968` |
| `census/stats.txt` | `32379ac6145952835bdc79791df6a04d28087f366e73af5283666ac17467e119` |
| `chain_report.json` | `36d830fac65b1b2e4d9cbf34874a07c248aebeaf202bd63c1604708d998c6cb6` |
| `component_manifest.json` | `574c1aa5ad65652c370ccafee3dfd707873197c2539bd46640ae13eab99b5497` |
| `inject/array.bin` | `c5a20d51616a7b3fe8f3b6954c01961e1d122af9bc606cb9f5ac004bbaa43338` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `221e0322666da2e76109867f1b38e65a9f5807ab527c86dd4fd4c5c6957934e0` |
| `inject/config.json` | `aef6d0d9986915de1cf841043d5b6e7d5f9e4a15531644e52d9f3415d4bb2a29` |
| `inject/fpu_injections.log` | `61f37f4c8a72b039de3211598668a621797de6c930e45987652511dd98032795` |
| `inject/prop_evt.txt.gz` | `927977358634b9d51ef9837ba236be22c063edf60ffd4b20ba38e904aa247dc9` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `eee31c37345d487ce689fc8545d499b6b3ef4c6710e7f6079309fa2e7bbe4fe6` |
| `manifest.json` | `8a271696f7ee3ffd60a9ea0cc5612f1ea6dcf126e76435726d2c6285e867c4e4` |
| `oracle.json` | `8d75a511845fdbb2dd0e57d5aac7d990b4d16e6b6f4cc125297105570f332d9c` |
| `oracle_elements.json` | `02bb1b0a02208faaacd3827b321f3417cee486ff759aab1a070301d4a23c2f3d` |
| `run.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `run.out` | `bb92017465433ece70e112231ce17fb978d8027bb99db0a7d20353c65dc498aa` |
| `stats.txt` | `eee31c37345d487ce689fc8545d499b6b3ef4c6710e7f6079309fa2e7bbe4fe6` |

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
