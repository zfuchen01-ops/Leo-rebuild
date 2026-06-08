# 项目验收摘要

## 交付范围

- 两个星座 A/B；
- 四种方法 RS、MSTS、MGCS、CAHS；
- 100 至 600 UEs，共 11 个采样点；
- throughput、delay、handover 三类指标；
- 400-slot 完整结果、目标对比、诊断图和可恢复参数筛选工具。

## Handover 专项 full400 结果

| 组别 | 综合误差 | Throughput 平均误差 | Delay 平均误差 | Handover 平均误差 |
|---|---:|---:|---:|---:|
| A / MGCS | 7.60% | 3.89% | 11.50% | 7.45% |
| B / MGCS | 8.50% | 8.55% | 8.86% | 8.21% |
| A / RS | 12.40% | 7.84% | 10.66% | 17.11% |
| B / RS | 19.47% | 11.14% | 7.14% | 34.97% |

## 验收判断

- MGCS：A/B 的 handover 已从明显偏离改善到可用校准范围。
- RS：destination 使用 channel-quality 决策后显著改善；B/RS 仍存在较大 handover 缺口。
- CAHS：已有四方法 full400 结果中保持较好的整体拟合。
- 所有关键结果均保留 CSV、metadata 和图片，能够追溯运行参数。

## 关键产物

- `results/final_calibrated_fig3_A_full400_4methods.csv`
- `results/final_calibrated_pathaware_fig4_B_full400_4methods.csv`
- `results/overnight_handover_screen/rankings/final_best.csv`
- `results/overnight_handover_screen/plots/`
- `docs/RUN_GUIDE_ZH.md`

## 结论边界

当前成果属于可复现、可追溯的校准复现。由于精确 gateway 布局、traffic demand、
destination-side handover 和部分信道更新细节未完整公开，不应将校准参数描述为唯一原始实现。

