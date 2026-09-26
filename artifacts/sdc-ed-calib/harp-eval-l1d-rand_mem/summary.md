# SFI detection — rand_mem / l1d

- N = 100（master seed 20260916）
- golden: `SUM=6686586968532386500 CRC=8525e1e3`
- detection = (SDC + Crash)/N = (0 + 4)/100 = **0.0400**
- Wilson 95% CI: [0.0157, 0.0984]
- detection | active（剔 Inactive+SimulatorError，n=99）= **0.0404** [0.0158, 0.0993]
- 六类分布: {'SDC': 0, 'Crash': 4, 'Hang': 0, 'Masked': 95, 'Inactive': 0, 'SimulatorError': 1}

## coverage vs detection（论文 Fig.4 形态）

- l1d ACE (l1dAvf): nan
- detection: 0.0400

## 全部结构 coverage

- l2.demandHits: 1
- l2.demandMisses: 27
- l1d.demandHits: 427
- l1d.demandMisses: 153
