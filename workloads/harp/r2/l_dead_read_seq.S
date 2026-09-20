# Negative-control sequence for SDC-ACE (SDC-ED Task 4.2): values are
# written AND read (so plain ACE counts them), but the consumers'
# RESULTS are then overwritten before the wrapper's store-back — the
# read chain's contribution never reaches the checkable output.
#   round 1: x9-x14 live chain; x15-x20 each read twice by dead
#            consumers writing x15-x20 themselves (in-place dead chain)
#   round 2: x15-x20 overwritten from the live chain (store-back sees
#            ONLY live-chain-derived values)
# Only x9-x20 are touched — every touched register is either live-chain
# or overwritten before the store-back, so no dead result leaks into
# the checkable output through an un-overwritten register.
add x9, x9, x9
add x10, x10, x10
add x11, x11, x11
add x15, x15, x15
add x16, x16, x16
add x17, x17, x17
add x18, x18, x18
add x19, x19, x19
add x20, x20, x20
add x15, x15, x16
add x16, x16, x17
add x17, x17, x18
add x18, x18, x19
add x19, x19, x20
add x20, x20, x15
add x15, x9, x10
add x16, x10, x11
add x17, x11, x9
add x18, x9, x10
add x19, x10, x11
add x20, x11, x9
