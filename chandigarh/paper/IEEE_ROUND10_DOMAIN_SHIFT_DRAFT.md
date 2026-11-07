# Spatial–Temporal Domain Shift in Urban Heat GeoAI: What Transfers Across Acquisitions and Locations?

**Manuscript status:** evidence-backed development draft, **NOT submission-ready**. This paper is framed as a generalization-evaluation and negative-results study, *not* a novel predictive model or validated municipal intervention procedure. Frozen five-acquisition Landsat-9 cross-sensor confirmation is complete; independent-area replication remains outstanding.

## Abstract

Satellite-derived urban land-surface-temperature (LST) regressors are commonly tested without simultaneously withholding acquisition date and geography. We define four evaluation regimes: D0 within-date random interpolation, D1 within-date geographic transfer, D2 new date at familiar sites, and D3 joint date-and-region shift. With 15 Landsat-8 Collection-2 Level-2 scenes across eight years over New Town–Rajarhat, fixed Ridge, Random Forest, gradient-boosted and coordinate-aware Random Forest models exhibit D2-to-D3 mean-centered anomaly-R² optimism of **0.515–0.687** under region-only unlabeled target normalization (eight-year-cluster p=0.0078). Coordinate RF scores R²=**0.741** under D2 but **0.054** under D3 and falls from best to worst rank. When whole-township unlabeled spectral imagery is supplied for normalization, D3 improves to **0.426–0.438** and the optimism gap narrows to **0.140–0.307**, highlighting a consequential information-set assumption. In a prospectively frozen test of five Landsat-9 dates, trained exclusively on Landsat-8 source labels, all four models again exhibit positive equal-date D2–D3 gaps (**0.315–0.477**), though five-date two-sided exact p=**0.0625** and the development rank reversal **does not replicate**: coordinate RF ranks first in both regimes. A prior site-memory spatial correction also harms D3 relative to spectral RF. The contribution is a reproducible demonstration of evaluation optimism and protocol sensitivity, not a new superior predictor. Independent-city replication, residual-dependence-aware uncertainty, and physical validation remain missing.

## 1. Motivation and contribution

Urban thermal patterns are spatially correlated and satellite acquisitions differ in weather, reflectance conditions and clear-sky support. Random within-scene splitting measures interpolation over familiar conditions; date-only transfer may exploit persistent location memories. The central question is **whether model-ranking and error estimates from D0–D2 remain trustworthy in D3, when neither test acquisition labels nor test-location historic labels are available**.

This work contributes a transparent four-regime urban-heat evaluation protocol, direct repeated-domain comparison of common model families, model-rank reversal and year-aware optimism estimates, and explicit negative evidence on naive persistent-residual correction. The concepts of spatial/temporal blocking predate this work (Roberts et al., *Ecography*, 2017, DOI 10.1111/ecog.02881); novelty is the structured empirical *urban-heat evaluation evidence*, not invention of block validation.

## 2. Data and thermal target

The analysis uses 15 quality-screened Landsat-8 C2L2 thermal and spectral scenes from 2018–2026, selected using WRS 138/045, a February–May acquisition window, <=25% scene cloud cover and predeclared minimum >=180 complete hex units. One selected scene failed quality screening (28 valid hexes). Eight calendar years are represented, with at most two selected scenes in any year. The ST_B10 product conversion is `DN*0.00341802 + 149 - 273.15` °C and QA_PIXEL cloud/fill flags are excluded (`docs/REMOTE_SENSING_VALIDATION.md`). A common subset of 180 hex units is available in all 15 acquisitions.

For observation i at date t, retrospective within-acquisition anomaly is A_it = LST_it - mean_j(LST_jt). The **true test acquisition mean is never used to fit a model or construct predictors**; it defines the evaluation target. Consequently anomaly skill does not imply operational absolute-LST forecasting. Ground-truth surface-emissivity and station validation are not independently established.

## 3. D0–D3 evaluation taxonomy and models

| Regime | Date | Geography | Validation purpose |
|---|---|---|---|
| **D0** | Seen | Intermixed same-scene units | Standard random interpolation |
| **D1** | Seen | Whole held-out quadrant | Geographic extrapolation at familiar date |
| **D2** | Held out | Previously observed places | Cross-acquisition transfer |
| **D3** | Held out | All historic labels from held quadrant withheld | Joint spatiotemporal extrapolation |

Geographic quadrants are determined from a fixed projected-centroid median x/y partition, with >=15 target hexes required. Three of four quadrants yield eligible tests, totaling 40 quadrant/date folds. All D3 models are trained solely on *other dates and other quadrants*. Models: Ridge(alpha10), Random Forest (45 trees, min leaf5, max features0.8), Histogram Gradient Boosting (80 iterations, min leaf10) and Random Forest with fixed projected coordinates. Spectral features are NDVI, NDBI and MNDWI, normalized by unlabeled acquisition-specific spectral distributions. For D1/D3 the target normalization window is the held region only; D0/D2 have whole-date target feature access. A separate analysis explores whole-scene transductive normalization under D3, since the deployment availability of unlabeled imagery can change the apparent generalization result.

## 4. Model performance and rank reversal

| Model | D0 R² | D1 R² | D2 R² | D3 R² | D3 RMSE °C | D3 AUROC |
|---|---:|---:|---:|---:|---:|---:|
| Ridge | 0.603 | **0.107** | 0.578 | 0.057 | 1.266 | **0.768** |
| RF | 0.610 | 0.031 | 0.599 | 0.080 | 1.251 | 0.742 |
| Histogram boosting | 0.573 | −0.014 | 0.602 | **0.087** | **1.246** | 0.737 |
| RF + coordinates | **0.689** | 0.086 | **0.741** | 0.054 | 1.296 | 0.767 |

D2-to-D3 R² optimism is +0.515 (boosting), +0.519 (RF), +0.521 (Ridge), and **+0.687 (coordinate RF)**. Exact eight-year-cluster paired tests return p=0.0078125 for each positive gap; coordinate RF's equal-year bootstrap interval is [0.603, 0.776]. The best D2 model (coordinate RF) becomes the **worst D3 model by R²**. D2–D3 Kendall rank correlation is 0.0 and Spearman −0.2 across four models. The D3 ranking differences between the best two models are small and not independently proven significant; rank reversal is *descriptive*, not a guaranteed universal order.

An earlier source-only persistent location correction attains D2 anomaly R² 0.737 but falls to D3 R² 0.027 relative to normalized RF D3 0.080 (paired ΔR² −0.053, clustered p=0.0078). Interpolated historical climatology has D3 R² −0.418. This negative result exposes why favorable date-only scores do not establish geographic transfer.

### 4.1 Unlabeled target-context sensitivity (material limitation)

The primary D3 protocol treats the target region as a standalone unseen domain and standardizes only its own observed spectra. A second exploratory protocol grants access to **unlabeled spectra over the *entire* target-date township** for estimating the z-score reference distribution. No additional LST labels are used. Under that more permissive transductive scenario, D3 R² changes markedly:

| Model | D3, region-only unlabeled normalization | D3, whole-township unlabeled normalization |
|---|---:|---:|
| Ridge | 0.057 | **0.438** |
| RF | 0.080 | 0.437 |
| Histogram boosting | **0.087** | 0.426 |
| Coordinate RF | 0.054 | 0.434 |

Consequently, D2–D3 optimism under whole-scene spectral reference access is only **0.140–0.307 R²**, rather than **0.515–0.687** under target-region-only normalization. This is not a difference in held-out target labels; it is a consequential difference in how unlabeled target covariates are available and normalized. The two regimes should **not** be pooled or presented as the same D3 test. The conclusion that date-only scores are optimistic remains directional in both settings, but its *magnitude* and the D3 model ranking are information-set dependent. This is a major caveat and a useful additional protocol variable to declare explicitly.

## 5. Frozen cross-sensor acquisition confirmation (Landsat 9)

Before new thermal outcomes were retrieved, a metadata-only search froze one eligible Landsat-9 Collection-2 Level-2 acquisition in each of 2022, 2023, 2024, 2025 and 2026 (`data/round10_landsat9_confirmatory_frozen.csv`). All five passed the predeclared >=180-valid-hex criterion, with 246, 232, 271, 204 and 220 valid units respectively. The original 15 Landsat-8 scenes supplied **all training labels**; no Landsat-9 data were used for model selection or training. This is an independent acquisition series on another satellite platform but **not** an independent urban area or field thermometry.

| Fixed model | L9 D2 anomaly R² | L9 D3 held-region normalization R² | L9 D3 whole-scene unlabeled normalization R² | Equal-date D2–D3 gap, held-region |
|---|---:|---:|---:|---:|
| Ridge | 0.562 | 0.164 | 0.347 | 0.315 |
| RF | 0.567 | 0.148 | 0.325 | 0.344 |
| Histogram boosting | 0.580 | 0.138 | 0.329 | 0.360 |
| RF + coordinates | **0.749** | **0.197** | **0.370** | **0.477** |

The D3 columns macro-average 11 eligible region/date folds across five dates; D2 macro-averages five whole dates. The final gap column separately equal-weights five date-specific differences (D2 R² minus mean D3 block R²), hence is not simply the difference of other displayed columns. Every model's gap was positive on every date. Under a two-sided exact sign-flip test over five dates, the smallest p-value for all-positive gaps is **0.0625**, so the independent trial should not be presented as reaching p<0.05. Crucially, unlike the Landsat-8 development set, coordinate RF **remains the best model in both D2 and D3**; the rank reversal did **not** replicate. The recurring result is evaluation optimism under joint domain shift, not a universal model ordering.

Unlabeled target-context sensitivity recurs (coordinate RF D3 R² 0.197 with only held-region spectra versus 0.370 with whole-scene spectra); these are different deployment information sets, not target-label leakage. Applying unmodified Landsat-8 empirical absolute-residual quantiles to the L9 D3 test yields mean empirical 90% coverage of 0.862–0.884 across model/date/region cells, with individual cells as low as 0.611. This is an **uncalibrated diagnostic**, not valid predictive coverage. Independent cross-platform thermometric calibration against in situ instruments has not been carried out.

## 6. Shift severity, spatial dependence and geographic support

Across 40 D3 block/date folds, mean one-dimensional Wasserstein distance for NDVI/NDBI/MNDWI correlates only weakly with RF RMSE (Spearman ~0.146, exploratory p~0.368); this simple domain-shift scalar is **not a validated failure predictor**. Date/region interaction and heterogeneous within-region errors remain. Permutation Moran's I remains significant under kNN4, kNN8, kNN12 and a 550-m distance band for the previously tested spectral and residual-correction RF models (all tested p≈0.005 at 199 permutations). A separate source-only spatial uncertainty model under D3 has not been established.

The study area's digitized map has approximate five-anchor fit RMS ~640m without geodetic control. Under eight hypothetical translation directions at radius 640m, the intersection of retained original hexes consists of just **109/537** units. D3 performance on eligible 640-m scenario-core folds is very unstable (negative R²), while the combined 640+962-m core has insufficient test support. This does not identify the legally correct boundary or enable parcel-scale planning inference.

## 7. Discussion: what transfers?

**Within-date spatial interpolation and across-date within-site transfer are different targets from joint spatial–temporal extrapolation.** Date-only models can benefit from persistent urban morphology and location-specific structure. Yet adding a location-residual correction can degrade D3. In our sample, high within-date or D2 R² does not guarantee useful unseen-site predictions; no D3 model exceeds mean R² 0.09. The best methodological contribution is the requirement to declare the deployment shift type and test all relevant dimensions, not to choose a model from an easier validation regime and generalize its headline score.

The broader field already recognizes geographic block cross-validation; this study's impact must come from rigorous urban-heat evidence, independent replication, careful physical interpretation and transparent data availability. Preliminary evaluation-practice comparisons appear in `paper/EVALUATION_PRACTICE_REVIEW.csv`, but they are **not a comprehensive or representative survey**. Unregistered planning boundaries, unaudited OSM and population proxies are kept outside central method claims.

## 8. Limitations and submission-readiness

1. All fifteen Landsat-8 development dates were examined repeatedly; five frozen Landsat-9 acquisitions provide independent cross-sensor confirmation of date-only optimism, but no independent city is tested and development-set rank reversal did not replicate.
2. D3 geographic folds sample three quadrants of one township, not independently chosen cities, and only eight calendar years are represented.
3. The target-normalization information set changes what constitutes achievable D3 accuracy; both region-only and whole-scene transductive assumptions must be reported.
4. Residual spatial correlation persists, and D3 prediction intervals are not proven calibrated.
5. New D3 models use only three optical indices and fixed projected coordinates; their small R² is not a universal limit on remote-sensing thermal modeling.
6. Absolute-LST meteorological reconstruction remains unreliable (prior best mean R² −0.441). Retrospective mean-centered anomalies are not forecasts.
7. Independent physical cross-sensor and field-ground-truth thermal validation, official geospatial boundary, current OSM network and independent population sensitivity remain unavailable.

**Manuscript status:** stronger evidence for a domain-shift/evaluation paper because independent cross-sensor acquisitions reproduce date-only optimism, **not yet submission-ready** without independent-area replication, stronger spatial-statistics/uncertainty validation and a more comprehensive evaluation-practice review. All reproducible per-domain CSVs and scripts are in the Round-10 package.

## Selected references

- Roberts et al. (2017), “Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure,” *Ecography*, DOI 10.1111/ecog.02881.
- Andriambololonaharisoamalala et al. (2025), “Downscaling of Urban Land Surface Temperatures Using Geospatial Machine Learning with Landsat 8/9 and Sentinel-2 Imagery,” *Remote Sensing*, 17(14), 2392.
- Bhushan et al. (2026), “Prediction of land surface temperature dynamics over Lucknow via Google Earth Engine and machine learning approach,” *Advances in Space Research*, DOI 10.1016/j.asr.2026.02.096.
