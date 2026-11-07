# Pre-registered evaluation protocol: round 4 (frozen before new model runs)

**Research target.** Test whether adding absolute projected location to morphology/spectral/accessibility RF improves 1-km *geographic* holdout accuracy robustly across arbitrary block origins, without hiding residual spatial autocorrelation.

## Primary model comparison

- Baseline: previously fixed RF (`n_estimators=120`, `min_samples_leaf=5`, `max_features=.8`), 11 covariates.
- Challenger: same RF and covariates plus projected centroid (kilometers, centered), no response-derived neighborhood feature.
- Primary metric: mean out-of-fold RMSE difference (challenger minus baseline) over **12 prespecified shifted geographic block origins**. Positive effect means lower RMSE (negative difference).
- Secondary: MAE, R², 8NN residual Moran's I; at least two deterministic RF seeds to inspect stochastic variation.
- Spatial folds: five GroupKFold folds of 1-km blocks per shift. Identical folds across models, no outer-fold target access in fitting.
- Success threshold: lower RMSE on ≥10/12 offsets for both seeds, bootstrap interval for mean paired offset difference wholly below zero, and no worsening of Moran I on majority of offsets. This is *internal* robustness only, not proof of temporal/external transfer.
- No hyperparameter search on outer fold outcomes. Do not alter the proposed method after seeing results.

## Independent dataset requirement

True temporal/external claims require comparable raw thermal and predictor stacks from independently acquired and harmonized periods or cities. Metadata-only STAC search is not a validation experiment. Freeze the above RF models and transforms before accessing independent target data. No external score may be reported without complete records.

## Decision-method novelty

The prior Pareto/acceptability gate failed. Treat it as an *auditing baseline*, not a claimed new algorithm. Before claiming ranking improvement, implement published SMAA/TOPSIS/robust ordinal comparators and preregister a new method and success metric. This round will not retrofit scores to generate an advantage.
