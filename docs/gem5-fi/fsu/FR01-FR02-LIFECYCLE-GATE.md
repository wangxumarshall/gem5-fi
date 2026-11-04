# FR01 / FR02 瞬态故障终局语义与生命周期门禁

> 范围：FR01（单 bit 翻转）与 FR02（两个不同 bit 翻转）在
> `CHAOSPhysReg` `phys` 模式下的 F0 真实证据。本文只描述**只读**离线门禁
> `tools/fsu_fr01_fr02_gate.py` 的判定模型、真实运行结果、证据缺口与所需
> C++ 改动。本文没有运行 gem5、没有 scons、没有新增任何正式 RunID/seed，
> 也没有修改 `runs/` 下的任何证据。
>
> 真实结果基线：`runs/fsu-gates/FR01-FR02-F0-W1/`（2026-11-04 已存在，
> 非正式 seed，不进入 519/240 计数）。

---

## 1. 为什么需要这个门禁

纯 C++ host 单测（`tests/unit/chaos_vec_transient_test.cc`）只能证明
128-bit 位选择/翻转模型本身。它不能证明一次真实 gem5 运行里：

- 被改的物理 cell 身份（`reg_class/phys_reg/lane/lane_width/bit_in_lane`）
  与命令行/manifest 一致；
- FR02 的两个 bit 真的是两个不同位置，而非随机碰撞后退化成单 bit；
- 除目标 bit 外的 128-bit 值保持不变；
- 故障最终是 commit、写覆盖、squash、free/realloc，还是根本没有 consumer；
- 写覆盖之后故障是否真的消失，还是仍可能残留在物理 cell 中；
- 瞬态故障有没有被错误地当成永久 stuck 再次施加。

`tools/fsu_fr01_fr02_gate.py` 对每个 attempt 目录重算这些事实，并输出
逐项 `PASS/FAIL/SKIP`、证据文件路径 + sha256、字段来源，以及独立的
生命周期 `certification`（`CERTIFIED/BLOCKED/FAILED`）。

**`status=PASS` 只表示“磁盘上的证据内部一致、按记录的终局闭合”；它不等于
`Masked` 认证。** 二者在 JSON 中分开报告。

---

## 2. 输入与字段来源

门禁接受一个 attempt 目录，或一个包含多个 attempt 的 gate 目录（递归发现
带 `prop_evt.txt[.gz]` 或 `fault_injections.log + config.ini` 的目录）。
它是只读的：唯一可选的写操作是 `--json-out` 指定的报告文件。

| 来源 | 用途 |
|---|---|
| `prop_evt.txt[.gz]` | 唯一的事实事件流（L0/L1/L2/L5/lifecycle） |
| `fault_injections.log` | 命令侧交叉核对：`VecTransientInstall`、注入摘要行、`VecTransientOverwrite`、`VecFaultFailClosed`、`ReadTracePoll` |
| `config.ini` `[board.chaos_phys]` | `bitsToChange`、`faultMask`、`vecLaneWidth/Offset`、`semanticRole`、`faultType`、`injectionMode`、`regTargetClass`、`targetPhysRegIdx`、`rngSeed`、`maxFaults`、`requireAllocated` |
| `config.ini` `[board.chaos_propagation]` | `runId`、`sampleRunId` |
| `config.ini` core 段 | `numPhysVecRegs`（本次证据为 48），用于 phys index 范围校验 |
| `stats.txt` | `numFaultsInjected`、`numBitFlips`、`numPermanentFaults`、`numStuckAtZero/One`、`simTicks`、`simInsts`（运行边界） |
| `expect.json`（可选） | 合成测试/外部 manifest 的显式期望；与 `config.ini` 冲突即 FAIL |
| `--expect FILE`（可选） | 对每个 attempt 追加显式期望 |

每个 attempt 报告中的 `expectation_sources` 记录每个字段最终来自哪个文件。
缺失字段一律报 `evidence_missing`/`SKIP`，不填默认值。

---

## 3. FR01 / FR02 身份与合法性判定

事件流中 FR01/FR02 的根是 `kind=fault_applied`、`field=transient_bit_flip`、
`model_id ∈ {FR01,FR02}`。非根事件按 `fault_id` 且 `model_id ∈ {FR01,FR02}`
分组。

> 注意：真实流里每个 fault 有**两条** `chain_end`。一条是
> `finalizeVecTransient()` 发出的瞬态终局（`corr=fsu_taint`，带
> `model_id/phys_reg/terminal`）；另一条是 `CHAOSPropagation` 在 exit
> flush 时按 fault 发出的空白收口（`corr=none`、`model_id=`、`phys_reg=`、
> `terminal=`）。门禁用 `model_id ∈ {FR01,FR02}` 过滤，只认前者。后者只作为
> “流已关闭”的旁证，不参与终局判定。naive 的“数 chain_end”检查会误判。

| 检查 | FR01 | FR02 | 依据 |
|---|---|---|---|
| bit 数 | 恰好 1 | 恰好 2 | `bit_indices`；根 `model_id` 必须与 bit 数一致（1→FR01，2→FR02）；与 manifest `bitsToChange` 一致 |
| mask popcount | =1 | =2 | 根 `fault_mask`（128-bit）的 popcount；且 mask 的置位集合必须**逐一等于** `bit_indices` |
| bit 去重/域 | 单 bit 天然不同 | 两个位置必须不同，且都在 `[0,127]` | `bit_indices` 去重；越界/重复/非升序均 FAIL |
| 显式 mask 与命令一致 | `fault_mask` 低 64 bit == `config.ini faultMask` | 同左 | 配置 `faultMask` 是 `UInt64`；随机 mask（`faultMask=0`）时只以事件流为准（SKIP 该子项） |
| lane 身份 | `lane_width ∈ {8,16,32,64}`；`lane_offset == min(flat)//lane_width`；`bit_in_lane == min(flat)%lane_width` | 同左 | 根字段重算；与 manifest `vecLaneWidth` 比较；定向 `vecLaneOffset>=0` 时必须与真实 bits 所在 lane 一致 |
| lane_mask | 重算 lane 内相对 mask 必须等于根 `lane_mask` | 同左 | FR02-c 的 `lane_mask` 只覆盖首个 bit 所在 lane（bit 37 在 lane 1，不进入 `lane_mask`），完整两位只在 `fault_mask` 与 `full_*` 中体现 |
| before/after | `after == before ^ lane_mask` 且 `before != after` | 同左 | 根 `before/after` |
| 非目标位不变 | `(full_before ^ full_after) == fault_mask`；目标位在 `full_before` 中必须为 0；`full_*` 取出的 lane 值必须等于 `before/after` | 同左 | `full_before/full_after`（128-bit）与 lane 值交叉验证，而不是只看 lane 值 |
| 几何分类 | FR01-a FP64 lane / FR01-b FP32 lane / FR01-c NEON lane | FR02-a 同 lane 相邻、FR02-b 同 lane 非相邻、FR02-c 跨 lane、FR02-d 跨 32-bit 字段 | 用真实 flat bits + `lane_width` 重算 `lanes/fields/distance`，再与 `semanticRole` 比较；不一致 FAIL |
| phys cell 身份 | `reg_class=vec`；`phys_reg` 在 `[0,numPhysVecRegs)`；若 `targetPhysRegIdx>=0` 必须相等；否则以注入日志 `PhysReg[n]` 交叉核对；根/carrier/overwrite/commit/squash/chain_end 的 `phys_reg` 必须一致 | 同左 | 事件流 + `fault_injections.log` + `config.ini` |
| generation | 根 `reg_generation` 必须存在；carrier/chain_end 必须等于安装世代；consumer 读取世代必须等于安装世代；overwrite 世代只能更大或相等（释放/重分配会递增） | 同左 | 事件流 |
| run 身份 | 根与所有生命周期事件的 `run_id/sample_run_id` 必须非空且与 `config.ini` 一致 | 同左 | 事件流 + 配置 |
| precision | 当前 C++ 不发射 → `SKIP (evidence_missing)`；若 manifest 与根都有 `precision` 且不一致 → FAIL | 同左 | 见第 7 节缺口 |
| FP 字段名 | 当前 `field=transient_bit_flip`，不发射 sign/exp/mant → `SKIP`；仅按 bit 位置给出候选字段 | 同左 | 见第 7 节缺口 |

### 3.1 注入前拒绝（fail closed）

以下条件会被 C++ 在写 PRF 之前拒绝。门禁独立重算这些条件；一旦发现
manifest 不自洽，就要求磁盘上出现对应的 `VecFaultFailClosed` 证据：

- `vecLaneWidth ∉ {8,16,32,64}`；
- `vecLaneOffset < -1` 或 `>= 128/vecLaneWidth`；
- 显式 `faultMask` 的 popcount 不等于 `bitsToChange`；
- 显式 mask 不满足声明的 FR02 几何（跨 lane/跨字段/相邻/非相邻），或
  定向 lane 不含目标 bit。

判定为 fail-closed 的 attempt 必须同时满足：

1. 事件流中没有 FR01/FR02 `fault_applied` 根；
2. `fault_injections.log` 有 `VecFaultFailClosed`，reason 与门禁推导出的
   条件一致；
3. `stats.txt` 的 `numFaultsInjected/numBitFlips/numPermanentFaults/
   numStuckAtZero/numStuckAtOne` 全为 0；
4. 没有 `VecTransientInstall` 行；
5. `stats.txt` 存在且 `simInsts>0`（运行正常走完）。

满足时 `mode=fail_closed`、`certification=CERTIFIED`、
`masked_certification=NOT_APPLICABLE`。若配置不自洽却仍出现根 → FAIL；
若配置自洽却出现 fail-closed → FAIL。

---

## 4. 生命周期终局判定

终局由事件流**重算**，再与瞬态 `chain_end.terminal` 对比。映射：

| 事件事实 | 重算终局 | 当前 C++ 是否可发出 | 认证含义 |
|---|---|---|---|
| 至少一个 consumer `commit`（L5） | `committed` | 是 | `CERTIFIED`：L2 读取是 commit 的直接 parent，世代/值一致；SDC vs benign 仍需 oracle |
| 无 commit，但第一个真实写覆盖 | `overwritten` | 是 | `BLOCKED`：只有 L1 含住事件；写覆盖范围与覆盖后读取不可见 |
| 无 commit/覆盖，但有 `squash` | `squashed` | **否**（当前 `finalizeVecTransient()` 会误写成 `exposed_unconsumed`） | `BLOCKED`：squash 不清除物理 cell，缺陷可能仍在 |
| 无 commit/覆盖/squash，但有 `generation_change/cell_free/...` | `free_realloc` | **否**（瞬态路径不发射） | `BLOCKED`：缺少终局词表与后释放证据 |
| 有 consumer 读，但 run 结束时无任何终局事件 | `exposed_unconsumed` | 是 | `BLOCKED`：故障可能在 run 结束时仍存活 |
| 无 consumer 读、无写、无释放 | `not_consumed` | 是 | `BLOCKED`：UNKNOWN，绝不是 Masked |

`chain_end` 必须满足：

- `terminal` 等于上表重算值；不在语义词表 `committed/overwritten/
  squashed/free_realloc/exposed_unconsumed/not_consumed` 中即 FAIL；
- `phys_reg/reg_generation/install_event/lane_width/lane_offset/lane_mask/
  bit_indices` 与根一致；
- `contained` 只在 `overwritten` 时为 `1`；
- `commit_events/squash_events/read_exposures_total/write_exposures_total/
  consumers_recorded` 与流内实际事件数一致
  （`write_exposures_total = 1 + overwrite 数`）；
- 有 commit 时 `first_impact_sn`/`l5_witness_event` 指向首个 commit；
- 有 overwrite 时 `affected_sn` 等于最后一次写的 `dyn_inst_seq`；
- 是同一 fault 的最后一个事件（不允许 `tick > chain_end.tick`）；
- `tick <= stats.simTicks`，且 `stats` 证明一次完成的运行。

### 4.1 commit / squash 身份

- `commit` 必须是 `detection_layer=L5`、`outcome=errant_commit`、
  `contained=0`；其 `consumer_seq` 必须命中一条真实 `operand_read`，
  `parent_event_id` 必须等于该读取事件 id，`reg_generation` 与读取时一致，
  值等于读取时观察到的 lane 值。
- `squash` 必须是 `outcome=squashed`、`squashed=1`、不声明 L5；
  `commit_events` 不得因 squash 增加。squash **永远不是** commit。
- `operand_read` 的 lane 值必须等于安装后的翻转值；`before==after`
  （它是观察，不是写）。

### 4.2 overwrite 身份

- `detection_layer=L1`、`containment_layer=L1`、
  `containment_reason=phys_cell_rewritten`、`contained=1`；
- `producer_seq == dyn_inst_seq`；
- `reg_generation >= install_generation`（世代递增表示该物理槽被释放/复用）；
- `before` 必须等于上一次观察到的 lane 值（无读取时等于根 `after`）。

写覆盖与 consumer 的先后关系单独判定（`overwrite_phase`）：

| 事实 | 判定 |
|---|---|
| 覆盖前没有任何 `operand_read` | PASS：`before_any_consumer_read` |
| 有读取、但都早于覆盖，且没有 commit | PASS：`after_consumer_reads_no_commit`（暴露过、被后写含住） |
| 出现 `tick > overwrite.tick` 的 `operand_read` | FAIL：当前发射端在覆盖后主动不发读取，这种流不属于已知发射语义 |

---

## 5. Masked 认证：为什么当前一律 BLOCKED

`Masked` 认证要求同时满足：

1. 指定安装世代的故障**已消失**；
2. 之后没有受影响读或错误副作用；
3. 覆盖/释放/运行结束边界可追踪。

当前证据只能满足第 3 条中的“覆盖事件 + chain_end 边界”。缺两条关键证据：

- **写覆盖范围/宽度（write coverage）**：C++ 只观察目标物理 cell 是某条
  指令的 dest，并读回整个 128-bit 值；它不记录该指令实际写了多少
  byte/bit。若写只覆盖低 64 bit（如 D 寄存器写），高半部分的目标 bit 可能
  仍是故障值。`full_after` 中目标 bit 是否为 1 **不能区分**“写入了正确值恰好
  该位为 1”与“故障位残留在未覆盖区域”。
- **覆盖后读取可见性**：`observeVecTransient()` 在 `overwritten` 后直接跳过
  L2 读取记录（`CHAOSPhysReg.cc:412`）。因此事件流里“覆盖后没有
  operand_read”是**工具主动不发射**，不是“没有发生读”。不能据此证明无
  受影响读。

因此：

- `overwritten` 的真实记录：`masked_certification.certified=false`，
  `verdict=BLOCKED`，`present=[L1 overwrite, chain_end boundary]`，
  `missing=[write coverage, post-overwrite read observation,
  oracle_diff/golden]`。
- `not_consumed`/`exposed_unconsumed`：`verdict=BLOCKED`，故障在 run 结束
  时状态未知，**永远不能**因为最终 workload hash 相同而判 Masked。
- `committed`：`verdict=NOT_MASKED`（已到 L5），但 SDC/benign 仍需
  oracle diff。

门禁 JSON 固定包含
`"final_hash_equality_alone_insufficient": true`。

---

## 6. 连续写与“不会误变永久 stuck”

瞬态路径在 C++ 中不调用 `armVecStuck()`、不写 `permanent_faults`、
不设置 `vec_stuck.valid`（见 `CHAOSPhysReg.cc:1901-1981` 与
`FR01-FR02-F0-AUDIT.md` 第 5 节）。门禁从三方面核查：

1. **配置/统计**：`faultType=bit_flip`；`stats.numPermanentFaults=0`、
   `numStuckAtZero/One=0`。
2. **事件流**：同一 fault 中不得出现 `fault_installed/stuck_reapplied/
   phys_write`；根 `field` 必须是 `transient_bit_flip`。
3. **连续写**：若流中有 ≥2 个真实写观察，则后一次写的 `before` 必须等于
   前一次写的 `after`（中间没有重新施加故障）。若 `before` 等于
   `after ^ fault_mask`，说明故障在两次真实写之间被重新施加 → FAIL。
   当前 C++ 只记录**第一次**覆盖，因此真实 run 只能证明第 1、2 条；
   第 3 条报 `SKIP(only one write observation)`。

合成测试用两条 `overwrite` 事件覆盖了 PASS 与两种 FAIL
（`stuck_reapplied` 事件、两次写之间 reflip）。

---

## 7. 真实结果（只引用磁盘上已存在的 gate）

### 7.1 命令与汇总

```bash
python3 tools/fsu_fr01_fr02_gate.py runs/fsu-gates/FR01-FR02-F0-W1 \
  --json-out /tmp/fr01_fr02_gate.json
```

真实输出：

```
FR01/FR02 gate: 11 attempt(s) PASS=11 FAIL=0 SKIP=0 certified=1 blocked=10 failed=0 -> /tmp/fr01_fr02_gate.json
exit=0
```

即：11 个 attempt 的证据记录全部内部一致；只有 1 个是 `CERTIFIED`
（碰撞负例的注入前拒绝）；10 个的终局认证 `BLOCKED`（不是 FAIL）。

### 7.2 逐 attempt

| attempt | model | closure | 根 phys | gen | bits | lane | certification | masked |
|---|---|---|---|---|---|---|---|---|
| FR01-a/seed1 | FR01 | not_consumed | 34 | 1 | 5 | 64/0 | BLOCKED | BLOCKED |
| FR01-a/seed2 | FR01 | overwritten | 1 | 1 | 5 | 64/0 | BLOCKED | BLOCKED |
| FR01-a/seed3 | FR01 | not_consumed | 33 | 1 | 5 | 64/0 | BLOCKED | BLOCKED |
| FR01-a/seed4 | FR01 | not_consumed | 26 | 1 | 5 | 64/0 | BLOCKED | BLOCKED |
| FR01-a/seed5 | FR01 | not_consumed | 41 | 1 | 5 | 64/0 | BLOCKED | BLOCKED |
| FR02-c/seed1 | FR02 | not_consumed | 34 | 1 | 5,37 | 32/0 | BLOCKED | BLOCKED |
| FR02-c/seed2 | FR02 | overwritten | 1 | 1 | 5,37 | 32/0 | BLOCKED | BLOCKED |
| FR02-c/seed3 | FR02 | not_consumed | 33 | 1 | 5,37 | 32/0 | BLOCKED | BLOCKED |
| FR02-c/seed4 | FR02 | not_consumed | 26 | 1 | 5,37 | 32/0 | BLOCKED | BLOCKED |
| FR02-c/seed5 | FR02 | not_consumed | 41 | 1 | 5,37 | 32/0 | BLOCKED | BLOCKED |
| FR02-collision-neg | FR02 | fail_closed | — | — | — | — | **CERTIFIED** | NOT_APPLICABLE |

关键事实：

- seed2 两个模型的真实 L1 覆盖：`overwrite` 事件 `dyn_inst_seq=11054`、
  `reg_generation=2`、`containment_reason=phys_cell_rewritten`；
  FR01 的 `before=0x20 after=0xcffccffccffccffc`，
  FR02-c 的 `before=0x20 after=0xcffccffc`；`chain_end tick=2922408335`
  与 `stats.simTicks=2922408335` 相等。
- 其余 seed 的注入 cell 在 run 结束时既无 consumer 读，也无覆盖：
  `chain_end.terminal=not_consumed`，`ReadTracePoll` 持续报
  `reads_before_overwrite=0 overwritten=0`。日志显示这些 cell 是
  “Active, held by in-flight inst, no current rename-map entry”。
- seed2 的覆盖相是 `before_any_consumer_read`：事件流里没有
  `operand_read`，覆盖发生在任何 consumer 之前。
- 碰撞负例：`config.ini` 为 `bitsToChange=2`、`faultMask=32`
  （popcount=1），日志为
  `VecFaultFailClosed: cycle=10000 model=FR02 phys=34 lane_width=32
  lane_offset=-1 bits=2 explicit_mask=0x20
  reason=mask_popcount_mismatch (no injection; fault not consumed)`；
  `stats` 的 `numFaultsInjected=0`、`numBitFlips=0`。

### 7.3 证据哈希（由门禁计算）

| attempt / 文件 | sha256 |
|---|---|
| FR01-a/seed2 `prop_evt.txt.gz` | `f166c7535d095f9dc8394b4e3a5424f0720c75f9df1aa746e02f807b0f9f0650` |
| FR01-a/seed2 `fault_injections.log` | `d0c7cf8dd3f8e8f67a343f54b1c44c0b42bbaaf3c98a899f7994724bc9033975` |
| FR01-a/seed2 `config.ini` | `3e03571657a3d1b42970787115c41570a9b3474cbceb0e4114cb2c694ed6d8a8` |
| FR01-a/seed2 `stats.txt` | `e62275a1e4040e3193637c3ae360d79e97f0a794798101870e197857710cc98f` |
| FR02-c/seed2 `prop_evt.txt.gz` | `2429061e48ca81b9ccc73a4c967e9fa3851fd4358ce74cf9d562d6f8c6732ec5` |
| FR02-c/seed2 `fault_injections.log` | `7414dbd66b214aced778aeb326a922c579a11eb304953419c2c0da50877f19ed` |
| FR02-c/seed2 `config.ini` | `f31618f0ade648193d34bdba2a589e3c0317aac072021fd670d38f4170ca22d9` |
| FR02-c/seed2 `stats.txt` | `1a6d42b98c7992f4f8b10f5d39f619c675d5a56ba323debae4d7d5278bf98365` |
| FR02-collision-neg `prop_evt.txt.gz` | `f468adae0cb84d355d747017c8c2804055e679a67f361083f3fbc01d91862311` |
| FR02-collision-neg `fault_injections.log` | `fe2d2bb5795ff9e6afb6add2ea532b0d5cf8390c69c72efb9b350a5925d326fe` |
| FR02-collision-neg `config.ini` | `1655fb171db4f5c815b8f57eebac3f16ca21761e604ace105d39e8cfd4b5ed55` |
| FR02-collision-neg `stats.txt` | `ac8ab84961a0fbf932848e2d08b6c912fd9dbadf7f7f104ba5bc4ec4816f0b2e` |

### 7.4 测试

```bash
python3 -m pytest tests/test_fsu_fr01_fr02_gate.py -q
# 27 passed in 0.53s

python3 -m pytest tests/test_fsu_suite.py -q
# 38 passed in 0.50s
```

---

## 8. 缺口与所需 C++ 改动（仅建议，未落地）

以下每一条都对应真实代码位置；在这些改动完成前，相应的认证保持
`BLOCKED` 或 `SKIP`。

1. **写覆盖范围/宽度缺失** — `CHAOSPhysReg.cc:495-596` 只记录 dest 物理
   cell 和写后整值。建议在 `overwrite` 事件增加：
   - `write_bytes_mask`（16-bit，标记 128-bit 值中被该指令真实写到的
     byte）或 `dest_width_bits`；
   - `full_before_write`（写前 128-bit 值）；
   - 门禁据此验证
     `((full_before_write ^ full_after) & ~written_bytes) == 0`，且
     `(fault_mask & written_bytes) == fault_mask`。
   若无法可靠得到宽度，必须把该写标记为 `partial_coverage_unknown`，
   不得默认全覆盖。
2. **覆盖后读取不可见** — `CHAOSPhysReg.cc:412` 在 `overwritten` 后跳过
   L2 记录。建议至少增加一个精确计数并写入 `chain_end`：
   `post_overwrite_reads_total`、`post_overwrite_reads_of_uncovered_bits`
   （需与第 1 条配合）；或对覆盖后的读取发一条 `downstream_read` 事件
   （`post_overwrite=1`，有上限采样，计数精确）。
3. **squash 终局缺失** — `CHAOSPhysReg.cc:733-744` 的
   `finalizeVecTransient()` 只产生
   `committed/overwritten/exposed_unconsumed/not_consumed`。建议在
   `overwritten` 判断之前增加：
   ```cpp
   else if (vec_transient.l5.squashEvents() > 0)
       terminal = "squashed";
   ```
   并把 `squashed` 纳入终局词表。当前门禁已把“有 squash 事件但
   terminal=exposed_unconsumed”判为 FAIL。
4. **free/realloc 事件缺失** — 瞬态路径不发射 `generation_change`/
   `cell_free`。建议在 `observeVecTransient()` 或现有 readTrace 轮询中
   监视 `generationOf(target)`：世代变化时发 `generation_change`
   （`generation_old/new`，`cell_allocated`），并在 `chain_end` 增加
   `free_realloc` 终局分支。
5. **precision/字段语义缺失** — 瞬态事件固定
   `field=transient_bit_flip`，不写 `precision`；`carrier_state` 也没有
   `bit_in_lane`。建议：
   - 新增 manifest/参数 `physPrecision`（`fp32|fp64`），由 runner 从
     RunID 子模型传入；
   - 根/carrier/read/overwrite/chain_end 全部写 `precision` 与
     `field=sign|exp|mant`（由 `bit_in_lane` 与精度推导）以及
     `field_lo/field_hi`；
   - 在 `processFault()` 中选择时校验 FR01-a 必须 64-bit lane、
     FR01-b 必须 32-bit lane；不匹配 fail closed。当前 C++ 不做这个
     校验（门禁在事件侧判 FAIL）。
6. **event_id=0 歧义** — `notePropEvt` 第一个事件 id 为 0，导致根
   `event_id=0` 与 `install_event=0` 无法区分“指向根”与“缺失”。建议
   event id 从 1 开始，或在根/carrier 增加显式 `root_event_id`（允许为
   0 但另有 `root_event_valid=1`）。
7. **生命周期事件身份字段不齐** — `overwrite` 没有 `fault_mask`，
   `carrier_state` 没有 `bit_in_lane/full_before/full_after`。建议所有
   瞬态事件统一携带 `fault_mask/bit_indices/lane_mask/bit_in_lane`，
   防止后续事件与根漂移。
8. **连续写不可证** — 当前只在第一次真实写时发 `overwrite`。建议在瞬态
   存活期间对每次真实写发一条 `overwrite`（或 `write_observed`）事件，
   带 `before`（写前观察 lane）与 `after`，并设置上限；这样第 6 节第 3
   条才能从真实 run 认证。
9. **空白 chain_end** — `CHAOSPropagation.cc` 在 exit 时按 fault 发一条
   `corr=none`、`model_id=` 的 `chain_end`，与瞬态 `chain_end` 同
   `fault_id`。建议改名为独立 kind（如 `prop_chain_end`）或至少带
   `model_id`/`corr` 可区分。门禁目前以 `model_id` 过滤。

---

## 9. 建议的后续正式运行（未执行）

1. **先补 C++ 证据再跑正式 seed**：第 8 节第 1–4 条决定 `Masked` 与
   squash/free-realloc 能否认证。在这些改动完成前，正式 FR01/FR02 运行
   仍只能得到“证据一致的 overwritten/not_consumed”，无法给出 Masked。
2. **正式 3 seed**：`FSU-FR01-F0-W1`、`FSU-FR02-F0-W1` 各 3 个独立
   seed（当前 gate 是 5 个非正式 seed，不计数）。每个 seed 固定一个
   子模型，子模型轮换覆盖 FR01-a/b/c 与 FR02-a/b/c/d。
3. **必须补一个“consumer→commit”真实样本**：当前 W1 的所有 seed 都没有
   L2 读取。建议用更长的 W3/W5 workload 或把注入点放在 FP kernel 真正
   复用目标物理槽的窗口；需要真实 `operand_read + commit` 才能认证 L5
   链。若仍无 consumer，应如实记为 `not_consumed`，不得改 workload 后
   混算同一 RunID 的样本。
4. **squash 样本**：需要分支误预测路径上的 consumer；建议在固定
   `phys_target_idx` + 较长 workload 上探索，先做非正式 gate。
5. **free/realloc 样本**：需要第 8 节第 4 条的 C++ 事件；否则不跑，避免
   产生无法认证的“伪终局”。
6. **fail-closed 负例**：每个子模型至少 1 个碰撞/越界配置，作为
   precondition-rejected 的独立证据（不占正式 seed）。
7. 正式运行前确认 `runs/fsu` 的 runner/audit/index 流程与
   `fsu-formal-seed-runbook` 一致；本任务不执行。

---

## 10. 阻塞项（当前）

- **Masked 认证 BLOCKED**：缺少写覆盖范围与覆盖后读取可见性；最终
  hash 相同不能替代。
- **L5 认证无真实样本**：现有 gate 没有 commit/squash 事件。
- **free/realloc 终局无实现**：瞬态路径不发射释放/世代事件。
- **precision/字段语义无证据**：FR01-a/b、FR02-d 的 FP 字段层声明无法
  在事件流中验证。
- **FR01/FR02 F0 仍未正式运行**：RunID 状态仍是 Not run；本文不改变
  519/240 计数，也不新增 seed。
