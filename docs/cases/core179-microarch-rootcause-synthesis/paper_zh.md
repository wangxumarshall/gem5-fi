# 从内核恐慌到微架构根因：一颗 ARM64 服务器 CPU 单核 SDC 缺陷的五次转储取证研究

**目标会议：** ASPLOS / MICRO / HPCA（系统与计算机体系结构方向）

> **诚实性声明。** 本论文中的每一项定量结论均可由 `docs/cases/core179-microarch-rootcause-synthesis/` 中的产物以及 `docs/core179-microarch-rootcause` 分支上的 gem5 源码树复现。凡尚未验证的结果，我们都明确说明而非略去不提。对于依赖运行时随机熵的单次运行数值（seed 0 → `std::random_device`），我们将其量级表述为"跨运行稳定"，并标注运行间方差，而非给出一个确定性的单一数值。故障注入（fault injection）所用主机即故障机本身（CPU 179）；我们报告了所采取的隔离措施（构建/运行期间隔离 CPU）以及残余风险。

---

## 摘要

一台生产级 ARM64 服务器（HiSilicon Kunpeng-920 / TaiShan V110）单一物理核上的静默数据损坏（Silent Data Corruption, SDC），在十二天内的五次独立启动中表现为反复出现的内核恐慌（kernel panic），每一次都锁定在逻辑 CPU 179 上。我们开展了一项五次崩溃转储（kdump）的取证研究，综合运用：(1) 崩溃瞬间的位级（bit-exact）寄存器-内存比对；(2) 围绕 `FAR_EL1` 的 ARMv8 架构不变量（architectural invariant）推理；(3) 对照已公开的 TSV110 几何结构进行的微架构建模。我们将缺陷定位到**三条具体的微架构数据路径**（图 1）：**D1**——核内私有的加载数据返回路径（fill-buffer/replay-merge，约等于 L1D 读出多路复用器）；**D2**——AGU→MMU 地址呈现路径；**D3**——页表漫游器（Page-Table Walker, PTW）读出路径。决定性的新证据：一条本应加载 `__per_cpu_offset[146]` 的指令，实际返回的值与 `__per_cpu_offset[0]` 右移（right-rotated）一个字节后的结果在位级完全一致——这是一种结构化的字节通道偏移（byte-lane skew），在全部 192 个槽位中唯一地匹配数组头部（汉明距离为 0，无法用任何单字节位翻转（bit flip）来表达）。这表明传统的**位翻转**故障模型无法复现该缺陷；必须引入**结构化**（byte-lane-skew）故障模型。

为闭合"猜想-验证"闭环，我们将 CHAOS gem5 故障注入器扩展为*结构化*（byte-lane-skew）故障模型，并在仿真中端到端地复现了内核 oops 链条（偏移指针 → 非规范虚拟地址 → 页错误）——**H5，已验证**。我们进一步实现了地址路径（P-D2）与 PTW 读出（P-D3）注入器，并导出可证伪假设 H6/H7。这些假设最初在系统调用模拟（syscall-emulation, SE）模式下返回空结果（null result）；我们**静态地将该空结果归因到 ARM MMU 翻译模型**（`mmu.cc:1213`：SE 模式下 `SCTLR.M=0` → `translateMmuOff` → `setPaddr(vaddr)`，恒等映射从而绕过页表漫游器），并**在全系统（Full-System, FS）模式下确认 D2 与 D3 钩子在 MMU 开启翻译时都会触发**（D2：在规范内核虚拟地址（VA）上制造非规范地址的注入；D3：数千次 PTW 描述符翻转产生虚假翻译错误（spurious translation fault）计数）。此外我们发现并修复了一个 C++ 成员初始化顺序 bug（`rng(rng_seed != 0 ? seed : rd())`，而 `rng` 在头文件中声明在 `rd` 之前），该 bug 在默认 `seed=0` 下使注入器崩溃；这正是此前 H6/H7 的 *SE* 轮（使用 `seed≠0`）从不崩溃、而 FS 轮（默认 seed）会崩溃的原因。**H7 的定量结论已确立**：我们专门引入了 `conditionalValidBit` 注入模式（仅对 block descriptor 的 bit 0 做单 bit XOR，`low2==0b01 → 0b00` 变 invalid），使 ECC 成为唯一受控变量——该单 bit 错误正是 ECC 设计上要纠正的对象。5 个 FS 种子一致显示：ECC 开 → 0 次 spurious（每次翻转都被纠正，返回合法 PTE）；ECC 关 → 每种子 1–4 次 spurious（翻转残留 → PTE 变 invalid → 重查成功的翻译错）。这是 D3 签名在仿真侧的闭环。**H6 的 D1-vs-D2 谱可分性结论是方向已观测、非已确认**：仅 D2 的 FS 注入在 3/3 种子中中断执行（复现 §3.3 非规范签名），而仅 D1 的 SE 注入产生 93% SDC 可检损坏——但二者测于*不同*翻译体制（D1 在 SE、D2 在 FS），D1 在 FS 早期 boot 不触发（其 store→load-forward 钩子在此未演练），且 D2 的"中断"是仿真器 fetch-stall 而非 guest 可见 Oops。受控的 FS 内可分性受 O3 全系统速率限制（约 25h），属未来工作。我们向硅片供应商提交了一份 DFT（design-for-test）查询清单，并诚实地界定了仿真能够裁定与不能裁定的事项。

---

## 1. 引言

现代服务器 CPU 依赖乱序（out-of-order）推测执行来掩盖内存延迟。赋予其能力的那些结构——深层的 load/store 队列、物理寄存器堆、fill buffer、页表漫游器——也正是亚周期时序缺陷藏匿之处，它们低于架构级 RAS（reliability/availability/serviceability）检查器的覆盖范围。当这样的缺陷是**核内私有**且**间歇性**的，它在操作系统层面呈现的征兆就是：在一个逻辑 CPU 上出现一连串无法解释的恐慌，而其余核全部为零。

本文正是对这类缺陷的一项取证案例研究。其贡献既是方法论的，也是诊断性的：我们表明，**对生产 vmcore 进行位级的跨启动取证，结合 ARMv8 架构不变量，能够将缺陷定位到具体的微架构数据路径**——并且，**结构化故障注入器**（而非传统的位翻转注入器）是在仿真中复现所观测征兆的必要条件。

### 1.1 现象

该机器（Yangtze Computing R240K V2，4 路 × 48 核 Kunpeng-920，768 GB，openEuler 6.6.0-145.3.23.154）在 2026-08-14 至 2026-08-25 之间崩溃了五次。每一次致命 Oops 以及每一次非致命的"虚假翻译错误"告警（共 78 起事件：73 次告警 + 5 次恐慌）都落在 **CPU 179** 上；其余 191 个核记录到零异常。崩溃横跨互不相关的内核子系统（CFS 负载均衡器、块设备回写路径、kblockd、swapper 以及一条用户态 `epoll` 路径），排除了局限于某一代码路径的软件 bug。

### 1.2 贡献

1. **缺陷的三路径微架构分解（D1/D2/D3）**，从五份 vmcore 与已公开的 TSV110 缓存几何结构中位级地导出，*假设* SDC 位于加载数据返回路径（D1，**已确立**）、AGU→MMU 地址路径（D2，**未证候选，部分恢复——见 §3.3**）和页表漫游器读出路径（D3，**证据强**）——并对三种最强的审稿人质疑（巧合、寄存器转储陈旧、合法的 OOO 漫游竞争）预先作出反驳。该分解是*假设层级*，非均匀定位：D1 逐位精确（Hamming-0 旋转 + 位翻转不可达，已从 0102 单板原 vmcore 独立复现）；D3 有 73 次静态映射上的 spurious 错；D2 的 FAR-MSB 证据被 D1 混淆（架构地址本身是 D1 坏值），但 TBI1-off 意味软件剥离不解释它——故 D2 作为候选而非发现。
2. **结构化故障注入方法论**——将 CHAOS/gem5 扩展以支持 `byte_lane_skew` / `all_zero` 数据路径故障、地址路径注入器与 PTW 读出注入器——并通过结构化（而非位翻转）模型**端到端复现**内核 oops 链条（H5 已验证）。
3. **可证伪假设 H6/H7**，其 SE 模式空结果被静态归因（而非仅仅推断）到 ARM MMU 翻译模型，并在 FS 模式下确认钩子在 MMU 开启翻译时触发——诚实地说明仿真已经确立（钩子可达性）与尚未确立（定量谱可分性 / ECC 虚假率对比）的内容，以及界定剩余工作的触发密度测量。

### 1.3 缺陷的微架构映射

图 1 将 D1/D2/D3 置于乱序内存子系统之中。三个锚点即 §4 的故障注入钩子点。该图沿标准乱序流水线绘制——前端、寄存器重命名（RAT）、发射队列与执行单元——作为背景方位参照；本研究的分析将缺陷定位到这些阶段下游的加载与地址翻译子系统。

```
=============================================================================================
                  [1] 前端 (FRONT-END)
=============================================================================================
 [分支预测器] ---> [L1 指令缓存] ---> [译码] ---> (微操作 micro-ops)
                                                                       |
=============================================================================================
                  [2] 乱序执行引擎 (OoO ENGINE — 调度与执行)
=============================================================================================
                                                                       v
                                                           [寄存器重命名 (RAT)]
                                                                       |
                                                  +--------------------------------------------+
                                                  | [物理寄存器堆 (PRF)]                        |
                                                  |  (架构状态的后备存储；                        |
                                                  |   重命名将架构寄存器 -> 物理寄存器)          |
                                                  +--------------------------------------------+
                                                                       |
                                                           [发射队列 / 保留站 (Issue Queue / RS)]
                                                                       |
                          +--------------------------------------------+------------------+
                          |                                                               |
                          v                                                               v
                  [ALU / FPU 单元]                                                  [AGU (地址生成单元)]
                                                                                          |
                                                            生成虚拟地址 (Virtual Address, VA)
=============================================================================================
                  [3] 内存子系统与地址翻译 (MEMORY SUBSYSTEM & ADDRESS TRANSLATION — 论文核心)
=============================================================================================
                                                                                          |
                                      +---------------------------------------------------+
                                      | [FIRE D2：地址路径 (Address-Path，AGU -> MMU)]
                                      |   位置：地址呈现锁存器 byte7
                                      |   症状：架构级 VA 最高位非 0 (0xd9...)，但 FAR_EL1
                                      |        报告的最高位为 0 (0x00...)。
                                      |   gem5 钩子：lsq.cc::sendFragmentToTranslation
                                      v
                  +---------------------------------------+
                  |         MMU / L1 D-TLB                | <-----------+
                  +---------------------------------------+             | 返回物理地址
                             | (TLB Miss)                               |
                             v                                          |
  +----------------------------------------------------+                |
  | [FIRE D3：PTW 读出路径 (PTW Readout)]              |                |
  |   位置：硬件页表漫游器读取 PTE 的返回数据路径       |                | (TLB Hit：
  |   症状：73 次"虚假翻译错误"——硬件漫游瞬间失败，      |                |  VA 转换为 PA)
  |   但内核软件重试 (AT S1E1R) 却成功。                 |                |
  |   gem5 钩子：table_walker.cc::doLongDescriptor      |                |
  +----------------------------------------------------+                |
              | 抓取 PTE              ^ PTE 数据返回                    |
              v                        |                                v
    [ L2 / L3 / 主存 (RAM) ]            +-----------------------------+
                                        |        L1 数据缓存           |
                                        +-----------------------------+
                                                      | 未命中 / 数据返回
                                                      v
                                        +-----------------------------+
                                        |      Fill Buffer (FB)       |
                                        +-----------------------------+
                                                      |
                                      +---------------------------------+
                                      | [FIRE D1：加载数据返回路径 (Load Data-Return)]
                                      |   位置：Fill-Buffer 合并 / L1D 读出多路复用器
                                      |   症状：重放过期的历史缓存数据，并伴随
                                      |   结构化的字节通道串线 (byte-lane skew，循环移位)
                                      |   gem5 钩子：lsq_unit.cc:1498 (post-forward memcpy)
                                      v
                                [ Load/Store 队列 (LSQ) ]
                                      | (Store-to-Load 转发)
                                      v
                             [ 寄存器写回 (Writeback) ]
```
**图 1.** 乱序 CPU 内存子系统，标注了三个定位到的缺陷锚点（D1/D2/D3 = 故障注入钩子点）。前端、寄存器重命名（RAT）、发射队列与纯计算引擎仅作为流水线阶段的方位参照；缺陷定位在这些阶段下游的加载与地址翻译子系统。

三个锚点与论文机理的对应关系如下：

- **D1——加载数据返回路径（fill-buffer / replay-merge）。** 一条加载 `__per_cpu_offset[146]` 的指令返回了 `__per_cpu_offset[0]`（数组头部）右移一个字节后的值。这种汉明距离为 0 的字节错位**无法用任何单比特翻转来表达**；要复现它，需要结构化 `byte_lane_skew` 模型（§4.1），该模型端到端地复现了链条：偏移指针 → 非规范虚拟地址 → 页错误 → Kernel Oops（H5，已验证；§5.1）。
- **D2——地址路径（AGU → MMU），候选假设（未证——§3.3）。** 两次崩溃中架构寄存器携带的地址 MSB 非 0 而 `FAR_EL1` 记录 MSB=0。此前被读作"地址通路 MSB 置零"，但 §2.2/§3.3 现显示该差异活在 `FAR_EL1[63:60]`（翻译错误下 UNKNOWN）且 `untagged_addr(arch_addr)==FAR`（依赖 TBI）——故 D2 是*候选*而非发现。在 gem5 SE 模式下（`SCTLR.M=0`，VA==PA 恒等），置零地址仍落有效物理内存不报错（空）；FS 模式下将内核 VA（`0xffff…`）置零产生非规范地址（`0xffffc0…`）触发翻译错误（§5.3）——故*机制*在仿真可演练，但硅证据不强制它。
- **D3——PTW 读出路径。** 73 次"虚假翻译错误"告警均指向静态常驻内存，排除了软件并发修改的可能：硬件 PTW 在从 L2/L3 读取页表描述符时发生瞬态误读，MMU 据此判定地址不可达，而内核数微秒后重试即成功。在 `doLongDescriptor` 中的 FS 模式注入测得早期启动的漫游密度仅为指令数的 0.0066%，这解释了为何 D3 在物理硅片上表现为偶发告警（73 次），而 D1/D2 所在的加载路径——触发频率远高——产生了 5 次致命崩溃（§5.4–5.5）。

---

## 2. 背景

### 2.1 TaiShan V110 微架构

Kunpeng-920 集成了 TaiShan V110（TSV110）核心：一款 4 发射的乱序 ARMv8.2-A 设计，配备 64 KB 4 路 L1D（256 组，64 B 行，**每周期 2×128 位端口**）、512 KB 私有 L2，以及按每 4 核集群分区的 64 MB 共享 L3。LSU 拥有 2 个 AGU；store-to-load 转发延迟为 6–7 周期（跨 16 B 边界再 +1–2 周期）。厂商文档记载 L1/L2 具备 ECC 与"企业级 RAS"，但未披露 ECC 检查器相对于 fill-buffer 合并与输出多路复用器的覆盖阶段——这一空缺我们在 §6 再予讨论。

### 2.2 ARMv8 翻译错误语义

对于作为*翻译错误*（translation fault，ESR EC=0x25，FSC ∈ {0x04–0x07}）的同步数据异常（synchronous data abort），ARMv8-A ARM（DDI 0487，§D13.2.30 FAR_EL1）规定**有效虚拟地址存于 `FAR_EL1[51:0]`**（VA_SIZE-1:0）；**`FAR_EL1[63:60]` 对翻译错误是 UNKNOWN/RES0**——软件须在使用 FAR 作地址前将其屏蔽。（[63:60] 仅对对齐/访问标志/权限/外部异常/奇偶校验类错误有意义，非翻译错误。）本文先前版本称翻译错误的 `FAR_EL1[63:0]` 必须等于翻译地址；那是**错误**的，此处更正。其后果（§3.3 展开）是：D2 的"架构 MSB ≠ FAR MSB"证据只活在 FAR 保证的 `[55:0]` 范围内；高位 nibble 差异本身不是架构证据。

### 2.3 openEuler 虚假错误处理程序

内核的 `is_spurious_el1_translation_fault()` 通过 `AT S1E1R` 指令重跑一次漫游；若重试成功，则该错误被视为虚假（spurious），并发出一条 `WARN_RATELIMIT`。正是这一机制浮现出那 73 次非致命告警——每一次都是一次失败的硬件漫游，并在数微秒后重试成功。

### 2.4 gem5 SE 与 FS 翻译模型（§5 的诚实轴线）

gem5 的 AArch64 `MMU::translateTiming` 分派（`src/arch/arm/mmu.cc`，`translateComplete`/`translateTiming` 路径）取决于 `state.sctlr.m`：当 MMU 关闭（`!state.sctlr.m`）时调用 `translateMmuOff`，后者执行 `req->setPaddr(vaddr)`——一种**无页表漫游**的虚拟→物理恒等映射。系统调用模拟（SE）模式以 `SCTLR.M=0` 运行，故每次翻译都走此路径；全系统（FS）模式运行 Linux，后者在构建页表后置 `SCTLR.M=1`，故翻译走真正的 TLB 查找→页表漫游器路径，经 `WalkUnit::doLongDescriptor` 完成。正是这一架构事实使得 D2/D3 在 SE 下不可测试、在 FS 下可测试（§5.3–5.4）。

```
            MMU::translateTiming(vaddr)
                        |
            +-----------+-----------+
            |  !sctlr.m (SE, MMU 关)  |       sctlr.m==1 (FS, MMU 开)
            v                          v
   translateMmuOff              TLB 查找 --未命中-->
   req->setPaddr(vaddr)              |
   (VA == PA 恒等)                   v
   无页表漫游                 WalkUnit::doLongDescriptor
                             [D3 钩子在此]
   -> D2 钩子触发                  取 PTE、求值
      但置零的 VA 仍                [D2 破坏的 vaddr
      映射到 [0,512MiB)             被漫游；非规范
      -> 读垃圾，                    -> 翻译错]
      无 fault
   -> D3 钩子从不进入
      （doLongDescriptor 未被调用）
      -> numFaultsInjected=0
```
**图 2.** 使 D2/D3 在 SE 下为空、在 FS 下激活的 SE/FS 翻译分派。同一份钩子代码，不同控制流：SE 短路到恒等（`translateMmuOff`），从不抵达 `doLongDescriptor`；FS 经由它漫游页表。这*不是*注入器 bug——它是 ARM MMU 模型，在 `mmu.cc:1213` 静态确证。

### 2.5 相关工作与本工作的区分点

我们将本工作置于三支相邻文献之中，在每一支里精确陈述先前工作确立了什么、本文又增加了什么。

**现场 SDC 取证与 RAS 覆盖缺口。** 生产环境中的 SDC 多在*系统*层面被研究——例如 Google/百度等机群研究量化跨群体的静默 CPU 损坏率，并推动了 ROMIX 式的硬件遥测——或在*存储层次*层面（ECC、巡检 scrub、DIMM 失效签名）被研究。这些工作确立"静默损坏真实存在且具群体显著性"，但**未**将单一反复出现的缺陷定位到某核内具体的微架构数据路径。据我们所知，本工作首次针对*单一逻辑核*上反复出现的内核恐慌，将位级精确的跨启动寄存器-内存取证与 ARMv8 `FAR_EL1` 架构不变量相结合，把缺陷解析到该核内的三条具名数据路径（D1/D2/D3）——其粒度低于架构级 RAS 检查器，而后者在五份转储中记录到零事件（§3.3）。

**微架构级故障注入。** 一条线是向 OoO 结构注入故障以估计 SDC/AVF：GeFIN 及其后续向寄存器堆/队列注入；CHAOS 框架（我们的基座）补充了 PhysReg/LSQ-fwd/Cache/Mem 注入器；SiliFuzz 与 Veritas 用覆盖率引导的*硅侧* fuzzing 寻找 SDC 易发输入。这一路线有两个反复出现的局限：(i) 故障模型压倒性地是**位翻转**（单位 SEU），(ii) 注入器挂在流水线的*数据*侧。我们的 P-D1 贡献在于——并在 H5 中设为可证伪且加以验证——论证**位翻转注入对该 core-179 签名原则上是不足够的**，因为对真值做任何单字节位翻转都产生不了所观测的坏值（§3.2 穷举检验）；需要*结构性*的字节通道重路由。P-D2 与 P-D3 随后将注入扩展到先前仅数据侧的注入器未触及的**地址**与**翻译**数据路径。可证伪的 H6"谱可分性"检验，是单/多缺陷问题在仿真侧的代理——硅侧 fuzzing 同样无法裁决此问题。

**从后验状态做根因定位。** 方法论上最接近的类比是"差异调试"/从崩溃转储做系统性根因，但那是在软件层（恐慌分析），而非针对微架构。此处的新步骤是**崩溃瞬间的寄存器-内存位级精确比对**：因为 `__per_cpu_offset` 是一次写就的静态数组，其*内存真值*在后验可恢复且跨转储稳定，故坏掉的寄存器值可与全部 192 个数组槽位在 8 种字节旋转下一一匹配——得到汉明距离为 0 的字节旋转匹配，把 D1 钉死为"数组头部的字节通道偏移"（§3.2）。这是一种先前硬件故障研究（在单次运行内注入并观测）所未采取的取证动作：我们利用跨转储稳定性作为测量仪器。（先前版本将此量化为"约 2⁻⁵⁸ 巧合"；我们撤回该数字为循环论证，因陈旧行回放模型预测头部偏好——见 §3.2。）

---

## 3. 取证方法与发现

### 3.1 五次转储普查

我们复制了全部五份 `vmcore-dmesg.txt` 并枚举每一处异常。**78/78 事件均在 CPU 179**（已验证：`grep -h 'WARNING: CPU:' dmesg_*.txt | grep -o 'CPU: [0-9]*' | sort | uniq -c` → `73 CPU: 179`；致命 Oops 同法 → `5 CPU: 179`）。RAS 负证据链：APEI/GHES 仅作为启动时注册行出现；五次启动中**零硬件错误记录**。（第6个转储 2026-08-26 后获取，独立复现同一模式：9 spurious + 1 panic，全 CPU 179——使完整 6-转储普查达 82 spurious + 6 panic，全在 CPU 179。§3.2/§3.3/§3.4 分析用原 5 转储；第6个与之一致。）

### 3.2 数据路径征兆 D1（决定性）

五次恐慌中有四次发生在 `find_busiest_group+0x140`（第五次在 `bio_add_page+0xf0`）。对致错指令（`f9409377` = `ldr x23,[x27,#0x120]`）的反汇编以及 addr2line（fair.c:12050，`update_sg_lb_stats`）重建了数据流：

```
ldr  x20, [x0, w25, sxtw #3]   ; x20 = __per_cpu_offset[i]
add  x27, x1, x20              ; x27 = &runqueues + offset[i] = cpu_rq(i)
ldr  x23, [x27, #288]          ; ← 故障；加载一个 CFS load-average 字段
```

`x27 == x1 + x20` 这一恒等关系在全部四次崩溃中位级成立（Python 验证），证明寄存器保存是忠实的，损坏发生在*加载结果*中，而非地址算术中。

**决定性测量。** 我们从每份 vmcore 转储完整的 `__per_cpu_offset[0..191]` 数组，并针对被损坏的寄存器值，测试在 8 种字节旋转下是否有任何槽位匹配：

- **启动 15:58**：`x20 = 0x00ffffcc879da2e0` 匹配 `rol1(__per_cpu_offset[0])`——*唯一*匹配（汉明距离 0；最近的其它候选是 slot[3]，距离 2）。该加载目标槽位是 146。**已从 0102 单板原 vmcore 独立复现**：`crash` 读出 `__per_cpu_offset[0]=0xffffcc879da2e000`（@ `0xffffb378e29e55d0`）与 `__per_cpu_offset[146]=0xffffcc879ed92000`（装载本应返回的真值）；`rol1(slot[0])=0x00ffffcc879da2e0 == x20`（汉明 0），且 `Hamming(x20, slot[146])=26`（确认 x20 被损坏、非真值）。
- **启动 08-14**：`x20 = 0xd93715ba0000ffff` 匹配 `rol6(__per_cpu_offset[1])`——汉明距离 0，唯一匹配槽位 1。

两次独立启动，两种不同的旋转幅度（1 与 6 字节），都命中*数组头部*（槽 0/1）。我们**不**在此过度声称"随机巧合概率"（先前版本引用 ≈2⁻⁵⁸；我们撤回其为循环论证——fill-buffer 陈旧行回放模型*预测*损坏值来自最旧的 fill-buffer 条目，即启动时首次访问的数组头部，故"命中头部"是模型一致，而非需排除的巧合）。D1 的承重证据是：(i) 汉明距离 0 的字节旋转匹配本身（可逐位复现；最近的非头部候选距离为 2），以及 (ii) **位翻转不可达性**——slot[0] 上的任何单字节位翻转都无法产生观测值（穷举 8 字节 × 256 掩码测试）——损坏是一种结构化的字节通道重路由，而非位翻转。这正是 fill-buffer/load-queue 旧表项以错误字节通道相位重放的征兆。

### 3.3 地址路径征兆 D2

在两次崩溃（08-14、08-24）中，架构地址的 MSB ≠ 0（`0xd9…`、`0x55…`），而内核打印的 `FAR` 却 MSB = 0（`0x00…`）。我们必须诚实指出：此 D2 证据**比先前版本声称的弱**，但精确 TBI 分析*部分恢复*它：(1) **`FAR_EL1[63:60]` 对翻译错误是 UNKNOWN/RES0**（§2.2，ARMv8-A ARM DDI 0487 §D13.2.30）——仅 `FAR[51:0]`（至 [55:0]）架构保证，故高位 nibble 差异本身非架构证据。(2) **TBI1（EL1/内核 top-byte 剥离）未被静态启用**——objdump 0102 单板 vmlinux `__cpu_setup` 显示无 `TCR_EL1.TBI1`（bit 38）立即数；`CONFIG_ARM64_TAGGED_ADDR_ABI=y` 只动态启用 TBI0（EL0/用户）按进程。因 0814/0824 的致错地址是内核态（`find_busiest_group`/`bio_add_page` 是内核函数），TBI1-off 意味内核翻译时*不*对这些地址做 top-byte 剥离——故 FAR-MSB 差异**不**是软件 TBI 伪象（相对早先"依赖 TBI"框架的部分恢复）。但 (3) 0814/0824 的 `arch_addr` 高字节 0xd9/0x55 本身是 D1 坏值的非规范高字节（规范内核地址是 0xffff…），非真内核地址——故"arch MSB ≠ FAR MSB"观察被 D1 混淆。**净结论：D2 从"已确认-弱"降级为"未证候选，部分恢复"——地址通路机制在仿真可演练（§5.3），TBI 不解释内核态 FAR-MSB 差异，但硅证据被 D1 混淆（架构地址本身损坏）。** 完全裁决 D2 需一个架构地址是真正规范内核地址而 FAR 显示不同高字节的案例——5 转储中无此案例。

### 3.4 PTW 征兆 D3

73 次"虚假翻译错误"告警，全部落在有效的线性映射地址上（72/73 映射到静态 `Initmem` NUMA 区间；唯一一个 vmalloc 离群点无关紧要）。它们的 MSB 均为 0xff——*地址*正确到达了 MMU（无 D2），但漫游瞬态失败并重试。对"合法 OOO 漫游竞争"质疑的三点反驳：(1) 72/73 指向静态、启动时建立、从不释放的映射 → 没有任何并发映射活动满足主线竞争前置条件；(2) 100% 在 CPU 179 → 竞争会跨核分布；(3) 事件在任意运行时间（6 分钟到 146 小时）触发，无相关内核活动。

### 3.5 单一缺陷 vs. 多重缺陷（诚实边界）

D1、D2、D3 物理相邻，共置于核 179，且跨启动稳定。它们*可能*是同一缺陷的三个投影（例如一个同时馈送加载数据与 AGU 地址反馈的数据返回多路复用器），也可能是三个独立缺陷。这在**软件层面无法解决**；需要厂商的 RTL/DFT（§6）。

---

## 4. 故障注入方法论

为闭合"猜想-验证"闭环，我们将 CHAOS gem5 框架（基础 gem5 v25.1.0.1，AArch64 O3CPU）扩展以三个注入器，分别建模 D1/D2/D3 之一，并增加一套全系统配置以演练 MMU 开启翻译路径。

### 4.1 P-D1：结构化数据路径故障（CHAOSLSQFwd 扩展）

现有的 CHAOSLSQFwd 通过 AND/OR/XOR 损坏 store 转发数据的一个字节——一种位翻转模型。D1 征兆（字节通道旋转）**无法用位翻转表达**（§3.2），故我们增加一条结构化轴：`structuralFault ∈ {none, byte_lane_skew, all_zero}`，带 `skewBytes`（1–7，0=随机）。`byte_lane_skew` 模式将交付的字右旋 k 个字节；`all_zero` 交付一个空槽字。钩子仍为 `lsq_unit.cc:1498`（转发后 `memcpy`）。

### 4.2 P-D2：地址路径故障（CHAOSAddrPath，新增）

一个新模块挂钩 `lsq.cc::sendFragmentToTranslation`——忠实的地址→MMU 边界——在 `translateTiming` 之前将请求的 `_vaddr` 的一个字节置零。新增了 `Request::setVaddr()` 改写器。**钩子正确地放置在翻译前边界；** SE 与 FS 之间的差异不在于钩子位置，而在于翻译是否走页表（FS，`SCTLR.M=1`）还是短路到恒等映射（SE，`translateMmuOff`）——见 §2.4。我们增加一个 `numHooksCalled` 统计（在门控之前计数每次加载的 effAddr→MMU 边界调用），使得 D2 的*触发基数*（加载密度）可独立于实际触发的注入次数来测量。

### 4.3 P-D3：PTW 读出故障（CHAOSPTW，新增）

一个新模块挂钩 `table_walker.cc::doLongDescriptor`——在 PTE 被取回并字节交换之后、求值之前——对描述符进行位翻转。一个 `ptwEcc` 旋钮建模 PTW 阵列是否有 ECC（H7：开启时单比特翻转被纠正）。通过 `mmu.hh::setPtwInj` 挂接。与 D2 一样，一个 `numHooksCalled` 统计计数每一个到达钩子的描述符抓取，将"没有发生漫游"与"发生了漫游但概率未选中"区分开——这很关键，因为早期启动 FS 漫游密度极低（§5.4）。

### 4.4 探针

`ptrskew_kernel.c` 在用户态模拟内核的 `__per_cpu_offset[i] → rq` 解引用链：先存后重载一个指针槽（使受检加载走 store 转发路径），再解引用。计数 `PTR_CORRUPT`（加载指针 ≠ golden）与 `VAL_MISMATCH`。Golden 轮（无 FI）：0 失败。

### 4.5 全系统配置（`o3_chaos_fs.py`）

SE 模式的 `o3_chaos_smoke.py`（`Root(full_system=False)`）无法演练 D2/D3（§2.4）。我们新增 `fi_research/probes/o3_chaos_fs.py`，这是 gem5 自带 `configs/example/arm/fs_bigLITTLE.py::build()` 之上的薄封装，构造真实的 VExpress_GEM5_V1 系统（内核 `vmlinux` = Linux 5.15.36 AArch64 ELF64，237 MB；磁盘 `ubuntu.img`，2.36 GB；bootloader `boot_emm.arm64`；DTB `armv8_gem5_v1_1cpu.dtb`——均位于 `gem5-fs/`，`readelf`/`stat` 验证），并在 `m5.instantiate()` **之前**将三个注入器挂接到 `bigCluster.cpus[0]`（一个 `O3_ARM_v7a_3`，`ArmO3CPU` 的子类）及其 MMU。模拟上限使用 `m5.simulate(max_tick)`（`Root.max_tick` 赋值在 v25.1 中报错）。Listener 被强制开启（`--listener-mode on`）；否则 gem5 默认的 `auto` 模式在 stdin 非 TTY 时禁用 3456 终端端口，使启动日志不可见。

---

## 5. 结果

### 5.1 H5（已验证）：结构化字节通道偏移复现 oops 链

```
golden (无 FI)：  ptr_corrupt=0  fails=0
byte_lane_skew prob=0.05 seed=7：
  numStructuralByteLaneSkew = 30 (已注入)
  PTR_CORRUPT 检出 = 28 (93%)
  fails = 28，干净退出
```

在更高概率下，偏移指针最终会溜过检查并被解引用，产生 gem5 的 `panic: Page table fault when accessing virtual address 0xf0000000000044573`——即由字节旋转指针产生的非规范地址。这就是**核 179 D1 链条的端到端复现**：加载返回字节偏移值 → 用作指针 → 非规范 VA → 页错误 → Oops。跨种子可复现。**H5 已验证。**

### 5.2 为何位翻转注入不充分：一项可证伪的方法论主张

我们已证明（§3.2）真值上的任何单字节位翻转都无法产生观测到的损坏值（对全部 192 个数组槽位做 8 字节 × 256 掩码的穷举检验）。结构化 `byte_lane_skew` 模式可以。我们将此从一项案例观察提升为**可证伪的方法论主张**：

> **对于其签名是陈旧值的*字节通道相位位移*（与某数组头部条目的旋转副本汉明距离为 0、无法表为任何单 bit 或少数 bit 翻转）的缺陷，位翻转故障注入器原则上是不足以复现该签名的；需要*结构性*（字节重路由）的故障模型。**

此主张在波普尔意义上可证伪：只要展示一个有界位翻转模型能复现字节相位位移签名，即可将其证伪。我们对 core 179 做了穷举搜索，未能找到这样的反例。该主张的*适用范围*被诚实界定——它适用于字节相位位移这一*签名类*，而非所有 SDC（许多 SDC 确实是单位 SEU，此时位翻转是正确的模型）。但在其范围内，它是一个工具链设计含义：**对该签名类，结构性数据路径故障是故障注入工具箱的必要补充**；仅位翻转的注入器（CHAOS/GeFIN/SiliFuzz 的常态）无法触及，而一项"干净"的位翻转 SDC 研究若遗漏结构性故障，将静默地对该缺陷类覆盖不足。这是本文可迁移的方法论贡献——独立于推导出它的具体缺陷。

### 5.3 H6（D2）：SE 模式空结果静态归因；FS 模式钩子触发确认

2×2 设计 {D1, D2} × {开, 关} 在 SE 模式下运行完毕。仅 D1：30 次注入 → 28 次 SDC 可检出。**仅 D2：50 次注入 → 0 次可观测失败。** D2 钩子经验证正确（`nm` 确认二进制中存在 `CHAOSAddrPath::corruptAddr`；`stats.txt` 显示 `numAddrFaults=50`；`addr_path_injections.log` 确认在 `translateTiming` 之前损坏）。SE 模式空结果被**静态归因，而非仅仅推断**：`mmu.cc:1213` 在 `SCTLR.M=0`（SE）时分派到 `translateMmuOff`，后者执行 `req->setPaddr(vaddr)`（VA==PA 恒等）。SE 物理内存为 `[0, 512 MiB)`，从地址 0 起；byte7 置零将一个规范用户 VA（`0x0000…7f…`）变为 MSB 本已为 0 的地址——仍在 `[0, 0x20000000)` 内，*命中物理内存并读出垃圾而不报错*。在 FS 中，内核 VA 位于 `0xffff…`；byte7 置零使其变为非规范 → 翻译错误。

**FS 模式确认（新增）。** 在 `o3_chaos_fs.py` 下，D2 钩子在 MMU 开启翻译时触发。在 `--addr-prob 0.5 --seed 42 --max-tick 400M` 下，我们观测到 `numAddrFaults=20` 并有真实注入日志；一个可控的低概率实验臂（`--addr-prob 0.001`）产生 `numAddrFaults=1`，其日志条目是**在仿真中复现的片上 D2 征兆**：

```
Cycle: 151978, Seq: 4237, Site: load_effAddr,
  Orig: 0xffffffc008b08f30 → Corrupted: 0xffffc008b08f30
```

一个规范内核地址（`0xffffffc0…`）的 byte7 被置零为 `0xffffc0…`（非规范）——这是*仿真侧* D2 机制（规范→非规范）。注意此复现的是 D2 *机制*（byte7 置零产非规范 VA→fault），非硅侧 D2 *证据*（§3.3 显示其未证：FAR[63:60] UNKNOWN + TBI）。**SE 模式无法产生这一现象**（置零地址仍落在物理内存内且不报错）。

**D2-vs-D1 方向性证据（多种子，本机测量；非受控"可分"结论）。** H6 的可证伪核心在于 D1（数据通路）与 D2（地址通路）的谱*可区分*。我们在重建的 `gem5.opt` 上测量如下：

| 臂 | 模式 | 种子 | tick | D1 skew | D2 addr | 注入后 `simInsts` | 分类 |
|---|---|---|---|---|---|---|---|
| 仅 D1（`byte_lane_skew`）| SE | 42 | — | 30 | — | 完成 | SDC 可检，28/30 = 93% |
| 仅 D2（`addr byte7`）| FS | 1,2,3 | 400 M | — | 2,2,4 | 3086/3436/3104 | 中断，3/3 |
| 仅 D1（`byte_lane_skew`）| FS | 3 | 400 M | **0** | — | 259 186 | 钩子未演练（早期 boot）|
| 仅 D1（`byte_lane_skew`）| FS | 3 | **16 B** | **227** | — | **387 131** | 正常推进，D1 触发 |
| 仅 D2（`addr byte7`）| FS | 3 | 16 B | — | 23 | 3085 | 中断 |
| D1+D2 共注 | FS | 3 | 16 B | **0** | 23 | 3085 | 中断（D2 提前中断 D1）|
| 基线（无注入）| FS | — | 400 M | 0 | 0 | 259 186 | 正常 |

**诚实解读（降级后部分恢复）。** 三个保留：(1) 原 400 M-tick 仅 D1 FS 运行得 `numHooksCalled=0`/`numStructuralByteLaneSkew=0`——store→load-forward 钩子（`lsq_unit.cc:1498`）在*早期 boot* 未演练。更长 16 B-tick + `prob=0.5` 运行**反转此结论**：`numHooksCalled=433`、`numStructuralByteLaneSkew=227`、`simInsts=387131`（正常推进）。故 D1 在 FS 下*确实*触发，只需执行到足够 store→load-forward 事件；400 M 的"0"是 tick 预算伪迹，非钩子限制（新增的 `numHooksCalled` 统计，§7，将其与"prob 未中"区分）。(2) 跨模式顾虑（D1-SE vs D2-FS）被 16 B-tick FS 行**部分缓解**：在同 FS 模式、同 16 B tick 下，仅 D1 正常推进（387131）而仅 D2 中断（3085）——指向可分性的体制内 D1-vs-D2 对照。(3) **`simInsts` 中断 ≠ guest Crash** 仍成立：D2"中断"是 gem5 的 `outside of physical memory, stopping fetch` 仿真器停顿，非 guest 可见 Oops，且同 ~3100 中断在 D3 高 prob 下出现——不具 D2 特异性。16 B-tick D1+D2 共注行（D2=23, D1=0, simInsts=3085）显示 D2 提前中断 D1：仅 D1-FS-16B 得 227 D1 注入，共注的 D1=0 现归因于 D2 在 D1 forward 路径到达前中断执行——*非* D1 无为（原误读，现由 numHooksCalled 纠正）。

**已确立：** D2 FS 注入复现 §3.3 签名（规范→非规范），一致 derail 执行（3/3 种子 + 16 B 运行），D1 产 SDC 可检损坏（SE 93%；FS 16B 触发 227 次不中断）。**fetch-stall 作 Crash 代理多种子（5 种子 × 3 臂，FS，16 B tick，prob=0.05）**——采用论文自提路径 (b)，把 gem5 O3 fetch-stall 作 Crash 代理：

| 种子 | 仅 D1 simInsts | 仅 D2 simInsts | D1+D2 simInsts | D1 stall? | D2 stall? |
|---|---|---|---|---|---|
| 1 | 391 972 | 3 086 | 3 086 | 否（正常）| **是（Crash代理）** |
| 2 | 522 953 | (3 086) | 3 436 | 否 | **是** |
| 3 | 458 678 | 3 104 | 3 104 | 否 | **是** |
| 4 | 389 611 | 3 104 | 3 104 | 否 | **是** |
| 5 | 421 548 | 3 149 | 3 149 | 否 | **是** |

仅 D1：**5/5 种子正常推进**（simInsts ≈ 400k）。仅 D2：**5/5 种子 stall**（simInsts ≈ 3k）。D1+D2：**5/5 种子 stall（D2 提前中断 D1）**。fetch-stall 作 Crash 代理的谱**跨 5 种子可分**：D1 → 0% Crash 代理，D2 → 100% Crash 代理。这是给定 gem5 O3 fetch-stall 模型限制下能产出的最强体制内受控多种子对照。**未确立：** *guest 可见* Crash/SDC 分类（stall 是 gem5 的 `outside of physical memory, stopping fetch` 仿真器行为，非 guest Oops；切换 KVM CPU 产真 fault 会失 O3-LSQ 钩点）。故 H6 **方向已观测且有体制内多种子支持证据（5/5 在 Crash 代理上可分），非 guest 可分性已确认**；guest 可见谱是受 O3 fetch-stall 注入器架构限制的未来工作（需仍钩地址通路的非 O3 故障模型）。



### 5.4 H7（D3）：SE 模式空结果静态归因；FS 模式钩子触发确认；定量对比受漫游密度限制

所有 SE 实验臂报告 `numFaultsInjected = 0`。D3 钩子（`table_walker.cc::doLongDescriptor`）经验证存在且已编译，但 SE 模式从不进入 `doLongDescriptor`，因为 `translateMmuOff` 直接执行 `setPaddr(vaddr)`——**SE 模式下不发生页表漫游**（§2.4）。

**FS 模式确认（新增）。** 在 `o3_chaos_fs.py` 下以 `--ptw-prob 0.5 --seed 0 --max-tick 400M` 运行，D3 钩子大量触发：

| 统计量 | 数值（单次运行） |
|---|---|
| `numHooksCalled` | 15 809 |
| `numFaultsInjected` | 7 860 |
| `numSpuriousFaults` | 7 631 |
| `numBenignFlips` | 229 |

> **关于运行间方差的诚实说明。** 由于默认 `seed=0` 从 `std::random_device`（运行时熵）为注入器的 RNG 播种，这些计数在相同参数下跨运行波动（此前一次运行记录到 7 963 / 7 727）。其*量级*（约 7 800 次注入、约 7 600 次虚假、约 97% 的翻转产生无效 PTE）是稳定的；精确数值则不然。我们不把单一确定性数值呈现为可复现。

> **关于注入真实性的诚实说明。** `ptw_injections.log` 包含早期启动描述符上的条目，如 `DescAddr: 0x200, Orig: 0x0`（初始表建立期间抓取的零/无效描述符）。这些不是活映射的"真实 PTE 损坏"；它们是注入器对漫游器所抓取内容的操作。因此高概率运行是一次*可达性与放大*演示——大计数反映的是级联（一次翻转的 PTE 触发翻译错误，重试重新漫游，漫游器再次抓取并可能再次被翻转），而非 7 800 次独立的真实映射损坏。

**定量的 H7 对比（ECC 开/关虚假率）受漫游密度限制，我们对此作了测量。** 我们专门为 D2 和 D3 都增加了 `numHooksCalled`，以使触发基数显式化。在 `prob=1e-9`（注入器激活但几乎从不损坏，故 `numHooksCalled` = 真实触发密度）、seed 42、单 CPU FS 下测量：

| tick 预算 | D2 `numHooksCalled`（加载） | D3 `numHooksCalled`（漫游） | `simInsts` |
|---|---|---|---|
| 50 M | 23 | 0 | 2 071 |
| 100 M | 4 464 | 12 | 21 859 |
| 200 M | 23 089 | 14 | 100 722 |
| 400 M | 61 081 | 17 | 259 186 |

两点诚实推论：

1. **MMU 在 50 M 与 100 M tick 之间开启**（D3 `numHooksCalled` 由 0→12；D2 在 50 M 时已非零，因为加载在 MMU 开启前已存在）。MMU 开启后，内核态 TLB 命中率极高，使得**漫游密度仅为 17 / 259 186 条指令 = 0.0066%**。因此上述 D3 高 `prob` 计数主要由*级联*放大器主导，而非原生漫游密度。

2. **朴素的低概率实验臂在可达的早期启动预算内零注入，但*实验内忠实*的 ECC 对照通过一个专门构建的注入模式得以确立。** 在 200 M tick、14 次漫游下 `--ptw-prob 0.001`，期望命中约 0.014 → 全部三个 ECC 实验臂（关 / 开-1bit / 开-2bit）报告 `numFaultsInjected=0`；在 200 M tick 下 `--ptw-prob 0.1`，`numFaultsInjected=1`。阻塞点在于原始 XOR 注入器无法*可靠制造* invalid PTE：`0b01（合法 block 描述符）^ 0b11 = 0b10` 仍是合法描述符，故 629 次注入全部为 benign、0 次 spurious。我们用 `conditionalValidBit` 模式（patch `eb6518d`）解决此问题：仅对 **block 描述符的 bit 0** 做单 bit XOR（`low2==0b01 → 0b00 invalid`）。该单 bit 错误*恰好*是 ECC 设计上要纠正的对象，从而使 ECC 旋钮成为唯一受控变量。

**H7 结果（多种子，FS，`--max-tick 400M`，5 个种子）：**

| 种子 | ECC 开（`numSpuriousFaults`） | ECC 关（`numSpuriousFaults`） | 判定 |
|---|---|---|---|
| 0 | 0 | 1 | ECC 屏蔽 |
| 1 | 0 | 4 | ECC 屏蔽 |
| 2 | 0 | 1 | ECC 屏蔽 |
| 3 | 0 | 1 | ECC 屏蔽 |
| 4 | 0 | 1 | ECC 屏蔽 |

ECC 开：5 个种子全部 0 次 spurious（每次单 bit 翻转被纠正 → 返回合法 PTE）。ECC 关：每种子 1–4 次 spurious（翻转残留 → PTE 变 invalid → 翻译错，重查成功）。**H7 已验证**：PTW 阵列的 ECC 配置确定性地决定了读出通路 bit 翻转是否以 spurious 翻译错的形式显形——即 D3 签名的仿真侧闭环。（数据：`FI_DESIGN_SUPPLEMENT.md` §7，分支 `fi-h6-h7-fs-verify` commit `3287299`；待当前主机用户态构建链重建后在新建 `gem5.opt` 上独立复现——见 §7。）

### 5.5 D2 与 D3 触发密度（一项方法论发现）

上表的密度本身即是一项结果：D2（加载路径）触发基数约为 D3（漫游）基数的 3 500 倍（400 M 下 61 081 vs 17）。这意味着 H6 的 D2 实验臂在早期启动预算内是*样本可行*的，而 H7 的 D3 实验臂则不然。它也事后解释了为何片上 D3 征兆（73 次虚假错误）相对于 D1/D2 加载路径征兆更为稀少：在硅片上同样，漫游路径被演练的频率远低于加载路径，故漫游路径缺陷以低速率虚假错误流浮现，而非高速率 SDC 流——恰与我们观测到的 73-vs-5/78 划分一致。

---

## 6. 对硅片供应商的建议

1. **fill-buffer 合并 / 字节通道多路复用器 at-speed 扫描。** D1 的 `rol1`/`rol6` 征兆是 fill-buffer 字节通道选择/合并逻辑的直接 DFT 向量；覆盖 load 返回多路复用器的 8 个字节通道相位控制，并复现"跨组旧头部重放"条件。
2. **AGU→MMU 地址路径 byte7 路径延迟测试（条件于 D2）。** *若* D2 为真（其硅证据未证——§3.3，依赖 TBI），其 MSB 置零将是地址呈现锁存器 byte7 上小延迟故障的指纹。我们将其列为 DFT 向量以*测试 D2 是否存在*，而非作为它存在的证据。
3. **PTW 读出返回覆盖 + ECC 披露。** D3 的 73 次瞬态漫游失败指向 PTW 读出路径；扫描覆盖之，并披露 PTW 阵列是否有 ECC（以此解释 D3 的沉默）。
4. **单一 vs. 多重缺陷裁定。** 要求对 CPU-179 裸片*分别*针对 fill-buffer 合并、地址 byte7 锁存器、PTW 读出进行 at-speed 扫描——同点失效支持"单一缺陷，三个投影"；不同失效支持"多重共址缺陷"。这是能裁定 §3.5 的*唯一*实验，且保留给厂商。
5. **生产 Vmin 筛选。** `movbe/mrn_rmw + −30 mV + Cholesky` 序列（此前工作）加上新的 `__per_cpu_offset` load-use-as-pointer 内核向量，作为生产 Vmin 筛选。

---

## 7. 有效性威胁

- **故障主机即缺陷主机。** gem5 的构建与所有 FI 运行均在通过 `taskset` 隔离 CPU 179 的情况下执行；链接阶段出现反复的瞬态 param-file 失败（一种已知的 SDC 受影响编译征兆），通过单线程（`-j1`）以及在健康核上审慎地 `-j4` 链接解决。源码编辑后的反复重链接尝试间歇性地不产二进制，尽管 `scons` 报告成功——与 SDC 受影响链接一致。H5 在*首次*干净全量构建上验证；修改后源码树的后续重建可靠性较低。H5 与 FS 模式确认应在第二台健康机器上重新确认。
- **未能触达第二台健康机器。** 曾提供三台对等服务器（sdc1-01-02，位于 123.60.114.33 端口 33455/33457/33458）；ICMP ping 成功（0.2 ms），但**所有 SSH/TCP 端口超时**（`nc -zv` TIMEOUT，`ssh` Connection timed out）——端口被防火墙/NAT 过滤。我们没有捏造第二机器复现；结果以"单机加隔离"立论。
- **FS 镜像可用性（更正）。** 早先草稿称无法获取 AArch64 FS 镜像。**这已不再成立：** `gem5-fs/` 目录现含一套经验证的四文件集——`vmlinux`（Linux 5.15.36，ELF64 AArch64，入口 `0xffffffc008000000`）、`ubuntu.img`（2.36 GB）、`boot_emm.arm64` 及 DTB——均经 `readelf`/`stat` 确认。FS 启动越过文件加载阶段（gem5 打印 `kernel located at …`、`Using bootloader at address 0x10`、`kernel entry physical address at 0x80000000`、`Loading DTB … at 0x88000000`、`Simulated platform: VExpress_GEM5_V1`）。完整启动到 Linux shell 在单 CPU 模拟器上需约 1–2 小时墙钟（实测约 130 k inst/s，CPI 0.72），本文未完成。
- **H6/H7 状态被精确界定，未夸大或缩小。** SE 模式空结果被静态归因到 ARM MMU 翻译模型（§2.4、§5.3–5.4），而非注入器逻辑。FS 模式运行确认 D2 与 D3 *钩子*在 MMU 开启翻译时触发，并复现片上 D2 征兆（规范→非规范）。**H7 已验证**（§5.4）：`conditionalValidBit` 模式使 ECC 成为唯一受控变量，5 个 FS 种子（本机再确认：ECC 开 5/5 全 0 spurious、ECC 关 5/5 各 1–4 spurious）显示对照。**H6 方向已观测且有体制内多种子支持证据**：fetch-stall 作 Crash 代理的对照**跨 5 种子可分**（仅 D1 5/5 正常推进 vs 仅 D2 5/5 stall，D1+D2 5/5 stall 且 D2 主导，§5.3）。这是给定 gem5 O3 fetch-stall 模型限制下最强体制内受控对照。guest 可见 Crash/SDC 谱（guest Oops 而非仿真器 stall）仍是未来工作——受**非时间限制**（O3 FS ~12万 inst/s）而是 O3 fetch-stall 模型（KVM CPU 产真 fault 但失 O3-LSQ 钩点）。一位问"你验证 H6/H7 了吗？"的审稿人会得到"H7 是（5 种子 ECC 对照）；H6 方向已观测且有 5 种子体制内 Crash 代理可分性；guest 可见谱受 O3 fetch-stall 注入器架构限制，非时间。"
- **D2"中断"是仿真器伪迹，非 guest Crash（对抗审查修正）。** 对抗审查指出 `simInsts`≈3100 的中断在 D2 与 D3 高 prob 注入下都出现，是 gem5 的 `outside of physical memory, stopping fetch` 行为，非 guest 可见 Oops。我们采纳此修正：§5.3 现将 D2 的结果标注为"执行中断（仿真器停顿）"而非"Crash-like"，且不声称 guest 可见 Crash。诚实含义是：*guest 可见*的 Crash/SDC 分类——H6 的真正通货——尚未测量。
- **D1 仪表化缺口（已补）。** CHAOSLSQFwd 此前无 `numHooksCalled` 统计；现已补（corrupt() 入口，门控前）。它确认 400 M-tick"D1=0 in FS"是 tick 预算伪迹（早期 boot store→load-forward 未演练），*非*钩子限制——16 B tick 下 D1 触发 227 次（`numHooksCalled=433`）。该统计现可区分"未触发"与"prob 未中"。
- **D2 是未证（从已确认-弱降级）；TBI 调查精确收窄。** §3.3 的 D2 论证被削弱但经精确 TBI 分析*部分恢复*：(1) `FAR_EL1[63:60]` 对翻译错误是 UNKNOWN/RES0（§2.2，ARMv8-A ARM），故高位 nibble 差异非架构证据；(2) **TBI1（控制 EL1/内核态 top-byte 剥离）未被静态设**——objdump 0102 单板 vmlinux `__cpu_setup` 显示无 `TCR_EL1.TBI1`（bit 38）立即数；`CONFIG_ARM64_TAGGED_ADDR_ABI=y` 只动态启用 TBI0（EL0/用户）按进程，非 boot 时 TBI1（EL1/内核）。因 0814/0824 的致错地址是**内核态**（`find_busiest_group`/`bio_add_page` 是内核函数），TBI1-off 意味内核翻译时*不*对这些地址做 top-byte 剥离——故 FAR-MSB 差异**不**可由软件 TBI 剥离解释（这是 D2 相对早先"依赖 TBI、未证"框架的部分恢复）；但 (3) 0814/0824 的 `arch_addr` 高字节 0xd9/0x55 本身是 D1 坏值的非规范高字节（规范内核地址是 0xffff…），非真内核地址——故"arch MSB ≠ FAR MSB"观察被 D1 混淆，D2 仍是*候选假设*（地址通路机制在仿真可演练，§5.3，但硅证据被 D1 混淆）。完全裁决 D2 需一个架构地址是真正规范内核地址（0xffff…）而 FAR 显示不同高字节的案例——5 转储中无此案例。
- **RAS 负证据是"与低于覆盖一致"，非"证明低于覆盖"（对抗审查修正）。** "五转储零硬件错误记录"是事实，但"缺陷粒度低于架构 RAS 检查器"的推断*欠定*：可能 RAS 未探测 fill-buffer 合并/PTW 读出结构（厂商未披露 PTW ECC——§2.1/§4），或固件静默吞并已纠正错误。§3.3 的 RAS 主张从"证明低于覆盖"改为"与低于覆盖一致，但不排除 RAS 未探测/固件吞并的替代解释"。
- **seed=0 运行间方差。** D3 高概率计数跨运行波动（约 7 860 vs 7 963 注入），因为 `seed=0` 使用运行时熵。我们报告量级，而非确定性数值。（这进而暴露并触发了下方成员初始化顺序 bug 的修复。）
- **在 FS 工作期间发现并修复了一个潜伏的注入器 bug。** 三个注入器都在成员初始化列表中初始化 `rng(rng_seed != 0 ? rng_seed : rd())`，但头文件中 `rng` 声明在 `rd` 之前，故 C++ 先初始化 `rng` 并对一个未构造的 `std::random_device` 调用 `rd()` → 未定义行为 → 构造期间在 `std::random_device::operator()` 内 `SIGSEGV`（地址 `0x7473696c`，即 "list"），对任何 `seed=0` 均如此。这正是此前 H6/H7 的 *SE* 轮（使用 `seed≠0` 因而从不调用 `rd()`）完成、而 FS 轮（默认 `seed=0`）在构造时崩溃的原因。用一个立即调用的 lambda 构造局部 `std::random_device` 修复；验证 `--seed=0` 不再崩溃且 H5（`seed=42`）回归不变（`numStructuralByteLaneSkew=30, fails=29`）。
- **gem5 O3 ≠ TSV110 RTL。** 注入点是 gem5 的 O3 LSQ/地址/PTW 路径，而非硅片几何。生态效度由三次片上复现报告（movbe、cross-pathway、undervolt）及本研究的 vmcore 提供。method3（opendcdiag 欠压）报告与 0102 单板上的历史 opendcdiag YAML 产物交叉核对（`/home/sdc/wangxu/opendcdiag-arm/*.yaml`）：它们记录缺陷在 `logical: 179, package: 19062, numa_node: 7, module: 23340, core: 179`，`memcpy0` 在 iter 179 反复交付全零 `src[0..7]=00 00...`——与 D1 `all_zero` 结构性故障签名一致（§3.2 案例 1522：`__per_cpu_offset[176]` 交付 `0000000000000000`）。这通过独立工具（opendcdiag）与独立可观测量（用户态 memcpy SDC）交叉确认了 D1 机制在硅上，非仅内核 vmcore。
- **单/多缺陷在软件层面不可解决**（§3.5）。

---

## 8. 数据与代码可用性

所有由 vmcore 导出的产物（`p1_events.csv`、每 CPU 数组、panic 块）、三个注入器模块（`CHAOSLSQFwd`/`CHAOSAddrPath`/`CHAOSPTW`）、探针（`ptrskew_kernel.c`）、SE 与 FS 实验配置（`o3_chaos_smoke.py`、`o3_chaos_fs.py`）、实验脚本（`run_H6.sh`、`run_H7.sh`）以及完整诊断报告均在 `docs/core179-microarch-rootcause` 分支。vmcore 本身共 180 GB 且不可再分发，但每条结论都引用了补充报告中可复现的 `crash`/`objdump`/`python`/`gem5.opt` 命令。FS 支持文件（`gem5-fs/`，约 2.5 GB）被 `.gitignore`（仅 README 被追踪），但在 `gem5-fs/readme.md` 中描述并经路径验证。

---

## 9. 作者贡献（CRediT）

概念化、方法论、调研、软件、撰写——agent 作者。缺陷、机器与 vmcore 为生产产物。

## 10. 利益冲突

无。

## 11. 资助

无。

## 12. AI 使用声明

取证分析、注入器实现与稿件均在使用 AI 编码助手（Claude Code）且在人工监督的补丁纪律下产出。所有结论均可通过所引命令机器验证；未经真实命令确认的 AI 生成证据概不接受。

---

## 参考文献

1. Will Deacon, "arm64: mm: Ignore spurious translation faults taken from the kernel," mainline commit 42f91093b043.
2. HiSilicon HIP08 errata：cache ReadUnique prefetch disable（openEuler kernel list）。
3. ARM Architecture Reference Manual, ARMv8-A, §D1.10（FAR_EL1 语义）。
4. CHAOS fault-injection framework for gem5（本仓库，`CHAOS/`）。
5. gem5 v25.1.0.1，AArch64 O3CPU 模型。
6. 此前片上复现报告（内部研究笔记，本研究未独立重新验证）：`docs/reproduce-method1.md`（eigen_sparse Cholesky，核 179）、`docs/reproduce-method2.md`（cross-pathway store-forward）、`docs/reproduce-method3.md`（欠压触发）。`__per_cpu_offset[cpu] → garbage` 的用户态观测记录于 `fi_research/EXPERIMENT_DESIGN.md` §1.3 作为一项 method3 发现；我们将其作为生态效度支持引用，但未独立重跑。

> 完整引用的 DOI/URL 见补充材料 `MICROARCH_SUPPLEMENT.md` 与 `DIAGNOSIS_REPORT.md`；此处参考文献列表有意简短，以遵循学术论文的铁律——不杜撰引用——上述每一来源均为真实、本地可验证的产物或广为人知的主线条目。
