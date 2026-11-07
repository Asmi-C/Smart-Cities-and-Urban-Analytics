# Round 10 domain-shift evidence and blockers (development corpus only)

**Primary scope:** evaluation-methodology study, not a new predictor or validated municipal intervention tool. All 15 original Landsat-8 acquisitions are reused exploratory/development data. The intended untouched final test and second city were not completed. This ledger gives exact outputs, including negative results and normalization assumptions.

## D0–D3 shared-model results

The four fixed model families were evaluated on identical date/region partitions per regime; D1/D3 target spectral normalization uses only the held region's **unlabeled** index distribution. R² is macro-averaged over scored domains, not pooled over hex observations.

| Model | D0 R² | D1 R² | D2 R² | D3 R² | D3 RMSE °C | D3 AUROC |
|---|---:|---:|---:|---:|---:|---:|
| Ridge z | 0.603 | 0.107 | 0.578 | 0.057 | 1.266 | 0.768 |
| Random Forest z | 0.610 | 0.031 | 0.599 | 0.080 | **1.251** | 0.742 |
| Histogram gradient boosting z | 0.573 | −0.014 | 0.602 | **0.087** | 1.246 | 0.737 |
| Random Forest z + projected coordinates | **0.689** | 0.086 | **0.741** | 0.054 | 1.296 | 0.767 |

**Rank reversal:** date-only D2 prefers coordinate-aware RF; joint D3 prefers histogram gradient boosting in R², but its margin over normalized RF is only 0.007 and has **not** been shown statistically distinguishable. D2-versus-D3 model-order Spearman correlation **−0.20**, Kendall τ **0.00** among four models. D0-versus-D3 Spearman **−0.80**, Kendall τ **−0.667**. Do not characterize such small four-model rank coefficients as precise population parameters.

**Date-only evaluation optimism D2 − D3:** HGB **0.515**, normalized RF **0.519**, Ridge **0.521**, coordinate-RF **0.687** R²; exact eight-calendar-year sign-flip tests **p=0.0078125** for each positive mean gap. Equal-year bootstrap intervals are in `outputs/tables/validation_optimism.csv`; e.g. coordinate RF **[0.603,0.776]**. This is a paired descriptive benchmark of our sampled acquisition years; spatial quadrants share common geometry and no independent-city transfer has yet been conducted.

**Relative-heat accuracy is not absolute forecasting.** Held-date target means were used solely for evaluation anomaly definitions, never as model inputs. Within-date random and within-date spatial regimes differ fundamentally in source information and cannot be interpreted as forecasting future date-mean temperatures.

## Why the joint result differs from Round-9 sensitivity

The primary D3 implementation standardizes test spectra **within each withheld quadrant**, matching Round-9 unseen geography (RF D3 mean R² ~0.080). An extra exploratory whole-scene unlabeled-normalization analysis is provided separately in `domain_shift_model_matrix_whole_scene_transductive.csv`; this uses additional *unlabeled* spectral access to other test-date quadrants and is not interchangeable with the core new-region deployment scenario. Under the more permissive protocol D3 R² rises to **0.438 Ridge, 0.437 RF, 0.426 HGB and 0.434 coordinate RF**; D2-minus-D3 optimism falls to **0.140–0.307**, compared with **0.515–0.687** under held-region-only normalization. This **large sensitivity** requires presenting both protocols and pre-registering unlabeled deployment information before future confirmatory tests. No held-date LST labels enter either normalization scheme.

## Severity and error structure

Source-vs-target raw NDVI/NDBI/MNDWI distributional shift was estimated with 1-Wasserstein distance. Across 40 D3 region/date folds, its mean distance correlates weakly with D3 RF RMSE (Spearman ~0.146, exploratory p~0.368); therefore shift-magnitude-based **failure prediction is not established**. The residual ANOVA-like sequential grouping attributes only a small fraction of sum-of-squares to date mean (anomalies are date-centered), more to between-region differences and date×region interaction, with large within-domain residual variation. These are descriptive non-orthogonal components, not identified latent physical random effects.

## Boundary core and residual caveats

An eight-direction, 640-m translation-scenario **intersection** retains only **109** of 537 source hexes. Re-scoring D3 only where at least 15 such scenario-core hexes remain yields **25** region/date folds; mean R² becomes highly unstable/negative because the core contains much less variation. On these 25 small-support folds normalized RF ~**−1.171**, HGB ~**−1.188**, coordinate RF ~**−0.846**, Ridge ~**−1.114**. This is a **severe support sensitivity**, not a corrected official boundary. The even stricter combined 640+962-m core has only 26 hexes and cannot support 15-test-hex region folds. `outputs/tables/stable_interior_joint_shift.csv` contains the exact tests.

Existing residual Moran tests remain significant for normalized RF and historical residual-corrected RF across kNN4/8/12 and 550-m weighting. No spatially valid new uncertainty model was proven under D3. Do not claim spatial dependence is solved.

## Untouched and external replication

No new acquisition outcomes have been inspected as final untouched confirmation. The pre-existing 2018–2026 Landsat-8 metadata search supplies 28 eligible scenes but the frozen rule selects at most two/year, so adding third same-year scenes would violate the original cap without a newly registered protocol. There is no eligible 2022 scene in the original catalog. Landsat-9/second-city replication would require a new, prospectively frozen acquisition protocol plus separate processing; neither was executed here. **These gates remain failed.**

## Supporting outputs

- `domain_shift_model_matrix.csv`, `domain_shift_model_matrix_long.csv` — D0–D3 matched model-family results.
- `model_rank_reversal.csv`, `validation_optimism.csv` — rank correlation and year-clustered R² optimism.
- `domain_shift_severity.csv`, `domain_shift_severity_correlations.csv` — exploratory Wasserstein analysis.
- `error_variance_decomposition.csv` — sequential descriptive date/region/interaction variance.
- `stable_interior_joint_shift.csv`, `boundary_stable_interior_640m.csv` — 640-m boundary-translation scenario core.
- `paper/EVALUATION_PRACTICE_REVIEW.csv` — **preliminary three-source** practice matrix, not a comprehensive survey.
