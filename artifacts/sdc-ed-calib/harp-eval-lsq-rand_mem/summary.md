# SFI detection — rand_mem / lsq

- N = 100（master seed 20260916）
- golden: `SUM=6686586968532386500 CRC=8525e1e3`
- detection = (SDC + Crash)/N = (0 + 69)/100 = **0.6900**
- Wilson 95% CI: [0.5937, 0.7722]
- detection | active（剔 Inactive+SimulatorError，n=100）= **0.6900** [0.5937, 0.7722]
- 六类分布: {'SDC': 0, 'Crash': 69, 'Hang': 0, 'Masked': 31, 'Inactive': 0, 'SimulatorError': 0}

## coverage vs detection（论文 Fig.4 形态）

- lsq ACE (sqAvf): 0.0170
- detection: 0.6900
- ACE >= detection（上界性质）: NO

## 全部结构 coverage

- irfAvf: 0.016658
- irfAvfInt: 0.055037
- irfAvfCommit: 0.016743
- irfAvfVec: 0.0
- l1dAvf: 0.001359
- sqAvf: 0.01696
- ibrIntAdd: 0.000259
- ibrIntMul: 0.0
- ibrFpAdd: 0.0
- ibrFpMul: 0.0
