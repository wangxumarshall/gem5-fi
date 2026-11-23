# MMU E2E V3 复现说明 (reproduction)

Round 0202c-close · `gem5-fi-mmu-when5x3` · 2026-11-18
所有命令在工作区根目录 `/home/sdc/gem5-fi-mmu-impl-v2` 下执行；无 git 操作。

## 1. 重生成因果 DAG / 统计 / 验收（本交付物已含结果，无需重跑实验）

```bash
cd /home/sdc/gem5-fi-mmu-impl-v2
# 1) 状态矩阵 + per_condition.json + control_map.json（读取现成 trace）
python3 campaign/finalize.py
# 2) analysis/*.csv（propagation_chains/chain_edges/chain_branches/completeness…）
python3 campaign/export_evidence.py
# 3) A01–A22 验收
python3 campaign/acceptance.py
# 4) 独立自检
python3 campaign/validate.py       # 期望 ALL CHECKS PASSED
# 5) 派生交付文件（V3）
python3 campaign/gen_v2_delivery.py
python3 campaign/gen_causal_dag.py
python3 campaign/gen_repair_evidence.py
python3 campaign/gen_report.py
python3 campaign/gen_issue_closure.py
python3 campaign/package_v2_delivery.py
```

## 2. 本轮代码修正要点

- `campaign/propagation.py`：新增 `writeback` 阶段；区分 rf_writeback /
  consumer(kind=consumer, consumer_of) / consumer 自己的 commit；恢复
  partial-entry→PTW→complete-entry 完整状态传递；`expected_stages` 按真实
  操作类型（Read/Write/Atomic/Execute）判定 consumer/writeback 适用性。
- `campaign/finalize.py`：`classify()` 增加 `REQUEST_PENDING_AT_ROI_END`；
  语义 oracle 比较。
- `campaign/control_map.py` + `campaign/oracle.py`：build-matched Control 解析 +
  语义 oracle（observed/result/signal，排除 pfn/va/pid 身份字段）。
- `campaign/acceptance.py`：A19 校验真实 ifu_response/ifu_decode/commit；
  A20 真实检查 build hash + 语义 oracle。
- `campaign/validate.py`：用 control_map + 语义 oracle 重推导终态，
  与 acceptance.json 的 TerminalStateSummary 交叉核对。

## 3. 定向补采（fb1b Control）

M05-C03/C04/C05 的 9 条 Fault 使用 fb1b 构建（MMU_CONSUMER_REUSE_CAP 界），
需要同构建 Control：

```bash
python3 campaign/run_fb1b_controls.py   # 写 runs/W5X3_RETRY2/CTRL2B-M05-C0{3,4,5}
```

之后重新执行第 1 节全部命令，control_map 自动纳入 CTRL2B 三控件。

## 4. 重新编译 gem5（观测二进制，可选）

```bash
cd /home/sdc/gem5-fi-mmu-impl-v2/CHAOS/gem5
scons -j64 build/ARM/gem5.opt
```

修改文件：`src/cpu/o3/CHAOSPropagation/{CHAOSPropagation.cc,.hh}`、
`src/cpu/o3/{fetch.cc,fetch.hh}`、`src/arch/arm/tlb.cc`（规格见
`work/0202c_instrumentation_spec.md` / `work/0202c_source_diff.md`）。

## 5. 工作负载反汇编

- `workloads/mmu_w5x3/w1[1-4].c`：W11–W14 源码。
- `workloads/mmu_w5x3/mmu_w1[1-4].dyn`：实际运行的动态二进制
  （`aarch64-linux-gnu-gcc -O2 -march=armv8-a+simd`，GCC 10.3.1）。
- `work/disasm/W13_consumer_disasm.md`：0x401c0c / 0x401bb4 / 0x401b50 反汇编。
- `campaign/rcs/M*.rcS`：嵌入 W11–W14 二进制的 rcS 脚本。