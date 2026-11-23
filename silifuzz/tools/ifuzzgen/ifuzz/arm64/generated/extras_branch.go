// Opt-in extension: branch encodings with a non-zero forward displacement.
//
// The upstream ifuzz table stores exactly one concrete word per branch class,
// and every one of them has displacement 0 (B/0x14000000, B.cond/0x54000000,
// CBZ/0x34000000, ...).  A zero displacement is a self-loop, so a stream that
// contains a branch class can never terminate and sf_fix rejects it as a
// timeout.  Pairing the branch-oriented sdcfuzz templates therefore needs
// branch forms that actually move forward.
//
// Words below are assembled output (b .+8 / b.eq .+8 / cbz x0, .+8 / ...) read
// back with objdump; masks are taken from the upstream table verbatim so the
// class names stay identical to arm64.ParseInsn.
package generated

import (
	. "silifuzz/tools/ifuzzgen/ifuzz/arm64"
)

var branchInsns = []*Insn{
	{Name: "B", OpcodeMask: 0xfc000000, Opcode: 0x14000000, AsUInt32: 0x14000002},
	{Name: "B", OpcodeMask: 0xfc000000, Opcode: 0x14000000, AsUInt32: 0x14000004},
	{Name: "B", OpcodeMask: 0xfc000000, Opcode: 0x14000000, AsUInt32: 0x14000008},
	{Name: "B.cond", OpcodeMask: 0xff000010, Opcode: 0x54000000, AsUInt32: 0x54000040},
	{Name: "B.cond", OpcodeMask: 0xff000010, Opcode: 0x54000000, AsUInt32: 0x54000061},
	{Name: "B.cond", OpcodeMask: 0xff000010, Opcode: 0x54000000, AsUInt32: 0x54000080},
	{Name: "CBZ", OpcodeMask: 0xff000000, Opcode: 0xb4000000, AsUInt32: 0xb4000040},
	{Name: "CBZ", OpcodeMask: 0xff000000, Opcode: 0x34000000, AsUInt32: 0x34000040},
	{Name: "CBNZ", OpcodeMask: 0xff000000, Opcode: 0xb5000000, AsUInt32: 0xb5000040},
	{Name: "CBNZ", OpcodeMask: 0xff000000, Opcode: 0x35000000, AsUInt32: 0x35000040},
	{Name: "TBZ", OpcodeMask: 0x7f000000, Opcode: 0x36000000, AsUInt32: 0x36000040},
	{Name: "TBZ", OpcodeMask: 0x7f000000, Opcode: 0x36000000, AsUInt32: 0x36180060},
	{Name: "TBNZ", OpcodeMask: 0x7f000000, Opcode: 0x37000000, AsUInt32: 0x37000040},
	{Name: "TBNZ", OpcodeMask: 0x7f000000, Opcode: 0x37000000, AsUInt32: 0x37180060},
}

// RegisterWith appends the opt-in tables requested by the caller.  With both
// switches off the registered set is byte-identical to the upstream table.
func RegisterWith(lse, branches bool) {
	out := append([]*Insn{}, insns_arm64...)
	if lse {
		out = append(out, lseInsns...)
	}
	if branches {
		out = append(out, branchInsns...)
	}
	Register(out)
}

// BranchInsns exposes the opt-in branch forms for tooling.
func BranchInsns() []*Insn { return branchInsns }
