# 传播分析器修订说明（analyze_5x3_r2.py）

批号 `FPU_SIMD_5x3_FORMAL` · 生成 2026-11-23

替换第一轮 `analyze_5x3.py` 的“物理寄存器编号匹配”逻辑为**架构寄存器 +
writer 版本的因果追踪**。

---

## 1. 第一轮缺陷

- 仅按 `dest phys` 编号匹配所有后续 `rename.src phys`，**物理寄存器重用**会造成
  无关读取被误计为传播链消费者（同一 phys 编号在旧值释放后可分配给他用途）。
- 终态 `MASKED_OVERWRITE` 仅由 `raw0_diff` 与 `raw2_diff` 的简单组合判定，未验证
  真实消费关系，导致第一轮把“覆盖前已消费导出”的 C03 误判为 masked。

---

## 2. 修订后的因果追踪

1. **重放 rename 流**（`rename` 事件按 `seq` 升序），维护
   `arch_writer[(class, arch_index)] = writer_seq`。
2. 目标的目的架构寄存器（来自目标自身 `rename.dst`）的“版本”即 `writer_seq == tseq`。
3. 对每个 `seq > tseq` 的指令：
   - 若其 `src` 含某个 arch 且 `arch_writer[arch] == tseq` → **直接消费者**；
   - 若其 `dst` 含目标 dest arch 且 `arch_writer[arch] == tseq` → **覆盖**
     （该指令重命名目标目的寄存器，目标版本失效，后续读取不再算其消费者）。
4. 区分：
   - **直接消费者**（读目标版本）；
   - **间接消费者**（经直接消费者的目的寄存器转发；可通过递归追踪）；
   - **已被 squash 的消费者**（该消费者 `seq` 出现在 `squash` 事件集合）；
   - **物理寄存器被重用后的无关读取**（由 `arch_writer` 版本隔离，自动排除）。
5. **Store 关联**：消费者中 `op` 以 `str/stp/st1/...` 开头者记为 Store，关联其
   数据源 `seq`（地址/数据由 issue/writeback 事件值佐证）。

---

## 3. 终态分类（证据驱动）

```
INJECTION_MISS     : fault_inject 缺失 / applied < 1
PARTIAL_TRACE      : 缺 target_begin/target_end/writeback 等关键事件
SQUASHED           : 目标 seq 出现在 squash 事件集合
WRONG_RESULT       : 目标提交 且 软件输出 raw0/raw1/fpsr/nzcv 与 Control 存在差异
MASKED_OVERWRITE   : 目标提交 且 无软件输出差异 且 目标 dest arch 在首个消费者前被重命名
MASKED_NO_CONSUMER : 目标提交 且 无软件输出差异 且 无覆盖、无消费者
OTHER              : 其余（如错误进入架构态但以其他方式未达输出）
```

关键：`MASKED_OVERWRITE` 不再由 `raw0_diff`/`raw2_diff` 组合判定，而必须满足：
故障施加 + 错误值产生（`fault_inject` + `target_end` dest 错误值）+ 覆盖发生在
首个消费者之前（`overwritten=True`，`n_direct=0`）+ 软件输出与 Control 一致。

---

## 4. 输出

- 逐运行证据 `FPU_5x3_Propagation_Evidence_R2.csv`：字段含 fault_site/old/new、
  target_seq、target_committed/squashed、overwritten、n_direct、direct_seqs、
  n_stores、raw0_diff、raw0_diff_iter、terminal 等。
- 汇总 `FPU_5x3_Propagation_Summary_R2.json`。

脚本：`scripts/analyze_5x3_r2.py`
（`--runs runs_r2 --counts counts_r2`，默认即 r2 目录）。

---

## 5. 修订后终态结果（72 fault 运行）

| 终态 | 数量 | 对应 |
|---|---:|---|
| MASKED_OVERWRITE | 36 | C03 × 12 模型 × 3 时机 |
| WRONG_RESULT | 24 | C05 T01/T02 × 12 模型 |
| SQUASHED | 12 | C05 T03 × 12 模型 |
| INJECTION_MISS / PARTIAL_TRACE / OTHER | 0 | — |