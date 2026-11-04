# FSU-FR07-F0-W5 seed7620721642600394686 审计

- attempt：`attempt-1`
- sample_run_id：`s7620721642600394686`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 8 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '6', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `1` → `3`：✓
- `3` → `4`：✓
- `4` → `5`：✓
- `5` → `6`：✓
- `6` → `7`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FR07-F0-W5-seed7620721642600394686.md` | `878cd4f152e2b89a8d364221b528d533cd0ed37788c653fef0110ee8c4115d48` |
| `census.err` | `aab1510bc39780187ded556b781e6fb104354304676b3bc41045a0db1c656efe` |
| `census.out` | `19431cf806c5c901ed6056643fbc9dddca012675a839815127c66c77ac912ca1` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `ea270000d4fd74f0e1cd94534f0df74b9bed3cbc512279671123970f884efc3b` |
| `census/config.json` | `5919cec9c719b35b73e39e32c006383002abc4f85237c23e37811945aa6036e1` |
| `census/fpu_injections.log` | `5739b49e01569c1bc9e80804280bf4c262d35794bd040e86ec638eda6337f532` |
| `census/stats.txt` | `054515f9bef368513b947962ac61a3f12605e668753788b3fff45bbe6a86b5fa` |
| `chain_report.json` | `680e0f34c174e154377d042ea5ec3d472edec6dedc0b7d445d41cf039c8997b6` |
| `component_manifest.json` | `1747902855a14f2a88514c2b9320bc4e5f44a5bb36b528429e107bcd9545bd01` |
| `inject/array.bin` | `658378554bb9154c409afe8bc9b1e3b9235417b8a66c37a322f3a13f7ee2c355` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `9b36bfc872a69cb2cf0bcff97da1bce66c740160165cfaaca8536cf8af757c45` |
| `inject/config.json` | `a710e365aee2a53d8adac6884092666776c732049c775fd66cce493f17f013df` |
| `inject/fpu_injections.log` | `306305712aaaf8548b15a9f952f2d752c0e4437c9ff103540d5764a0bf0ffaaf` |
| `inject/prop_evt.txt.gz` | `4155dc058d89b446ac53550335b3cfabb6930a2d89b1971871dd90b736c68419` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `3f283194eb4a786bb4d0360f807c94136bf805243c81e985fa3b31f8bc9c0bfa` |
| `manifest.json` | `897c7970f0bcf787137a0c40f34cb9a51d8758c55ae1cc42b18e9bea1d560040` |
| `oracle.json` | `916c05fe43c38edb206a93f6446634105d790a966166f031825c4ecfb08f9b4b` |
| `oracle_elements.json` | `744a40c14d0324eefdd35f8ca42e92ff24b3560824c388e756bf3d758facbbb0` |
| `run.err` | `aab1510bc39780187ded556b781e6fb104354304676b3bc41045a0db1c656efe` |
| `run.out` | `d59a66366b3e677f769ebffbd4ce90f356df92b912ad64e9bf8445b763647db6` |
| `stats.txt` | `3f283194eb4a786bb4d0360f807c94136bf805243c81e985fa3b31f8bc9c0bfa` |

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
| fault 1 F5 计数/去重/守恒校验 | PASS |
| MD event 0 存在于原始流 | PASS |
| MD event 0 kind 一致 | PASS |
| MD event 0 parent 一致 | PASS |
| MD event 1 存在于原始流 | PASS |
| MD event 1 kind 一致 | PASS |
| MD event 1 parent 一致 | PASS |
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
| MD event 7 存在于原始流 | PASS |
| MD event 7 kind 一致 | PASS |
| MD event 7 parent 一致 | PASS |
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
