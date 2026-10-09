# OOO P1 暂停复盘报告（2026-10-09，用户指令暂停）

> 本报告为用户指令（"暂停任务，关闭任务，释放占用节点。汇报进展，撰写总结复盘报告"）的正式交付物。
> 全部陈述均有命令实证或仓库证据路径；未执行/未验证/冻结状态如实区分。

## 一、关停动作执行记录（全部已完成并复核）

| 动作 | 结果 | 证据 |
|---|---|---|
| 释放占用节点 | dkill 1773145（ooo-holder-any，cn22986 RUNNING，09/30 16:54 起占）+ dkill 1823682（ooo-holder-22986-r2，PENDING）→ 均 accepted；djob 复核 **0 个 ooo-holder 残留** | 本段命令输出 |
| 第三个占用作业 | 1830226 此前已不存在（LSU 并行会话暂停时释放，commit 860f50f1）——非本次动作 | djob grep 空 |
| 他人作业保护 | sve-sweep-*/sve-rerun-* 系列（其他会话）**未触碰** | djob 列表核对 |
| 取消定时任务 | session cron 9177bcc2（VPN 重连探测）已删除 | 本段工具输出 |
| U5 现场冻结 | /tmp/u5 五文件 + FREEZE-NOTES.md → runs/ooo-node/evidence/u5-step2-frozen/ | 目录 ls 实证 |
| 计划文件 | U5 Step-2 冻结注记（恢复点）+ U11 Step-5 补勾（commit 6505d9b1 提交时漏勾） | 本次提交 diff |

## 二、P1 总体进度（16 单元：U0–U12 + U1b/U1c/U10b）

| 单元 | 内容 | 状态 | ooo-exec commit | fi-ding |
|---|---|---|---|---|
| U0 | 设计文档桥接（03/09/d-bridge 入库） | ✅ 完成 | bde8ee94 | 早期中继 |
| U1 | ooo_models.py 57 模型映射 + 310 ITEM 校验 | ✅ 完成 | 4c56bce6 | 早期中继 |
| U1b | ooo_guard guard_pid 竞态移植（F-025） | ✅ 完成 | 254df4e3 | 早期中继 |
| U1c | login01 原生 py3.9 平台复活（F-008/F-011） | ✅ 完成 | ac9686c5 | 早期中继 |
| U2 | 流水时序族A：D07/R08/FD09/FR09 | ✅ 完成 | 107de592（收口 22417e69） | 3c9677f6 |
| U3 | 流水时序族B：B08/B09/FB08/FB09 | ✅ 完成 | d8ed7271（收口 8a0c7b50） | d5464fdc |
| U4 | 控制状态换值族：D06/FD05 | ✅ 完成 | 1927018e（收口 39d576fa） | c148f141 |
| **U5** | **拼接/配对族：FD07/FR08/FB06** | **⏸ 冻结** | Step-1 注记 + Step-2 推导 80%（本次冻结提交） | 本次中继 |
| U6 | D09 decode 卡死（stuck-at） | ⬜ 未开始 | — | — |
| U7 | 双翻分层 ×6（D02/R02/B02/FD02/FR02/FB02） | ⬜ 未开始 | — | — |
| U8 | 换值变体 ×6 | ⬜ 未开始 | — | — |
| U9 | ROB/IQ 面缺口 15 项（三态预判） | ⬜ 未开始 | — | — |
| U10 | L0–L5 观测链 + 守恒分类器 | ✅ 完成 | 9f4a6946 | 早期中继 |
| U10b | legacy 证据一致性修正 | ✅ 完成 | 3a142d0c | 早期中继 |
| U11 | campaign 引擎全链 + 中断恢复实测 | ✅ 完成 | 6505d9b1 | 早期中继 |
| U12 | P1 收口 | ⬜ 未开始 | — | — |

**账面：16 单元中 10 完成、1 冻结、5 未开始。**

## 三、模型覆盖账（暂停时点实测）

```
$ python3 tools/ooo_models.py --check
models: 57 | items_scanned: 310 | item_refs_resolved: 310 | unresolved: 0
impl_status: implemented=19 partial=34 unimplemented=4
OK: 静态表 ↔ 03 索引/详表 ↔ 09 逐模型判定 ↔ 清单 ITEM 三方一致
```

- 基线（P1 计划前）9 个：D01, FD01, FD03, FR01, FR05, FR07, R01, R05, R07
- U2 +4（D07/R08/FD09/FR09）→ 13；U3 +4（B08/B09/FB08/FB09）→ 17；U4 +2（D06/FD05）→ **19**
- 未实现 4 = D09, FB06, FD07, FR08（U5 覆盖后三、U6 覆盖 D09）；部分 34 由 U7/U8/U9 收口
- 09 审计总账 F-010 已知缺陷维持如实注记（总账仅列两态、逐模型表权威）

## 四、平台与资产状态（暂停时点，全部可用）

- **构建**：build 007（2026-10-09T08:17）SCONS RC=0 + BUILD COMPLETE，零新增告警；repo-root build/ARM/gem5.opt sha256 `4add2fcd…c65632`（state/gem5.opt.sha256）
- **回归锚**：dep_chain off golden `45737cc9a76c0dce`；本构建四 golden 复核在位：gap `2ec8c1e59f2808c5`、rob_fill int `19eab7d0de27237e`、rob_fill_fp `85085fd5686d173b`
- **campaign 引擎**：--selftest 24/24；实机 D01-F0-W6 engineering 8/8 COMPLETE（含 TERM→INTERRUPTED→resume 中断恢复全链演练）；OOO 轨首例架构级 Crash（and→orr bit29→Page table fault @0，rc=134）
- **观测链**：ooo_observe.py L0–L5 + classify 守恒分类器 26 断言 PASS；guard F-025 12/12
- **节点**：已释放（第一节）；恢复时经 runs/ooo-node/holder.sh 重新 dsub

## 五、本续接段技术工作明细

1. **U4 状态延续**：8/8 子模式真实激活（D06 a–e 全 Masked；FD05-b 两态 SDC+Masked；FD05-a Masked/FD05-c SDC on gap——Q 位 .4s→.2s）；rob_fill_fp 上 FD05-a/c 诚实 0 激活（libc 位点不执行，6 种子）→ gap 替代成功；证据 runs/ooo-node/evidence/u4-step4/（18 行汇总）。
2. **U5 Step-1 挂点注记**（源码实证）：
   - FD07→CHAOSDecode 扩展（U4 表驱动同构 + 值依赖 kind 体系 K_SEL/K_ROT/K_FRAG——selector 互换与 imm 旋转非恒定 xor）；app 指令面普查：EXT 121 位点、MOVI 9、DUP 6、UZP1 2；谓词设计点：c 臂纯源互换改变序号序列顺序→multiset 比较，a/b/d 保持序列比较。
   - FR08→DynInst::setRegOperand（void* 重载，dyn_inst.hh:1235）——实证为结果→PRF 唯一写路径；prevDestIdx→cpu->getReg 旧容器可达；A64 语义：S/D 标量写零扩展（zero）与 INS 读改写（preserve）并存可换值；ARM 无独立 FloatRegClass。
   - FB06→processFUCompletion（inst_queue.cc:842 放行信号、:989 创建）完成事件登记表配对交换（c）+ 同一 setRegOperand 钩子 dest tag 互换（b）；a=arch-alias-of-c（DynInst 无 robIdx、identity=seqNum 与 ROB 槽 1:1——恒等，如实注记，U3 FB08-b 先例）。
   - 工作负载修正：dep_chain_vec 全 FMLA 对 FD07 零合格位点→gap + rob_fill_fp 替代（golden 已复核）。
3. **U5 Step-2 推导（冻结于 80%）**：FD07 五族编码规则全部实证推导完毕——EXT（0xBFE08400/0x2E000000，imm=b[14:11]）、UZP+ZIP 合并行（0x9F209C00/0x0E001800）、TBL+TBX（0x9FE0E800/0x0E000000）、DUP（0x9FE0FC00/0x0E000400，imm5=宽度位+索引）、MOVI cmode-1110（0x9FF8FC00/0x0F00E400，abc=imm8[7:5]@b[18:16]、defgh=imm8[4:0]@b[9:5]、b[15:10]=111001 固定——本段最终解开）。恢复清单：runs/ooo-node/evidence/u5-step2-frozen/FREEZE-NOTES.md。

## 六、复盘

### 做得好（保持）
1. **GNU-as 闭环对表方法论**（U4 创立、U5 延续）：规则从不手抄手册——gcc 汇编→objdump 反推→闭环验证后才进 .cc。U4 70 规则 ALL-PASS（corpus=97 neg=22 pairs=56 mod_checks=213）；U5 五族掩码同样全实证。
2. **诚实纪律落地可审计**：0 激活如实记录并换负载复验（FD05-a/c rob_fill_fp 6 种子后才换 gap）；arch-alias 如实注记不造模式（FB06-a、FB08-b）；复选框漏勾两例（U10/U11）清点时补勾注明；U3 总账漏更由 U4 透明修复并在提交信息声明。
3. **中断恢复先行实测**：U11 Step-4 完成 TERM→心跳冻结→INTERRUPTED→resume 全链演练——本次暂停即一次真实中断，恢复路径已被证明。
4. **gem5 结构事实沉淀**（后续单元直接复用）：setRegOperand 唯一结果写路径；FUCompletion 放行语义（值在 executeInsts 才算）；ARM 标量 FP/向量统一容器；DynInst 无 robIdx。
5. **资源纪律**：只杀验证过所有权的作业（本次两 holder 均 djob -l 核对 holder.sh 路径后才 dkill）；他人 sve 作业零波及；F-012 教训固化为守则。

### 教训（改进）
1. **09 审计总账 F-010**：总账只列两态、34 个"部分"未入账——U3 收口时曾漏更。改进：每单元 Step-5 总账+逐模型表双核对（U4 起已执行）。
2. **提交时复选框漏勾**（U10/U11 两例）：改进：Step-6 收口显式含"勾选核对"。
3. **工作负载选型先普查**：rob_fill_fp 的 FD05-a/c 位点在未执行 libc 静态区（6 种子 0 激活才发现）。改进：U5 起选负载前先 objdump app 区指令面普查（本次已执行）。
4. **/home/share 配额**曾满致编译 EIO（U3 build003）：编译前查配额。
5. **通道 2 分钟期限 + ~4KB 命令上限**：长活 nohup 落盘 + 短周期轮询；长写入分块（本报告即分 3 块写入）。

## 七、剩余工作与恢复路径

1. **U5 恢复**（首选下一步）：完成 u5verify.py 闭环 ALL-PASS → 程序化生成 C++ VecStitchRule 表 → 三模型实现（挂点全在 Step-1 注记）→ build 008 → 两态验证（gap + rob_fill_fp）→ 22/57 → 提交+中继。恢复清单：runs/ooo-node/evidence/u5-step2-frozen/FREEZE-NOTES.md。
2. U6 D09 decode 卡死 → 未实现清零。
3. U7 双翻 ×6、U8 换值变体 ×6、U9 ROB/IQ 15 项三态预判（BLOCKED 项走 Decision Request）。
4. U12 P1 收口：确定性测试、重复 seed、守卫强制、G0-02 57 模型终态对账。
5. **HARD GATE**：任何 F4/F6 pilot 之前 chaos_trigger 事件级门禁（总方针）。
6. P2 探针负载（W3/W8/W9/W13 深验证）不在 P1 范围。

### 恢复操作提示（下次 session）
- 工作树 /home/share/suke/wangxu/gem5-fi-ooo（ooo-exec）；提交经 bundle 中继至 fi-ding（login01 无外网）
- SHA-256 门禁复核：Excel `b73b6304…7ae75` + 清单 `f520d42a…30c91`（不匹配即 BLOCKED）
- 重新占节点：dsub -s /home/share/suke/wangxu/gem5-fi-wx-paper/runs/ooo-node/holder.sh（#DSUB 头在脚本内）
- 编译：单实例 flock（-j16 全量 / -j126 增量），repo-root build/ARM/gem5.opt

## 八、证据索引

| 项 | 路径 |
|---|---|
| U5 冻结快照 | runs/ooo-node/evidence/u5-step2-frozen/（FREEZE-NOTES.md + 5 文件） |
| U4 证据 | runs/ooo-node/evidence/u4-step1..u4-step4/ |
| 实施计划（勾选即进度） | docs/superpowers/plans/2026-10-08-ooo-p1-injectors-observation-campaign.md |
| 覆盖审计 | docs/gem5-fi/ooo/09-v2-coverage-audit.md |
| 构建日志/哈希 | logs/gem5-build-007.out、state/gem5.opt.sha256 |
| 节点释放 | 本段 dkill×2 + djob 复核输出（会话记录） |
| 本报告 | docs/gem5-fi/ooo/10-p1-pause-retrospective.md |
