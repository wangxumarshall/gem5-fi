# STZ2G — O3 微架构链路

> 原文：[Load-Store-STZ2G.md](../../armv8-isa/Load-Store-STZ2G.md)
> tier: unimplemented · behavior: absent

## 短链路

FETCH → DECODE（无匹配编码）→ Unknown64 → IllegalInstFault → 提交异常

## 证据

| 断言 | 锚点 |
|---|---|
| A64 解码树无匹配（scan_tiers 候选为空：生成代码无此助记符类） | CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:3820 |
