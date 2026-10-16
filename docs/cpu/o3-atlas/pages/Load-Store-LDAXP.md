# LDAXP — O3 微架构链路

> 原文：[Load-Store-LDAXP.md](../../armv8-isa/Load-Store-LDAXP.md)
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
    I0[CHAOSAddrPath] -.-> N5
    I1[CHAOSCache] -.-> N5
    I2[CHAOSCommitTrace] -.-> N5
    I3[CHAOSDecode] -.-> N5
    I4[CHAOSExMon] -.-> N5
    I5[CHAOSFreeList] -.-> N5
    I6[CHAOSIQ] -.-> N5
    I7[CHAOSL1DForward] -.-> N5
    I8[CHAOSLSQFwd] -.-> N5
    I9[CHAOSMem] -.-> N5
    I10[CHAOSPhysReg] -.-> N5
    I11[CHAOSProbe] -.-> N5
    I12[CHAOSROB] -.-> N5
    I13[CHAOSReg] -.-> N5
    I14[CHAOSRenameMap] -.-> N5
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

- decoder 格式：ldaxp
- StaticInst 类：LDAXPW64
- 解码锚点：CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:1491

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
| A64 解码树 return new LDAXPW64(...)；family=exclusive 骨架引用（分类任务深填） | CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:1491 |
