# Advanced experiment results (3 November 2026)

- The original 537-hex dataset was reused without relabeling.
- **RF 1 km block RMSE:** 0.621°C. Full eight-scheme validation matrix includes spatial KNN and three statistical/ML baselines.
- **RF contiguous x-strip holdout RMSE:** 0.655°C; **2 km block holdout:** 0.629°C.
- **Combined minus morphology RF RMSE:** -0.0726°C, geographic-block bootstrap 95% CI [-0.1085, -0.0368]°C. A zero-crossing interval does not support superiority.
- **Combined RF block-1 residual Moran I:** 0.411, permutation p=0.001.
- **Nominal 90% prediction interval:** observed coverage 91.5%, mean width 2.190°C. This is empirical; no guaranteed coverage under spatial shift.
- **Priority acceptability:** 91 hexes in the most severe quintile in at least 80% of 501 policy weighting scenarios, among which 67 have lower-than-median model interval widths.
- **Pareto front 1:** 10 nondominated hexes under heat, service-access deficit and blue-green deficit. Pareto position does not establish optimal intervention or causal benefit.

Sources: `outputs/tables/ieee_validation_matrix.csv`, `residual_spatial_diagnostics.csv`, `paired_model_uncertainty.csv`, `prediction_uncertainty.csv`, `rank_uncertainty_pareto.csv`, `priority_summary.csv` and `scale_sensitivity.csv`.
