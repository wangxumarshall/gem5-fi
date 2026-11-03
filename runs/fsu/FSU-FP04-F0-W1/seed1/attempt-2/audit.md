# FSU-FP04-F0-W1 seed1 审计

- attempt：`attempt-2`
- sample_run_id：`s1`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 7 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '5', 'kind': 'commit', 'outcome': 'errant_commit'} |
| oracle | Masked |
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
| `FSU-FP04-F0-W1-seed1.md` | `665ba17ff39aa36ad94bbc5c5023dfc7578fbb31565b4981663afd6fc0cb1c8c` |
| `census.err` | `70c903c6b501403db8b5162ced9bbf43f40b13e120d7c1df4354edaa225c9f68` |
| `census.out` | `2db6a778ec445a146baf8a47b0bde89307c65e23d3f13f150b2466ce50b251e5` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `c5e70a94b7ffae1b3288c9d5bcc31c5017ac7ee51428348110c742d6ed8e3914` |
| `census/config.json` | `3003fe34591a00bd82c41210ff64f6857784b6f6268a17ceac3e3d7c45e079b6` |
| `census/fpu_injections.log` | `79dd5620fc033243feb8c1f3723113b9390eec5fe81ae57da6ca3a4347ff957e` |
| `census/stats.txt` | `9feced708e0994f934be29b66f8f015c631072f4b2f3ecd1dd36d9a377588143` |
| `chain_report.json` | `93e2c2317ea714cc288205e3fe1b7fb6320c248b2950bdcaf8e6dcbbbbf85872` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `460826407d77804584fb8260331c9b8eb1a6634f969e326649e53101c3b239c1` |
| `inject/config.json` | `9595d8f41fc059ab292daf692e66859e258b76836975f3dde254ef6c97da767e` |
| `inject/fpu_injections.log` | `926060f8345999f330908ffa5260c5f2e3d027ef6ed2295794f7ce33f37612f8` |
| `inject/prop_evt.txt.gz` | `2a5280e74936a45bfed0d18fff4ec6b2ad108b5333623307262f374ed3ef0fd3` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `8021eef3835c1bb938708d5dd0f5e7d46d912d4c316eb6661760cdd84ac6ec3a` |
| `manifest.json` | `4a099b3fa64bc77fca3d9cb81e18de47ba2786280dd2377ee25f23052debdad7` |
| `oracle.json` | `60dda9a7bbbd4b296d51faa07c2f4e7a1f362c779bdde3b0d56519206acb709e` |
| `run.err` | `70c903c6b501403db8b5162ced9bbf43f40b13e120d7c1df4354edaa225c9f68` |
| `run.out` | `3d92868b4dab5fedb9325a3d1beae05b2f53625ca27a03b2877456e01655aae8` |
| `stats.txt` | `8021eef3835c1bb938708d5dd0f5e7d46d912d4c316eb6661760cdd84ac6ec3a` |

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
| B0 运行态配置匹配（census） | PASS |
| B0 运行态配置匹配（inject） | PASS |
| admitted=True | PASS |
| violations=[] | PASS |

**结论：PASS**
