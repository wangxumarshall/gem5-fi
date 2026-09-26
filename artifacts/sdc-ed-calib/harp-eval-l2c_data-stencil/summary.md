# SFI detection — stencil_5pt_kernel / l2c_data

- N = 100（master seed 20260916）
- golden: `FINAL=6216d7bd62318f00`
- detection = (SDC + Crash)/N = (20 + 0)/100 = **0.2000**
- Wilson 95% CI: [0.1334, 0.2888]
- detection | active（剔 Inactive+SimulatorError，n=49）= **0.4082** [0.2822, 0.5475]
- 六类分布: {'SDC': 20, 'Crash': 0, 'Hang': 0, 'Masked': 29, 'Inactive': 51, 'SimulatorError': 0}

## coverage vs detection（论文 Fig.4 形态）

- l2c_data：arm_chaos_cache 板无 CHAOSCov，ACE 不适用；注入面活跃度（golden run）：
  - l2.demandHits: 11063
  - l2.demandMisses: 2354
  - l1d.demandHits: 202491
  - l1d.demandMisses: 5390

## 全部结构 coverage

- l2.demandHits: 11063
- l2.demandMisses: 2354
- l1d.demandHits: 202491
- l1d.demandMisses: 5390
