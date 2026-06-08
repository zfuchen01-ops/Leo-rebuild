# LEO Handover Reproduction and Calibration

This repository rebuilds and calibrates the LEO handover experiments for two
constellations and four handover methods:

- RS: random selection
- MSTS: maximum service time
- MGCS: maximum channel quality
- CAHS: context-aware handover selection

The main reproducible outputs cover throughput, propagation delay, and handover
frequency for 100 to 600 UEs using 400 simulation slots.

## Current Acceptance Results

The calibrated handover-focused results use all-user handover frequency and
have been validated on all 11 UE points with 400 slots.

| Constellation / Method | Score | Throughput mean error | Delay mean error | Handover mean error |
|---|---:|---:|---:|---:|
| A / MGCS | 7.60% | 3.89% | 11.50% | 7.45% |
| B / MGCS | 8.50% | 8.55% | 8.86% | 8.21% |
| A / RS | 12.40% | 7.84% | 10.66% | 17.11% |
| B / RS | 19.47% | 11.14% | 7.14% | 34.97% |

MGCS is within a useful calibrated range. RS improves substantially when the
destination side uses channel-quality decisions, but its remaining handover
gap indicates that the original destination-side policy or statistic is not
fully specified.

## Quick Start

```powershell
python -m pip install -r requirements.txt
python -m unittest test_focused_handover_optimization.py test_overnight_handover_screen.py test_score_calibration.py test_output_semantics.py test_gsl_interference.py
python run_paper_rebuild.py --constellation B --users 100 350 600 --methods RS MSTS MGCS CAHS --slots 80 --jobs 3 --traffic-mode ground_backbone --gateway-count 12 --out results\acceptance_smoke_B.csv
```

See [docs/RUN_GUIDE_ZH.md](docs/RUN_GUIDE_ZH.md) for calibrated full-run
commands, plotting, comparison, troubleshooting, and output interpretation.

## Main Entry Points

| File | Purpose |
|---|---|
| `run_paper_rebuild.py` | Main independent simulation runner |
| `run_experiments.py` | Source-adjusted experiment runner |
| `compare_to_paper.py` | Compare simulation CSV against digitized targets |
| `plot_paper_comparison.py` | Plot targets and simulation results |
| `overnight_handover_screen.py` | Resumable staged RS/MGCS parameter screening |
| `focused_handover_optimization.py` | Focused residual-error optimization |
| `make_report.py` | Generate consolidated reproduction reports |

## Important Outputs

- `results/final_calibrated_fig3_A_full400_4methods.csv`
- `results/final_calibrated_pathaware_fig4_B_full400_4methods.csv`
- `results/overnight_handover_screen/rankings/final_best.csv`
- `results/overnight_handover_screen/plots/`
- `results/paper_targets_fig3_A.csv`
- `results/paper_targets_fig4_B.csv`

## Reproduction Status

This project supports a calibrated numerical reproduction, not a claim of an
identical hidden implementation. Exact gateway placement, traffic demand,
destination-side handover policy, and parts of the channel update process are
not fully specified by the source material. All added assumptions are exposed
through environment variables and recorded in output metadata.

