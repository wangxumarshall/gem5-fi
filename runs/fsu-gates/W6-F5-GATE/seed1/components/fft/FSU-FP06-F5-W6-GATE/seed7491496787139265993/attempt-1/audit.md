# FSU-FP06-F5-W6-GATE seed7491496787139265993 审计

- attempt：`attempt-1`
- sample_run_id：`s7491496787139265993`

| 项 | 值 |
|---|---|
| gzip EOF 完整 | True（ok） |
| event_count | 522 |
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
- `1` → `4`：✓
- `4` → `7`：✓
- `7` → `8`：✓
- `8` → `9`：✓
- `9` → `10`：✓
- `10` → `521`：✓

## 证据 SHA-256

| 文件 | SHA-256 |
|---|---|
| `FSU-FP06-F5-W6-GATE-seed7491496787139265993.md` | `cc91cc5565394d61792238c9b78dd795e6376219154f2d74dac147474058dab1` |
| `census.err` | `e798c107ac5ec23672815724a64d0efaab3e9a7a5c4a78f21880c7252f78fe80` |
| `census.out` | `71b0fec718fc3877f1b9d14881b902f6a946569c8e349e47508f127b566107e9` |
| `census/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `census/config.ini` | `453a4c9c334c3b4a115d2ce80044bff8ab4be4e08abf733ec0c54673afea6514` |
| `census/config.json` | `3de28e71648c0f4e6fa5dc233628b3a49a210d42fd1fe4c990cf0f64cfcbe733` |
| `census/fpu_injections.log` | `087bc3ceedd301bd607f7361e9afb309f73a49379488262b1a933d1238a5d32f` |
| `census/stats.txt` | `0d0f91b7266a54a713c9250b7be476dcc741cdaed64d6f5f4cfe13bb64b8ce2c` |
| `chain_report.json` | `584128d8c1128e848a6bebfff34bcf629c18aeea2916ccde9d70038d4778d29a` |
| `component_manifest.json` | `d5ca06061538fbec3a2d00633799a1ebeae6dc2031e5acb0add00da6dd095264` |
| `inject/array.bin` | `cbd5cd4021f0ac99422f376594bc24f72ad2b93801702a03295875f666c4e95e` |
| `inject/citations.bib` | `107591e44a9aaf00921aa25e1ff6542570e2a7eb81536764c828f6646f2a8dd5` |
| `inject/config.ini` | `15dde4091d27db47c645a597937b7c641b46e451f49869ee45f51b5e73f42bad` |
| `inject/config.json` | `93d8773ce696026a75c8709485ff43d8df2efb882b37a19184007532851ea41e` |
| `inject/fpu_injections.log` | `7746564e3711cd1edc798d23ce18214f8bb7b6acc978f71c736c651f1e79b19f` |
| `inject/prop_evt.txt.gz` | `5b1e2068274531f948a4c57360cd4cf877e10b0b0e1e6287df042c70c1ed3838` |
| `inject/prop_trace.csv.gz` | `bac917a242450d5cba2c51cf61351aab9afb86ce96c89ed567f6bd9d6a9efafe` |
| `inject/stats.txt` | `dc076e3942bde048c9c900caeab8ce3f44c03126469599918dabd0ba08a3972f` |
| `manifest.json` | `c72b0652f3cf94fef5f9eeeae3320fac1eeeb5e0924b883156e59b95b0bd3a50` |
| `oracle.json` | `895aaf143cc327de10a1cd2b27d43b1fd8b82d1a89bd69b422eeaf8472917951` |
| `oracle_elements.json` | `5733ade968e2182a89a96838c348b871182f89d2375a8fa5e1f21e56d5b1ac02` |
| `run.err` | `e798c107ac5ec23672815724a64d0efaab3e9a7a5c4a78f21880c7252f78fe80` |
| `run.out` | `ca7dcccc3a99083fd117e9ad9713717a6d19301332d170856c7db2f550a96d6a` |
| `stats.txt` | `dc076e3942bde048c9c900caeab8ce3f44c03126469599918dabd0ba08a3972f` |

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
| MD event 4 存在于原始流 | PASS |
| MD event 4 kind 一致 | PASS |
| MD event 4 parent 一致 | PASS |
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
| MD event 521 存在于原始流 | PASS |
| MD event 521 kind 一致 | PASS |
| MD event 521 parent 一致 | PASS |
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
