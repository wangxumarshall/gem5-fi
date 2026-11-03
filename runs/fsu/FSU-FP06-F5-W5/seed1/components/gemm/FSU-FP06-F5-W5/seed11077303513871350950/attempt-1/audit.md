# FSU-FP06-F5-W5 seed11077303513871350950 审计

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
| `FSU-FP06-F5-W5-seed11077303513871350950.md` | `3910c9f1619037cdead63946a07f1da6d4215ab4c709f5bd38762bf12fdb4056` |
| `census.err` | `aab1510bc39780187ded556b781e6fb104354304676b3bc41045a0db1c656efe` |
| `census.out` | `19431cf806c5c901ed6056643fbc9dddca012675a839815127c66c77ac912ca1` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `e201605d1ff1ded43e02b474aa2f261f490c28331be18f7eb87b6905e41e59f6` |
| `census/config.json` | `1e4ae1538ab5f63a543f6631afe973a4758611443f6c6bb313cb417869cd029f` |
| `census/fpu_injections.log` | `c572620f84da4017f4dbf0ecf0779476a9a7aaca7c2c50031dcb18f76c0a0305` |
| `census/stats.txt` | `80a1f8cceccb60db897154d1b96666d337260527e8f4b39ddaee54d0df4dc943` |
| `chain_report.json` | `465740261a2207d7853767747c03eed3979c2f6525e5e30b2851d38e7f5f363f` |
| `component_manifest.json` | `6e66a56a7fa46319ef4a806884f8dc5d946596b82c84cd71b0d2be096fc440ad` |
| `inject/array.bin` | `44100065dc1514d479e8997fba81b027595c22817e95d0bbb6f68f70a37591d5` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `5eedba50d70bbe548c212a610b970a8e6d76ec8b3c63144670a1ecab6eeed393` |
| `inject/config.json` | `f42229d752eb4a6f3bf52176c5debadf926644efcb71422d26bac46eb425ed2a` |
| `inject/fpu_injections.log.gz` | `ae590d5131af785e2070ec5e35b6580c8e0b68a2334d2ea06491af2cd696b8ff` |
| `inject/prop_evt.txt.gz` | `97e7687652e5ef95a410c97a5fa500cd0fc7f7be5c5afd72a3bbca2b74ad29a7` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `cecf82176259889a39520550b8ce612c8f85dbf5a698bd7bb9ab9690c99715e8` |
| `injection_log_storage.json` | `e28bdff56f7bfdb8dad5285fc9c406bb57b0347a31ee051d6b5037557b03b390` |
| `manifest.json` | `bd29fa9341533b6ba30847eedece91c3a806a9683a64b566e6c941d945c91bdb` |
| `oracle.json` | `36f2d04826ab290218b849afe1017d405f656faf43241be0bdeddac9dc61195c` |
| `oracle_elements.json` | `399d06533fe4e7330839ad7e54bf3466721293d4042ca08221b63b20cddae466` |
| `run.err` | `aab1510bc39780187ded556b781e6fb104354304676b3bc41045a0db1c656efe` |
| `run.out` | `c8add0e449865f0f27ee4775395fb3bcf2217c26b4755e0045e21274486b428a` |
| `stats.txt` | `cecf82176259889a39520550b8ce612c8f85dbf5a698bd7bb9ab9690c99715e8` |

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
