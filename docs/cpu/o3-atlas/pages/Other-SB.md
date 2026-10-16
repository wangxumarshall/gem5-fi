# SB — O3 微架构链路

> 原文：[Other-SB.md](../../armv8-isa/Other-SB.md)
> tier: unimplemented · behavior: illegal-fault

## 短链路

FETCH → DECODE（解码但实现拒绝）→ fault → COMMIT

## 证据

| 断言 | 锚点 |
|---|---|
| 实证：.inst 0xd50330ff (SB) 经 gem5 O3 解码为 Unknown64，执行 panic（faults.cc:784 Attempted to execute unknown instruction） | CHAOS/gem5/src/arch/arm/faults.cc:784 |
