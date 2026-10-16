# LDSMAXH, LDSMAXAH, LDSMAXALH, LDSMAXLH — O3 微架构链路

> 原文：[Load-Store-LDSMAXH_LDSMAXAH_LDSMAXALH_LDSMAXLH.md](../../armv8-isa/Load-Store-LDSMAXH_LDSMAXAH_LDSMAXALH_LDSMAXLH.md)
> tier: implemented · family: atomic-lse

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
    I4[CHAOSFreeList] -.-> N2
    I5[CHAOSIQ] -.-> N4
    I6[CHAOSL1DForward] -.-> N6
    I7[CHAOSLSQFwd] -.-> N6
    I8[CHAOSMem] -.-> N6
    I9[CHAOSPhysReg] -.-> N5
    I10[CHAOSProbe] -.-> N8
    I11[CHAOSROB] -.-> N8
    I12[CHAOSReg] -.-> N8
    I13[CHAOSRenameMap] -.-> N2
```

## 分站链路

| 站点 | 代码锚点 |
|---|---|
| FETCH | CHAOS/gem5/src/cpu/o3/fetch.cc:1059 |
| DECODE | CHAOS/gem5/src/cpu/o3/decode.cc:636 |
| RENAME | CHAOS/gem5/src/cpu/o3/rename.cc:537 |
| DISPATCH | CHAOS/gem5/src/cpu/o3/iew.cc:1026 |
| ISSUE | CHAOS/gem5/src/cpu/o3/inst_queue.cc:868 |
| EXECUTE | CHAOS/gem5/src/cpu/o3/lsq_unit.cc:714 |
| MEMORY | CHAOS/gem5/src/cpu/o3/lsq_unit.cc:1730 |
| WRITEBACK | CHAOS/gem5/src/cpu/o3/lsq_unit.cc:848 |
| COMMIT | CHAOS/gem5/src/cpu/o3/commit.cc:1125 |

## 解码身份

- decoder 格式：ldsmaxh
- StaticInst 类：LDSMAXH
- 解码锚点：CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:1136

## 队列与执行单元

- 队列：LSQ · FU：MemWriteOp

## CHAOS 注入器命中

| 注入器 |
|---|
| CHAOSAddrPath |
| CHAOSCache |
| CHAOSCommitTrace |
| CHAOSDecode |
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
| A64 解码树 return new LDSMAXH(...)（主定义类，变体见 variants；链路骨架=family atomic-lse，注入器命中见 injectors） | CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:1136 |
