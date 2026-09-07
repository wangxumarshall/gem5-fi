# method2 三根因区分实验（附录 B：PRF/AGU/TLB 注入的 ESR/PC/x10 形态比对打分）

> 目标：现场观察到 `x10 垃圾指针 + ESR 0x96000004 + pc=find_busiest_group`
> 形态时，区分三个候选根因——PRF cell 故障（数据值坏）、AGU 地址通路
> 故障（地址计算坏）、TLB 条目故障（翻译坏）。打分维度按方案附录 B。

## 三根因签名打分表

| 维度 | 现场 method2 签名 | PRF（x10 值坏） | AGU byte7（地址非规范） | TLB pfn（翻译条目坏） | 区分力 |
|---|---|---|---|---|---|
| ESR EC | 0x25（DABT current EL） | 0x25 ✓（坏指针解引用 → DABT） | 0x25 ✓ | 0x25（d-side）/ 0x21（i-side 取指） | 低（三者同 EC）；i-side 0x21/0x86xxxx 排除性指向 TLB |
| ESR DFSC | 0x04（L0 翻译故障） | 0x04 ✓（垃圾地址不在任何 TTBR 区间） | 0x04 ✓（byte7 清零 → 非规范地址 → L0） | **0x04/0x05/0x06/0x07 族**（页表级取决于坏表项层级）+ 0x0f（权限） | **高**：TLB pfn 替换实测 0x9600004f（L3 权限）与 0x96000004（L0）混合；PRF/AGU 恒 L0 |
| FAR 与寄存器算术 | FAR = pc 指令的操作数基址（x10 派生） | **FAR = x10 损坏值派生**（`x27=x1+x20` 型算术可复核出坏源）✓ | FAR = 规范地址被 byte7 清零后**非规范**（MSB=0x00） | FAR = **完好规范地址**（翻译错——地址本身对） | **高**：FAR 规范性 + 寄存器复核（crash `rd` 对照内存完好=PRF；FAR 非规范=AGU；FAR 规范但走表失败=TLB） |
| pc 复发 | 同指令（find_busiest_group+0x1b8） | ✓ 同指令（同寄存器消费点） | ✓ 同指令 | ✓ 同指令 | 低（三者都同指令） |
| 损坏值分布 | 随机（每次不同非法值） | **随机多位**（popcount 中位 >16，method1 对标） | **结构性**（byte7 恒 0——0x00 前缀模式） | **离散跳变**（pfn 变为另一活页——值落在合法物理区间） | **高**：损坏值 popcount/模式是第一 discriminator |
| 内存对照 | vmcore 中源数据完好 | ✓（寄存器坏、内存好——决定性实验 §4） | ✓（地址错、数据好） | ✓（表项坏、页表内存好） | 低（三者皆然——排除软件写坏） |

## 判定流程（打分器用法）

1. **损坏值模式先行**：popcount>16 随机 → PRF 主嫌；MSB byte=0x00 结构性 → AGU；
   值域落在合法页框 → TLB。
2. **FAR 规范性**：非规范（0x00xx…）→ AGU 确诊；规范但 MMU 走表失败 → TLB；
   FAR=寄存器算术派生且源坏 → PRF。
3. **DFSC 层级分布**：L0 恒定 → PRF/AGU；L0/L3/权限混合 → TLB。

## 仿真侧数据支撑（本仓库实测）

- TLB pfn_to_mapped_page（FS n=32 进行中 + Task 1.3）：guest Oops
  `0x9600004f`（DABT WnR=1 FSC=L3 permission）与 `0x96000004` 混合——
  与打分行 2 预测一致。
- AGU byte7（H6 已闭环）：numAddrFaults=20/20 seed，FAR 非规范模式。
- PRF：SE formal x10 类位段（popcount 中位对标 method1 >16）；
  **FS 侧 PRF 注入 deferred**（PRF 为 O3-only，FS O3-switch 未落地——
  诚实边界，解锁条件 D-FS-O3-switch）。
