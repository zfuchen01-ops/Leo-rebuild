# 运行与验收指南

## 1. 环境准备

建议使用 Windows PowerShell 和 Python 3.10 或更高版本。

```powershell
cd <项目解压目录>
python -m pip install -r requirements.txt
```

核心复现实验仅依赖 `numpy` 和 `matplotlib`。`opencv-python` 用于重新提取
图中目标点；`pandas` 和 `torch` 仅用于原始强化学习相关模块。

## 2. 快速验收

先运行核心测试：

```powershell
python -m unittest test_focused_handover_optimization.py test_overnight_handover_screen.py test_score_calibration.py test_output_semantics.py test_gsl_interference.py
```

再运行 B 星座关键点烟雾实验：

```powershell
$env:LEO_SOURCE_LAYOUT="random"
$env:LEO_GATEWAY_LAYOUT="left_open"
$env:LEO_GATEWAY_ASSIGN="cycle"
$env:LEO_HANDOVER_SCOPE="all"
$env:LEO_RESET_HANDOVER_AFTER_INITIAL="1"
$env:LEO_ISL_BANDWIDTH="3500"
$env:LEO_GSL_RATE_CAP_POINTS="100:580,350:1050,600:1000"
$env:LEO_CHANNEL_QUALITY_MIN_HOLD_SLOTS_POINTS="100:2,150:2,200:3,600:4"
$env:LEO_PAPER_SQ_FREE_ALPHA="0.5"
$env:LEO_PAPER_HANDOVER_CONTROL_MODE="constant"
$env:LEO_PAPER_HANDOVER_COST_POINTS="100:0.085,350:0.125,600:0.125"
$env:LEO_PAPER_CAHS_DELAY_WEIGHT="0.40"

python run_paper_rebuild.py --constellation B --users 100 350 600 --methods RS MSTS MGCS CAHS --slots 80 --jobs 3 --traffic-mode ground_backbone --gateway-count 12 --out results\acceptance_smoke_B.csv
```

## 3. 完整校准复现

### 3.1 A 星座四方法 full400

```powershell
$env:LEO_SOURCE_LAYOUT="random"
$env:LEO_GATEWAY_LAYOUT="left_open"
$env:LEO_GATEWAY_ASSIGN="cycle"
$env:LEO_HANDOVER_SCOPE="all"
$env:LEO_RESET_HANDOVER_AFTER_INITIAL="1"
$env:LEO_ISL_BANDWIDTH="5000"
$env:LEO_ISL_BANDWIDTH_POINTS="100:5000,500:5000,550:7000,600:9000"
$env:LEO_GSL_RATE_CAP_POINTS="100:500,350:1000,600:2600"
$env:LEO_PAPER_SQ_FREE_ALPHA="0.5"
$env:LEO_PAPER_HANDOVER_CONTROL_MODE="none"
$env:LEO_PAPER_UTILITY_HYSTERESIS_POINTS="100:0.04,150:0.065,200:0.075,250:0.105,300:0.13,350:0.15,600:0.20"

python run_paper_rebuild.py --constellation A --users 100 150 200 250 300 350 400 450 500 550 600 --methods RS MSTS MGCS CAHS --slots 400 --jobs 16 --traffic-mode ground_backbone --gateway-count 16 --out results\acceptance_A_full400.csv
```

### 3.2 B 星座四方法 full400

保留第 2 节中的 B 星座环境变量，然后执行：

```powershell
python run_paper_rebuild.py --constellation B --users 100 150 200 250 300 350 400 450 500 550 600 --methods RS MSTS MGCS CAHS --slots 400 --jobs 16 --traffic-mode ground_backbone --gateway-count 12 --out results\acceptance_B_full400.csv
```

## 4. 最佳 handover 专项配置

专项结果允许 A/B、RS/MGCS 使用不同的校准假设。

| 组别 | 关键额外配置 |
|---|---|
| A / RS | `LEO_DESTINATION_DECISION_MODE=CHANNEL_QUALITY` |
| B / RS | `LEO_DESTINATION_DECISION_MODE=CHANNEL_QUALITY` |
| A / MGCS | `LEO_CHANNEL_QUALITY_MIN_HOLD_SLOTS=4`，清空 hold points，并设置 `LEO_GSL_RATE_CAP_POINTS=100:500,350:1000,600:2200` |
| B / MGCS | 使用 B 星座基础校准配置 |

如需复跑某个专项配置，应在独立 PowerShell 会话中设置环境变量，避免上一组配置残留。

## 5. 对比与绘图

```powershell
python compare_to_paper.py --targets results\paper_targets_fig3_A.csv --results results\acceptance_A_full400.csv --out results\compare_acceptance_A_full400.csv
python plot_paper_comparison.py --targets results\paper_targets_fig3_A.csv --results results\acceptance_A_full400.csv --out results\acceptance_A_full400.png --title "Constellation A calibrated reproduction"
```

B 星座将 `fig3_A` 和 `acceptance_A` 替换为 `fig4_B` 和 `acceptance_B`。

## 6. 参数筛选

分阶段、可恢复的筛选：

```powershell
python overnight_handover_screen.py --budget-hours 8 --jobs 16
```

残余误差局部搜索：

```powershell
python focused_handover_optimization.py --budget-hours 4 --jobs 16
```

筛选器会复用已有 summary，单个异常候选具有超时限制，不会占满全部预算。

## 7. 输出解释

每个实验 CSV 同时包含：

- `handover_frequency`：当前验收采用的全用户切换频率；
- `source_handover_frequency`：源侧诊断值；
- `destination_handover_frequency`：目的侧诊断值；
- `avg_delay_ms`：平均传播时延；
- `avg_allocated_mhz`：整体已分配带宽指标。

对应的 `.meta.json` 保存命令、seed、slots、参数和未公开假设，验收时应与 CSV 一并保留。

## 8. 已知限制

- RS 对 destination-side 决策规则高度敏感，B/RS handover 仍有明显残余偏差。
- A/MGCS 已显著改善 handover，但 delay 仍存在系统性偏高。
- 精确 gateway 布局、traffic demand 和部分更新规则缺失，因此结果应表述为校准复现。
- `python -m unittest discover` 会导入旧版 `test.py/loop.py` 路径并产生无关输出，建议使用第 2 节列出的核心测试命令。
