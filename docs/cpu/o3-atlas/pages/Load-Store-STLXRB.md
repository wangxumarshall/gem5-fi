# STLXRB — O3 微架构链路

> 原文：[Load-Store-STLXRB.md](../../armv8-isa/Load-Store-STLXRB.md)
> tier: implemented · family: exclusive

## 一图链路

```mermaid
flowchart LR
    N0[FETCH]
    N1[DECODE]
    N2[RENAME]
    N3[DISPATCH]
    N4[ISSUE]
    N5[EXECUTE]
    N6[MEMORY]
    N7[WRITEBACK]
    N8[COMMIT]
    N0 --> N1
    N1 --> N2
    N2 --> N3
    N3 --> N4
    N4 --> N5
    N5 --> N6
    N6 --> N7
    N7 --> N8
    I0[CHAOSAddrPath] -.-> N6
    I1[CHAOSCache] -.-> N6
    I2[CHAOSCommitTrace] -.-> N8
    I3[CHAOSDecode] -.-> N1
    I4[CHAOSExMon] -.-> N6
    I5[CHAOSFreeList] -.-> N2
    I6[CHAOSIQ] -.-> N4
    I7[CHAOSL1DForward] -.-> N6
    I8[CHAOSLSQFwd] -.-> N6
    I9[CHAOSMem] -.-> N6
    I10[CHAOSPhysReg] -.-> N5
    I11[CHAOSProbe] -.-> N8
    I12[CHAOSROB] -.-> N8
    I13[CHAOSReg] -.-> N8
    I14[CHAOSRenameMap] -.-> N2
```

## 分站链路

| 站点 | 代码锚点 |
|---|---|
| FETCH | CHAOS/gem5/src/cpu/o3/fetch.cc:1059 |
| DECODE | CHAOS/gem5/src/cpu/o3/decode.cc:636 |
| RENAME | CHAOS/gem5/src/cpu/o3/rename.cc:537 |
| DISPATCH | CHAOS/gem5/src/cpu/o3/iew.cc:1015 |
| ISSUE | CHAOS/gem5/src/cpu/o3/inst_queue.cc:868 |
| EXECUTE | CHAOS/gem5/src/cpu/o3/lsq_unit.cc:642 |
| MEMORY | CHAOS/gem5/src/cpu/o3/lsq_unit.cc:1376 |
| WRITEBACK | CHAOS/gem5/src/cpu/o3/lsq_unit.cc:1136 |
| COMMIT | CHAOS/gem5/src/cpu/o3/commit.cc:1125 |

## 解码身份

- decoder 格式：stlxrb
- StaticInst 类：STLXRB64
- 解码锚点：CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:1407

## 队列与执行单元

- 队列：LSQ · FU：MemReadOp

## CHAOS 注入器命中

| 注入器 |
|---|
| CHAOSAddrPath |
| CHAOSCache |
| CHAOSCommitTrace |
| CHAOSDecode |
| CHAOSExMon |
| CHAOSFreeList |
| CHAOSIQ |
| CHAOSL1DForward |
| CHAOSLSQFwd |
| CHAOSMem |
| CHAOSPhysReg |
| CHAOSProbe |
| CHAOSROB |
| CHAOSReg |
| CHAOSRenameMap |

## 证据

| 断言 | 锚点 |
|---|---|
| A64 解码树 return new STLXRB64(...)（主定义类，变体见 variants；链路骨架=family exclusive，注入器命中见 injectors） | CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:1407 |
