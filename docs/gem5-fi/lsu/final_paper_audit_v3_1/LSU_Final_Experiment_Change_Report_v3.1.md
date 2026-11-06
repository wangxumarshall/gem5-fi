# LSU最终方案 v3.1 变更报告

**更新文件**：`docs/gem5-fi/lsu/final_paper_audit_v3_1/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.1.xlsx`
**SHA256**：`79b981d66c0053fd4196f4eba436499a2ba9adc55ce9f8c135956c1ff43a5310`
**时间**：2026-11-06

## 修订
1. A01/A03：确认当前 `a01_bit`/`a03_stuck` 为 POST hook；`pushRequest` PRE 模式未实现，标 NEEDS_HOOK。
2. LQ04：`clear()` 调用 `freeLSQEntry`，提前失效资源安全未证明，标 NEEDS_USER_DECISION。
3. RP01：reschedule 与 replayMemInst 双路径；单点抑制未证明，标 NEEDS_HOOK/BLOCKED。
4. 六个专用工作负载：实际 C 源码 + 静态 aarch64 二进制 + 运行脚本 + oracle + SHA256；gem5 SE 无故障基线 exit 0。
5. W1/W4：当前 gem5 Commit/配置/二进制重跑基线，exit 0，输出匹配 golden。
6. Excel Workload Audit 按真实表头重写并二次读取校验。
7. Trace/终态改为四维：RunStatus/FaultActivationStatus/TerminalState/TraceCompleteness。
8. 12模型/60样本/原始ID/Seed不变；未修改gem5源码/未编译gem5/未正式注入。
