# Read-after-write chain: every dest reg is re-read as a source soon after
# (write->read = ACE => HIGH int AVF expected, contrast to overwrite_seq)
add x9, x9, x9
add x10, x10, x10
add x11, x11, x11
add x12, x12, x12
add x13, x13, x13
add x14, x14, x14
add x15, x15, x15
add x16, x16, x16
add x17, x17, x17
add x18, x18, x18
