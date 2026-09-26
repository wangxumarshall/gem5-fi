# Random-bit-pattern FP sequence for SDC-ED Task 3.2 verification: the
# wrapper's xorshift-initialized memory gives 64-bit lanes with random
# exponent/mantissa fields, so ldr-loaded d-registers cover ALL five
# IEEE754 classes (~0.05% NaN, ~0.05% Inf, ~0.1% subnormal by bit
# pattern statistics) — the value-class histogram must show every bin
# non-zero, unlike rand_fp's computed operands (only normal+zero).
ldr d15, [x8, #40]
ldr d8, [x8, #0]
ldr d9, [x8, #8]
ldr d10, [x8, #16]
ldr d11, [x8, #24]
fadd d12, d15, d8
fmul d13, d9, d10
fadd d14, d11, d12
fmul d15, d13, d14
fadd d8, d14, d15
fmul d9, d15, d8
fadd d10, d8, d9
fmul d11, d9, d10
