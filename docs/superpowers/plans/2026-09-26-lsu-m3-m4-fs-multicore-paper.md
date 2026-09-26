# LSU M3（FS TLB 单元 + TC'22 锚点）+ M4（多核）+ 结合 ooo 的论文级综合 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付总纲（09-implementation-plan.md）剩余里程碑 M3（FS 管线 + T 系 42 格 + TC'22 锚点复现）与 M4（多核 FS + O 系多核格），并把 ooo 轨道（本仓 runs/ 的 100+ formal 产物）与 LSU 轨道合并为领先 `docs/papers/ref/` 30 篇顶会论文的综合工作（竞争矩阵 + 论文骨架）。

**Architecture:** FS 管线复用仓内已验证的三步流水线（`arm_chaos_fs.py` + `boot_ckpt.rcS`：Atomic boot→`m5 checkpoint`→`--restore-checkpoint` O3 + firstClock 重基），仅初始化 gem5-fs 子模块即可在本仓二进制上重建；T 系经 `--chaos_armtlb` 族挂载（arm_chaos_fs.py:81-100 参数已就绪）；多核走 gem5-fs 的多核 dtb（1-16cpu 在姊妹仓镜像内）+ ArmBoard 多核处理器；ooo 产物收割与竞争定位是纯数据/文档工作。

**Tech Stack:** gem5 v25.1.0.1 vendored（本仓 `build/ARM/gem5.opt`，含全部 CHAOS 注入器）、gem5-fs 子模块（git@github.com:wangxumarshall/gem5-fs.git，aa234b94，SSH 已验证可达）、Python 3 工具链（lsu_campaign/backfill/meta_analysis）。

**Spec:** `docs/gem5-fi/lsu/09-implementation-plan.md`（§3 W7/W8、§4 M3/M4、§1.2 TC'22 锚点原文）；`docs/gem5-fi/lsu/01-units-and-research.md`（TC'22/TC'23 锚点数字）；`docs/papers/ref/`（30 篇竞争论文）。

## Global Constraints（全阶段适用）

- **TC'22 锚点（M3 门）**：T01 DTLB 单 bit 对照"平均 Crash AVF≈50%、Hang≈10%、SDC AVF<1%"——**复现不出先怀疑注入器/负载，不得继续新结论**（09 §1.2 ②）。
- **FS 并发硬上限下调为 2**（CLAUDE.md §FS：FS 运行内存占用更高，M3/M4 阶段按实测单独下调并发数）。
- **锚点/口径纪律不变**：SDC 率分母=activated；FS Crash=kernel panic/Oops（exit-event 分类，10de4e9 先例）；SE 与 FS 数字不混算；blocked 不伪造。
- **每 patch 真机验证**：FS 步骤的验证=真实 boot/restore 运行输出为证；不可验证的代码不提交（本计划把此前 deferred 的 T05-T08 排在 FS 上电**之后**，正是为了使其变为可验证）。
- gem5-fs 子模块**只初始化不提交内容**（3GB；`.gitmodules` 已注册，`git status` 中子模块指针不变即可，绝不 `git add gem5-fs` 下的镜像文件）。
- checkpoint 用**本仓二进制重建**，不跨二进制复用姊妹仓 cpt（SimObject 集不同：本仓多 CHAOSPrefetch 等）。

---

### Task 1: gem5-fs 子模块就位 + FS 资产清点

**Files:**
- Verify: `gem5-fs/`（vmlinux、ubuntu.img、armv8_gem5_v1_{1,2,4}cpu.dtb）
- Modify: 无（只读清点）

**Interfaces:**
- Produces: `FS_ASSETS = {vmlinux, ubuntu.img, dtb_1cpu, dtb_2cpu, dtb_4cpu}` 的存在性事实，后续所有 FS 任务的输入路径。

- [ ] **Step 1: 等待/确认子模块克隆完成**（后台已启动，`tail /tmp/submodule_init.log`）

```bash
git submodule status gem5-fs   # 预期: 无前缀 '-' 且 commit=aa234b94
ls -la gem5-fs/vmlinux gem5-fs/ubuntu.img gem5-fs/armv8_gem5_v1_1cpu.dtb gem5-fs/armv8_gem5_v1_2cpu.dtb
du -sh gem5-fs   # 预期 ~3.0G（与姊妹仓 /home/sdc/gem5-fi/gem5-fs 一致）
```

- [ ] **Step 2: 确认不污染 git 状态**

```bash
git status --short | head -5   # 预期: gem5-fs 不出现（子模块指针未变）
```

- [ ] **Step 3: Commit（本任务无代码变更——若 Step 2 干净则无提交；把清点结论追加 progress.md 并提交文档）**

```bash
cat >> progress.md << 'EOF'
### M3/M4 立项: FS 资产就位(2026-09-26)
- gem5-fs 子模块 aa234b94 初始化(vmlinux+ubuntu.img+1/2/4/8/16cpu dtb, 3.0G)
- checkpoint 流水线复用仓内 arm_chaos_fs.py(--restore-checkpoint + boot_ckpt.rcS), 不跨二进制复用姊妹仓 cpt
EOF
git add progress.md && git commit -m "docs(pwf): M3/M4 kickoff — gem5-fs submodule initialized, FS asset inventory" && git push origin fi-ding
```

---

### Task 2: 本仓二进制走通 FS checkpoint 流水线（boot → cpt → restore O3）

**Files:**
- Create: `runs/fs_lsu/boot/`（Atomic boot 产物 + checkpoint）
- Verify: `configs/se/arm_chaos_fs.py`（已存在，只运行不改）

**Interfaces:**
- Produces: `runs/fs_lsu/boot/cpt.<tick>/`——Task 3/4/7/8 所有 FS 注入运行的 restore 源；`<tick>` 具体数值以运行产出为准记录进本计划执行备注。

- [ ] **Step 1: Atomic boot + 采 checkpoint**（姊妹仓验证过的管线第一步；`--readfile` 走 virtio 传入 rcS）

```bash
mkdir -p runs/fs_lsu/boot
build/ARM/gem5.opt --outdir=runs/fs_lsu/boot configs/fs/kp920_proxy_fs.py \
  --cpu Atomic --readfile configs/fs/boot_ckpt.rcS 2>&1 | tail -5
# 预期: "[boot_ckpt.rcS] booted to userspace; taking checkpoint" +
#       "checkpoint taken" + 模拟退出; runs/fs_lsu/boot/cpt.<tick>/m5.cpt 出现
```
超时上限 30 分钟（首 boot 慢；若 virtio_blk 挂起——姊妹仓风险表已记录该模式——重试一次，仍挂则查 uart 日志定位）。

- [ ] **Step 2: restore O3 冒烟**（无注入；验证 checkpoint 与本仓二进制兼容 + O3 切换 + 重基）

```bash
CPT=$(ls -d runs/fs_lsu/boot/cpt.* | head -1)
build/ARM/gem5.opt --outdir=runs/fs_lsu/restore_smoke configs/fs/kp920_proxy_fs.py \
  --cpu O3 --restore-checkpoint "$CPT" \
  --readfile configs/fs/m2_ptrchase.rcS 2>&1 | tail -4
# 预期: restore 成功 + m2_ptrchase rcS 输出 + 正常退出; 无 "unserialized object" 类错误
```

- [ ] **Step 3: 记录 checkpoint tick 与 restore 运行时长**（后续 firstClock 重基与超时设定的输入；FS 格超时 = golden restore 时长 ×10 + 绝对上限 1800s，05 r17 FS 版）

```bash
echo "CPT=$CPT  restore_smoke_wall=<实测秒数>" >> progress.md
```

- [ ] **Step 4: Commit**（progress.md 记录；runs/ 不入 git）

---

### Task 3: CHAOSArmTLB FS 注入冒烟（T 系注入面真机验证）

**Files:**
- Create: `runs/fs_lsu/tlb_smoke/`

**Interfaces:**
- Consumes: Task 2 的 `runs/fs_lsu/boot/cpt.<tick>`。
- Produces: 验证事实"armtlb 注入在 FS restore 运行中发生且可分类"（armtlb_injections.log ≥1 行 + 运行结局）——Task 5 映射的依据。

- [ ] **Step 1: T01 等价注入（bit_flip，maxFaults=1，概率 1.0）**

```bash
build/ARM/gem5.opt --outdir=runs/fs_lsu/tlb_smoke configs/fs/kp920_proxy_fs.py \
  --cpu O3 --restore-checkpoint "$CPT" --readfile configs/fs/m2_ptrchase.rcS \
  --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 \
  --tlb_fault_type bit_flip --tlb_max_faults 1 --tlb_rng_seed 7 2>&1 | tail -5
grep -c "Site:\|Tick:" runs/fs_lsu/tlb_smoke/armtlb_injections.log  # 预期 ≥1
```

- [ ] **Step 2: 结局分类核对**（FS 分类先例：panic/Oops=Crash；存活=按 rcS 负载输出）——记录实际结局进 progress.md；若 log=0，先查 `--tlb_first_clock` 相对 checkpoint tick 的重基语义（arm_chaos_fs.py --ckpt_first_clock 块）再修参数，不视为注入器错误。

- [ ] **Step 3: Commit**（progress.md + 计划勾选）

---

### Task 4: lsu_b0_fs.py —— LSU-B0 FS 变体（DTLB=32）

**Files:**
- Create: `configs/fs/lsu_b0_fs.py`
- Modify: 无（新文件链 arm_chaos_fs.py，模式拷贝 kp920_proxy_fs.py 的 exec+链钩子）

**Interfaces:**
- Produces: `configs/fs/lsu_b0_fs.py`——行为=arm_chaos_fs 基线 + **B0 关键差**：DTLB=32 项全相联（02 表 r11；gem5 默认 64，W1 ③ 已核）+ LQ/SQ=16/16（02 表，与 kp920 V110 的 48/42 相区分）。T 系 FS 格的正式平台。

- [ ] **Step 1: 读 arm_chaos_fs.py 的 TLB mount 块**，确认 D-TLB 对象的获取路径（`--chaos_armtlb` 挂到哪个 ArmTLB 实例——mmu 内部 dtb 还是独立 SimObject；据此决定 size 覆盖写在 `_pre_instantiate` 链钩子还是 ArmBoard 参数）。
- [ ] **Step 2: 写 lsu_b0_fs.py**（骨架照抄 kp920_proxy_fs.py 的 63 行结构）：

```python
# lsu_b0_fs.py — LSU B0 FS platform (09 W7): arm_chaos_fs baseline +
# B0 deltas (02 表): DTLB=32 (S1 敏感性=64), LQ/SQ=16/16.
print("[lsu_b0_fs] arm_chaos_fs baseline + LSU-B0 deltas (DTLB=32, LQ/SQ=16/16)")
import os, sys
se_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "se")
exec(compile(open(os.path.join(se_dir, "arm_chaos_fs.py")).read(),
             "arm_chaos_fs.py", "exec"))

_b0_done = [False]
_orig_pi_b0 = getattr(cache_hierarchy, "_pre_instantiate", None)
def _apply_b0(root):
    if _orig_pi_b0:
        _orig_pi_b0(root)
    if _b0_done[0]:
        return
    _b0_done[0] = True
    # DTLB size: 按 Step 1 核实的对象路径覆写 (02 r11: 32 vs 默认 64)
    #   <tlb_obj>.size = 32 (全相联+LRU 是 ArmTLB 默认组织, W1 ③)
    # LQ/SQ (02 r7/r8): 仅 O3 restore 运行生效 — 非 O3 分支静默跳过
    core0 = processor.get_cores()[0]
    try:
        cpu0 = core0.core
        cpu0.LQEntries = 16
        cpu0.SQEntries = 16
        print("[lsu_b0_fs] B0 applied: DTLB=32, LQ=16, SQ=16")
    except Exception:
        pass  # Atomic/TIMING boot pass — 无 LQ/SQ
cache_hierarchy._pre_instantiate = _apply_b0
```

- [ ] **Step 3: 验证——用 lsu_b0_fs 重复 Task 2 Step 2 的 restore 冒烟**，并断言 config dump 中 DTLB size=32：

```bash
build/ARM/gem5.opt --outdir=runs/fs_lsu/b0_smoke configs/fs/lsu_b0_fs.py \
  --cpu O3 --restore-checkpoint "$CPT" --readfile configs/fs/m2_ptrchase.rcS 2>&1 | tail -3
grep -i "size.*32\|dtb" runs/fs_lsu/b0_smoke/config.ini | head -5   # DTLB=32 证据
```
注意：若 DTLB 是 checkpoint 序列化对象，size 覆盖可能只在 boot 阶段生效——若 restore 后 config 显示 64，则 checkpoint 需用 lsu_b0_fs 的 Atomic boot 重采（B0 平台自己的 cpt），如实执行。
- [ ] **Step 4: （如需）用 lsu_b0_fs 重采 checkpoint**——B0 平台的正式 cpt 落在 `runs/fs_lsu/boot_b0/cpt.<tick>`，此后 T 系全部用它。
- [ ] **Step 5: Commit + push**

---

### Task 5: T 系 campaign 解锁（FS 路由 + FS oracle/分类）

**Files:**
- Modify: `tools/lsu_campaign.py`（MODEL_FLAGS 加 T01-T04/T10；run_single_cell 加 FS 分支）

**Interfaces:**
- Consumes: Task 4 的 lsu_b0_fs + B0 checkpoint；arm_chaos_fs.py 的 `--chaos_armtlb/--tlb_*` 参数面。
- Produces: `FS_FAMILY` 分支——T 模型经 `configs/fs/lsu_b0_fs.py --cpu O3 --restore-checkpoint <b0_cpt> --readfile <负载 rcS> --chaos_armtlb ...` 运行；分类走 FS 通道（stdout 的 panic/Oops/`Kernel oops in guest` 退出事件=Crash；rcS 负载输出比对=Masked/SDC；`--timeout` 1800s）。
- 模式映射（faultType 全集已核，arm_chaos_fs.py:89-92）：`T01→bit_flip`、`T02→bit_flip+--tlb_fault_mask 按位宽或 bitsToChange`（以 CHAOSArmTLB.py:35 参数为准）、`T03→stuck_at_zero/stuck_at_one`（seed 奇偶交替）、`T04/T10→pfn_to_mapped_page`；T05-T08 本任务**仍留 deferred**（Task 7 之后实现——先锚点后新模式）。

- [ ] **Step 1: campaign 加 FS 分支**（run_single_cell 内：family=='armtlb' → config 换 lsu_b0_fs、cmd 集 `--restore-checkpoint`/`--readfile`/`--chaos_armtlb` 族、超时 1800、分类调 lsu_l5_classify 的 FS 判据——checksum 缺省时按 rcS 输出与退出码）。
- [ ] **Step 2: dry-run 断言**——T 系 42 格从 `blocked(fs-infra)` 变为 runnable（T05-T08 格仍 deferred）。
- [ ] **Step 3: 单格真机验证**（T01-F0-? 挑一个 MiBench/GAP 负载格——rcS 用现有 m2_ptrchase 先冒烟，正式负载在 Task 6）断言 injected≥1。
- [ ] **Step 4: Commit + push**

---

### Task 6: TLB-AliasPerm FS 负载（W4）+ MiBench/GAP FS 载体评估

**Files:**
- Create: `configs/fs/tlb_aliasperm.rcS`（+ 若镜像无合适二进制：`workloads/fs/tlb_walk.c` 静态编译入镜像的方案）
- Modify: `tools/lsu_campaign.py`（FS 负载表）

**Interfaces:**
- Produces: W4 负载格的运行载体。**决策树（实现时按序核实，不臆断）**：
  1. `ubuntu.img` 是否已含 TLB 压力工具（`debugfs`/`mincore` 类）——先 `strings gem5-fs/ubuntu.img | grep -i -m5 "busybox\|bash"` 确认基本环境；
  2. 若镜像可写（ext 镜像可 `debugfs -w` 或 loop 挂载）——把本仓 `workloads/directed/` 的静态二进制（AGU-AddrModes/STREAM 等本就 `gcc -O2 -static`）注入 `/root/lsu/`，rcS 逐个运行 + 输出回显（`m5 writefile` 回传或 uart 比对）；
  3. 若镜像不可写——诚实记录，W4 负载格维持 blocked(workload-not-on-image)，T 系 trial 先用镜像内已有负载（W1 MiBench 若在镜像；否则 GAP FS 化也依此判定）。
- 负载语义（06 表 W4）：TLB-AliasPerm = 大工作集多页遍历（触发 TLB miss/alias）+ 别名页权限访问——用 `workloads/directed/stream_chase`（已 static、golden 在册）作 TLB 压力代理为可接受近似，实测备注注明。

- [ ] **Step 1: 镜像内容核实**（决策树 1/2）
- [ ] **Step 2: 按核实结果落 rcS + 负载表**（或如实 blocked）
- [ ] **Step 3: 真机跑一格 W4 负载 T 格验证**（injected≥1 + 结局可分类）
- [ ] **Step 4: Commit + push**

---

### Task 7: TC'22 锚点复现（M3 门）+ T05-T08 模式实现

**Files:**
- Create: `runs/fs_lsu/tc22_anchor/`（锚点数据）
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.{hh,cc,py}`（T05-T08 四模式——**FS 已上电，模式变为可真机验证**，此前 deferred 决定解除）

**Interfaces:**
- Produces: M3 门判定（数字对 01 表 TC'22 行：Crash AVF≈50%、Hang≈10%、SDC AVF<1%）。

- [ ] **Step 1: T01 锚点 trial**（n=30 activated：`--phase trial --cells <T01 各负载格>`）。
- [ ] **Step 2: 判定**——Crash 份额落在 [0.2, 0.8]（宽容带）且 SDC < 5% → **M3 门通过**；Crash≈0 或 SDC 高 → 停下回修（锚点纪律：先注入器次负载）。
- [ ] **Step 3: T05-T08 模式**（W1 ③/§2.1 事件映射表已给落点：T05 valid/global/ASID 状态、T06 权限合法替换、T07 命中伪造/way 选择、T08 walk 配对——挂 `TLB::lookup`/PTW 路径；每模式 FS 真机验证 injected≥1 后才算实现）。
- [ ] **Step 4: 构建 + 回归**（reg_chain golden `f247ef3fe6c02cfd` 不变——TLB 注入器 SE-inert，零回归是结构保证）。
- [ ] **Step 5: Commit + push**（锚点结果 + 四模式，分开两个 commit：锚点数据一个、T05-T08 代码一个）

---

### Task 8: T 系 42 格 trial + 回填 + M3 收口

- [ ] **Step 1**: `--phase trial`（T 系全格；FS 并发=2）
- [ ] **Step 2**: 回填（blocked(fs-infra) → 试跑）+ 分族抽查 4 格
- [ ] **Step 3**: `docs/gem5-fi/lsu/12-m3-fs-results.md`（锚点对照表 + T 系谱 + 诚实边界）
- [ ] **Step 4**: Commit + push —— **M3 完成**

---

### Task 9: 多核 FS 冒烟（M4 前置：2 CPU boot + checkpoint）

**Files:**
- Create: `runs/fs_lsu/mc2_boot/`（双核 cpt）
- Verify: `configs/se/arm_chaos_fs.py` 的 CPU 数参数（实现时读配置：ArmBoard processor cores 列表 / `--num-cpus` 类参数，按实际参数名落命令）

- [ ] **Step 1**: 双核 Atomic boot + checkpoint（`armv8_gem5_v1_2cpu.dtb`；命令形态同 Task 2，仅 CPU 数/dtb 变化）
- [ ] **Step 2**: 双核 O3 restore 冒烟（rcS 起双进程负载验证两核都在跑——uart 输出两核交错为证）
- [ ] **Step 3**: Commit（progress.md 记录双核 cpt 路径）

---

### Task 10: W7 Atomic-Litmus 多核负载

**Files:**
- Create: `workloads/fs/litmus_pair.c`（双核 LDXR/STXR 竞争 + per-core 最终态 checksum——**沿用 atomics_probe 的设计纪律：校验和只覆盖最终数据态**）
- Create: `configs/fs/atomic_litmus.rcS`

- [ ] **Step 1**: litmus 负载（双核竞争窗口 + 各自 checksum 输出；native 不可跑多核→golden 语义=双核 gem5 无注入运行的对齐输出，如实记录与 SE 探针的差异）
- [ ] **Step 2**: rcS + 双核 restore 验证（无注入 baseline + O01/O03 注入各一，结局可分类）
- [ ] **Step 3**: Commit + push

---

### Task 11: O05-O07 多核语义评估与实现

**Files:**
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSExMon/`（多核模式——评估后实现）
- Modify: `tools/lsu_campaign.py`（O 系映射更新）

- [ ] **Step 1**: 语义评估（逐模式：O05 RMW 丢失/重复/提前 done——多核下=STXR 判定在竞争窗口的错乱，CHAOSExMon 的 monitor 置位/清除路径（isa.cc handleLockedRead/Write/Snoop）在多核下天然暴露跨核语义；O06 barrier completion、O07 order-tag swap——评估 gem5 内存系统可实现面）写成映射表（可实现/近似/deferred+原因）。
- [ ] **Step 2**: 可实现面落地（预期 O05≈stxr 判定类模式多核化、O07≈合法 order 交换需要新钩子可能 deferred——以评估为准，不预写结论）。
- [ ] **Step 3**: 每新模式双核真机验证（injected≥1 + 结局分类）。
- [ ] **Step 4**: Commit + push

---

### Task 12: 多核格 trial + PARSEC 诚实评估 + M4 收口

- [ ] **Step 1**: O 系多核格 + W7/W13 负载格 trial（FS 并发=2）
- [ ] **Step 2**: PARSEC 评估（镜像是否含 PARSEC——大概率不含；如实 blocked(workload-not-on-image) 或以 litmus/多线程代理近似并注明）
- [ ] **Step 3**: 回填 + `13-m4-multicore-results.md`
- [ ] **Step 4**: Commit + push —— **M4 完成**

---

### Task 13: ooo 轨道产物收割（统一数据模型）

**Files:**
- Create: `tools/ooo_harvest.py`
- Create: `artifacts/ooo-harvest/ooo-results.csv`

**Interfaces:**
- Consumes: `runs/` 下 100+ ooo 目录（pwf_v11/v12/v13 formal、method2 三臂、tlbf5_formal_fs、p20_h7_formal 等——每目录 results.jsonl/summary 形态先抽样核实）。
- Produces: 统一 CSV（track/unit/mode/workload/n/P_SDC/P_DUE/CI/source_run）——Task 14/15 的数据底座。

- [ ] **Step 1**: 抽样 5 个目录核实产物形态（results.jsonl 字段/summary 聚合有无）
- [ ] **Step 2**: 写收割脚本（字段映射 + Wilson CI + 来源目录列——每个数字可溯源到 run 目录）
- [ ] **Step 3**: 跑出全量 CSV + 抽查 5 行对源目录
- [ ] **Step 4**: Commit + push

---

### Task 14: 竞争矩阵（30 篇 ref 论文逐篇定位）

**Files:**
- Create: `docs/papers/competitive-analysis.md`

**Interfaces:**
- Consumes: `docs/papers/ref/` 30 篇（AVF 方法类 / gem5-FI 工具类（GemFI、MARVEL、CHAOS、Differential FI）/ 产线 SDC 类（PinDrop、Sentinel、SEVI、Fleetscanner、Silifuzz）/ 防御类（Harpocrates、ITHICA、Orthrus）/ DelayAVF、跨层传播类）；Task 13 的统一数据 + LSU 网格数据。
- Produces: 逐篇一行（它做什么 / 它不做什么 / 我们的对应资产与数字）+ 汇总差异声明（我们独有：事件归一触发 F0-F6 × L0-L5 错误生命周期 × 结构化五类故障模型 337 格 × FS 多核 × 保护反转 × 自适应统计）。

- [ ] **Step 1**: 逐篇读摘要+方法节（PDF 逐个 Read，30 篇分批）
- [ ] **Step 2**: 写矩阵文档（每篇 ≤6 行；差异声明引用我方具体 RunID/数字）
- [ ] **Step 3**: Commit + push

---

### Task 15: 论文骨架

**Files:**
- Create: `docs/papers/draft-skeleton.md`

- [ ] **Step 1**: 骨架（标题候选/摘要框架/贡献列表 4-5 条/方法-结果章节映射到三轨数据/核心图表清单：①错误生命周期图(L0-L5 全链) ②保护反转图 ③337 网格结局热图 ④TC'22+TC'23 锚点复现表 ⑤ooo×LSU 单元全景排序）
- [ ] **Step 2**: 目标会议评估（依竞争矩阵判定：MICRO/HPCA/ASPLOS/DSN/SC 各自 fit）
- [ ] **Step 3**: Commit + push —— 综合工作骨架就绪

---

## Self-Review 记录

- **Spec 覆盖**：M3（Task 1-8：FS 管线/T 系/锚点/B0 参数）✓；M4（Task 9-12：多核/litmus/O05-O07/PARSEC 诚实）✓；结合 ooo（Task 13 收割 + 14/15 定位与骨架）✓；T05-T08 的 deferred 决定在 FS 上电后解除（Task 7 Step 3）✓。
- **占位符扫描**：Task 4/5/6/9 含"实现时核实"步骤（TLB 对象路径/镜像内容/CPU 数参数名）——这些是**决策树+核实命令**（防臆断的探索步骤），每步给出了核实的具体命令与落点，非 TBD。
- **类型一致性**：`$CPT`/`b0_cpt` 路径在 Task 2→3→4→5 间传递；campaign 的 FS_FAMILY 接口与 lsu_l5_classify 的 FS 判据衔接；Task 13 CSV 列名与 Task 14/15 消费一致。
- **风险前置**：checkpoint 跨配置兼容（Task 4 Step 3-4 的 B0 重采分支）、镜像可写性（Task 6 决策树）、PARSEC 存在性（Task 12）——全部有诚实回退路径而非硬承诺。
