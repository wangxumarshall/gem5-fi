# 零前兆 77 分钟速死 + 撕裂移位族第 7 案（强推）：CPU 179 上 `find_busiest_group` 迭代 i=161 时 `__per_cpu_offset[161]` 装载为跨槽错相位窗口值

## 副标题：vmcore 127.0.0.1-2026-09-07-15:16:31 深度诊断报告（core179 第 19 次致命转储；kdump vmcore 文件缺失，dmesg 法证 + 代数闭合 + 形态学降级判定）

| 项 | 值 |
|---|---|
| 转储 | `127.0.0.1-2026-09-07-15:16:31/vmcore-dmesg.txt`（2642 行）。**vmcore 文件缺失**（目录内仅 dmesg），内存真值对照不可执行 |
| 内核 | 6.6.0-145.3.23.154.oe2403sp3.aarch64 #1 SMP（KASLR on） |
| 整机 | Yangtze Computing R240K V2/BC82AMQA，BIOS 7.48 06/15/2026 |
| CPU | 192 核 / 8 NUMA 节点，故障核 CPU 179 = MPIDR 0x7a0300，节点 7 |
| 崩溃时刻 | uptime 4615.69s ≈ 1.28h（约 2026-09-07 14:00 开机） |
| 崩溃进程 | HeapHelper（PID 57029，JVM 堆管理线程），futex_wait → newidle_balance 路径 |
| 唯一异常块 | CPU 179 / ESR=0x96000004 / FSC=L0 / FAR=`ffdbc44e0c5e98df`（非规范，"address between user and kernel address ranges"） |
| 前兆 | **零**。开机后无任何 WARNING/MCE/EDAC 事件（负证据，§4）——零前兆第 2 案（继第 11 次 11:00） |
| 子族 | 撕裂移位·跨槽错相位窗口【强推】（无 vmcore 不能窗口直读，区别于第 7/8/9 案实锤） |
| 报告产物 | 本报告 + `dmesg_forensics.txt` + `algebra.py`/`algebra_out.txt`（10/10 PASS） |

## 1. 执行摘要

1. **【实锤】** 与既往 fbG 案完全同型：`find_busiest_group+0x140/0xb60`，致命指令字 `(f9409377)` = `ldr x23,[x27,#0x120]`，Code 五指令字逐字相同；经 newidle_balance 进入（futex 睡眠触发），执行核 CPU 179。
2. **【实锤】** 代数闭合：`x27 = x1 + x20 (mod 2⁶⁴)` 与 `FAR = x27 + 0x120` 精确成立（python 复算，10/10 PASS）。KASLR 不变式三件套（x9−x1 / x21−x1 / x24−x21）全部成立，锁定 x1 = `&runqueues` 模板、同一确定性代码路径同一执行点。
3. **【实锤】** x20 实收 `ffdc206dfa4000ff`——非零、非对齐、非任何合法 per-cpu 偏移形态；x25=161（迭代 CPU 161 ≠ 执行核 179）。FAR 落用户/内核地址范围之间的非规范区 → L0 翻译故障，与撕裂移位族第 1/2/5/7/8/9 案几何完全一致。
4. **【强推】** x20 是 `__per_cpu_offset` 字节流的跨槽错相位 8 字节窗口（撕裂移位族第 7 案）：小端字节流 `ff 00 40 fa 6d 20 dc ff` 呈"上一槽尾字节 + 本槽低 6 字节"的跨槽拼接形态。**与第 2/5 案的 ≫8 形态（高 3 字节 00ffff）不同，是更接近第 9 案（非规范大值）的原样跨槽窗口**。因 vmcore 缺失无法做窗口直读比对（第 7/8/9 案的实锤法），子族归类降级【强推】。
5. **【实锤】** 零前兆第 2 案：从 94.7s（最后常规消息）到 4615.7s（panic）共 4521 秒 dmesg 完全静默，单发即死。继第 11 次（11:00）后再次证明 D1（装载腐化）可独立发作直接致命、不需 D3（PTW 瞬态）前兆铺垫。
6. 本案与案 18（同日 13:51，零塌缩）相隔约 1.4h 构成**同日双子族复发对**：同一缺陷核在连续两次开机中分别呈现零塌缩与撕裂移位两种交付形态——census §3 "同一选路失控的两种交付形态"模型的最直接印证。

## 2. 证据规则与方法

1. 一手证据：仅 `vmcore-dmesg.txt`（崩溃块寄存器转储是唯一数据源）；64 位运算 `algebra.py` 机器完成。
2. **诚实声明（本案核心限制）**：kdump 的 vmcore 文件缺失（目录内只有 vmcore-dmesg.txt，说明 crash kernel 完成了 dmesg 抢救但内存转储未落盘或未保存）。因此：内存真值对照、反事实 vtop、撕裂窗口直读比对**均不可执行**。凡依赖这些步骤的结论全部降级【强推】并注明验证途径（如能找回 vmcore 文件或复现后转储）。
3. 标注分级：【实锤】dmesg 内可复核；【强推】形态/代数收敛推断；【假设】微架构层。

## 3. 本次开机时间线【时间线】

| 时刻（uptime） | 事件 | 证据 |
|---|---|---|
| 0.000s | 开机（≈2026-09-07 14:00:15 CST 推算），KASLR enabled | dmesg L1/L3 |
| 0.330s | CPU179（MPIDR 0x7a0300）上线 | dmesg L1206 |
| 1.50s | ghes_edac 接管 DIMM（此后零硬件错误上报） | dmesg L2177 |
| 30.3s | ext4 挂载完成 | dmesg |
| 40.8~42.6s | firewalld/hns3 常规消息 | dmesg |
| 94.67s | **最后一条常规内核消息**（dm-2 capability deprecation），此后 4521 秒完全静默 | dmesg L2589 |
| 4615.69s | HeapHelper（PID 57029）futex_wait → newidle_balance → find_busiest_group 迭代 i=161，x20 装载为 `ffdc206dfa4000ff` → x27 非规范 → L0 → Oops → kdump | dmesg L2590 起 |
| 4616.10s | `Starting crashdump kernel...`（dmesg 被抢救保存；vmcore 内存转储未落盘） | dmesg L2641 |

## 4. 故障现象【故障现象】

dmesg L2590 起崩溃块原文（摘录）：

```
[ 4615.693020] Unable to handle kernel paging request at virtual address ffdbc44e0c5e98df
[ 4615.709613]   ESR = 0x0000000096000004
[ 4615.715628]   EC = 0x25: DABT (current EL), IL = 32 bits
[ 4615.723224]   FSC = 0x04: level 0 translation fault
[ 4615.750336] [ffdbc44e0c5e98df] address between user and kernel address ranges
[ 4615.866609] CPU: 179 PID: 57029 Comm: HeapHelper Kdump: loaded Not tainted
[ 4615.893784] pc : find_busiest_group+0x140/0xb60
[ 4615.908264] x27: ffdbc44e0c5e97bf ... x25: 00000000000000a1 ... x20: ffdc206dfa4000ff
Call trace:
 find_busiest_group+0x140/0xb60
 load_balance+0x108/0x6c0
 newidle_balance+0x198/0x510
 pick_next_task_fair+0x110/0x718 → __schedule → schedule → futex_wait_queue → futex_wait → do_futex → __arm64_sys_futex（用户态 HeapHelper 发起 futex）
[ 4616.074886] Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)
```

**负证据【实锤】**：全 dmesg `WARNING|Machine check|Hardware error|Bad mode|SError` 计数 0（仅有的两行 EDAC 是 0.87s/1.50s 的驱动初始化注册）。无任何前兆。

## 5. 业务现象【业务现象】

- 受害进程 **HeapHelper**（PID 57029）：JVM（某 Java 服务）的堆管理/GC 辅助线程，`Comm: HeapHelper` 是 JVM `ConcurrentGCThread` 族的典型命名。崩溃时它在 `futex(FUTEX_WAIT)` 等待 GC 协调点，睡眠入队触发 CPU 179 的 `newidle_balance`。
- 业务表现：机器第 19 次非计划重启（同日第 2 次，距案 18 重启约 1.4h），该 Java 服务中断。零前兆意味着应用层与监控层在崩溃前没有任何异常信号。
- 调度器负载均衡是全部 CPU 共享热路径，业务侧不可规避（census §5.6）。

## 6. 诊断定位过程【诊断定位过程】

**P1 勘察（dmesg）**：崩溃块六要素提取（§4）；零前兆负证据确认；无 MCE/EDAC 记录。

**P2 静态反汇编**（沿用同内核既有反汇编，见案 18 报告 §6 P2 与 crash_session2_vtop_dis.log，同一 #1 构建）：

```
find_busiest_group+300: ldp x0, x1, [sp, #8]     ← x0=&__per_cpu_offset[], x1=&runqueues
find_busiest_group+312: ldr x20, [x0, w25, sxtw #3]  ← w25=0xa1=161，装载 off[161]，实收 ff dc 20 6d fa 40 00 ff
find_busiest_group+316: add x27, x1, x20          ← x27 = ffdbc44e0c5e97bf（代数闭合 PASS）
find_busiest_group+320: ldr x23, [x27, #288]      ← (f9409377) FAR=ffdbc44e0c5e98df = x27+0x120（PASS）
```

**P3 动态取证**：**不可执行**（vmcore 文件缺失）。诚实声明：本案无法复算 off[161] 真值、无法 vtop 反事实地址、无法窗口直读。既往 12+5 案中同型不可验证案为第 2 次（08-17）与第 12 次（09-04-12:33），本案为第 3 例。

**P4 软件根因排除（基于 dmesg 可得证据）**：
- 代数自洽：x27=x1+x20、FAR=x27+0x120 双闭合，x20 是唯一自由变量且其装载位于坏指针链最上游；
- KASLR 不变式三件套成立（x9−x1 / x21−x1 / x24−x21 + x9 低 16 位 ae58），排除地址错位/寄存器错源；
- x25=161 与 x22==x26 一致性正常，迭代上下文完好；
- x23=0x400 残留与既往多数案相同（前次迭代 load_avg），表明前若干次迭代装载正常——损坏是单发瞬态而非持续；
- 若 x20 是软件可产生的值（越界读/未初始化），`__per_cpu_offset` 是静态已初始化数组、w25=161 在 [0,192) 界内，无软件路径产出 `ffdc…` 形态。

**P5 定论**：见 §8。

## 7. 逻辑链条（寄存器代数闭合）【逻辑链条】

`algebra.py` → `algebra_out.txt`，**10/10 PASS**：

```
x27 == x1 + x20 (mod 2^64)   ffdbc44e0c5e97bf = ffffa3e0121e96c0 + ffdc206dfa4000ff  PASS
FAR == x27 + 0x120           ffdbc44e0c5e98df                              PASS
x25 == 161 ≠ 179                                                            PASS
x9 - x1 == 0xfffffffffe5d1798 / x21 - x1 == 0x3f65f0 / x24 - x21 == 0x5350  PASS×3
x9 低 16 位 == ae58 / x23 == 0x400 / x22 == x26                              PASS×3
```

x20 撕裂形态（【强推】，形态学）：
- 小端字节流 `ff 00 40 fa 6d 20 dc ff`。合法 off 槽形如 `ffff XXXX YYYY e000`（小端 `…e0 00 YY YY XX XX ff ff`）。x20 的首字节 `ff`（上一槽最高字节）+ `00 40 fa 6d 20 dc`（跨槽窗口主体）+ 尾部 `ff`，符合"跨槽 +非对齐字节窗口"的结构（与第 7 案槽 125+2B、第 8 案槽 123+1B、第 9 案槽 9+5B 同族）。
- ROL6B(x20) = `00ffffdc206dfa40`——旋转后呈现 `00ffff` 前缀（≫8 形态特征字节），提示窗口字节流与第 2/5 案同源数组、不同相位。
- 反事实不可验证：x27_true = `&runqueues + off[161]` 的 off[161] 真值无法读出（vmcore 缺失）。

## 8. 故障根因【故障根因】

**【强推】撕裂移位族第 7 案**：`ldr x20,[x0,w25,sxtw#3]` 在 CPU 179 上把 `__per_cpu_offset[161]`（真值应为 `ffffXXXXYYYYe000` 形态的非零合法偏移）装载为字节流跨槽错相位窗口值 `ffdc206dfa4000ff`。归类依据：x20 非零非合法形态 + 非规范 FAR + L0 FSC + 代数闭合 + x25≠179 + 零前兆——与已实锤的第 1/5/7/8/9 案全部几何特征吻合；缺内存真值比对故降级【强推】。

**【假设】微架构层**（与 census §3 一致）：CPU 179 核私有 load 返回通路（fill-buffer 合并/返回 mux）错相位交付；本案窗口相位未能测定（无法直读），但从形态看不同于 1/2/3/5 字节已测相位，可能为 6/7 字节相位或负相位窗口——census §2.3 预测"3~7 字节相位仍可能出现"的又一枚候选样本。

**同日双子族复发对**【实锤】：案 18（13:51，零塌缩/L2）与本案（15:16，撕裂/L0）相隔约 1.4h、同一物理核、同一指令、同一数组、两种交付形态——"同一选路失控的两种交付形态"（census §3 根因模型第 4 条）的最强同日印证。

## 9. 启示【启示】

1. **零前兆第 2 案**：D1 可独立发作直接致命（继第 11 次后再次实证）。被动遥测（spurious fault 监控）对这类开机完全没有拦截机会；census §5.4 的"被动+主动 SBST 组合"结论再添一枚边界样本。
2. **kdump 落盘可靠性是法证能力边界**：本案 dmesg 抢救成功但 vmcore 未落盘，导致实锤降级为强推。对这类单核 SDC 排查，**vmcore 完整落盘比 dmesg 更关键**——建议核查该机 kdump 配置（disk 满？dump 目标路径？压缩失败？），否则后续案件的真值对照链会持续缺失。
3. **同日双子族对**：零塌缩与撕裂在同日连续两次开机分别出现，进一步否定"两种子族是不同缺陷"的可能，任何修复/RMA 验证方案都必须同时覆盖两种形态。
4. 处置建议（第 19 次重申）：立即 offline CPU179 并持久化；整机 RMA；核查 kdump 落盘配置。

## 附录：命令索引

```
# dmesg 法证（全部输出存 dmesg_forensics.txt）
grep -cE "WARNING: CPU|Machine check|Hardware error|Bad mode|SError" vmcore-dmesg.txt   # = 0
sed -n '2590,2642p' vmcore-dmesg.txt                                                    # 崩溃块全文
# 代数
python3 algebra.py   # 10/10 PASS
# 反汇编依据（同内核 #1 构建，案 18 目录）
docs/cases/vmcore-diagnosis-report-127.0.0.1-2026-09-07-135142/crash_session2_vtop_dis.log
```
