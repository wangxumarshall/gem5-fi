# CBNZ — O3 微架构链路

> 原文：[Branch-CBNZ.md](../../armv8-isa/Branch-CBNZ.md)
> tier: implemented · family: branch-cond

## 一图链路

```mermaid
flowchart LR
    N0[BPU]
    N1[FTQ]
    N2[FETCH]
    N3[DECODE]
    N4[RENAME]
    N5[DISPATCH]
    N6[ISSUE]
    N7[EXECUTE]
    N8[WRITEBACK]
    N9[COMMIT]
    N10[REDIRECT]
    N0 --> N1
    N1 --> N2
    N2 --> N3
    N3 --> N4
    N4 --> N5
    N5 --> N6
    N6 --> N7
    N7 --> N8
    N8 --> N9
    N9 --> N10
    I0[CHAOSBPU] -.-> N0
    I1[CHAOSCommitTrace] -.-> N9
    I2[CHAOSDecode] -.-> N3
    I3[CHAOSExec] -.-> N7
    I4[CHAOSFreeList] -.-> N4
    I5[CHAOSIQ] -.-> N6
    I6[CHAOSPhysReg] -.-> N7
    I7[CHAOSProbe] -.-> N9
    I8[CHAOSROB] -.-> N9
    I9[CHAOSReg] -.-> N9
    I10[CHAOSRenameMap] -.-> N4
```

## 分站链路

| 站点 | 代码锚点 |
|---|---|
| BPU | CHAOS/gem5/src/cpu/o3/bac.cc:565 |
| FTQ | CHAOS/gem5/src/cpu/o3/ftq.cc:186 |
| FETCH | CHAOS/gem5/src/cpu/o3/fetch.cc:1059 |
| DECODE | CHAOS/gem5/src/cpu/o3/decode.cc:636 |
| RENAME | CHAOS/gem5/src/cpu/o3/rename.cc:537 |
| DISPATCH | CHAOS/gem5/src/cpu/o3/iew.cc:881 |
| ISSUE | CHAOS/gem5/src/cpu/o3/inst_queue.cc:868 |
| EXECUTE | CHAOS/gem5/src/cpu/o3/iew.cc:1138 |
| WRITEBACK | CHAOS/gem5/src/cpu/o3/iew.cc:1380 |
| COMMIT | CHAOS/gem5/src/cpu/o3/commit.cc:1125 |
| REDIRECT | CHAOS/gem5/src/cpu/o3/fetch.cc:711 |

## 解码身份

- decoder 格式：cbnz
- StaticInst 类：Cbnz64
- 解码锚点：CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:643

## 队列与执行单元

- 队列：IQ · FU：IntALU

## CHAOS 注入器命中

| 注入器 |
|---|
| CHAOSBPU |
| CHAOSCommitTrace |
| CHAOSDecode |
| CHAOSExec |
| CHAOSFreeList |
| CHAOSIQ |
| CHAOSPhysReg |
| CHAOSProbe |
| CHAOSROB |
| CHAOSReg |
| CHAOSRenameMap |

## 证据

| 断言 | 锚点 |
|---|---|
| A64 解码树 return new Cbnz64(...)（主定义类，变体见 variants；链路骨架=family branch-cond，注入器命中见 injectors） | CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:643 |
