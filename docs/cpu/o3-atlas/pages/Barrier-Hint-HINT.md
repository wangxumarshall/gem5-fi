# HINT — O3 微架构链路

> 原文：[Barrier-Hint-HINT.md](../../armv8-isa/Barrier-Hint-HINT.md)
> tier: unimplemented · behavior: warn-nop

## 短链路

FETCH → DECODE → WarnUnimplemented（警告 + NOP 语义）→ ISSUE → EXECUTE(nop) → WRITEBACK → COMMIT

## 证据

| 断言 | 锚点 |
|---|---|
| decodeHints 未分配兜底：return new WarnUnimplemented("unallocated_hint") | CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:619 |
