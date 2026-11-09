// lq_lifetime_ordinal — explicit-anchor entry for LQ04 (LSU v3.2.10).
//
// Freestanding AArch64 program: no libc, no dynamic loader; the ELF entry is
// _start itself.  The first five data loads of the whole process are the five
// anchors A1..A5 of anchor_tbl (distinct PC, address, data, destination
// register and consumer); adrp/add compute the table address without any
// data access, so nothing loads before A1..A5.  The sixth table entry is
// reserved (six-entry table per design §4).
    .section .text
    .global _start
_start:
    adrp x1, anchor_tbl
    add  x1, x1, :lo12:anchor_tbl
    ldr  x2, [x1, #0]
    ldr  x3, [x1, #8]
    ldr  x4, [x1, #16]
    ldr  x5, [x1, #24]
    ldr  x6, [x1, #32]
    mov  x0, x2           // a -> x0
    mov  x1, x3           // b -> x1
    mov  x2, x4           // c -> x2 (x2 already consumed)
    mov  x3, x5           // d -> x3 (x3 already consumed)
    mov  x4, x6           // e -> x4
    bl   main
    mov  x0, #0           // exit status 0
    mov  x8, #93          // exit
    svc  #0
    .section .data
    .align 3
    .global anchor_tbl
anchor_tbl:
    .quad 0x0102030405060708
    .quad 0x1112131415161718
    .quad 0x2122232425262728
    .quad 0x3132333435363738
    .quad 0x4142434445464748
    .quad 0x5152535455565758
