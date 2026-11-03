# FSU-FP06-F5-W5 seed18166053919936268521 审计

- attempt：`attempt-1`
- sample_run_id：`s18166053919936268521`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 521 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L4, L5；N/A=['L3'] |
| L5 witness | {'event_id': '8', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
| 1 | full | True | True | True | True | L0, L1, L2, L4, L5 | [] |

## 边（主 fault）

- `0` → `1`：✓
- `1` → `3`：✓
- `3` → `4`：✓
- `4` → `7`：✓
- `7` → `8`：✓
- `8` → `520`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W5-seed18166053919936268521.md` | `fbaddf8e6158395db38c9cc13266ee4a5eede848289a11e811fb82c8e27c604f` |
| `census.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `census.out` | `ebd792f6461d512abb42df564d9864a21c462de74f95e4b3be8c792d316f3851` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `3d298941daeb7d49f7984aad7dcb44f7f57f514ec81fd4298a929ab3c4fece9f` |
| `census/config.json` | `2b5b401d5ad2642ba80bb42c7b4df62a79345a82010db32a81d5eeb2231ebce9` |
| `census/fpu_injections.log` | `6888b5f440be65818781c1e962672d465a94da01be8d84aea2d5b24ec3abc9aa` |
| `census/stats.txt` | `72bba2e391985b0c5f0eb736b3bfe94f262dc53a90e7e7038adfdb8e2af3f51b` |
| `chain_report.json` | `738ab7fe644ca5330e1e91a2082a99085f705af3aeb6d7bfbe3feb062241cc66` |
| `component_manifest.json` | `eb0b1447a8daa1cdb953b2ab27a7b25e3f6128136fb010b712026cb430c9f5f9` |
| `inject/array.bin` | `0f4c215ca763a24e4f65f7d18744d75c6e55a31caa8edd6295ad78d970565820` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `77babc9eef556145cd964dd326ee460f75658ca0da4b2038dbf6c62dad18dcf8` |
| `inject/config.json` | `28697c2071db16d5eddc95565881259fd11cffabdffc39eb06c07737727209a5` |
| `inject/fpu_injections.log.gz` | `6d9432d44a38c475347ea862a0a8d013dd29966f7d4005417b47f74ed557e599` |
| `inject/prop_evt.txt.gz` | `22987b952a64ea337a2deac768ac762bcd49e9b46b4ba97fdea2b072f9d72820` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `7f99c5cffe24ac8dd5a46bed205a071335e28dac9be6225130ac73144639b33f` |
| `injection_log_storage.json` | `336e0466b75c723e14efcd2e316f668fe75ca6e3c3468e1351aa3509a7100a96` |
| `manifest.json` | `388522943e8d2798999460d903d556403fd290aa072f61618d197ce8e21f1ee4` |
| `oracle.json` | `e5b8912a27d4aa33fda53aeb4dcd891269d7d9a6cf5f2cc9673c82dac220b6a7` |
| `oracle_elements.json` | `a77cc8421228cb2285fed98ceb84f2014128f4f48ed8d141b8ca7bad4dd807dc` |
| `run.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `run.out` | `f6017fe294425dcb717adb48d8d70f46e8f2c586388bd5e99fe211fcafe069a2` |
| `stats.txt` | `7f99c5cffe24ac8dd5a46bed205a071335e28dac9be6225130ac73144639b33f` |

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
| MD event 3 存在于原始流 | PASS |
| MD event 3 kind 一致 | PASS |
| MD event 3 parent 一致 | PASS |
| MD event 4 存在于原始流 | PASS |
| MD event 4 kind 一致 | PASS |
| MD event 4 parent 一致 | PASS |
| MD event 7 存在于原始流 | PASS |
| MD event 7 kind 一致 | PASS |
| MD event 7 parent 一致 | PASS |
| MD event 8 存在于原始流 | PASS |
| MD event 8 kind 一致 | PASS |
| MD event 8 parent 一致 | PASS |
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
