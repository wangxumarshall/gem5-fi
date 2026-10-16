# PSB CSYNC — O3 微架构链路

> 原文：[Other-PSB_CSYNC.md](../../armv8-isa/Other-PSB_CSYNC.md)
> tier: unimplemented · behavior: warn-nop

## 短链路

FETCH → DECODE → WarnUnimplemented（警告 + NOP 语义）→ ISSUE → EXECUTE(nop) → WRITEBACK → COMMIT

## 证据

| 断言 | 锚点 |
|---|---|
| 解码为 WarnUnimplemented（"psb csync"）——警告 + NOP 语义 | CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:573 |
