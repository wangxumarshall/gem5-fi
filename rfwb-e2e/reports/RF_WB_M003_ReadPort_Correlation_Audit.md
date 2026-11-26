# RF/WB M003 Read-Port Correlation Audit

M003 locks the actual read object at injection:

- `faultReadReg` = renamed source PhysRegId of the selected read.
- `faultReadSeq` / generation / source index are in the trace row.
- `M003_INJECT` records original PRF value and corrupted return.
- `M003_PRF_READ` now filters on `faultReadReg`, not the producer register.
- Example C03-T01: injection seq=14801, phys=51, orig=38, return=39.
  M003_PRF_READ later reads phys=51 with PRF value 38, proving PRF itself stayed correct.
- `M003_CONSUMER_WRITE` records destination writes after injection, including the
  overwrite in C03.
