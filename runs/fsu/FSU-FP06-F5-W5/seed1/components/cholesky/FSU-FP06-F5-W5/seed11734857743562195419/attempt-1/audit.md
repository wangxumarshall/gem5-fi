# FSU-FP06-F5-W5 seed11734857743562195419 审计

- attempt：`attempt-1`
- sample_run_id：`s11734857743562195419`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 521 |
| 身份一致 | True |
| 单祖先直接 parent | True |
| tick 单调 | True |
| 层映射 | L0, L1, L2, L3, L4, L5；N/A=[] |
| L5 witness | {'event_id': '42', 'kind': 'commit', 'outcome': 'errant_commit'} |
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
- `2` → `39`：✓
- `39` → `40`：✓
- `40` → `41`：✓
- `41` → `42`：✓
- `42` → `520`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W5-seed11734857743562195419.md` | `f4df54e47b626e93818d9a524c7fea2d75bdfe4873c2c32469250bc0715e7f8c` |
| `census.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `census.out` | `ebd792f6461d512abb42df564d9864a21c462de74f95e4b3be8c792d316f3851` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `8079afe16c94ae9e1ba04249cf0ef2ee70e3008b3626e55d9b25a1361e4cd9ea` |
| `census/config.json` | `ddb96c3f40ac82d652758a95829eb640647c1d90ce810630aaa5c0215b31eeb6` |
| `census/fpu_injections.log` | `6888b5f440be65818781c1e962672d465a94da01be8d84aea2d5b24ec3abc9aa` |
| `census/stats.txt` | `1c79884a3fd7be7e27268c62f5396aea9bcc8844dc7e2b104f4541964e424f81` |
| `chain_report.json` | `3bfcec91b7130ca6219c433745f92ae90f76a8d66234e861261fb340bee1a266` |
| `component_manifest.json` | `8037967512551109bc4e8f54feaea27121f4c210382706e32a3489b57fb3cdbf` |
| `inject/array.bin` | `51ce8e215036381118ffbee3b946f9093677c42964c46d6abcedb81197391844` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `4de6834ab958433385480b62b1031b7a34d4deb057841edd6e6b2c800ee1d07f` |
| `inject/config.json` | `13d68c73215aad5b4bdef7113c98b8904d097632635514015598aab4e20c1dbf` |
| `inject/fpu_injections.log.gz` | `a1a8a6778d6e3d3150209d6b58afef59247efec3eee57603bbd1e67dc54214be` |
| `inject/prop_evt.txt.gz` | `87bf319774a2842a607490c9212d68503e6faef3f97aa71a1665872de43e9b95` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `5cf329a1aeb2bd13f6bb8c7c83d8016a022567a31f22c5ae9be6fd7abefd4c31` |
| `injection_log_storage.json` | `c1e86081208aac6dd8ca3187e677f269217c75e4b68f8dd44625edd216e3b0db` |
| `manifest.json` | `c1fb4f0badcad628f4c3c81635019673df85041c8d8a7a7cc7fdc43cf42db46b` |
| `oracle.json` | `472811f60448943e60ecb5cd0dea590ed20711da786be12e5c222a416614d710` |
| `oracle_elements.json` | `b97429614c822363b968ec5bed15acdb086ab65701e772f6926b99bf69b1cf62` |
| `run.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `run.out` | `752fa2ab47c2cb921d281c7e9036cdbaa2d5fd6cb6e382d018ad67ae673d3b47` |
| `stats.txt` | `5cf329a1aeb2bd13f6bb8c7c83d8016a022567a31f22c5ae9be6fd7abefd4c31` |

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
| MD event 39 存在于原始流 | PASS |
| MD event 39 kind 一致 | PASS |
| MD event 39 parent 一致 | PASS |
| MD event 40 存在于原始流 | PASS |
| MD event 40 kind 一致 | PASS |
| MD event 40 parent 一致 | PASS |
| MD event 41 存在于原始流 | PASS |
| MD event 41 kind 一致 | PASS |
| MD event 41 parent 一致 | PASS |
| MD event 42 存在于原始流 | PASS |
| MD event 42 kind 一致 | PASS |
| MD event 42 parent 一致 | PASS |
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
