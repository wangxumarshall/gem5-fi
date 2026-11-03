# FSU-FP06-F5-W5-GATE seed11077303513871350950 审计

- attempt：`attempt-1`
- sample_run_id：`s11077303513871350950`

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
| `FSU-FP06-F5-W5-GATE-seed11077303513871350950.md` | `193c953fe0a3a330cbbab7637bcd70da474a1b50ce4e4594d2a2bd037963656c` |
| `census.err` | `aab1510bc39780187ded556b781e6fb104354304676b3bc41045a0db1c656efe` |
| `census.out` | `19431cf806c5c901ed6056643fbc9dddca012675a839815127c66c77ac912ca1` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `e201605d1ff1ded43e02b474aa2f261f490c28331be18f7eb87b6905e41e59f6` |
| `census/config.json` | `1e4ae1538ab5f63a543f6631afe973a4758611443f6c6bb313cb417869cd029f` |
| `census/fpu_injections.log` | `c572620f84da4017f4dbf0ecf0779476a9a7aaca7c2c50031dcb18f76c0a0305` |
| `census/stats.txt` | `ba223b42c2bf2f3d49acae79d372be3135a7de81b9cca8a8fd037e6a7fe6b721` |
| `chain_report.json` | `90471364a8979159cf7bd545a3f6c3a907ac70a97c5e6e5a557ed25e353401c3` |
| `component_manifest.json` | `e923e28b5acd3088f1b55727192c686a47f6bb21f3855b6cac59a9a09b011768` |
| `inject/array.bin` | `44100065dc1514d479e8997fba81b027595c22817e95d0bbb6f68f70a37591d5` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `6d3673093a02db34f1fd4f29d0d2bcb6c6cfcccd769460b8ff0a319c3878b24a` |
| `inject/config.json` | `14625a04cdd54448587d6066320af3783bd1641204e06b72a85a6a276e4d641c` |
| `inject/fpu_injections.log` | `34104643808ed75d825576b9774cbaa4c3b58035ba9c532248decf3d1993831c` |
| `inject/prop_evt.txt.gz` | `062a5b2b5fdf5276d601fbcfffcdba0588b2db8c9ab964a19a562ef88c083665` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `ac7fa10b42458abc30ee033ef25afc839d08c47493d23c64034c491c3d66e315` |
| `manifest.json` | `06d52b4e06c33c67c0d2315372ebb5cf89ec2d87c1df882e9854ab39e999f001` |
| `oracle.json` | `36f2d04826ab290218b849afe1017d405f656faf43241be0bdeddac9dc61195c` |
| `oracle_elements.json` | `7d72a3a2b31a4896ef192cba6b6d76b13bc1d52eb6d3aeb569a6d9eff02335b6` |
| `run.err` | `aab1510bc39780187ded556b781e6fb104354304676b3bc41045a0db1c656efe` |
| `run.out` | `4fd33811a3b932fc909dfd5e81f73941216a9238dfce5f3fac90b9ca78d9d00d` |
| `stats.txt` | `ac7fa10b42458abc30ee033ef25afc839d08c47493d23c64034c491c3d66e315` |

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
