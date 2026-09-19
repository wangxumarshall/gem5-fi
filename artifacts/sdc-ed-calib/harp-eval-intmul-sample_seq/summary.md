# SFI detection — sample_seq / intmul

- N = 100（master seed 20260916）
- golden: `SUM=17994817166615565002 CRC=8f333d15`
- detection = (SDC + Crash)/N = (0 + 71)/100 = **0.7100**
- Wilson 95% CI: [0.6146, 0.7899]
- detection | active（剔 Inactive+SimulatorError，n=87）= **0.8161** [0.7219, 0.8835]
- 六类分布: {'SDC': 0, 'Crash': 71, 'Hang': 16, 'Masked': 0, 'Inactive': 0, 'SimulatorError': 13}

## coverage vs detection（论文 Fig.4 形态）

- intmul ACE (ibrIntMul): 0.0407
- detection: 0.7100
- IBR（相关性指标，非上界）：detection 0.7100 vs IBR 0.0407

## 全部结构 coverage

- irfAvf: 0.014838
- irfAvfInt: 0.049023
- irfAvfCommit: 0.015823
- irfAvfVec: 0.0
- l1dAvf: 0.00025
- sqAvf: 0.014102
- ibrIntAdd: 0.039486
- ibrIntMul: 0.040698
- ibrFpAdd: 0.0
- ibrFpMul: 0.0
