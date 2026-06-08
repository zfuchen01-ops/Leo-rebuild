# A/MGCS 与 RS Handover 一夜筛选说明

生成时间：2026-06-08T01:46:52

## 结论口径

论文对照仍使用全用户 handover frequency。source/destination 分解只用于诊断，不用于偷偷替换论文指标。

## 最佳候选

| 星座 | 方法 | 候选 | 综合分数 | throughput mean | delay mean | handover mean |
|---|---|---|---:|---:|---:|---:|
| A | MGCS | hold_4__cap_2200 | 7.598% | 3.891% | 11.499% | 7.453% |
| B | MGCS | baseline_reused_full400 | 8.503% | 8.545% | 8.858% | 8.205% |
| A | RS | destination_mode_channel_quality | 12.397% | 7.843% | 10.661% | 17.114% |
| B | RS | combo_destination_mode_channel_quality__baseline | 19.470% | 11.138% | 7.138% | 34.969% |

## 结果解释

- RS 的源侧切换频率本来就接近论文，但目的侧切换频率明显偏低；全用户统计因此约少一半。若 destination 决策搜索仍无法修复，最合理的结论是论文没有公开完整的目的侧切换或统计定义。
- MGCS 对干扰参与方式、信道质量平滑和最小保持时隙极敏感。改善若依赖这些参数，应称为 calibrated reproduction，而不是声称恢复了论文原始实现。
- 所有候选都同时受吞吐和时延护栏约束，避免通过压制切换事件制造一条看似漂亮但网络性能错误的曲线。

## 已有负面证据（本轮不重复浪费计算）

- MGCS channel-quality hysteresis 0.05/0.10
- MGCS fixed service time 30/60/90 seconds
- MGCS thermal-only decision noise
- MGCS delay weights -1/-2/-4
- MGCS capacity tolerances 0.01/0.03/0.05
- MGCS average window 30 seconds with the previous baseline
- B gateway left_open + nearest
