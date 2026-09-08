# AGENT_TASKS.md — 任务登记簿（方案附录 G.1）

> 单行格式：`<id> | depends=[<id>,…] | owner | status | assert_hint`
> status ∈ {done, in_progress, pending, deferred}。每完成一任务在此更新状态；
> deferred 项必须带原因与解锁条件。详细验证证据见 task_plan.md 与 git history。

## S0 — 基础与缺陷修复（已完成）

S0-00-复验卡           | depends=[]          | agent | done     | 附录 A"已有"项逐项复验通过（findings.md 2026-09-07 盘点）
S0-06-已知缺陷修复     | depends=[S0-00]     | agent | done     | 附录 D 的 D1–D10 修复（D1/D4/D5/D6 见 CHAOSArmTLB，D2 见 AddrPath）
S0-02-fs-checkpoint    | depends=[S0-00]     | agent | done     | FS 两阶段流水线 configs/se/fs_checkpoint.py（boot/inject）

## S1 — 注入器（18 个，全部 done）

S1-01-CHAOSPhysReg     | depends=[S0-06]     | agent | done     | phys/arch_commit/arch_frontend + F3 trigger + vecLane + read-trace
S1-02-CHAOSRenameMap   | depends=[S0-06]     | agent | done     | map_bitflip/f5_substitute/f4_field_stuck + read-trace（5bd791d7）
S1-03-CHAOSFreeList    | depends=[S0-06]     | agent | done     | mark_free/pop_wrong
S1-04-CHAOSROB         | depends=[S0-06]     | agent | done     | entry_bitflip/exc_suppress/spec_leak + read-trace（5bd791d7）
S1-05-CHAOSLSQFwd      | depends=[S0-06]     | agent | done     | 7case 转发破坏 + D2 修复
S1-1a-CHAOSCache字段   | depends=[S0-06]     | agent | done     | tag/valid/dirty/repl/coh 元数据注入（6c672323）
S1-2-CHAOSCache-victim | depends=[S1-1a]     | agent | done     | §5.8A writeback 载荷破坏（7f78b325）
S1-3-CHAOSArmTLB-pfn5  | depends=[S0-02]     | agent | done     | pfn_to_mapped_page F5 活页（50bdbc64）
S1-4-CHAOSArmTLB-itlb  | depends=[S1-3]      | agent | done     | iTLB 挂载 + parity_interleaved（ac3f977f）
S1-06-CHAOSArmSysReg   | depends=[S1-02]     | agent | done     | MRS 读路径白名单注入
S1-07-CHAOSPTW         | depends=[S0-02]     | agent | done     | 页表行走破坏 + ptwEcc
S1-08-CHAOSAddrPath    | depends=[S0-06]     | agent | done     | byte7 清零（core179 D2 复现）
S1-09-CHAOSMem         | depends=[S0-00]     | agent | done     | 主存位翻转 + ECC 逻辑
S1-10-CHAOSExec        | depends=[S0-00]     | agent | done     | 整数执行结果破坏
S1-11-CHAOSFPU         | depends=[S0-00]     | agent | done     | FSU 位段注入
S1-12-CHAOSIQ          | depends=[S0-06]     | agent | done     | src_ready_bitflip/tag_sub/wake_omit/wake_phase
S1-13-CHAOSBPU         | depends=[S0-00]     | agent | done     | 分支结果翻转
S1-14-CHAOSL1DForward  | depends=[S0-00]     | agent | done     | L1D 转发破坏（PCE）
S1-15-CHAOSExMon       | depends=[S0-00]     | agent | done     | 独占监视器（4332eb49）

## 收尾计划任务（task_plan.md，2026-09-07）

T1-1..T1-5-工具补全    | depends=[S1-*]      | agent | done     | Phase 1 全 5 任务（6c672323..5bd791d7）
T1-6-AGENT_TASKS       | depends=[]          | agent | done     | 本文件
T2-1..T2-4-kernel库    | depends=[T1-6]      | agent | done     | gemm/svd/fma/int 对照/indirect_jmp/struct/crc/movbe（feeba037..a276723f）
T3-1..T3-10-formal     | depends=[T2-*]      | agent | done     | §4.6 n=384 批量全 10 任务（853133cb/76ddb2c9/77207f09/2e315a3b/7bf51d7c/3e07f7d0/31db39fa/e4829acb/1b611bd4）
T4-1..T4-5-诊断引擎    | depends=[]          | agent | done     | §7 ESR/日志/七步法/反哺/CLI（71e3c1c4..bd9c41a8 + a83a9630）
T5-1..T5-6-建议产出    | depends=[T3-*]      | agent | done     | §8 CHAOSRAS/逃逸/优先级/DFT/TRM（f61abc0e..ac33041a）
T6-1..T6-3-论文收尾    | depends=[T3,T4,T5]  | agent | done     | 五贡献点+诚实边界+终态收尾（d2d111ab/d7646210/本提交）
T7-1..T7-7-环境门控    | depends=[]          | agent | done     | 全 7 项显式登记（2df8e9a5）

## Deferred（环境门控，显式不遗漏）

D-S4-系统级            | depends=[T3-*]      | agent | deferred | CHAOSCHI/NoC/HCCS ~20 补丁独立子项目；解锁：独立排期立项
D-S6-健康机复现        | depends=[T3-*]      | agent | deferred | 需第二台健康鲲鹏机；解锁：硬件到位
D-S7-实机校准          | depends=[T3-*]      | agent | deferred | RAS/EINJ 枚举需授权实机（E3/E4→升级）；解锁：实机授权
D-D10-G7-sanitizer     | depends=[]          | agent | deferred | SConstruct socket configure 环境受阻；解锁：CI 层解决
D-ExMon-多核           | depends=[]          | agent | deferred | stale_reservation 多核场景；解锁：多核 SE/FS 配置
D-Decode-P4            | depends=[]          | agent | skipped  | 方案 §5.11 明示"可跳过"
D-FS-O3-switch         | depends=[S0-02]     | agent | deferred | checkpoint restore 后切 O3（stdlib 无 clean switchCpus）；解锁：CPU 切换路径落地或 atomic-only 分类验证失败
