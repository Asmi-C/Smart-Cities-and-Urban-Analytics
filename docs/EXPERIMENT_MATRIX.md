| ID | Hypothesis | Design | Metric | Status | Evidence |
|---|---|---|---|---|---|
| E1 | Random CV is optimistic | random vs 1 km geographic blocks | R², RMSE, MAE | Complete | ieee_validation_matrix.csv |
| E2 | Skill depends on separation | 1/1.5/2 km blocks, 250 m buffer, contiguous strips | RMSE, MAE | Complete | ieee_validation_matrix.csv |
| E3 | Extra feature families do not reliably help | morphology plus spectral/access additions | RMSE difference | Complete | ieee_validation_matrix.csv |
| E4 | Spatial baseline may be competitive | SpatialKNN8 vs mean/Ridge/RF/HGB | RMSE | Complete | ieee_validation_matrix.csv |
| E5 | Residuals preserve geography | 8NN Moran and 999 permutation | Moran I, p | Complete | residual_spatial_diagnostics.csv |
| E6 | Geographically calibrated intervals may undercover | train-group calibration and held-out test groups | empirical coverage, width | Complete | prediction_uncertainty.csv |
| E7 | Ranks vary under plausible policy weighting | 501 preference schemes | top-quintile acceptability, rank entropy | Complete | rank_uncertainty_pareto.csv |
| E8 | Spatial aggregation affects summary | 250/500/750/1000 m square aggregation | unit count, dispersion | Preliminary | scale_sensitivity.csv |
| E9 | Robust interventions need multiple evidence dimensions | Pareto depth and separate policy/heat uncertainty | candidate classes | Complete as screening | ieee_priority_results.gpkg |
| E10 | Network and straight-line access differ | OSM network rerouting | distance ratio, Gini | Original pipeline network distance only; independent benchmark pending | original code |
| E11 | Models transfer to another year | temporal holdout | RMSE | Not possible from present single-year hex response | future work |
| E12 | Method transfers to another city | independent city | all primary metrics | Not conducted | future work |
