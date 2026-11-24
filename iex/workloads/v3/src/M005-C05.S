	.arch armv8-a
	.text
	.global _start
	.type _start,%function
_start:
	bl iex_run
	bl iex_print_mem
	.global iex_run
	.type iex_run,%function
iex_run:
	ldr x9, =0x0000000000000007
	ldr x10, =0x0000000000000007
	ldr x11, =0xA5A5A5A5A5A5A5A5
	ldr x12, =iex_output
	ldr x22, =v3_cold1
	ldr x23, =v3_cold2
	mov x20, #128
	.global iex_roi_start
iex_roi_start:
.Lloop:
	ldr x13, [x22]
	add x22, x22, #4096
	ldr x14, [x13, x23]
	add x23, x23, #4096
	.global iex_older_branch_pc
iex_older_branch_pc:
	cbnz x14, .Lold_taken
	cmp x9, x10
	.global iex_target_pc
iex_target_pc:
	b.eq .Lgold
	ldr x2, =0x0000000000000051
	b .Lmerge
.Lgold:
	ldr x2, =0x00000000000000A1
.Lmerge:
	eor x1, x2, x11
	str x2, [x12]
	str x1, [x12, #8]
	add x12, x12, #16
	.global iex_iter_pc
iex_iter_pc:
	sub x20, x20, #1
	cbnz x20, .Lloop
	.global iex_roi_end
iex_roi_end:
	b .Ldone
.Lold_taken:
	ldr x2, =0x00000000DEADBEEF
	str x2, [x12]
.Ldone:
	ret
	.section .rodata
	.global iex_context
iex_context: .asciz "IEX-M005-C05"
	.ltorg
	.section .bss
	.align 12
v3_cold1: .skip 0x80000
	.align 12
v3_cold2: .skip 0x80000
