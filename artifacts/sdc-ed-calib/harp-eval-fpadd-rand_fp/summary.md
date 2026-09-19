# SFI detection — rand_fp / fpadd

- N = 100（master seed 20260916）
- golden: `SUM=15693161701610300260 CRC=938707ee`
- detection = (SDC + Crash)/N = (0 + 0)/100 = **0.0000**
- Wilson 95% CI: [0.0000, 0.0370]
- detection | active（剔 Inactive+SimulatorError，n=100）= **0.0000** [0.0000, 0.0370]
- 六类分布: {'SDC': 0, 'Crash': 0, 'Hang': 0, 'Masked': 100, 'Inactive': 0, 'SimulatorError': 0}

## coverage vs detection（论文 Fig.4 形态）

- fpadd ACE (ibrFpAdd): 0.0715
- detection: 0.0000
- IBR（相关性指标，非上界）：detection 0.0000 vs IBR 0.0715

## 全部结构 coverage

- irfAvf: 0.037975
- irfAvfInt: 0.054016
- irfAvfCommit: 0.042074
- irfAvfVec: 0.04652
- l1dAvf: 0.000668
- sqAvf: 0.007488
- ibrIntAdd: 0.000221
- ibrIntMul: 0.0
- ibrFpAdd: 0.071508
- ibrFpMul: 0.053073
