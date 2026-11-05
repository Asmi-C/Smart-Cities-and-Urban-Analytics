# Verified research results (3 November 2026)

## Spatial model, 1-km block CV

- Baseline RF: RMSE 0.891°C, R² 0.511, residual Moran I 0.439 (p=0.001).
- RF + projected coordinates: RMSE 0.820°C, R² 0.586, residual Moran I 0.383 (p=0.001).
- Cross-fitted residual KNN: Moran I 0.310, but worse RMSE 0.904°C.
- Paired 1-km block-bootstrap of fixed OOF predictions: coordinate improvement −0.071°C, 95% interval [−0.113, −0.035]°C.

## Repeated grid origin (completed)

- 12 prespecified 1-km grid origins and 2 RF seeds, 24 paired comparisons.
- RF + coordinates improved RMSE and residual Moran I in all 24 matched comparisons.
- Mean RMSE: 0.804°C (RF) versus 0.742°C (RF + coordinates).
- Mean Moran I: 0.419 (RF) versus 0.333 (RF + coordinates); still positive.

## Independent thermal data (metadata only)

- Public STAC search verified Landsat 8 Level-2 scenes 2021-03-24 and 2026-03-22, same path/row.
- TLS certificate-chain failure blocked thermal COG reading; **no temporal transfer experiment completed**.

## Decision-method novelty caveat

- Prior Pareto/acceptability/interval-gated shortlist underperformed equal weights: top-quintile retention 0.886 vs 0.942, perturbed top-37 Jaccard 0.319 vs 0.506.
- Published SMAA/SMAA-2 already established preference-weight rank acceptability; this is not a novel algorithm on its own.

**Status:** internal spatial validation substantially strengthened; strict 5/5 publication thresholds remain unmet.
