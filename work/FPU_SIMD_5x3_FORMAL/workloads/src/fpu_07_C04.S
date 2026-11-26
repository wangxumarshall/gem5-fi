// 5x3 context workload FPU-M007 C04 (model 7, C04)
.text
.global _start
_start:
    msr fpsr, xzr
    msr fpcr, xzr
    adr x20, outbuf
    mov x21, #0
    mov x22, #100
loop_top:
    add x8, x20, x21, lsl #7
    add x9, x8, #40
    ldr x10, =0x3149554650465046
    str x10, [x8, #0]
    mov x10, #7
    str x10, [x8, #8]
    mov x10, #4
    str x10, [x8, #16]
    mov x10, #5
    str x10, [x8, #24]
    str x21, [x8, #32]
    movz w7, #0x0
    movk w7, #0xc040, lsl #16
    fmov s1, w7
    movz w7, #0x0
    movk w7, #0xc0a0, lsl #16
    fmov s2, w7
    mov x5, #0x11
    mov x6, #0x22
fpu_target_r:
    fcmp s1, s2
        csel x10, x5, x6, lo
        add x4, x10, x10
        mul x5, x4, x4
        sub x6, x5, x10
        mov x10, x6
        str x10, [x9]
        mov x11, x4
        str x11, [x8, #96]
    mrs x10, fpsr
    str x10, [x8, #56]
    ubfx x11, x10, #27, #1
    str x11, [x8, #104]
    mrs x10, fpcr
    str x10, [x8, #64]
    mrs x10, nzcv
    str x10, [x8, #72]
    mov x10, #-1
    str x10, [x8, #80]
    mov x10, #0
    str x10, [x8, #88]

    add x21, x21, #1
    cmp x21, x22
    b.ne loop_top
    mov x2, x22
    lsl x2, x2, #7
    adr x1, outbuf
write_exit:
    mov x0, #1
    mov x8, #64
    svc #0
    mov x0, #0
    mov x8, #93
    svc #0

.section .data
.align 4
src_data: .word 0xc0400000, 0xc0a00000
.section .bss
.align 8
outbuf: .skip 16384
