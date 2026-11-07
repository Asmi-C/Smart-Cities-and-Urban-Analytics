# Current presentable results (automatically generated)

All results below are **VERIFIED computations on the existing exported 537 hexagons**, not independent field validation.

- Spatial CV: 1 km geographic groups, 5 held-out folds, 52 unique blocks; random 5-fold comparison.
- Best combined-feature model under spatial CV: **RF**, RMSE **0.876 °C**, out-of-fold R² **0.527**.
- Baseline mean, Ridge, RF, HGB, and four feature groups were evaluated. Full matrix: `outputs/tables/spatial_cv_results.csv`.
- Intervention screening: **79** hexagons are in the bottom liveability quintile under at least 80% of 302 weighting schemes.
- Equal weights and original AHP overlap: **74 / 108** original priority hexagons. Full-rank Spearman rho **0.857**.

## Slide figures

1. `outputs/PPT_FIGURES/01_spatial_cv.png`
2. `outputs/PPT_FIGURES/02_ablation.png`
3. `outputs/PPT_FIGURES/03_intervention_map.png`
4. `outputs/PPT_FIGURES/04_predicted_vs_observed.png`

## Important safeguards

- LST target and spectral predictors share remote-sensing acquisition context; this is spatial interpolation evaluation, **not causal attribution or independent forecast skill**.
- The original 2016 Dynamic World agreement (21.21%) and ESA WorldCover 2021 agreement (43.79%) raise substantial concerns for temporal land-cover change claims.
- Intervention labels are exploratory rules, not independently validated policy recommendations.
- Spatial block size is fixed at 1 km; further buffer / block-size robustness is needed before publication.
