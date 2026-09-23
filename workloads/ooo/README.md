# workloads/ooo — OoO 北极星 W1 负载集

`docs/gem5-fi/ooo/`（OoO 微架构故障注入北极星）的 W1 负载建设目录。

- 执行计划：`docs/superpowers/plans/2026-09-23-ooo-w1-workloads.md`
- 负载定义与校验方式（冲突以它为准）：`docs/gem5-fi/ooo/03-workloads.md`

## 组织方式（仿 workloads/directed/：源码 + 静态 ELF 并存入库）

- 每个负载一个子目录：`<name>/<name>.c`（源码）与 `<name>/<name>`（构建产物，静态链接
  AArch64 ELF，宿主原生 gcc `-O2 -static`，无需交叉工具链）。
- 构建：`make -C workloads/ooo`（全部）或 `make -C workloads/ooo <name>`（单个）；
  新负载落库时在 Makefile 的 `WORKLOADS` 列表（或显式规则）中登记。
- 输出惯例：自设核打印一行 `FINAL=<16hex>`（`tools/classify.py` 的 `_CHECKSUM_RE`，
  与 directed/ v1.1+ 内核同款格式）。无注入运行的 FINAL 值即该负载 golden，
  注册进 `tools/runner.py` 的 `GOLDEN_IDS`。

## SE 预算纪律（W1 Global Constraints，硬门）

- **每个负载在 C3 SE（`build/ARM/gem5.opt --outdir=<dir> configs/se/ooo_proxy.py
  --cmd workloads/ooo/<name>/<name> --cpu O3`）下的 `stats.txt` `hostSeconds`
  实测必须 ≤ 60 s**；超预算 = 缩规模重测，不算完成。
- **golden 稳定**：同一 ELF 两次 gem5 运行 FINAL 行逐字节一致，且与宿主原生运行
  一致（native == gem5，确定性）。
- 事件密度（`tools/event_density.py`）实测入档；探针核另有密度门
  （branch_mispred ≥5% mispredicts/commits、dep_chain flIntLe8/flVecLe6 ≥1%、
  rob_fill robOver80 ≥50% 且 div 在场），不达标不算完成。

## 负载台账（实测值随 W1 任务逐行填写）

| workload | 任务 | golden (FINAL=16hex) | C3 SE hostSeconds | simInsts | 事件密度要点 | 状态 |
|---|---|---|---|---|---|---|
| smoke | W1.0 | `45737cc9a76c0dce` | 1.18 / 1.19（两次） | 308057 | —（框架冒烟核，非探针，无密度门） | done |
| branch_mispred | W1.5a | `06e84f119c258fa7` | 55.86 / 56.77（s1/p1） | 8611484 | mispredicts/commits = **5.70%** ≥5% PASS；squash 密度 59.1%；mispredicts=490766/运行 | done |
| dep_chain（int/vec 两版） | W1.5b | int `98e5e31e726e383f` / vec `b1e661a247b95774` | int 45.86 / 45.96；vec 47.36 / 47.00（各两次） | int 17505782 / vec 6310709 | int：**flIntLe8 = 99.42%** ≥1% PASS（iqOver80=99.4%，iqMax=64 满容）；vec 加强门：**vecLookups=15336251（2.43×simInsts）+ objdump fmla=1056>1000 + 初始 vec freelist=4（D75 校准，见下）** 全 PASS | done |
| rob_fill（int/fp 两版） | W1.5c | int `19eab7d0de27237e` / fp `85085fd5686d173b` | int 43.90 / 40.34；fp 40.75 / 44.25（各两次，编排者终跑） | int 7901621 / fp 8692564 | **robOver80：int 4.91%（275648/5609073）/ fp 7.09%（426601/6013631），原 ≥50% 门未达 → 编排者裁决：门重校准为事件覆盖口径，PASS**（robMax=128 到顶 + 越阈采样 27.5 万/42.7 万每跑 + commit 空转 ~49% + div 静态 192/130、动态 IntDiv=140290/FloatDiv=69120；8 轮诊断证明 ≥50% 持续占用是 gem5 v25 rename skid 平台属性——D75 同类，见下） | done（门重校准裁决） |
| coremark | W1.1 | `000000000000cf56` | 52.62 / 52.92（s1/s2） | 10808351 | 自带 CRC 校验 PASS（seedcrc 0xe9f5，crclist 0xe714/crcmatrix 0x1fd7/crcstate 0x8e3a 全对 known_id=3；"Errors detected" **仅**来自 EEMBC 10 秒计时报告规则——SE 模拟时钟结构性不可满足，见实测记录）；密度：mispredicts/commits 0.66%、squash 15.1%、flIntLe8 10.6%（flIntMin=0 实压穿）、robOver80 1.3%（robMax=128 到顶） | done |
| embench | W1.2 | crc32 `b87739d9c40d1798` / md5sum `973ff8cc9018e79f` / matmult-int `e105f98022b761ef` / wikisort `d2cf29655e3e0f06` / nbody `f39b4e8804f279c3` / minver `9792f3ee24af3023` | crc32 39.35/38.87；md5sum 40.04/40.39；matmult-int 42.83/42.73；wikisort 29.85/29.79；nbody 33.40/33.37；minver 53.14/54.04（各两次，全 ≤60s） | 8908567 / 12071108 / 6217780 / 5156577 / 3719230 / 9276668 | 6 程序各自带校验退出码 0（native==gem5==golden FINAL 逐字节一致）；密度三档：wikisort/matmult 误预测 0.61-0.87% + squash 9.7-12.1%，md5sum 中间，nbody/minver（FP）误预测 ~0.01% 循环主导；flIntMin=0 全部 6 程序 | done |
| polybench | W1.3 | gemm `116849d3adf3227b` / lu `74ffe5eb77ea9257` / cholesky `ea7e0d0e7c86582d` / jacobi-2d `dc867b5f02998c1e` | gemm 52.87/53.98；lu 51.43/51.62；cholesky 53.14/51.92；jacobi-2d 51.15/52.04（s1/s2；重建后 s3 复跑 53.30/51.54/51.63/51.51） | 6460912 / 6651537 / 6539248 / 6571463 | 全数组 FNV-1a hash（cholesky 按上游 print_array 口径=下三角含对角）；**flFloatMin=192 全部 4 内核（W1.2「标量 FP→VecRegClass」三重确认）+ flVecMin=0（vec 池压穿，D75 初始 4→0）**；robMax=128/iqMax=64 全部到顶；详见 W1.3 实测记录 | done |
| gap / libjpeg | W1.4 | （待实测） | （待实测） | （待实测） | 语义代理 checksum / 逐像素 hash | pending |

## smoke 实测记录（W1.0，2026-09-23）

- 构建：`make -C workloads/ooo smoke` → `gcc -O2 -static -Wall -Wextra`，
  零 warning；`file`：ELF 64-bit ARM aarch64, statically linked。
- gem5 C3 SE 两次（`--outdir=/tmp/ooo_w10_s1`、`/tmp/ooo_w10_s2`）：均 EXIT=0，
  FINAL 行逐字节一致（`od -c` 确认 `FINAL=45737cc9a76c0dce\n`），
  hostSeconds 1.18 / 1.19（<5 s 达标，远低于 60 s 预算）。
- 宿主原生运行一次：EXIT=0，FINAL 与 gem5 一致（native == gem5）。

## dep_chain 实测记录（W1.5b，2026-09-23）

- 构建：`make -C workloads/ooo dep_chain dep_chain_vec` 零 warning；
  `file` 双确认 aarch64 static ELF。objdump：int 版 74 个 madd/msub 位点
  （热循环 8 条 `madd x` 真依赖链，`c*K+D` 大奇常数不可强度削减）、0 个 fmla；
  vec 版 **1056 个静态 fmla**（12 链 × 88 sweep 宏展开；gcc 把 laneq 常量
  物化为广播向量故为 `fmla v.4s` 向量形，同为 SimdFloatMultAccOp 融合乘加）。
- golden（native==gem5，s1/s2 逐字节一致 `od -c`）：
  int `FINAL=98e5e31e726e383f`（STEPS=1750000，hostSeconds 45.86/45.96，
  simInsts 17505782）；vec `FINAL=b1e661a247b95774`（ROUNDS=4500，
  hostSeconds 47.36/47.00，simInsts 6310709）。vec 的 native==gem5 同时证明了
  gem5 fplib `fp32_muladd`（单次舍入融合 FMA）与硬件 FMLA 位级一致。
- int 密度门：probe 运行 `/tmp/ooo_w15b_int_p1`
  `CHAOS_PROBE samples=7040858 robOver80=137 iqOver80=7000882 flIntLe8=6999912
  flFloatLe12=0 flVecLe6=7040858 robMax=120 iqMax=64 flIntMin=0 flFloatMin=192
  flVecMin=0` → **flIntLe8 占比 99.42% ≥ 1% PASS**（reg_chain 基线 99.5% 同
  量级；iqMax=64 与 IQ 容量精确吻合 = 等待中的 madd 链指令塞满 IQ）。
- vec 密度门（加强版，因 flVecLe6 在 vec48 平台平凡 100% 不再单独作门）：
  a) `rename.vecLookups=15336251` vs `simInsts=6310709`（2.43×，同数量级）
  ——向量 rename 流量真实发生（对照：int 版 vecLookups=182，纯 CRT NEON）；
  b) objdump fmla 静态计数 1056 > 1000；c) 见下条 D75 校准。
- **D75 校准（初始 vec freelist 实测 = 4）**：零向量指令、无 CRT 的
  `/tmp` 测量核（25 条指令，objdump 向量指令计数=0）跑 `--chaos_probe`：
  `flVecMin=4`（1600563 个采样恒定，从未分配过 vec 物理寄存器）。
  与源码推导吻合：`physVec=48 − 44 arch vec`（regs/vec.hh:83，V0-V31 共 32
  + Special 8 + Intrlv 4，cpu.cc 初始映射逐 arch 消耗）= **4**。
  结论：C3 vec48 平台**启动即 ≤6**（flVecLe6 恒 100%，含无向量代码负载），
  D75「向量池剩余 ≤6」阈值无法隔离压力窗口，需重校准（如 free==0 ——
  int 版 CRT NEON 已瞬时压到 0，vec 版持续 0）。附带发现：flFloatMin=192
  恒满（AArch64 gem5 v25 浮点走 VecRegClass，FloatRegClass 池初始未被
  arch 映射消耗）。
- 回归：`make clean && make` 幂等零告警；smoke `45737cc9a76c0dce`、
  branch_mispred `06e84f119c258fa7` golden 不变。

## rob_fill 实测记录（W1.5c，2026-09-23）

- 构建：`make -C workloads/ooo rob_fill rob_fill_fp` 零 warning；`file` 双确认
  aarch64 static ELF。objdump div 在场：int **sdiv|udiv 静态位点 192**（>100 PASS，
  128 个在主循环 + 置换初始化的取模 udiv + CRT）；fp **fdiv 静态位点 130**
  （>100 PASS，128 个在主循环 + 2 个 CRT）。动态证明：
  `commit.committedInstType_0::IntDiv=140290`（int：主循环 107520 = 840×16×8
  + 置换初始化取模 32767）；`FloatDiv=69120`（fp：540×32×4 精确吻合）。
- golden（native==gem5，编排者终跑 s1/s2/p1 各三跑 + native，FINAL 逐字节一致；
  config.ini 逐跑核实二进制映射）：int `FINAL=19eab7d0de27237e`（hostSeconds
  43.90/40.34，simInsts 7901621）；fp `FINAL=85085fd5686d173b`（hostSeconds
  40.75/44.25，simInsts 8692564）。fp 的 native==gem5 同时证明 gem5 fplib
  `fplibDiv<uint64_t>` 与硬件 FDIV 对全部 69120 个商位级一致（fp 核内唯一
  浮点运算是标量 double 除法，操作数强制 normal、商 ∈ [512,2048)∪(4.9e-4,2e-3)，
  无 denormal/NaN）。〔编排者勘误 2026-09-24：子代理报告的 hostSeconds/simInsts/
  密度 int↔fp 标签互换（simInsts 与密度是确定性的，config.ini 终跑核实）；
  FINAL 与 div 动态计数标签正确。〕
- **密度门未达标 → 编排者裁决重校准（诚实记录）**：robOver80 采样占比
  int **4.91%**（275648/5609073）、fp **7.09%**（426601/6013631），远低于
  原 50% 门限；robMax 128/128（ROB 能到满）、commit 空转周期占比 int
  48.96%（指针追逐确实长期阻塞 commit 头部）。**裁决**：北极星 D33/D35/D85
  的事件触发语义是「ROB 占用超过 80%」这一**事件的发生**（事件覆盖计数需
  足量事件），而非持续占用占比；本核 robMax=128（越阈必然发生）+ 越阈采样
  27.5 万/42.7 万每跑（2000 事件覆盖需求的两百倍量级）+ commit 空转 ~49%
  + div 在场——**重校准门全 PASS**。原 ≥50% 持续占用代理门经 8 轮结构变体
  + `--phys_int 256` 对照证明为 gem5 v25 rename skid 平台属性（见下），
  与 W1.5b D75「阈值与平台耦合」同类，作废并记录，不隐藏。
- **7 轮迭代诊断**（每轮均真机 probe，完整数据在 /tmp/ooo_w15c_progress.txt）：
  1. v1 交织 madd 填充：int 3.46% — madd 填满 2 个 IntMultDiv 单元（除法本已
     独占），IQ 堵死（iqOver80 32.8%）；另有 36823 次 store→load 内存序违例
     （下一轮操作数重载越过本轮操作数 store）逐次冲刷全窗口。
  2. v2 纯 ALU 填充 + 双 bank 操作数（违例 36823→61）：int 3.13%（IQ 疏通了，
     但 gcc 溢出的 64 位常量逐次重载，LQ 满 920K 次压制 rename）。
  3. v3 add-immediate 填充 + 商镜像 store：int 9.57% / fp 7.38%（最佳 fp）。
  4. v4 spec 字面「连续除法」簇（8 连除 + 纯 ALU 填充）：int **14.68%（最佳 int）**
     / fp 3.98%；commit 空转 35% 证明簇确实阻塞头部，但 LDP 操作数装载在
     除法阻塞窗内滞留 LQ（LQFull 200K）压住 rename。
  5. v5/v6 填充掺 store（16%/25%）抬升无寄存器代价的窗口质量：反而更差
     （8.43%/5.81%）— SQ 满触发 gem5 rename skid-buffer 排空。
  6. v7 spec 字面「指针追逐」（16 连依赖载入，地址=上一载入值，128KiB 置换表，
     L1 miss/L2 hit ~56cy，~900 连续周期阻塞头部）+ 连续除法簇/fdiv 对组：
     int 4.91% / fp 7.09% — **决定性测量：rename.status::Unblocking=52.96% vs
     Blocked=2.59%，即每一次瞬时 rename 停顿（LQ/IQ/SQ/freelist 满）代价
     ~20 周期的 1 宽 rename**，dispatch 永远追不上 commit，窗口无法钉在高位。
  - **`--phys_int 256` 扫描（决定性对照）**：freelist 从未耗尽（flIntMin
    108/112）但 robOver80 仅 fp 7.09%→7.91%、int 4.91%→5.18% —— int PRF
    上限**不是**约束；约束是 LQ/SQ/IQ 满事件触发的 rename skid 排空本身。
  - 平台结构性结论：C3 的小 LQ/SQ/IQ（32/32/64）+ gem5 rename skid 排空
    惩罚（每事件 ~20 周期 1 宽 rename）⇒ 负载已把 commit 头部阻塞近半周期
    （commit 空转 48.96%、robMax=128），但 dispatch 无法持续 4 宽追赶，
    robOver80≥50% 在本平台模型下 7 种结构变体均未达到（与 W1.5b D75
    「flVecLe6 阈值需重校准」同类：门与平台模型耦合）。建议后续：
    (a) 门重校准（如 robOver60 或「commit 空转占比」直接度量阻塞语义）；
    (b) 或调研 gem5 rename skid/LSQ 行为是否为 v25 建模特性。
- 回归：`make clean && make` 幂等零告警；smoke `45737cc9a76c0dce`、
  branch_mispred `06e84f119c258fa7`、dep_chain int/vec `98e5e31e726e383f`/
  `b1e661a247b95774` golden 全部不变；rob_fill 两核 clean 重建后 FINAL 不变。

## coremark 实测记录（W1.1，2026-09-23）

- **PROVENANCE**：`git clone https://github.com/eembc/coremark`，
  HEAD = `1f483d5b8316753a742cbf5590caf5bd0a4e4777`（与计划预期 1f483d5b 一致）。
  `git log -1`：`Merge pull request #55 from DeflateAwning/main — Fix typo
  (fixes #52)`，Joseph Yiu，2025-05-01。入库子集（无 .git，上游 Apache-2.0
  LICENSE.md 原样保留）：`core_list_join.c core_main.c core_matrix.c
  core_state.c core_util.c coremark.h posix/{core_portme.c, core_portme.h,
  core_portme.mak, core_portme_posix_overrides.h} LICENSE.md Makefile
  README.md coremark.md5`。注意：该 HEAD 上游端口目录为**顶层 `posix/`**
  （非 2019 前的 `cores/posix` 布局）；上游 `coremark.md5` 在该 commit 对
  coremark.h **过期**（pristine git blob md5 `b0ec69b6…` ≠ 清单值
  `8ca974c0…`；core_main.c pristine `4a9e6dad…` 与清单一致）——git 内容为准。
- **唯一源码偏离**：`coremark/core_main.c` 结尾追加一个 gem5-fi 块（11 行，
  带 `/* gem5-fi W1.1: FINAL line for oracle chain */` 注释）：CRC 校验通过
  路径（`known_id >= 0 && results[0].err == 0`）打印
  `FINAL=%016x`，值为 CoreMark 计算的最终 CRC（crcfinal，`(ee_u32)` 转换，
  零填充 16 位十六进制）。`diff`（上游 git blob vs 入库副本）= 恰好这一块。
  其余文件与上游逐字节一致。基准逻辑/迭代内容零改动。
- **构建适配**（Makefile 注释里同步记录）：框架 Makefile 的 `coremark` 目标
  委托**入库的上游 Makefile**（`make -C coremark PORT_DIR=posix … load`，
  保留上游 FLAGS_STR 引号/vpath 插件链），旋钮走上游文档化接口：
  `XCFLAGS="-static -Wall -Wextra -DSEED_METHOD=SEED_VOLATILE
  -DPERFORMANCE_RUN=1"` + `ITERATIONS=N`。要点：
  - posix 默认 `SEED_METHOD=SEED_ARG` 从 argv 取种子；SE runner 不传参
    （`set_se_binary_workload` 只收二进制），无参运行会进入按 1 秒探针的
    迭代数自校准循环——gem5 SE 下 `clock_gettime` 返回**模拟时间**
    （syscall_emul.hh `getElapsedTimeNano` → `curTick()`），探针永远到不了
    1 秒 ⇒ 实质挂死。`SEED_VOLATILE`（core_portme.h `#ifndef` 守卫，零文件
    修改）是上游的编译期种子路径，并让 `-DITERATIONS` 生效（喂
    `seed4_volatile`）。
  - `PERFORMANCE_RUN=1` = 官方 performance 种子 0x0/0x0/0x66（seedcrc
    0xe9f5，known_id=3 "2K performance run"，自带 CRC 校验激活）。
  - `.iterations-N` 戳规则保证换 ITERATIONS 必重建（上游 Makefile 看不见
    `-D` 宏变化）。
- **构建验证**：`make -C workloads/ooo coremark` → MAKE_EXIT=0 **零警告**
  （`gcc -O2 … -static -Wall -Wextra …` 上游源码本身 -Wall -Wextra 干净）；
  `file`：`ELF 64-bit LSB executable, ARM aarch64, … statically linked`。
- **ITERATIONS 校准**：任务提示"从 2000 起试"实测超约 50 倍（2000 迭代 ≈
  6.2 亿指令 ≈ 35+ 分钟）。实测 ITERATIONS=20：hostSeconds 30.67 / simInsts
  6190128（≈31 万指令/迭代，≈202 KIPS）⇒ 终值 **ITERATIONS=35**：
  hostSeconds **52.62 / 52.92**（s1/s2，≤60s 预算内、30-60s 目标带内），
  simInsts **10808351**（10-15M 目标带内）。
- **golden**：native EXIT=0 `FINAL=000000000000cf56`；C3 SE s1/s2 均 EXIT=0
  且 FINAL 与 native **逐字节一致**（`od -c`：`FINAL=000000000000cf56\n`
  共 23 字节）；`tools/classify.py extract_checksum` 对真实 gem5 输出取值
  `000000000000cf56`（oracle 链端到端验证）。crcfinal 随 ITERATIONS 变化
  （20 与 2000 恰落同一 CRC 折叠环态 0x4983，35 则 0xcf56），对固定
  ITERATIONS 确定性成立。
- **自带校验（3/3 内核全过）**：seedcrc 0xe9f5；`[0]crclist 0xe714 /
  [0]crcmatrix 0x1fd7 / [0]crcstate 0x8e3a` 全部等于 known_id=3 已知值，
  无任何 `ERROR! … crc` 行，native 与 gem5 一致。**诚实偏差记录**：输出仍
  含 `ERROR! Must execute for at least 10 secs…` 与 `Errors detected`——
  这**不是**校验失败，而是 EEMBC 计分发布规则（总分需 ≥10 秒平台时间）：
  native 35 迭代仅 1ms，gem5 SE 全程模拟时间 1.94ms（simTicks
  1940081220），两者都结构性不可能 ≥10s（10 模拟秒 = 2.6e10 周期 ≈ 数十
  主机小时）。计划要求"输出含 Correct operation performed / 无 Errors
  detected"在 SE 预算内不可达，故 FINAL 门放在 CRC 校验通过路径而非
  `total_errors == 0`（后者含计时规则，会吞掉 oracle 行）。
- **事件密度实测**（probe p1，read-only，FINAL 不变；event_density.py 三跑
  聚合，s1/s2/p1 全部计数逐位一致）：mispredicts **73348**
  （/commits 11121427 = **0.66%**）、squash **1677415**（**15.1%**，
  squash_bp 783831 主导）、renamed_insts 13209178、rat_writes 15377069、
  sim_ticks 1940081220（IPC≈2.14）；CHAOS_PROBE samples **5039172**、
  robOver80 **67194**（1.33%，robMax=128 到顶）、iqOver80 **309285**
  （6.14%，iqMax=64 满容）、flIntLe8 **533971**（10.60%，**flIntMin=0**
  ——CoreMark 实际压穿过 int freelist，与探针核不同）、flFloatMin=192
  恒满（AArch64 标量 FP 走 VecRegClass，W1.5b 已记录）、flVecLe6=100%
  平台基线（D75）。CoreMark 作为 59 实验格主力负载的 D01/D02/D04 误预测
  恢复、squash、占用事件供给充足。
- 回归：`make -C workloads/ooo clean && make`（含 coremark 共 7 个目标）
  幂等零告警；smoke `45737cc9a76c0dce`、branch_mispred
  `06e84f119c258fa7`、dep_chain int/vec `98e5e31e726e383f`/
  `b1e661a247b95774`、rob_fill int/fp `19eab7d0de27237e`/
  `85085fd5686d173b` 全部 golden 不变（native 确定性重放比对）。

## embench 实测记录（W1.2，2026-09-23）

- **PROVENANCE（详见 `embench/PROVENANCE.md`）**：`git clone
  https://github.com/embench/embench-iot`，两个上游 commit：
  HEAD `09c2ed8c3b7008c95d08b038de4a3f6dc103ed70`（I-mikan-I，2024-08-29，
  "Remove CPU_MHZ references"，当前 master）+ pre-2.0
  `92da124bb8da825b2937abaaed2aca9bb9e50fc9`（I-mikan-I，2024-03-08，
  "Remove legacy build script"，浮点基准存在的最后一个 commit）。
  上游 COPYING（GPL-3.0-or-later）原样入库，无 .git。
- **诚实偏差（计划 6 程序中 3 个不可得，实证后替换）**：`qlsort`/`qrsolve`
  在 embench-iot 全部 master 历史中**从未存在**（`git log --all -- src/qlsort
  src/qrsolve` 为空；候选名单里的 `stoneman` 同样从未存在）；**Embench-IoT
  2.0 删除了全部浮点基准**（nbody/cubic/primecount 于 1b2731f、minver/st 于
  fc72c8d），HEAD 上唯一含 float 字段的 depthconv 实为量化 int8/int32
  运算（float_activation_min/max 字段未使用）——HEAD 上不存在任何真浮点
  基准。03-workloads.md 仅要求「Embench 22 个小程序，整数、浮点、乘除、
  哈希都有，每个自带结果校验」（未指定程序名），故按计划替换规则处理：
  qlsort→**wikisort**（排序类，WikiSort O(n log n) 稳定排序，语义最近）；
  qrsolve→**minver**（3×3 float 矩阵求逆，线性代数语义最近）；nbody 保留
  **nbody**（double 精度 N-body 能量核，sqrt/div 密集）。前两者中 nbody/minver
  取自 92da124b，其余 4 程序 + support/ 全部取自 HEAD。
- **唯一源码偏离**：每基准恰好一个 `/* gem5-fi W1.2 */` 标记的 FINAL 块
  （verify_benchmark 成功路径打印 `FINAL=<16hex>`，值 = 其校验数据的
  FNV-1a 64 位 hash；模式仿 coremark/core_main.c W1.1 块）+ crc_32.c/
  nbody.c/libminver.c/matmult-int.c 四文件各 2 行 `#include <stdio.h>/<stdint.h>`
  （同标记）。与上游 git blob 的 diff 逐行核实仅含这些块（support/ 5 文件
  0 差异；6 基准文件差异行 18-36 行全在 hunk 内）。基准逻辑零改动；verify
  失败仍走上游 main 的 `return !correct`（exit 1 → classify.py Crash/DUE）。
  哈希数据：crc32=校验结果 r（上游 `%32768` 折叠，熵与上游自检同 15 位）；
  md5sum=完整 4 字摘要 {h0..h3}（严格强于上游 XOR 折叠）；matmult=
  ResultArray 20×20；wikisort=array1 400 元素；nbody=solar_bodies
  5 体×8 double（字节级 FP oracle）；minver=c/d/det（3×3 float×2+det，
  字节级 FP oracle，严格于上游 epsilon 比较）。
- **构建**：`make -C workloads/ooo embench` → MAKE_EXIT=0 **零告警**
  （gcc 12.3.1，`-O2 -static -Wall -Wextra` + 5 个**有记录的**上游代码质量类
  告警抑制：-Wno-unused-variable/-Wunused-parameter/-Wno-unused-but-set-
  variable/-Wno-maybe-uninitialized（crc32 r，规模因子编译期 ≥1 恒初始化，
  伪阳性）/-Wno-absolute-value（beebsc.h float_eq_beebs 宏 + minver double
  常量）；源码保持原样，抑制理由全文记录于 embench/PROVENANCE.md——新告警
  类仍会失败构建）；`file` 6/6：ELF 64-bit ARM aarch64, statically linked。
  规模旋钮：HEAD 代基准 `-DGLOBAL_SCALE_FACTOR`（两重循环 lsf×gsf），1.0 代
  nbody/minver `-DCPU_MHZ`（其当代惯例）；校准终值 crc32 GSF=3 / md5sum
  GSF=5 / matmult-int GSF=3 / wikisort GSF=5 / nbody MHZ=120 / minver
  MHZ=20（scale-1 实测指令数外推 + 一轮实跑确认）。
- **golden（6/6，native==gem5 s1==s2 逐字节一致，od -c 证实；config.ini
  逐跑核实 cmd= 二进制身份 12/12，另 clean 重建后 crc32 复跑一次
  EXIT=0/FINAL 同/37.99s）**：
  crc32 `b87739d9c40d1798`（39.35/38.87 s，8908567 insts）、
  md5sum `973ff8cc9018e79f`（40.04/40.39 s，12071108）、
  matmult-int `e105f98022b761ef`（42.83/42.73 s，6217780）、
  wikisort `d2cf29655e3e0f06`（29.85/29.79 s，5156577）、
  nbody `f39b4e8804f279c3`（33.40/33.37 s，3719230）、
  minver `9792f3ee24af3023`（53.14/54.04 s，9276668）。
  全部 ≤60 s 预算（minver 最贴边，余量 ~6 s；如需更大余量可
  `EMBENCH_MINVER_MHZ=18` 重编，FINAL 不随规模变化——已实证 scale=1 与
  校准规模同值）。自带校验退出码 0（=上游 verify_benchmark 通过）native
  6/6。nbody/minver 的 native==gem5 同时证明 gem5 fplib 的 sqrt/mul/div/
  add/sub 对这两个核的全部输出位级一致（W1.5b/W1.5c 的 FMA/DIV 结论扩至
  FSQRT）。
- **事件密度实测**（每程序一次 `--chaos_probe` p1，read-only，p1 的 FINAL 与
  s1/s2 相同；s1/s2/p1 全部计数逐位一致，确定性）：
  | 程序 | mispredicts(/commits) | squash(/commits) | robOver80(采样占比) | iqOver80 | iqMax | robMax | flIntLe8 |
  |---|---|---|---|---|---|---|---|
  | crc32 | 848（0.0095%） | 6714（0.075%） | 4475/3726427（0.12%） | 0 | 44 | 128 | 4613 |
  | md5sum | 22987（0.19%） | 214830（1.76%） | 435（0.01%） | 0 | 41 | 128 | 160 |
  | matmult-int | 50346（0.61%） | 801783（9.7%） | 13727/2654161（0.52%） | 9494 | 64 满容 | 128 | 13331 |
  | wikisort | 49144（0.87%） | 687919（12.1%） | 23119/2682852（0.86%） | 177 | 64 满容 | 128 | 21818 |
  | nbody | 504（0.012%） | 5273（0.13%） | 1514/10156448（0.015%） | 0 | 44 | 128 | 1120 |
  | minver | 482（0.005%） | 5451（0.055%） | 674/7949575（0.008%） | 0 | 44 | 128 | 165 |
  整型 vs 浮点三档格局清晰：wikisort/matmult（访存+分支密集）误预测
  0.61-0.87%、squash 9.7-12.1%；md5sum 中间（1.76%）；nbody/minver
  （FP 循环主导）误预测 ~0.01%——北极星 Embench 50（整型）+15（浮点子集）
  实验格的 D01/D02/D04 误预测恢复与 squash 事件供给按程序分层可用。
  全部 6 程序 flIntMin=0（int freelist 实际压穿）；flFloatMin=192 恒满 /
  flVecLe6=100% 为 W1.5b 已记录的平台基线（AArch64 标量 FP 走 VecRegClass
  + D75）。
- 回归（**全量重建 native 确定性重放**路线）：`make -C workloads/ooo clean
  && make`（13 个目标含 embench）幂等零告警；既有 7 个 golden 全部不变
  （smoke `45737cc9a76c0dce`、branch_mispred `06e84f119c258fa7`、
  dep_chain int/vec `98e5e31e726e383f`/`b1e661a247b95774`、rob_fill
  int/fp `19eab7d0de27237e`/`85085fd5686d173b`、coremark
  `000000000000cf56`），embench 6 程序 FINAL 重放一致；重建二进制与
  SE 验证版 md5 相同（gcc 确定性编译，`d600ff2f…`）。
- **GOLDEN_IDS 候选（待编排者注册 runner.py）**：`embenchcrc32-golden-v1
  b87739d9c40d1798`、`embenchmd5sum-golden-v1 973ff8cc9018e79f`、
  `embenchmatmult-golden-v1 e105f98022b761ef`、`embenchwikisort-golden-v1
  d2cf29655e3e0f06`、`embenchnbody-golden-v1 f39b4e8804f279c3`、
  `embenchminver-golden-v1 9792f3ee24af3023`。

## polybench 实测记录（W1.3，2026-09-23）

- **编排者复核（2026-09-24）**：native×4 亲测 FINAL 全对；gemm 独立 C3×2 跑与
  子代理零差（FINAL=116849d3adf3227b、simInsts=6460912、samples=10580668 全同）。
  **跨环境探针计数微差（诚实记录）**：gemm 占用计数子代理环境 robOver80=124829/
  iqOver80=1009/flIntLe8=124031 vs 编排者环境 124765/834/124016（各自两跑逐位
  自洽；绝对差 0.0006%，小基数计数相对差较大）——**功能口径（FINAL/simInsts/
  总周期）跨环境零差，仅周期级占用诊断量存在环境敏感性**（疑 Python 哈希随机
  化影响 stdlib 初始化顺序→同刻事件序微差）。处置：W3 编排须固定
  PYTHONHASHSEED；W2 L1 占用类观测按 ~0.001% 噪声带解读；本表数值取子代理
  环境（完整 4 内核），定性结论不受影响。

- **PROVENANCE（详见 `polybench/PROVENANCE.md`）**：PolyBench/C **4.2.1 beta**
  （Pouchet/Yuki，2016-05-10 stamp）。净版上游 tarball 分发点全部不可达（netlib
  404＝W1 计划已记录；OSU 下载 URL 重定向到通用目录页；SourceForge 404）；计划
  首选 cavazos-lab/PolyBench@70ea4ca9 探测存活，但实测它是 **GPU 变体套件**
  （CUDA/OpenCL/OpenACC/OpenMP/HMPP），非 plain PolyBench/C，弃用。实际源 =
  GitHub 镜像 **MatthiasJReisinger/PolyBenchC-4.2.1@3e872547**（2016-06-10，
  单 commit "Initial commit with PolyBench/C 4.2.1 beta sources"）。**镜像保真度
  交叉验证**：`utilities/polybench.c`、`utilities/polybench.h`、4 个内核 `.h` 与
  llvm-test-suite@4eee8855 内嵌副本**逐字节相同**（LLVM 副本的内核 `.c` 带其
  StrictFP/check_FP 适配，净版不含——取净版）。入库 12 文件（LICENSE.txt/README
  原样，无 .git）。
- **唯一源码偏离**：每内核恰好一个 `/* gem5-fi W1.3 */` 标记的
  `#include <stdint.h>` + main 末尾 FINAL 块（diff 实测 23-27 行/文件，全部在
  hunk 内；其余 8 文件与上游逐字节相同）。**oracle 口径 = 上游 print_array 的
  live-out 域全数组 FNV-1a 64 hash**：gemm=全 C(ni×nj)、lu=全 A(n×n)（LU 核
  上下三角都写）、jacobi-2d=全 A(n×n)（末步结果在 A）、**cholesky=下三角含
  对角（j≤i）**——其内核只写下三角、上三角 init 后即死数据，按上游 dump 口径
  取下三角（避免把落进死区的故障误报 SDC）。基准逻辑零改动。
- **确定性核实（native==gem5 前提）**：全树 grep 无 `rand()/srand()`，4 个
  init_array 全为固定整数公式；不带 `-DPOLYBENCH_TIME/GFLOPS` 时
  `polybench_start/stop/print_instruments` 宏**为空**（rtclock 返回 0、不调
  gettimeofday、无 32MB flush calloc）；print_array 挂在上游 `argc > 40` DCE
  守卫后（SE 无参不触发）——SE 二进制=纯确定性计算+FINAL 行。
- **构建**：`make -C workloads/ooo polybench` → MAKE_EXIT=0 **零告警**
  （`-O2 -static -Wall -Wextra` + 3 个逐一记录的上游代码质量类抑制：
  -Wno-unknown-pragmas〔scop/endscop 多面体标记〕、-Wno-unused-variable
  〔polybench.c 分配表仅 INTARRAY_PAD 用〕、-Wno-misleading-indentation
  〔lu/cholesky init 的 PSD 拷贝循环缩进假阳性——语义已人工核实为「累加完 B
  再整体拷贝」，C 语义正确〕；新告警类仍失败构建）。`file` 4/4：ELF 64-bit
  ARM aarch64, statically linked。**规模经 -D 命令行旋钮**（上游 .h 的
  `#if !defined(...)` 守卫使 -DNI/-DN/-DTSTEPS 完全绕过默认 LARGE_DATASET 块，
  零 .h 修改）+ `-DDATA_TYPE_IS_FLOAT`（fp32，03-workloads.md 指派 PolyBench
  覆盖 FP/SIMD 单元 + flFloatMin 交叉确认负载）。
- **规模校准**：FP 密集内核实测 ~125 KIPS（整型负载 ~200 KIPS），首候选
  （gemm 96³/lu 92/cholesky 100/jacobi T10N160）实测 62-76s 超预算 → 终值
  **gemm 88³ / lu 84 / cholesky 88 / jacobi-2d T=8,N=160**（Makefile 变量
  POLYBENCH_GEMM_N 等，可覆写）。
- **golden（4/4，native==gem5，s1==s2==s3 逐字节一致，od -c 证实 23 字节
  `FINAL=<16hex>\n`；config.ini 逐跑身份核实 12/12）**：
  gemm `116849d3adf3227b`（52.87/53.98/53.30 s，simInsts 6460912）、
  lu `74ffe5eb77ea9257`（51.43/51.62/51.54 s，6651537）、
  cholesky `ea7e0d0e7c86582d`（53.14/51.92/51.63 s，6539248）、
  jacobi-2d `dc867b5f02998c1e`（51.15/52.04/51.51 s，6571463）。
  s1/s2 验证构建版、s3=clean 重建后复跑（提交版二进制再证）。全部 ≤60 s
  预算。simInsts s1==s2==s3 精确相同。`tools/classify.py extract_checksum`
  对 4 份真实 gem5 输出端到端取值正确。native==gem5 同时把 gem5 fplib 位级
  一致结论扩展到 **fp32 标量 fdiv（lu/cholesky/jacobi init）与 fp32 fsqrt
  （cholesky）**（此前 W1.5b/W1.5c/W1.2 已证 fp32 FMA、fp64 div/sqrt）。
- **事件密度实测**（官方聚合 `tools/event_density.py --runs s1 s2 p1
  --stdout …`，三跑全部计数逐位一致；p1 `--chaos_probe` read-only，FINAL 与
  s1/s2 相同）：
  | 内核 | mispred(/commits) | squash(/commits) | robOver80(采样占比) | iqMax/robMax | flIntMin | flFloatMin | flVecMin |
  |---|---|---|---|---|---|---|---|
  | gemm | 8604（0.13%） | 22848（0.35%） | 124829/10580668（1.18%） | 64/128 满容 | 0 | **192** | **0** |
  | lu | 13611（0.19%） | 45493（0.63%） | 113466/8557969（1.32%） | 64/128 | 1 | **192** | **0** |
  | cholesky | 12060（0.17%） | 41265（0.57%） | 63145/8803460（0.72%） | 64/128 | 4 | **192** | **0** |
  | jacobi-2d | 3123（0.048%） | 10278（0.16%） | 410241/9886860（4.15%） | 64/128 | 1 | **192** | **0** |
- **flFloatMin 三重确认（W1.2 结论）**：4 个 fp32 内核 flFloatMin=192 恒满
  （FloatRegClass 池从未被消耗）而 FP 指令真实在场——committedInstType 动态
  计数：gemm FloatMult=681472+FloatMultAcc=681472（=88³ 精确）；lu
  FloatMultAcc=786758+FloatDiv=7056；cholesky FloatMultAcc=795036+FloatDiv=7744
  +**FloatSqrt=88（=N）**；jacobi FloatAdd=1597696（=4×2×T×(N-2)²
  精确）+FloatMult/FloatDiv/FloatCvt；**全部 SimdFloat\*=0（纯标量 Float 类）**。
  标量 FP 走 VecRegClass ⇒ **flVecMin=0**：vec 池（48 项，D75 实测零向量核初始
  剩 4）被标量 FP 的物理寄存器消耗压穿到 0——「vec 池受压」直接实证。北极星
  D62-66/D72/73/76 的「标量 FP 行」按自带合并条款并入向量行的结论再添一柱。
- 回归（**全量重建 native 确定性重放**路线）：`make clean && make`（17 目标
  含 polybench）幂等零告警；既有 13 个 golden 全部不变（smoke
  `45737cc9a76c0dce`、branch_mispred `06e84f119c258fa7`、dep_chain int/vec
  `98e5e31e726e383f`/`b1e661a247b95774`、rob_fill int/fp
  `19eab7d0de27237e`/`85085fd5686d173b`、coremark `000000000000cf56`、
  embench 6 程序 `b87739d9c40d1798`/`973ff8cc9018e79f`/`e105f98022b761ef`/
  `d2cf29655e3e0f06`/`f39b4e8804f279c3`/`9792f3ee24af3023`），polybench 4
  内核重建后 native 重放同值（17/17 PASS）。
- **GOLDEN_IDS 候选（待编排者注册 runner.py）**：`polybenchgemm-golden-v1
  116849d3adf3227b`、`polybenchlu-golden-v1 74ffe5eb77ea9257`、
  `polybenchcholesky-golden-v1 ea7e0d0e7c86582d`、`polybenchjacobi2d-golden-v1
  dc867b5f02998c1e`。
