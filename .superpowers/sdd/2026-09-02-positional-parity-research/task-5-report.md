# Task 5 Report — 原型实验：检出率矩阵（结构化故障 vs 位翻转 × 校验器 on/off）

**Status: DONE**
**Commit: c8ad61bc7**（c8ad61bc758737007527d14a57687688c7e7b4dc，branch `research/posparity-core179`，已推送 origin，162187632..c8ad61bc7）
**Task: 论文 §6.2 检出率矩阵实验 — 故障 {golden, byte_lane_skew, all_zero, bit_flip} × 校验器 {off, on} + panic 单点 + 5-seed 稳定性 + unipar 对抗数据臂**

## 交付物

- 新建 `fi_research/probes/run_posparity.sh`（实验主脚本，2×3 设计 + panic + unipar 对抗臂 + 自适应重试）
- 修改 `fi_research/probes/o3_chaos_smoke.py`（--max-tick 修复：Root 无 max_tick 参数，改为 `m5.simulate(max_tick)` 传参 — 与 o3_chaos_smoke.py 旧代码 `root.max_tick=` 会抛 `AttributeError: Invalid assignment for Class Root with parameter max_tick`，实测复现后修复，同 o3_chaos_fs.py 的既有修法）
- 原始数据 + 分析：`/tmp/posparity/results.md`（302 行；逐 arm 逐 seed 的 stats 抽取 + 分析总结 + 逃逸机制穷举验证）

## 实验设计（对 brief 的两处必要适配，均已写入脚本注释）

1. **注入量**：brief 模板未指定 `--max-faults`，runner 默认为 1（每次运行只注 1 个故障）——矩阵实验需要多事件，全部注入臂用 `--max-faults 0`（无限）+ prob 0.15（ptrskew）/0.20（unipar）+ 2000/5000 iters + **显式非零 seed**（seed 0 会从 std::random_device 取种，非确定）。
2. **stats 捕获（自适应 max-tick 重试）**：无限注入风暴下客户机几乎总在第一个栈溢出槽/退出路径 skew 时页表错误崩溃，gem5 abort **不 dump stats.txt**（Task 4 报告 Concern 5 的直接后果）。脚本 `run()`：崩溃于 tick T → 同 seed 确定性重跑，封顶 T-500000；若该窗口跨过了唯一（致命）注入（0 注入被捕获）→ 再紧窗口 T-100000 重试。模拟器确定性保证重跑注入序列一致。panic 臂与校验器 OFF 臂不封顶（abort/静默 SDC 本身就是实验结果）。

## 原始结果矩阵（5 seeds：42/1/2/3/4；ptrskew 2000 iters, prob 0.15）

| arm | seed | numTagged | numFaults (类型计数) | numMismatches | 检出率 | 客户机结局 |
|---|---|---|---|---|---|---|
| 1 golden+ON | 42/1/2/3/4 | 2029 ×5 | 0 | 0 ×5 | —（零误报） | 正常退出 fails=0 ×5 |
| 2 skew+OFF | 42 | — | 1 (skew) | —（无校验器） | — | **崩溃**（0x4b9000 页表错误，tick 53.2M） |
| | 1 | — | 1 | — | — | **崩溃**（0xb00000000000497d，tick 12.2M） |
| | 2 | — | 2 | — | — | **崩溃**（0x4986e00000000000，tick 17.5M） |
| | 3 | — | 2 | — | — | **崩溃**（0x497bb000000000，tick 12.2M） |
| | 4 | — | **452** | — | — | 正常退出但 **ptr_corrupt=308, fails=308（静默 SDC）** |
| 3 skew+ON | 42 | 15 | 1 (skew) | 1 | 100% | 封顶捕获（崩溃前） |
| | 1 | 8 | 1 | 1 | 100% | 紧窗口捕获 |
| | 2 | 16 | 1 | 1 | 100% | 封顶捕获 |
| | 3 | 7 | 1 | 1 | 100% | 封顶捕获 |
| | 4 | 102 | **14** | **10** | **71.4%（4 逃逸）** | 存活至 60M 封顶 |
| 4 all_zero+ON | 42 | 2370 | 362 | 362 | 100% | 正常退出 fails=310 |
| | 1 | 8 | 1 | 1 | 100% | 紧窗口捕获 |
| | 2 | 2343 | 329 | 329 | 100% | 正常退出 fails=289 |
| | 3 | 8 | 1 | 1 | 100% | 封顶捕获 |
| | 4 | 18 | 2 | 2 | 100% | 早退（exit 路径被腐蚀，2 注入后） |
| 5 bit_flip+ON | 42 | 2453 | 385 (bits) | 385 | 100% | 正常退出 fails=307 |
| | 1 | 2343 | 338 | 338 | 100% | 正常退出 fails=288 |
| | 2 | 15 | 2 | 2 | 100% | 封顶捕获 |
| | 3 | 2355 | 338 | 338 | 100% | 正常退出 fails=287 |
| | 4 | 15 | 1 | 1 | 100% | 封顶捕获 |
| 6 panic（k=1, seed 42） | 42 | —（abort 无 stats） | ≥1 | numMismatchesPanic≥1 | — | **fail-fast abort**：`panic: CHAOSPosParity: positional-parity mismatch ... (vaddr=0x496690)`，tick 9412000 |
| 7 unipar k=1 | 42/1/2/3/4 | 7/8/12/7/7 + mf1 29/8/32/29/29 | 1+1+2+1+1 + mf1 1×5 | 全部=注入数 | **11/11 = 100%**【已修正，见fix节：此行为旧-O2空洞构建的数据，作废；修正后为 39/39 buf字注入（k=1）】 | mf1 臂 intact=5000/5000 正常退出【同样作废：intact 计数循环无访存，空洞】 |
| 7 unipar k=4 | 同上 | 同上 | 11 | 11 | **11/11 = 100%**【已修正，见fix节：作废；修正后为 4/4 buf字注入（k=4）】 | 同上【作废】 |

**跨 seed 汇总（检出率 = numMismatches / 该臂故障数）：**

| 臂 | 检出/注入 | 率 | 理论预期 | 判定 |
|---|---|---|---|---|
| bit_flip（3 bit，单字节） | 1064/1064 | **100.00%** | 100%（奇权定理，0 逃逸；穷举 1,284,032 例） | **精确一致** — 每 seed numMismatches == numBitFlips 严格相等 |
| all_zero | 695/695 | **100.00%** | 1-2^-13（逃逸 iff 原 (W1,W2)=(0x40,0xC0)） | 一致（n=695 无一命中逃逸点） |
| byte_lane_skew（随机 k） | 14/18 | **77.8%** | ≈1-2^-10（均匀随机数据） | **偏差 — 见下，诚实归因** |
| golden（误报率） | 0/10145 | **0%** | 0 | 一致 |
| unipar 对抗数据 k=1 | 11/11 | 100% | 100%（该字不在 17-perm 逃逸集） | 一致【已修正，见fix节：作废；修正后 39/39】 |
| unipar 对抗数据 k=4（最弱情形） | 11/11 | 100% | 100%（同上） | 一致【已修正，见fix节：作废；修正后 4/4】 |

## 关键发现 1：bit_flip 是唯一硬 100% 臂，实测精确验证

n=1064（5 seeds 池化），numMismatches == numBitFlips 在**每个** seed 上严格相等（385=385, 338=338, 2=2, 338=338, 1=1）。奇权定理（w·2^b ≢ 0 mod 256 对任意 b，w 奇）的确定性预测在模拟器内逐事件成立。这是论文 §6.2 可引用的最强实证数字。

## 关键发现 2：skew 臂 4 次逃逸（77.8%）— 偏差的机理归因（不隐藏、不重掷）

4 次逃逸全部在 seed 4（10/14）。用 `--debug-flags=LSQUnit` 确定性重跑该 seed（14 注入、10 mismatch，与无 debug 运行一致——RNG 流不受 DPRINTF 影响），逃逸的 4 个注入是 vaddr 0x497fc0/0x498200/0x498800/0x498940，全部 FwdSize=8 堆地址。穷举计算（results.md 附录，可复现）：

- 探针合成金标值 `targets[j]=0x1000*(j+1)`（单非零字节字）：17/1792 (word,k) 对逃逸 = **0.95%**，为均匀随机数据（MC 2×10^5：0.50%，与理论 2^-5/7+…≈0.48% 一致）的**两倍**；集中于 ror_4（136 个单字节逃逸对中 56 个 k=4）；
- **targets[7]=0x8000 逃逸全部 7 个旋转**；targets[3]=0x4000、targets[11]=0xc000 逃逸 k∈{2,4,6}；
- seed 4 的 14 个注入 vaddr 的**指针值本身**（0x48fb78..0x498960，穷举核验）不逃逸任何旋转 —— 逃逸类是低熵合成常量，**不是 D1 指针链**。

结论：双加权聚合的逃逸概率是数据分布的函数；对高熵指针型数据（D1 链的真实形态）~0.5%/事件量级，对单非零字节常量 ~0.95% 且存在整字逃逸点。论文应表述为"概率性检测，逃逸率依赖数据熵"，而非恒定 2^-10。

## 关键发现 3：无校验器现状臂（arm 2）的两种 SDC 结局

- 4/5 seed：客户机**页表错误崩溃**（被 skew 的栈/退出路径值被解引用）——即 core 179 Oops 链的用户态复现；
- 1/5 seed（seed 4）：**静默存活**，452 次注入下 ptr_corrupt=308、fails=308，无任何告警 —— 这正是"无校验器 = SDC 静默逃逸"的实证对照组。

## 关键发现 4：panic fail-fast 实证

`--posparity-action panic`：第一个 mismatch 即 `panic: CHAOSPosParity: positional-parity mismatch on the store->load forwarding path (vaddr=0x496690) — fail-fast (paper §6.1/§6.2)`，tick 9412000 abort。§6.1 哲学的机械实证。

## 验证（全部真实命令，CLAUDE.md 三项要求）

1. **构建清洁**：本任务未改 gem5 C++（仅 .py/.sh）；提交前跑了增量 `scons build/ARM/gem5.opt -j32` 确认树为最新（EXIT=0，`grep -cE "warning:|error:"` = 0，仅 3 条既有 capstone/png/HDF5 主机环境告警；无 CHAOS 源码重编译——工作树与 HEAD 一致已 diff 核验）。
2. **功能验证**：实验本身就是（35+ 次 gem5.opt 真实运行，每次 1-3 分钟，全部落盘 /tmp/posparity/）；关键单元格的数字均引自 stats.txt 原文（results.md）。
3. **无关测试回归**：无验证器无注入的 ptrskew 500-iter 金标运行：`iters=500 ptr_corrupt=0 val_mismatch=0 fails=0`，正常退出，`grep -c posparity stats.txt` = 0 —— o3_chaos_smoke.py 的 max-tick 修改零附带破坏（不传该参数时行为不变）。

## Commit

```
c8ad61bc7 fi(posparity): 检出率矩阵实验 — 结构化故障 vs 位翻转 × 校验器开关
162187632 fi(posparity): 修复检测语义 — 双加权非交换聚合替代纯XOR/快照标签（位置常数相消缺陷）
```
2 files changed, 208 insertions(+), 3 deletions(-)。提交信息含 headline 数字（1064/1064、695/695、14/18+归因、panic tick）。无 Co-Authored-By。已推送 origin（162187632..c8ad61bc7）。

## Concerns

1. **skew 臂 n=18 偏小**（风暴下客户机早死 → 每格 1-14 事件）。77.8% 的总检出率中 4 逃逸全来自 seed 4 的合成常量类；对论文引用建议同时给出 (a) 总率 14/18，(b) 剔除低熵合成常量后的指针链表现（0 逃逸观测），(c) 穷举机理表。若 Task 7 需要更大 n：用 crash-free 探针（无解引用、栈槽最小化）或 per-seed 多窗口拼接。
2. **低熵字逃逸是设计属性不是 bug**：0x8000 逃逸所有旋转是数学事实（单字节字在双加权聚合下存在整字逃逸点）。若需覆盖此类数据，需第三权重向量或 mod 素数（如 251）聚合 —— 与 Task 4 修复轮 Concern 2 的建议一致，留作 future work。
3. **自适应封顶重试是方法学折衷**：崩溃后重跑依赖模拟器确定性（同 seed 同注入序列——已由 debug 运行 14/14 注入、10/10 mismatch 与普通运行一致佐证）。若未来 gem5 版本引入非确定性时序，此法失效。
4. **panic 臂无 stats**（abort 不 dump）——numMismatchesPanic 只能从 count 模式旁证；panic 文本本身携带证据（与 Task 4 Concern 5 相同）。
5. **runner `--fault bit_flip --lsq-fwd-bits 3` 语法怪癖**（无 --lsq-fault）已在脚本注释中记录；未改 CHAOSLSQFwd 接口（超范围）。
6. o3_chaos_smoke.py 旧代码 `root.max_tick = ...` 在本 gem5 版本会抛 AttributeError（实测复现）——说明该参数自加入以来从未被成功用过；本任务修复并验证（`cause=simulate() limit reached` + stats 落盘）。

## FIX ROUND 1（2026-09-03，评审 2 Critical + 1 Important 的修正）

**状态：DONE（本节）。原报告的上表数字凡被修正处均已标注；被推翻的结论明确划出。**

### Critical 1 — unipar 探针在 -O2 下被优化掉，arm 7 的 "11/11" 是空洞的（已修复 + 重测）

评审对 /tmp/unipar_rebuilt 的反汇编证明：-O2 下循环体（`buf[i&3]=v; x=buf[i&3]; intact+=(x==v)`）被 load/store 消除——main 里 0 条访存指令。我复核确认（旧二进制 main 循环 = `add/cmp/b.gt` 三条，无 str/ldr）："5000 次迭代" 的 numTagged=29 证明循环从未走转发路径；11 次注入全部落在 loader/glibc 前递（vaddr 0x7ffffeecd8/0x7ffffef580/0x496698）；0x0102040810204080 从未经过转发路径——原 "11/11=100%" 无效。

**修复（双重防御）**：
1. 源码：`fi_research/probes/unipar_probe.c` 改 `static volatile uint64_t buf[4];` + `sink = x;`（volatile 逼出 store+reload）。单 volatile 修复在 -O2 下也验证保留 str/ldr（0x40052c/0x400530）。
2. 脚本：`run_posparity.sh` unipar 改 `-O0` 编译 + objdump 门禁（main 无 str/ld 即 FATAL 退出）。
3. 反汇编验证（新二进制，-O0）：`4006c0: str x2,[x0,x1,lsl#3]`（store）、`4006d4: ldr x0,[x0,x1,lsl#3]`（reload）、`40070c: str x1,[x0]`（sink）——store+reload 真实存在。

**重测（关键改变：`--first-clock 53000` 跳过启动阶段，让风暴打在探针循环上；金标 run：numTagged=30015、numMismatches=0、intact=5000/5000，证明循环每迭代 ~6 次前递）**：

| k | seed | 检出/注入 | 对抗字（buf 0x491990..0x4919a8）注入/检出 | 逃逸事件 |
|---|---|---|---|---|
| 1 | 42/1/2/3/4 | 74/75, 80/81, 65/66, 61/61, 83/84 | 7/7, 7/7, 9/9, 8/8, 8/8 全检出 | 4 次，全部 FwdSize=4 退出路径栈字（0x7ffffef478/0x7ffffef480） |
| 4 | 42/1/2/3/4 | 7/9, 6/6, 2/4, 15/15, 18/18 | 0, 0, 0, 2/2, 2/2 全检出 | 风暴臂 4 次逃逸：s42:2（0x7ffffef480+0x7ffffef478，均 FwdSize=4 栈字）、s2:2（同两 vaddr，FwdSize=4 栈字）；另有 mf1 单点臂 5 个 seed 各 1 次 i=1021 循环计数器逃逸（ror_4 逃逸字，agg(ror_4(1021))==agg(1021)，与 intact=1021/5000 精确吻合）——两类分开计：风暴臂栈字逃逸 4 + mf1 臂计数器逃逸 5 = 9 次逃逸事件（原报告合并写作"6 次"是算错的，已更正） |

**对抗字真实检出（修正轮 2 更正）**：**buf 字（0x491990..0x4919a8）注入 43/43 = 100% 全检出（k=1: 39/39 = 7+7+9+8+8；k=4: 4/4 = 0+0+0+2+2），0 逃逸**；更口径（含 x 栈槽 0x7ffffefc88 等所有携带对抗值 0x0102040810204080 的前递，由 MISMATCH 快照聚合 (45,15)=agg(adv) 逐事件识别）：k=1 149/149、k=4 17/17，合计 **166/166 全检出**。与验证过的数学一致（ror_k(0x0102040810204080) 对全部 k=1..7 改变双聚合，不在任何逃逸超平面上）。所有逃逸都不是对抗值：k=1 的 4 次全是 FwdSize=4 退出路径栈字（LSQUnit debug 注入/MISMATCH vaddr 差分逐一核实，/tmp/posparity_dbg_ufc1*）。修正轮 1 写的 "19/19（13 k=1 + 6 k=4）" **算错了**（13/6 与任何工件集合都对不上），由本节数字取代；提交信息 c2b3b0f73 中的 19/19 无法改写，在此公开更正。

**对抗计数逐 seed 重构表（k=1，来自 /tmp/posparity/ufc_s*{_k1,_k1_r} 的 lsq_fwd_injections.log 与 /tmp/posparity_dbg_ufc1{,s1,s2,s3,s4}/lsqdbg.txt）：**

| seed | buf字注入/检出 | x槽(0x7ffffefc88)注入 | x槽检出 (45,15) | x槽检出 (47,61) | 全臂注入/检出 | 逃逸 |
|---|---|---|---|---|---|---|
| 42 | 7/7 | 25 | 22 | 3 | 75/74 | 1（0x7ffffef478 栈字） |
| 1 | 7/7 | 29 | 29 | 0 | 81/80 | 1（0x7ffffef480 栈字） |
| 2 | 9/9 | 24 | 16 | 8 | 66/65 | 1（0x7ffffef478 栈字） |
| 3 | 8/8 | 22 | 17 | 5 | 61/61 | 0 |
| 4 | 8/8 | 30 | 26 | 4 | 84/83 | 1（0x7ffffef478 栈字） |

**（k=4，来自 /tmp/posparity/ufc_s*{_k4,_k4_r} 与 /tmp/posparity_dbg_ufc4{,s1,s2,s3,s4}/lsqdbg.txt）：**

| seed | buf字注入/检出 | x槽注入 | x槽检出 (45,15) | x槽检出 (53,7) | 全臂注入/检出 | 逃逸 |
|---|---|---|---|---|---|---|
| 42 | 0/0 | 2 | 2 | 0 | 9/7 | 2（0x7ffffef480+0x7ffffef478 栈字） |
| 1 | 0/0 | 2 | 2 | 0 | 6/6 | 0 |
| 2 | 0/0 | 1 | 1 | 0 | 4/2 | 2（0x7ffffef480+0x7ffffef478 栈字） |
| 3 | 2/2 | 7 | 5 | 2 | 15/15 | 0 |
| 4 | 2/2 | 4 | 3 | 1 | 18/18 | 0 |

**口径说明（三级，全部可 grep 复算）**：
1. **buf 字注入（主口径）**：43/43 = k=1 39（7+7+9+8+8）+ k=4 4（0+0+0+2+2），全检出、0 逃逸。来自 lsq_fwd_injections.log 的 vaddr∈{0x491990..0x4919a8} 计数。
2. **对抗值本体前递（包容口径）**：快照聚合 (45,15)=agg(adv) 的全部前递 = **166/166**（k=1 149 = 39 buf + 110 x槽；k=4 17 = 4 buf + 13 x槽），全检出、0 逃逸。来自 10 个 lsqdbg.txt 的 `grep -c 'snapshot 45, W2: [0-9]* vs snapshot 15'`。**评审的 145/145 无法从工件重构**（多种口径求和均不得 145；评审时 10 格中只有 5 格有 lsqdbg 取证，应为部分取证下的估计；补齐全部 10 格逐事件落盘后精确值为 166——以 166 为准，本节公开说明）。
3. **对抗值旋转级联（附加，不计入上两口径）**：x 槽另有 23 次前递的原始值是 ror_1(adv)（快照 (47,61)，k=1 共 20 次 = 3+0+8+5+4）或 ror_4(adv)（快照 (53,7)，k=4 共 3 次 = 0+0+0+2+1）——这些是同迭代 buf 前递被 skew 后 x 携带旋转值的级联前递，被再次注入且全部检出（23/23）。

### Critical 2 — 逃逸归因错误（已重写）

原报告把 seed-4 的 4 次逃逸归因于"探针合成金标值 targets[j]=0x1000*(j+1)"。评审取证反驳，我逐条复核确认：
- 14 次注入的 load PC 全在 0x444538/0x44419c = `_dl_find_object_init`/`_dlfo_sort_mappings`（**loader 启动排序阶段**，非栈溢出）；探针主循环（0x4005e4-0x40061c）在 60M 窗口内从未执行；
- 10 个检出事件的快照聚合精确解码为：**0x48c3c8（RW 段起点）、0x400000（RE 段起点）、2（映射数）——loader _dlfo 映射数组字**，不是 targets[j]；
- 我的"指针值不逃逸任何旋转"检查算的是注入 **vaddr** 的聚合而不是被转发的**内容**（范畴错误）。

**修正后的归因（写入 results.md）**：逃逸是 loader 启动阶段的低熵映射数组字——强推断（未逐字记录逃逸字）：0x400000 在偶 k 下（可证逃逸 ror_2/4/6）和/或 NULL 字段（逃逸全部 k）。正确的类级结论（数值不变、机制更正）：**低熵字（单非零字节常量如 0x400000、NULL）以 ~0.95%/（字,k）对逃逸——均匀随机率（MC 0.46-0.50%）的两倍，集中于偶 k/ror_4**。已推送的提交信息（c8ad61bc7）中的 targets[j] 归因无法改写，在 results.md 附录 [F] 和本节公开更正。

### Important 1 — skew-ON 臂未覆盖 D1 指针链（已补测，检出率大幅上修）

seed-4 skew+ON 重跑 `--max-tick 175000000`（原 60M 截断在探针循环之前）：
```
[smoke] Exiting @ tick 173678500 | iters=2000 ptr_corrupt=308 val_mismatch=0 fails=308
numTagged=2884 numFaultsInjected=452 numStructuralByteLaneSkew=452 numMismatches=434
```
**相位拆分**（同 seed 确定性 debug 重跑 /tmp/posparity_dbg_s4_175/lsqdbg.txt，46 万行）：
- 启动/loader 相（cycle<313287）：67/84 检出，17 逃逸（全部 loader brk 堆字 0x497fc0..0x49bde0）；
- **D1 探针循环相（cycle≥313287）：367/368 检出；D1 链本体（golden_ptr 溢出 [sp,#104]=0x7ffffefca8，load PC 0x4005fc）367/367 = 100.0%**；唯一逃逸是退出相 printf 缓冲字（0x7ffffef9b0，PC 0x422e3c），不属于 D1 链。
- 367 个 D1 检出的快照聚合全部 = (59,97) = agg(golden_ptr=0x4b1c30=&targets[146])，且观测到的 7 个 (W1,W2) 对恰为 agg(ror_k(golden_ptr)) k=1..7 —— 逐事件位级证实：被转发的是 D1 指针，其**每一个旋转都被捕获**；golden_ptr 不逃逸任何旋转（穷举核验）。

**结论修正（重大）**：skew 臂总检出率从 77.8%（14/18，60M 窗口）上修为 **96.0%（434/452，seed-4 全程）**，且 **D1 指针链本体 100%（367/367）**——论文 §6.2 的引用口径应为："对高熵指针型数据（D1 链真实形态）确定性检出（367/367，含全部 7 个旋转）；总检出率 96.0%， shortfall 全部来自低熵 loader 启动字"。原报告的"77.8% + 指针链 0 观测"口径作废。

### Minor 修复

- `--max-tick` help text 去掉错误的 "Root.max_tick"（改为 "passed to m5.simulate()"）；
- results.md 行数更正为 320（原文写 302；修正轮后 495 行；修正轮 2 后现 546 行，含附录）；
- 崩溃位点措辞更正：arm-2 的崩溃是 **loader 排序/启动阶段**值被 skew（非"栈溢出"）；arm-2 的 4 个崩溃 vaddr（0x4b9000 等）与 brk 堆布局一致；
- 报告引用取证目录：/tmp/posparity_dbg_s4/（60M 窗口 debug 日志）、/tmp/posparity_dbg_s4_175/（175M 全程）、/tmp/posparity_dbg_ufc1*/ufc4（unipar 逃逸差分）、/tmp/posparity/ufc_*（unipar 重测原始 stats）。

### 修正轮验证（CLAUDE.md 三项）

1. **构建清洁**：本修正轮未改 gem5 C++（.c/.sh/.py）；`python3 -m py_compile o3_chaos_smoke.py` = OK，`bash -n run_posparity.sh` = OK。
2. **功能验证**：上文全部数字引自真实运行的 stats.txt / lsqdbg.txt（unipar 重测 20+ 次运行、175M 全程 1 次 + debug 重跑 1 次、LSQUnit debug 差分 5 次）；探针 volatile 化以反汇编逐指令验证。
3. **无关回归**：修正探针金标运行（无注入）numMismatches=0、intact=5000/5000、正常退出——校验器零误报在 30015 次前递上复确认；ptrskew 各臂数据未受影响（本轮未重跑未改动的臂）。

### 修正轮提交

`fi(posparity): 修正检出矩阵 — unipar探针volatile化、逃逸归因更正、D1链skew统计补测`（branch research/posparity-core179；unipar_probe.c + run_posparity.sh + o3_chaos_smoke.py help text + 本报告；results.md 在 /tmp 为原始数据不入库）。

## FIX ROUND 2（2026-09-03晚，复评确认原3项已修但发现 2 个新 Important）

**状态：DONE（本节）。复评的 Important A/B + 4 个 Minor 全部修复。**

### Important A — objdump 门不禁门（已修复：运行时门为承重门 + 静态配对门）

评审实证：修正轮 1 的正则 `\b(st|ld)[rp]?\b` 会匹配 `stp`/`ldp`（帧序言）和 argv 的 `ldr`，旧 -O2 空洞二进制**通过**该门（评审自己构建旧源码跑了门管线：GATE-PASSES）——FATAL 分支对任何现实回归不可达，是虚假保证。我复核确认（本次重新构建旧源码验证，见下）。

**修复（双门，运行时门承重）**：

1. **运行时门（承重）**：`run_posparity.sh` arm 7 在注入运行前先跑金标 unipar 运行（`--no-fi`），要求 `numTagged >= iters`——volatile+(-O0) 循环每迭代前递 ~6 次（金标实测 5000 iters → numTagged=30015），`numTagged >= iters` 是循环确实走转发路径的可靠下界；空洞 -O2 构建给出 numTagged≈29-31 ≪ iters，正是该门捕获的失效模式。不满足则 FATAL 退出、整个 arm 7 中止。
2. **静态配对门（辅助）**：替换为寄存器索引的 store+reload 配对检查——main 中必须存在 `str xN,[xM,xK(,lsl #3)]` 且存在对应 `ldr`（buf[i&3] 寻址模式）。旧二进制 0 匹配（FAIL），新二进制各 1 匹配（PASS）。

**门验证（真实命令输出，/tmp/gate_verify_r2.sh）**：

```
[good(-O0+volatile)] static pair gate: str=1 ldr=1 -> PASS
[good(-O0+volatile)] OLD broken regex: GATE-PASSES (false assurance)
[old(-O2,vacuous)] static pair gate: str=0 ldr=0 -> FAIL
[old(-O2,vacuous)] OLD broken regex: GATE-PASSES (false assurance)   <- 评审发现的缺陷复现
[good(-O0+volatile), 5000 iters] runtime gate PASSED: numTagged=30015 >= iters=5000
[old(-O2,vacuous), 200 iters] RUNTIME GATE FAILED: numTagged=31 < iters=200   <- 门拒绝旧二进制
```

- 旧二进制构建：`git show c8ad61bc7:fi_research/probes/unipar_probe.c > /tmp/unipar_oldsrc_r2.c && gcc -static -O2 -o /tmp/unipar_old_r2`，反汇编确认 main 循环体 = `add/cmp/b.gt` 三条、零访存指令（`stp x29,x30` 帧序言 + `ldr x0,[x2,#8]` argv 读取是仅有的 st/ld 类指令——正是旧正则误匹配源）。
- 金标运行（好二进制，与脚本门同一命令）：`Exiting @ tick 73940500 cause=exiting with last active thread context | intact=5000/5000 | numTagged=30015 numMismatches=0`（/tmp/posparity/gate_good_golden{,.out}）。
- 旧二进制金标运行（200 iters 低量快跑）：`Exiting @ tick 26478500 | intact=200/200 | numTagged=31 numMismatches=0`（/tmp/posparity/gate_old_o2{,.out}）——31 < 200，门 FAIL。注意 intact=200/200 本身就是空洞的（无访存的循环照样计数"完好"），恰好证明只有 numTagged 能承重。

### Important B — "19/19 (13 k=1 + 6 k=4)" 算术错误、不可重构（已修复：43/43 为主口径 + 166/166 全对抗值口径，逐 seed 重构表补齐）

评审从原始注入日志求和：k=1 buf 字注入 39（7+7+9+8+8）、k=4 为 4（0+0+0+2+2）= 43/43 全检出；计入全部对抗值前递（含 x 栈槽 0x7ffffefc88）评审估为 145/145。13/6=19 与任何工件集合都对不上。我复核：buf 字 43/43 与评审一致；**全对抗值口径逐事件数出 166/166（k=1: 149、k=4: 17）而非 145**——评审时 10 个单元格只有 5 个有 lsqdbg 取证（s3k1 与 k=4 的 s1/s2/s3/s4 缺），145 应是部分取证下的估计；本轮补齐全部 5 格 debug 重跑后逐事件精确值为 166。识别方法：MISMATCH 快照聚合 (45,15)=agg(0x0102040810204080) 逐事件匹配（buf 字与 x 栈槽都携带对抗值本体）。三级口径（buf 字 43/43 → 对抗值本体 166/166 → 旋转级联 23/23 附加）都已写入（见上文修正轮 1 节的两张逐 seed 重构表与口径说明）。

**修复内容**：
- 本报告：主口径改为 **43/43 buf 字注入（k=1: 39/39，k=4: 4/4）**，更广口径 **166/166 全对抗值前递（k=1: 149/149，k=4: 17/17）**；补齐逐 seed 重构表（每格数字来自对应 seed 的 lsq_fwd_injections.log 与 lsqdbg.txt，可 `grep -c` 复算）；明确标注修正轮 1 的 19/19（13+6）算错、由本节取代，提交信息 c2b3b0f73 中的 19/19 无法改写、公开更正。
- results.md：[C]/[F] 与 arm-7 汇总同步更正（见下）。
- **为可重构性补采的取证**：5 个新 debug 单元格（/tmp/posparity_dbg_ufc1s3、ufc4s1、ufc4s2、ufc4s3、ufc4s4；--debug-flags=LSQUnit 同 seed 确定性重跑，注入/检出计数与无 debug 运行逐一相符：61/61、6/6、4/2、15/15、18/18——前四格 stats.txt 落盘核对；ufc4s4 的 guest 在 tick 31876000 崩溃（stats 未 dump），其 18 注入/18 检出计数取自 lsqdbg.txt 逐行 grep，与封顶运行 ufc_s4_k4_r 的 stats 完全一致）——修正轮 1 只有 s42k1/s1k1/s2k1/s4k1/s42k4 五格有 lsqdbg，s3k1 与 k=4 其余 seed 的对抗值前递计数原来只能靠 vaddr 推断，现已逐事件落盘。

### Minor 修复（本轮 4 项）

1. `run_posparity.sh` arm-7 协议与实际修正单元格对齐：`UBASE_ARGS` 改 `--first-clock 53000`（原 2000），prob 0.20 显式变量 `UPROB_UNIPAR`，mf1 臂 prob 1.0 + `--first-clock 54000`（与 ufx_* 实跑命令一致）；注释说明原 60M 默认 cap + first-clock 2000 协议只打到 loader 相事件（已废止，ptrskew 臂不受影响）。
2. 报告 k=4 逃逸行更正为可重构口径：风暴臂 4 次逃逸（s42:2 + s2:2，全为 FwdSize=4 栈字 0x7ffffef480/0x7ffffef478）与 mf1 臂 5 次 i=1021 计数器逃逸**分开列**（合计 9 次逃逸事件；修正轮 1 合并写作"6 次"是把两类混算且漏计）。
3. 原始结果矩阵的旧 11/11 行加就地标注"【已修正，见fix节】"。
4. results.md [F] 显式记录提交信息更正：19/19→43/43（buf 字主口径）。

### 修正轮 2 验证（CLAUDE.md 三项）

1. **构建清洁**：本轮未改 gem5 C++（.sh/.md/results.md）；`bash -n run_posparity.sh` = SYNTAX-OK；静态门正则以真实 objdump 输出验证（好二进制 str/ldr 各 1 匹配，旧二进制 0 匹配——注意 objdump 输出逗号后有空格 `[x0, x1, lsl #3]`，正则已按真实格式写）。
2. **功能验证**：门验证 2 次真实 gem5 运行（金标好二进制 numTagged=30015≥5000 PASS；旧 -O2 二进制 200 iters numTagged=31<200 FAIL，/tmp/posparity/gate_good_golden{,.out}、gate_old_o2{,.out}）+ 可重构性补采 5 次 debug 运行（数字与原运行严格一致）+ 全部计数引自 lsq_fwd_injections.log/lsqdbg.txt/stats.txt 原文（grep -c 可复算）。
3. **无关回归**：金标好二进制运行本身即无关回归（numMismatches=0，零误报复确认）；ptrskew 臂未改动未重跑（u42_golden gate 用 --no-fi 无注入，与 arm 1-6 零交集）。

### 修正轮 2 提交

`fi(posparity): 修正arm7门控与对抗数据计数 — 运行时门替代假objdump门、19/19更正为43/43`（branch research/posparity-core179；run_posparity.sh + 本报告 + /tmp/posparity/results.md）。
