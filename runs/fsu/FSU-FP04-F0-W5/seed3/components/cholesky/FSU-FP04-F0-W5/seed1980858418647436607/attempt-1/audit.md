# FSU-FP04-F0-W5 seed1980858418647436607 审计

- attempt：`attempt-1`
- sample_run_id：`s1980858418647436607`

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
| `FSU-FP04-F0-W5-seed1980858418647436607.md` | `58a2476d64401136666a604ccaff0e54b8a1d7df02a31a7ba502ba9f9a3ba90a` |
| `census.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `census.out` | `ebd792f6461d512abb42df564d9864a21c462de74f95e4b3be8c792d316f3851` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `e391326f84b9e4b6a80f6c06f1c7a1ffb26d2a8c7dd1492dac1bf83baa1687a3` |
| `census/config.json` | `882b4e0ae8f0b45145423349d370ae0d6bf3f191a996a96762a64e2dc0d5a7bc` |
| `census/fpu_injections.log` | `8b66562bae879a94dd4b30dbecea756d9847812eee986c294b925dc0b6f0d968` |
| `census/stats.txt` | `347188b1efe61d22d60770d141bf183fd7a2d377b05b130216a81b9958acdfee` |
| `chain_report.json` | `2ffbd9c4986a5ac58cc74f7fcc48c44de214b541c94b149258af4cccf9ba07d9` |
| `component_manifest.json` | `bdad55f01f8c5a2037fe17fa227fbb14c2c7c86bcd80d75c8762a0d83060c768` |
| `inject/array.bin` | `3c9105e878aef6e7e8222473cf638a311e2ddaf18d460c99e22282a23ded5dbb` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `7b44d2e0f0cde6b23189b4d594ccae2c7b62ba5e7a2ec93833c98b9ca6dea9b0` |
| `inject/config.json` | `415877b0f0655ac5174fa2172f1baaae39ee0878cae53d35a5c63314729a0a9a` |
| `inject/fpu_injections.log` | `5e5cf55ad5ed3465259aefd9de1aaf983eb3268c0106189bcdfe3e6549427cfd` |
| `inject/prop_evt.txt.gz` | `b02ec3679cfc8e8f35a9ad7b715602c9072496de148052e41faf3ab929c97ce3` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `90b9cecb417122db8e67fafd01ab2ffe638d53a4b2b43c52475f74a525f94339` |
| `manifest.json` | `72c6ff330b05c2fdfea9076f668af161a73545e31d32d868da798b7a7ee23772` |
| `oracle.json` | `2395b79aced7666278b9be15d300e8833bb156fb7e8656cb89d7b8c93ad083ad` |
| `oracle_elements.json` | `73ad9a0ea1aef4ec1202813f4ec2dd367c6d54c643819bb49dc25f2ea1967e3f` |
| `run.err` | `83d08de2fb2bec371fda146b8d893c9461a9e8568f72ea943fc0c7010f4e08a0` |
| `run.out` | `46def36fd85a8e59f656c6bb7e5d06afc8b624631a6e0fa1f7f74468c7ac7802` |
| `stats.txt` | `90b9cecb417122db8e67fafd01ab2ffe638d53a4b2b43c52475f74a525f94339` |

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
