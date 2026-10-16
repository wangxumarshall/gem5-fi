# PACIA, PACIA1716, PACIASP , PACIAZ, PACIZA — O3 微架构链路

> 原文：[Pointer-Authentication-PACIA_PACIA1716_PACIASP__PACIAZ_PACIZA.md](../../armv8-isa/Pointer-Authentication-PACIA_PACIA1716_PACIASP__PACIAZ_PACIZA.md)
> tier: implemented · family: dataproc-1src

## 一图链路

```mermaid
flowchart LR
    N0[FETCH]
    N1[DECODE]
    N2[RENAME]
    N3[DISPATCH]
    N4[ISSUE]
    N5[EXECUTE]
    N6[WRITEBACK]
    N7[COMMIT]
    N0 --> N1
    N1 --> N2
    N2 --> N3
    N3 --> N4
    N4 --> N5
    N5 --> N6
    N6 --> N7
    I0[CHAOSCommitTrace] -.-> N5
    I1[CHAOSDecode] -.-> N5
    I2[CHAOSExec] -.-> N5
    I3[CHAOSFreeList] -.-> N5
    I4[CHAOSIQ] -.-> N5
    I5[CHAOSPhysReg] -.-> N5
    I6[CHAOSProbe] -.-> N5
    I7[CHAOSROB] -.-> N5
    I8[CHAOSReg] -.-> N5
    I9[CHAOSRenameMap] -.-> N5
```

## 分站链路

| 站点 | 代码锚点 |
|---|---|
| FETCH | CHAOS/gem5/src/cpu/o3/fetch.cc:1059 |
| DECODE | CHAOS/gem5/src/cpu/o3/decode.cc:636 |
| RENAME | CHAOS/gem5/src/cpu/o3/rename.cc:537 |
| DISPATCH | CHAOS/gem5/src/cpu/o3/iew.cc:881 |
| ISSUE | CHAOS/gem5/src/cpu/o3/inst_queue.cc:868 |
| EXECUTE | CHAOS/gem5/src/cpu/o3/iew.cc:1138 |
| WRITEBACK | CHAOS/gem5/src/cpu/o3/iew.cc:1380 |
| COMMIT | CHAOS/gem5/src/cpu/o3/commit.cc:1125 |

## 解码身份

- decoder 格式：pacia
- StaticInst 类：Pacia
- 解码锚点：CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:2432

## 队列与执行单元

- 队列：IQ · FU：IntALU

## CHAOS 注入器命中

| 注入器 |
|---|
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
| A64 解码树 return new Pacia(...)；family=dataproc-1src 骨架引用（分类任务深填） | CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:2432 |
