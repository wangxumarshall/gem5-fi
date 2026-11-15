# M07 Permission Bypass Repeatability

## REP-FINAL-MMU-M07-R01-01 / R01

- Activation: MATCH; Propagation: MATCH; Terminal: MATCH
- Formal terminal SDC → repeat SDC
- Repeat oracle: `W14_RESULT ctx=R01 signal=0 phase=store_ro observed=0x11223344556677c1 observed_kind=value si_code=-1 fault_addr=0x0 fault_class=none fault_code_ok=1 pte_present=1 shared_before=0x1122334455667788 shared_after=0x11223344556677c1 shared_changed=1 injected_success=1 expected=0x11223344556677c1 value_o`

## REP-FINAL-MMU-M07-R05-01 / R05

- Activation: MATCH; Propagation: MATCH; Terminal: MATCH
- Formal terminal SDC → repeat SDC
- Repeat oracle: `W14_RESULT ctx=R05 signal=0 phase=fetch_xn_indirect observed=0x5a observed_kind=value si_code=-1 fault_addr=0x0 fault_class=none fault_code_ok=1 pte_present=1 shared_before=0x1122334455667788 shared_after=0x1122334455667788 shared_changed=0 injected_success=1 expected=0x5a value_ok=1 msg=done result`

R01 is UNAUTHORIZED_WRITE; R05 is UNAUTHORIZED_EXECUTION. R02 limitation is not part of the 10-run set.
