# SFI detection — stencil_5pt_kernel / l2c_tag

- N = 100（master seed 20260916）
- golden: `FINAL=6216d7bd62318f00`
- protection_model: secded
- detection = (SDC + Crash)/N = (24 + 0)/100 = **0.2400**
- Wilson 95% CI: [0.1669, 0.3323]
- detection | active（剔 Inactive+SimulatorError，n=48）= **0.5000** [0.3639, 0.6361]
- 六类分布: {'SDC': 24, 'Crash': 0, 'Hang': 0, 'Masked': 24, 'Inactive': 52, 'SimulatorError': 0}

## coverage vs detection（论文 Fig.4 形态）

- l2c_tag：arm_chaos_cache 板无 CHAOSCov，ACE 不适用；注入面活跃度（golden run）：
  - l2.demandHits: 11063
  - l2.demandMisses: 2354
  - l1d.demandHits: 202491
  - l1d.demandMisses: 5390

## 全部结构 coverage

- l2.demandHits: 11063
- l2.demandMisses: 2354
- l1d.demandHits: 202491
- l1d.demandMisses: 5390
