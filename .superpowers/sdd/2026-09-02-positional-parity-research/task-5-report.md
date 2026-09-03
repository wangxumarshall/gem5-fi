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
| 7 unipar k=1 | 42/1/2/3/4 | 7/8/12/7/7 + mf1 29/8/32/29/29 | 1+1+2+1+1 + mf1 1×5 | 全部=注入数 | **11/11 = 100%** | mf1 臂 intact=5000/5000 正常退出 |
| 7 unipar k=4 | 同上 | 同上 | 11 | 11 | **11/11 = 100%** | 同上 |

**跨 seed 汇总（检出率 = numMismatches / 该臂故障数）：**

| 臂 | 检出/注入 | 率 | 理论预期 | 判定 |
|---|---|---|---|---|
| bit_flip（3 bit，单字节） | 1064/1064 | **100.00%** | 100%（奇权定理，0 逃逸；穷举 1,284,032 例） | **精确一致** — 每 seed numMismatches == numBitFlips 严格相等 |
| all_zero | 695/695 | **100.00%** | 1-2^-13（逃逸 iff 原 (W1,W2)=(0x40,0xC0)） | 一致（n=695 无一命中逃逸点） |
| byte_lane_skew（随机 k） | 14/18 | **77.8%** | ≈1-2^-10（均匀随机数据） | **偏差 — 见下，诚实归因** |
| golden（误报率） | 0/10145 | **0%** | 0 | 一致 |
| unipar 对抗数据 k=1 | 11/11 | 100% | 100%（该字不在 17-perm 逃逸集） | 一致 |
| unipar 对抗数据 k=4（最弱情形） | 11/11 | 100% | 100%（同上） | 一致 |

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
| 4 | 42/1/2/3/4 | 7/9, 6/6, 2/4, 15/15, 18/18 | 0, 0, 0, 2/2, 2/2 全检出 | 6 次：FwdSize=4 栈字 + 循环计数器 i=1021（ror_4 逃逸字，agg(ror_4(1021))==agg(1021)，与 intact=1021/5000 精确吻合） |

**对抗字真实检出：19/19 = 100%（13 次 k=1 + 6 次 k=4），0 逃逸**——与验证过的数学一致（ror_k(0x0102040810204080) 对全部 k=1..7 改变双聚合，不在任何逃逸超平面上）。所有逃逸都不是对抗字：k=1 的 4 次全是 FwdSize=4 退出路径栈字（LSQUnit debug 注入/MISMATCH vaddr 差分逐一核实，/tmp/posparity_dbg_ufc1*）。

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
- results.md 行数更正为 320（原文写 302；修正轮后现 495 行，含附录）；
- 崩溃位点措辞更正：arm-2 的崩溃是 **loader 排序/启动阶段**值被 skew（非"栈溢出"）；arm-2 的 4 个崩溃 vaddr（0x4b9000 等）与 brk 堆布局一致；
- 报告引用取证目录：/tmp/posparity_dbg_s4/（60M 窗口 debug 日志）、/tmp/posparity_dbg_s4_175/（175M 全程）、/tmp/posparity_dbg_ufc1*/ufc4（unipar 逃逸差分）、/tmp/posparity/ufc_*（unipar 重测原始 stats）。

### 修正轮验证（CLAUDE.md 三项）

1. **构建清洁**：本修正轮未改 gem5 C++（.c/.sh/.py）；`python3 -m py_compile o3_chaos_smoke.py` = OK，`bash -n run_posparity.sh` = OK。
2. **功能验证**：上文全部数字引自真实运行的 stats.txt / lsqdbg.txt（unipar 重测 20+ 次运行、175M 全程 1 次 + debug 重跑 1 次、LSQUnit debug 差分 5 次）；探针 volatile 化以反汇编逐指令验证。
3. **无关回归**：修正探针金标运行（无注入）numMismatches=0、intact=5000/5000、正常退出——校验器零误报在 30015 次前递上复确认；ptrskew 各臂数据未受影响（本轮未重跑未改动的臂）。

### 修正轮提交

`fi(posparity): 修正检出矩阵 — unipar探针volatile化、逃逸归因更正、D1链skew统计补测`（branch research/posparity-core179；unipar_probe.c + run_posparity.sh + o3_chaos_smoke.py help text + 本报告；results.md 在 /tmp 为原始数据不入库）。
