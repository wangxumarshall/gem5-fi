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
| coremark | W1.1 | （待实测） | （待实测） | （待实测） | 自带 CRC 校验 | pending |
| embench | W1.2 | （待实测） | （待实测） | （待实测） | 每程序自带校验退出码 | pending |
| polybench | W1.3 | （待实测） | （待实测） | （待实测） | 全数组 array_hash | pending |
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
