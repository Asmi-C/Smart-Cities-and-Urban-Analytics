# Urban heat GeoAI domain-shift taxonomy (Round 10, frozen before evaluation)

All spatial features are observed satellite reflectance indices; LST is an outcome. No test LST is used in features or model fitting. Each date's true mean is used **only for retrospective anomaly evaluation**. All metrics refer to modeled same-scene land-surface temperature anomalies, not prospective absolute temperature forecasts.

| Code | Date during training | Test geographic units in training? | Construction |
|---|---|---|---|
| D0 | Same | Familiar geographic domain | Within-date seeded 80:20 random split, training labels restricted to train 80% |
| D1 | Same | No | Centroid-median quadrant held out; train on that date in other quadrants |
| D2 | No | Yes or historically overlapping | Entire acquisition held out; train on other dates' labeled units |
| D3 | No | No | Date and entire quadrant withheld; train on other dates and other quadrants |

Use identical fixed model configuration across regimes: Ridge with standardized covariates, RandomForest (45 trees/leaf5), HistGradientBoosting (max_iter=80, leaf10), and RandomForest with projected geographic coordinate features. All spectral indices normalized using unlabeled covariates: in D1/D3, held-region spectra alone define the target-domain normalization (matching Round 9); in D0/D2, the full available target acquisition spectra define it. Geographic coordinates normalized globally from fixed hex grid, not from target labels. This normalization-window choice is a potential deployment assumption, not interchangeable with full-township transductive alignment.

**Spatial-block feasibility:** fixed four quadrant IDs defined at global projected median x/y; score only domain cells with at least 15 test samples. One quadrant is small/unrepresented; report actual cells and do not pretend all four are populated. Treat 15 previously explored acquisitions as development data. This run cannot prove untouched confirmation.

Primary **descriptive** outcome: per-domain mean R² and ranking change D2 to D3. Secondary RMSE, hotspot AUROC, source–target index-shift severity and domain-level variance. No p-value claim without year/region cluster analysis. Historical-site climatology is not included in this common-feature matrix because D0/D1 have no prior-year history and site climatology has a different information set; its separate fair D3 comparison remains in Round 9.
