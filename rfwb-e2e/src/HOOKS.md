# RF/WB source and hook map

`RF_WB_Source_Injection_Final.patch` is applied to gem5-fi baseline
`2f4e00b434ec8690fbb8cb6965e435094de7e784`.  It touches 12 files; the full
injector is `rfwb/rfwb.cc` + `rfwb/rfwb.hh` (copied here for reading).

| Patch file | Role |
|---|---|
| `CHAOS/gem5/src/cpu/o3/SConscript` | adds `rfwb.cc` to the build |
| `CHAOS/gem5/src/cpu/o3/rfwb.cc` | all five model implementations |
| `CHAOS/gem5/src/cpu/o3/rfwb.hh` | injector state and hook API |
| `CHAOS/gem5/src/cpu/o3/dyn_inst.hh` | scalar read/write hooks, vector writable-read hook, M002 shadow fields |
| `CHAOS/gem5/src/cpu/o3/dyn_inst.cc` | execute and squash hooks |
| `CHAOS/gem5/src/cpu/o3/free_list.hh` | PhysRegId allocate/free generation tracking |
| `CHAOS/gem5/src/cpu/o3/iew.cc` | M004 `instToCommit` gate; M005 global-ready gate |
| `CHAOS/gem5/src/cpu/o3/inst_queue.cc` | M005 IQ repair observation |
| `CHAOS/gem5/src/cpu/o3/inst_queue.hh` | read-only IQ scoreboard view (`isRegReady`) |
| `CHAOS/gem5/src/cpu/o3/rename.cc` | M005 consumer Rename observation |
| `CHAOS/gem5/src/cpu/o3/commit.cc` | M004 stall/commit observation |
| `configs/se/ooo_proxy.py` | `--max_ticks` bounded run support |

Model mapping:

| Model | Fault action | Primary hook |
|---|---|---|
| M001 | `physRegFile().setReg(producerReg, value ^ (1<<bit))` | `DynInst::getRegOperand` / `setRegOperand`; free-list generation |
| M002 | zero one target byte in a per-DynInst vector shadow, then `setReg` | `DynInst::getWritableRegOperand`; execute; vector read |
| M003 | return `value ^ (1<<bit)` from the read port; never write PRF | `DynInst::getRegOperand` |
| M004 | skip `instToCommit` for the selected executed instruction | `IEW::executeInsts`; commit stall/commit/squash logging |
| M005 | skip `scoreboard->setReg(dest)` for the selected WB | `IEW::writebackInsts`; Rename/IQ-repair logging; `isRegReady` |

The patch is the complete implementation; do not keep only `rfwb.cc` without
these hooks — the models will not activate.  The baseline source itself is
provided by the RF_WB branch (parent commit `2f4e00b4`).
