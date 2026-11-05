# Spatial Generalization and Preference-Robust Intervention Screening in New Town, Kolkata: A Reproducible GeoAI Case Study

*Draft research manuscript, 3 November 2026. Not yet submitted or independently validated.*

## Abstract

Urban spatial models can appear accurate under random validation while failing at geographically separated locations. We study this issue using 537 existing 250-m analysis hexagons in New Town, Kolkata, and construct a decision-screening approach that reports geographic predictive uncertainty separately from multiobjective policy-weight uncertainty. We evaluate mean, Ridge, Random Forest (RF), histogram gradient boosting and coordinate-only spatial k-nearest neighbors over eight randomized, block, buffered-block and contiguous-region validation schemes. Under random five-fold CV, combined-feature RF achieves an LST RMSE of 0.725°C, rising to 0.891°C for 1-km spatial blocks and 0.954°C for 2-km blocks with 250-m exclusion buffers. Residual spatial dependence persists (Moran's I=0.439, permutation p=0.001). A paired geographic-block bootstrap provides no support for superiority of combined features over morphology alone (ΔRMSE=0.016°C, 95% interval [−0.092, 0.164]°C). In a separate three-objective intervention screening, 58 of 537 hexes occupy the highest-concern quintile under at least 80% of 501 explicit policy-weight scenarios. Of these, 37 have below-median model interval width. The analysis demonstrates an auditable separation of geographic generalization, policy preference uncertainty and multiobjective severity. The results remain preliminary because thermal labels are remotely sensed, residual spatial dependence is significant and proposed interventions lack outcome validation.

**Index Terms:** GeoAI, spatial cross-validation, urban heat island, multicriteria decision analysis, uncertainty, New Town Kolkata, spatial autocorrelation.

## I. Introduction

Surface temperature and uneven public-service access can coexist within rapidly developing planned urban areas. The planning task requires identifying candidates for investigation while accounting for geographically dependent learning and uncertain policy preferences. Prior work already quantifies land-cover and heat changes in New Town [2]. This paper investigates model transfer within the township and the stability of spatial priorities under alternative policies.

**Contributions.** (i) A suite of spatial generalization stress tests using randomized, variable-size block, buffered and leave-region-out splits; (ii) spatial-baseline, feature-ablation, residual spatial autocorrelation and paired-bootstrap evaluations; (iii) a separable Pareto/rank-acceptability/interval-width screening method; (iv) a reusable georeferenced, code-generated evidence package.

## II. Related Work

Mahata et al. [2] studied 1991–2021 LULC and UHI variation in New Town, including Getis–Ord Gi*. Their findings provide local environmental context; their period, labels and spatial boundaries are insufficiently matched to compare our predictive metrics directly. Roberts et al. [1] explain why random splits may understate generalization error when observations share spatial dependence. We therefore report multiple split structures rather than interpreting one spatial score as universal. The exact novelty of this combined decision protocol relative to the full MCDA, robust optimization and urban GeoAI literature still requires more exhaustive review.

## III. Study Area and Data

The study uses the existing NKDA digitized boundary, ~29.2 km², 537 hexagon-derived records and pre-monsoon satellite LST, satellite indices (NDVI, NDBI, MNDWI), built/vegetation/water shares and OSM-derived service distances. The records come from the original repository export `hex_results.gpkg`; no new field survey or independent LST labels were collected. Some inputs and the LST target share a remote-sensing provenance. The original temporal LULC results are excluded from the main inference due to weak reference agreement and inconsistent 2016-versus-later Sentinel preprocessing.

## IV. Proposed Method

Let \(x_i\) be the feature vector, \(s_i\) the centroid and \(y_i\) the satellite-derived temperature. Models are trained on geographic training sets \(T_k\) and assessed on disjoint held-out sets \(V_k\):

\[\mathrm{RMSE}=\sqrt{\frac{1}{n}\sum_{i=1}^n(y_i-\hat{f}_{T_{k(i)}}(x_i))^2}.\]

We compare geographic blocks of 1, 1.5 and 2 km, 250-m exclusion buffer variants, contiguous x- and y-oriented strips, and random folds. For spatial residuals, global Moran's I uses eight nearest spatial neighbors and 999 location permutations. Geographic-block bootstrap contrasts two out-of-fold model residual sets, resampling 1-km blocks rather than individual correlated hexagons.

For the decision model, three normalized concern dimensions are \(z_i=(\mathrm{heat}_i,\mathrm{serviceDeficit}_i,\mathrm{blueGreenDeficit}_i)\), each increasing with concern. Pareto depth identifies nondominated severity layers. Preference scenarios \(w_b\) lie on the simplex and produce rank \(r_i(w_b)\). Top-quintile acceptability is:

\[A_i=B^{-1}\sum_b\mathbf{1}\{r_i(w_b)\le\lceil 0.2n\rceil\}.\]

We report mean/median/SD of rank, rank-decile entropy, Pareto depth, acceptability and separate heat interval width. We deliberately avoid creating a single conflated confidence score. Section `docs/PROPOSED_METHOD.md` gives full definitions.

## V. Experimental Design

Models: constant mean, Ridge, RF (120 trees, minimum leaf size 5), histogram gradient boosting and coordinate-only eight-nearest-neighbor regression. Feature families: morphology; morphology plus satellite indices; morphology plus access; all features. Every split uses the same held-out evaluations for matched comparisons. RF random seed is 42. No hyperparameter tuning on the outer held-out folds was conducted, but hyperparameters were set heuristically, not via nested selection.

The prediction interval diagnostic uses group-separated internal calibration in each outer geographic training fold. Nominal coverage is 90%; only empirical held-out coverage is claimed. Policy weights comprise equal weights plus 500 seeded Dirichlet(2,2,2) samples. The Dirichlet distribution is an explicit scenario assumption rather than observed policy preference data.

## VI. Results

**Table I. Geographic generalization of combined-feature RF.**

| Validation scheme | RMSE (°C) | MAE (°C) | R² |
|---|---:|---:|---:|
| Random 5-fold | 0.725 | 0.586 | 0.676 |
| 1-km blocks | 0.891 | 0.682 | 0.511 |
| 1.5-km blocks | 0.827 | 0.666 | 0.579 |
| 2-km blocks | 0.914 | 0.720 | 0.485 |
| Contiguous x strips | 0.825 | 0.661 | 0.581 |
| Contiguous y strips | 0.885 | 0.693 | 0.517 |
| 1-km blocks + 250-m buffer | 0.929 | 0.704 | 0.469 |
| 2-km blocks + 250-m buffer | 0.954 | 0.744 | 0.439 |

Split geometry produces non-monotonic results: the 1.5-km and x-strip evaluations are easier than 1-km blocking. Geographic block size is not a simple numerical distance variable. This cautions against presenting a monotonic separation law.

**Table II. Residual structure under 1-km blocks.**

| Model | Moran's I | Two-sided permutation p |
|---|---:|---:|
| Ridge | 0.496 | 0.001 |
| RF | 0.439 | 0.001 |
| HGB | 0.422 | 0.001 |
| SpatialKNN8 | 0.345 | 0.001 |

All four leave spatially clustered errors. A geographically aware predictor alone does not eliminate missing spatial structure.

**Table III. Decision uncertainty.**

| Quantity | Result |
|---|---:|
| Preference scenarios | 501 |
| Top-quintile acceptability ≥0.8 | 58 hexes |
| High-consensus with below-median interval width | 37 hexes |
| First Pareto front | 7 hexes |
| Empirical coverage of nominal 90% intervals | 91.4% |
| Mean interval width | 2.930°C |

These intervals estimate the dispersion of satellite-derived LST predictions, not directly measured human exposure.

## VII. Ablation and Robustness

Under 1-km blocking, combined RF achieves 0.891°C. The combined-minus-morphology difference is +0.016°C and geographic-group bootstrap 95% interval is [−0.092, 0.164]°C. The difference is not distinguishable from zero by this analysis. Additional features may be redundant, affected by measurement mismatch or correlated with morphology. These are hypotheses requiring further testing, not established mechanisms. Aggregation at 250/500/750/1000 m square bins is an exploratory MAUP diagnostic, not a substitute for regenerating independent hex-grid products.

## VIII. Planning Implications

The model separates geographic model error from decision preference variability. A high-consensus priority candidate with a wide thermal interval merits independent thermal verification; stable candidates with narrower intervals can be examined first for local feasibility. Pareto-front units represent diverse, severe tradeoffs and should not all receive the same intervention. Service access rules generate candidate audits, not guaranteed optimal investments. No monetary objective, stakeholder preference survey or post-treatment outcome was available.

## IX. Limitations

Significant residual Moran's I is a major unresolved methodological weakness. Fixed grid origins and one township limit universality. Same-date satellite covariates may have shared measurement errors with the temperature target. Spatially calibrated intervals have no guaranteed spatial-shift coverage. Rank probabilities are conditional on a chosen preference distribution, not empirical uncertainty probabilities. Network accessibility depends on source OSM completeness. Historical LULC change lacks sufficient independent validation. No temporal or external-city transfer test has been performed. No intervention cost or measured causal effectiveness is available.

### Additional submission-blocker experiments (3 November 2026)

**Leakage-safe spatial correction.** We retained 1-km outer geographic folds and tested RF with projected centroids, 750-m neighborhood covariate summaries, both combined, and RF residual correction. Residual correction was learned solely from *inner geographically out-of-fold training residuals*, with fixed 700-m kernel bandwidth or eight training residual neighbors. The held-out response was never used in any spatial feature or correction. The unaugmented RF RMSE was 0.891°C, R² 0.511 and residual Moran I 0.439 (p=0.001). Adding coordinates improved RMSE to **0.820°C**, R² to **0.586** and Moran I to **0.383** (p=0.001). Cross-fitted residual KNN reduced Moran I further to **0.310** but increased RMSE to **0.904°C**. This creates a genuine error-versus-residual-dependence trade-off rather than a complete solution. See `outputs/tables/spatial_model_comparison.csv` and `outputs/PPT_FIGURES/08_residual_diagnostics.png` for residual mapping, semivariogram, Moran scatterplot and FDR-adjusted Local Moran categories.

The paired 1-km-block bootstrap of *fixed* OOF predictions estimates the coordinate model's RMSE improvement as −0.071°C (95% percentile interval **[−0.113, −0.035]°C**). It supports a conditional gain for these predictions, but does not represent fully repeated model retraining or an external test. Details: `outputs/tables/spatial_model_gain_ci.csv`.

**Generalization scope.** Harmonized second-period LST predictors or a second city's matching records were unavailable locally; the 2016 and 2021 artifacts are *land-cover class* rasters and must not be treated as thermal observations. The strongest available internal stress test trained on 423 western NKDA hexes and tested on 114 contiguous eastern hexes. RF achieved RMSE 1.000°C, R² 0.360; RF with coordinates achieved RMSE **0.844°C**, R² **0.544**. These hexes were exposed during previous experimentation and this is explicitly an **internal, not independent external or temporal, transfer** experiment. See `docs/GENERALIZATION_EXPERIMENT.md`.

**Decision-method comparison.** At an identical 37-candidate budget, the proposed Pareto/rank-acceptability/interval-width gate was compared with equal-weight, AHP-proxy and fixed-weight priority rankings. The evaluation used 300 new, disjoint Dirichlet(0.7,0.7,0.7) preference scenarios and separate 0.04-standard-deviation normalized-feature perturbations. Mean retained top-quintile status was **0.886** for the proposed method, **0.942** for equal weight, **0.834** for AHP proxy and **0.941** for fixed weight. Mean Jaccard overlap with each perturbed scenario's top-37 set was **0.319**, **0.506**, **0.421** and **0.489**, respectively. **The proposed method underperformed equal weighting on both robustness outcomes.** This negative comparison prevents a claim that the new method is currently an empirically superior robust selector. It nevertheless makes predictive interval width and Pareto trade-offs explicit, a transparency property not assessed by these two ranking metrics. For fair interpretation, the AHP comparator is a three-objective proxy to the original five-indicator AHP, not the original index. See `outputs/tables/ranking_baseline_comparison.csv`.

**Updated methodological claim.** Unlike a conventional weighted index, the proposed protocol **reports multiobjective severity, preference acceptability and predictive interval width separately**; experiments show that this added scrutiny **does not improve ranking robustness over equal weights under the tested candidate budget and perturbations**. Therefore its predictive/decision advantage remains unproven and the novelty claim is not sufficiently validated for a strong IEEE/ACM full-paper submission.

### Round-4 research update: repeated geographic validation and independent-data attempt

We preregistered an additional fixed-hyperparameter evaluation in `docs/METHOD_EVALUATION_PROTOCOL.md` before running 12 1-km block-origin offsets with two RF seeds (24 matched pairs). The coordinate-augmented RF achieved lower RMSE in all 24 comparisons, with mean RMSE 0.742°C versus 0.804°C for RF without coordinates. Mean out-of-fold residual Moran I declined from 0.419 to 0.333, also in all 24 comparisons. The mean paired RMSE difference was −0.063°C; a 12-origin bootstrap averaging seeds yielded a conditional 95% interval [−0.067, −0.058]°C. These are correlated re-partitions of the *same* 537 hexagons, not 24 independent cities, and their uncertainty must not be overinterpreted. The result supports internal robustness of spatial coordinate features but does not demonstrate their cross-city transfer or removal of residual dependence. Exact rows: `outputs/tables/shifted_block_validation.csv`; aggregate: `shifted_block_summary.csv`.

For temporal replication, the Planetary Computer STAC catalog independently verified Landsat 8 Collection 2 Level-2 scenes on 24 March 2021 and 22 March 2026, same path/row and near-identical acquisition time, with scene-level cloud percentages of 6.78% and 8.51%. The acquisition script implements matching OLI/TIRS band transformations and QA masking, but actual COG access failed due a TLS certificate-chain error in the raster reader. Thus **no thermal values or temporal transfer metrics have been measured**. `data/thermal_metadata.csv` contains catalog metadata only; `docs/EXTERNAL_DATA_ATTEMPT.md` gives the blocker and recovery requirements.

Our literature audit also corrects the earlier novelty framing. Lahdelma et al. (1998) established stochastic multiobjective acceptability analysis, and Lahdelma and Salminen (2001) extended rank acceptability through SMAA-2. Hengl et al. (2018) developed RFsp for spatial prediction. Consequently neither rank sampling nor spatial proxy features are original algorithms in this project. The scientifically defensible current contribution is a careful, spatially stress-tested case study and an uncertainty-auditing application; a novel method and independent transfer advantage remain unproven. See `paper/RELATED_WORK_MATRIX.csv`.

### Round-5 evidence update: **executed** independent temporal test (3 November 2026)

**Supersedes the earlier data-acquisition failure reported above.** The previous GDAL TLS failure was resolved through verified-HTTPS full downloads to local COG files, without disabling certificate verification. Three actual Landsat 8 Collection 2 Level-2 WRS 138/045 observations—24 March 2021, 1 April 2024 and 22 March 2026—were harmonized for band transformations and QA masking and aggregated to the same NKDA hexagons. Exactly **207 hexagons** are clear in all three. This constitutes independent *time* observations in the same geographic area, not external-city validation. The COG SHA256 manifest, scene IDs, conversion script and outputs are supplied.

**Table IV. Independent temporal generalization, with completely frozen source models.**

| Training → evaluation | RMSE (°C) | MAE (°C) | R² | Residual Moran I (p) |
|---|---:|---:|---:|---:|
| Same-date 2021 geographic CV | 0.917 | 0.731 | 0.632 | 0.469 (.001) |
| Same-date 2026 geographic CV | 1.253 | 1.025 | 0.272 | 0.332 (.001) |
| 2021 → 2026 | 4.436 | 4.276 | −8.128 | 0.379 (.001) |
| 2026 → 2021 | 5.422 | 5.318 | −11.887 | 0.517 (.001) |
| 2024 → 2026 | 7.921 | 7.833 | −28.105 | 0.202 (.001) |
| Combined 2021+2024 → 2026 | 7.373 | 7.274 | −24.220 | 0.204 (.001) |

This **falsifies** a claim of adequate absolute-temperature transfer: 2021 and 2026 observed mean LST on the common hexes differs by **6.464°C**, and 90%-nominal source-period intervals cover only **1.45%** of 2026 targets in forward transfer (0% in reverse). The observed hot-quintile overlap is only 21/42 hexes, Jaccard 0.333. The multi-period source stack does not solve the shift. Atmosphere, meteorology, acquisition variability and varying clear-pixel support may be contributors; they are **not causally identified**. These results are worse than an in-period CV score, not evidence of improved generalization. The protocol used no 2026 target labels to train or tune a source-to-2026 model. Full tables: `outputs/tables/temporal_validation_detailed.csv`, `three_period_transfer.csv`, `temporal_interval_coverage.csv`, `temporal_hotspot_overlap.csv`.

**Table V. Target-safe spatial model extensions, 1-km geographic CV (537 original study hexes).**

| Model | RMSE °C | R² | Residual Moran I (p) |
|---|---:|---:|---:|
| RF + projected coordinates, fixed settings | 0.820 | 0.586 | 0.383 (.001) |
| Nested-geographic tuned RF + coordinates | **0.790** | **0.616** | 0.369 (.001) |
| RF + coordinates + inner-geographic crossfit Matern-GP residual correction | 0.831 | — | **0.304** (.001) |

The nested selector chooses RF configurations using only inner training geographic groups. The GP residual correction uses only *inner out-of-fold training residuals*, not withheld outer targets. Its better residual Moran I comes with a **worse RMSE**. Thus spatial autocorrelation remains unsolved. See `outputs/tables/nested_spatial_model_results.csv` and `gp_spatial_residual_comparison.csv`.

**Planning exposure audit.** Using a modelled **WorldPop 2020**, not contemporary verified 2026 population, overlay yields about 98,028 estimated residents within the study units; approximately 20,687 in hottest-quintile hexes, 31,936 in low-accessibility quintile hexes, and 4,296 in their intersection. No independent verification of population, parcel ownership, service functionality, intervention cost or thermal benefit was performed. Consequently these numbers support *screening* only (`outputs/tables/population_exposure.csv`). The proposed Pareto/acceptability/uncertainty candidate gate still performs **worse than equal weighting** under matched perturbations (Jaccard 0.319 vs 0.506), so a novel superior selector cannot be claimed.

**Updated novelty and limitation.** Unlike a conventional fixed weighted index, the proposed reporting protocol explicitly disaggregates Pareto depth, preference acceptability and geographic prediction uncertainty; however, the controlled experiments **show no stability superiority over equal weights**, while direct same-sensor temporal transfer yields strongly negative R². The defensible contribution is a spatially and temporally *audited* urban-heat planning case study highlighting limitations of seemingly high in-period accuracy—not a demonstrated transferable spatial algorithm or causally effective intervention strategy. We do **not** consider it ready for a strong IEEE research submission. Evidence and frozen rubric scores are in `docs/RUBRIC_FINAL_EVIDENCE.md`.

### Updated conclusion and submission status

The repeated-grid experiment provides stronger internal evidence that projected coordinates improve thermal prediction under geographic withholding, despite persistent residual autocorrelation. The available independent Landsat scene metadata is a concrete path toward temporal transfer, but signed raster acquisition failed and **must not be counted as an external evaluation**. Since the decision gate underperforms equal weights and closely related SMAA methods already exist, the current work does not meet the preregistered 5/5 rubric or a serious full-paper acceptance gate. `docs/FINAL_5_OF_5_AUDIT.md` records unmet thresholds without inflating scores.

## X. Conclusion

The NKDA case shows how performance estimates and decision rankings change under geographic and preference uncertainty. The work contributes a reproducible screening workflow with negative findings explicitly reported, but the residual spatial structure and absent independent/external validation remain obstacles to a strong peer-reviewed submission. Our next priority is to improve spatial error modelling and independently verify the underlying geographic data.

## References

[1] D. R. Roberts et al., “Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure,” *Ecography*, vol. 40, pp. 913–929, 2017. DOI: 10.1111/ecog.02881.

[2] B. Mahata et al., “Spatiotemporal dynamics of land use/land cover (LULC) changes and its impact on land surface temperature: A case study in New Town Kolkata, eastern India,” *Regional Sustainability*, vol. 5, no. 2, 100138, 2024. DOI: 10.1016/j.regsus.2024.100138.
