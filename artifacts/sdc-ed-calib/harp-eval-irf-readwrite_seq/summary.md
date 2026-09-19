# SFI detection — readwrite_seq / irf

- N = 100（master seed 20260916）
- golden: `SUM=3682923676342812808 CRC=8f333d15`
- detection = (SDC + Crash)/N = (0 + 5)/100 = **0.0500**
- Wilson 95% CI: [0.0215, 0.1118]
- detection | active（剔 Inactive+SimulatorError，n=100）= **0.0500** [0.0215, 0.1118]
- 六类分布: {'SDC': 0, 'Crash': 5, 'Hang': 0, 'Masked': 95, 'Inactive': 0, 'SimulatorError': 0}

## coverage vs detection（论文 Fig.4 形态）

- irf ACE (irfAvfInt): 0.0891
- detection: 0.0500
- ACE >= detection（上界性质）: YES

## 全部结构 coverage

- irfAvf: 0.026969
- irfAvfInt: 0.089106
- irfAvfCommit: 0.053536
- irfAvfVec: 0.0
- l1dAvf: 0.000408
- sqAvf: 0.090165
- ibrIntAdd: 0.203034
- ibrIntMul: 0.00043
- ibrFpAdd: 0.0
- ibrFpMul: 0.0
