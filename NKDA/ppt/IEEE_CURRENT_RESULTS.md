# Advanced experiment results (3 November 2026)

- The original 537-hex dataset was reused without relabeling.
- **RF 1 km block RMSE:** 0.891°C. Full eight-scheme validation matrix includes spatial KNN and three statistical/ML baselines.
- **RF contiguous x-strip holdout RMSE:** 0.825°C; **2 km block holdout:** 0.914°C.
- **Combined minus morphology RF RMSE:** +0.0162°C, geographic-block bootstrap 95% CI [-0.0916, +0.1643]°C. A zero-crossing interval does not support superiority.
- **Combined RF block-1 residual Moran I:** 0.439, permutation p=0.001.
- **Nominal 90% prediction interval:** observed coverage 91.4%, mean width 2.930°C. This is empirical; no guaranteed coverage under spatial shift.
- **Priority acceptability:** 58 hexes in the most severe quintile in at least 80% of 501 policy weighting scenarios, among which 37 have lower-than-median model interval widths.
- **Pareto front 1:** 7 nondominated hexes under heat, service-access deficit and blue-green deficit. Pareto position does not establish optimal intervention or causal benefit.

Sources: `outputs/tables/ieee_validation_matrix.csv`, `residual_spatial_diagnostics.csv`, `paired_model_uncertainty.csv`, `prediction_uncertainty.csv`, `rank_uncertainty_pareto.csv`, `priority_summary.csv` and `scale_sensitivity.csv`.
