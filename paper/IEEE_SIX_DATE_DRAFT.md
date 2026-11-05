# Within-Scene Skill Does Not Imply Cross-Acquisition Skill: A Six-Date Landsat-8 Domain-Shift Audit for New Town Kolkata

*Research manuscript v7 — draft, not yet an IEEE-ready submission*

## Abstract

Spatially accurate land-surface-temperature (LST) prediction may fail when the satellite acquisition changes. We examine New Town–Rajarhat, Kolkata using an existing 537-hexagon urban spatial dataset and six independently acquired Landsat 8 Collection 2 Level-2 observations from March–April of 2019, 2020, 2021, 2023, 2024 and 2026. A nested geographically blocked coordinate-aware random forest obtains within-period RMSE 0.790°C on the original dataset yet leaves residual Moran's I 0.369 (p=.001). In six leave-one-date-out tests of source-trained spectral models, absolute-LST R² is negative for every unseen date (−0.189 to −22.896), while source-date-mean-centered *relative* anomaly R² is positive on all six (0.067 to 0.654). Under concurrent 1-km geographic and temporal withholding, five of six relative results remain positive; 2021 becomes −0.014. Unsupervised spectral feature standardization increases mean held-date anomaly R² from 0.445 to 0.578, but its paired six-date advantage is not significant (exact sign-flip p=.438). A three-weather-variable ridge model fitted to the other five dates' observed means improves absolute RMSE on four of six dates, including 2026 from 7.177 to 4.977°C, yet the mean improvement lacks date-level statistical support (p=.188) and 2026 absolute R² remains −10.489. Among 207 hexes valid in all six acquisitions, 42 are in the hottest quintile during at least three dates, representing approximately 8,546 modelled WorldPop-2020 residents. The study is a negative-and-relative-target transfer audit; established anomaly normalization and CORAL are baselines, not proposed novel algorithms. Boundary registration (~640-m fitted-anchor RMS), unresolved residual dependence and unverified OSM/population sources preclude fine-scale intervention claims.

## 1. Introduction

Urban heat prediction is often evaluated by randomly splitting spatial pixels or cells from one satellite scene. Such evaluation mixes geographic autocorrelation with sensor/acquisition context and does not establish prediction at an unseen acquisition date. Absolute LST is influenced by meteorology and atmospheric conditions; its observed spatial *ordering* may be more persistent than its absolute level. The motivating questions are: (RQ1) how does geographically withheld LST skill compare with conventional cross-validation? (RQ2) do absolute and relative thermal targets transfer across multiple independent same-sensor dates? (RQ3) does unlabeled-spectral alignment or an independently observed date-weather baseline improve transfer? (RQ4) which observed hotspots persist across six dates, and how reliably can their population/service exposure be screened?

## 2. Prior work and critical local comparator

Roberts et al. (2017) provide the foundational rationale for spatial/temporal blocked validation. Hengl et al. (2018) establish coordinate/spatial random-forest prediction; Sun, Feng and Saenko (2016) introduced CORAL for unsupervised covariance alignment. Mean/z-normalized surface thermal anomalies also have established urban-heat precedents, including a 2026 Chennai Landsat temporal study. Thus neither normalization, spatial RF, cross-validation nor CORAL is claimed as algorithmic novelty.

The strongest geographically close competitor is **Kundu, Mukherjee and Mukhopadhyay (2026)**, *Sustainable Cities and Society*, vol. 140, article 107246, DOI `10.1016/j.scs.2026.107246`. Their New Town–Rajarhat seasonal explainable ML work examines LightGBM/CatBoost, SHAP, road proximity, bareness, moisture, vegetation, morphology and population, reporting R² up to **0.99 in summer** and **0.96 in winter**. Their accessible abstract does not establish a matched spatial- and acquisition-held-out test. Our scores **cannot** be compared directly because of different geographic extents, dates, targets, variables and evaluation. We do not claim that their paper is invalid. This close competitor **precludes novelty claims based merely on integrating local thermal indices and explainable ML**. See `CLOSEST_COMPETITOR_MATRIX.csv` for comparisons and bibliographic corrections.

## 3. Data, provenance and bias risks

The canonical NKDA hex layer contains 537 ~250-m units in EPSG:32645. Its official-sheet-derived digitized boundary has approximately **640 m RMS** registration residual against five *place-label* anchors, not independent surveyed cadastral points. Under deliberate 640-m translations in eight compass directions, only **351–408 original hex centroids** remain inside. This diagnoses sensitivity but does not identify the true boundary or measure newly included geography.

We queried all 683 Landsat catalog items returned for the predefined bbox, multi-year March–April date search. Inclusion required Landsat-8 Collection 2 Level-2 Tier-1, WRS 138/045, 15 March–15 April and scene cloud fraction at most 15%; one lowest-cloud qualifying scene per year was retained, with three pre-existing comparison scenes kept. Six years qualified: **2019-03-19, 2020-04-06, 2021-03-24, 2023-04-15, 2024-04-01, 2026-03-22**. Scene data were downloaded over verified HTTPS, SHA256 checksummed, USGS scaled and QA-cloud-masked; the same projected hex aggregation and spectral-index definitions were used. Valid thermal/spectral sample counts are **309, 273, 298, 283, 255, 207**, respectively. Their exact intersection is 207 hexagons. See `data/thermal_acquisition_manifest.csv` (selected and rejected candidates) and `external_case/temporal_landsat.py`/`fetch_selected_dates.py`.

Acquisition timestamps (~04:31 UTC) were paired with the most recent **04:00 UTC** historical ERA5-Land hourly reanalysis returned by the Open-Meteo archive mirror at ~22.58°N, 88.48°E. Fields include 2-m temperature, dew point and upper-layer soil moisture, plus other retrieved context/units. The preceding 24-hour rainfall uses no later hour. Some mirror fields are missing and never imputed. This is coarse **retrospective reanalysis**, not verified local surface-station measurements or an operational meteorological forecast. Five other dates—only five training time units—are used for every held-date weather-baseline fit.

## 4. Models and leakage restrictions

For the original 537-hex dataset, compare random and geographic/grouped RF, 1/1.5/2-km and buffered geographic folds, 24 shifted block-origin/seed repeats, nested inner-geographic hyperparameter selection and crossfit residual-GP alternatives. A held-out target never contributes its thermal value to a correction feature or fit. Report out-of-fold RMSE, R² and 999-permutation Moran I.

For each independent acquisition test, combine the other **five dates** for source training. RF uses 120 trees/minimum leaf 5/max features .8 and **only** NDVI/NDBI/MNDWI input. Evaluate absolute LST and period mean-centered, median-centered, z-standardized, within-date percentile and hot-quintile targets. Source targets are normalized by **source-date** moments. Target-date moments appear **only in retrospective evaluation labels**, not in model inputs, alignment, weather predictions or tuning. We therefore never advertise an anomaly prediction as an absolute thermal forecast. A stricter experiment also excludes *all source-date examples from the held-out 1-km spatial block* and aggregates five geographic folds per target date. We report rank, Jaccard, AUROC, PR-AUC and residual Moran alongside error.

Feature-domain adaptation uses source and **unlabeled target spectral covariates only** for source/target per-date z-standardization or CORAL; HGB on the same spectral variables is an additional fixed baseline. No target-date LST is used. A separate date-state model predicts each unseen date's global LST mean from **only five previously observed date means and retrospective reanalysis temperature, dew point, and soil moisture** via fixed Ridge(α=10) and combines that predicted mean with a source-trained spatial anomaly RF. A constant-source-mean alternative and raw absolute RF provide controls. This has inherently high date-level variance and cannot support reliable inference from six dates.

## 5. Results

### 5.1 Within-period spatial validation

Original 1-km block RF: RMSE 0.891°C, R² 0.511, residual Moran I 0.439 (p=.001). Coordinate RF: 0.820°C, R² 0.586, Moran I 0.383. Nested coordinate RF: **0.790°C**, R² **0.616**, residual I **0.369** (p=.001). Crossfit Matern GP residual correction lowers I to **0.304** but increases RMSE to **0.831°C**. All residual structure remains significant. The 24 shifted spatial comparisons favour coordinates internally; repeated repartitions of one township are not independent study sites.

### 5.2 Six-date temporal transfer

| Held date | Absolute R² | Mean anomaly R² | Anomaly Spearman | Hot quintile AUROC | Anomaly Moran I |
|---|---:|---:|---:|---:|---:|
| 2019-03-19 | −1.876 | 0.301 | 0.729 | 0.763 | 0.289 |
| 2020-04-06 | −3.676 | 0.647 | 0.797 | 0.777 | 0.569 |
| 2021-03-24 | −0.189 | 0.067 | 0.724 | 0.697 | 0.429 |
| 2023-04-15 | −2.881 | 0.627 | 0.772 | 0.800 | 0.441 |
| 2024-04-01 | −0.840 | 0.654 | 0.767 | 0.762 | 0.333 |
| 2026-03-22 | −22.896 | 0.372 | 0.593 | 0.753 | 0.265 |

All anomaly residual Moran values remain significant (permutation p=.002). Under **combined spatial-and-temporal** withholding, anomaly R² values by year are **0.304, 0.626, −0.014, 0.614, 0.651, 0.361**; every absolute R² is still negative. Consequently a simplistic "six positive years" generalization claim does **not** survive geographical separation: **2021 is a negative holdout** under the stricter test.

### 5.3 Unlabeled adaptation and weather baseline

Mean anomaly R² across six dates: raw RF **0.445**, HGB **0.451**, target-unlabeled spectral standardization **0.578**, CORAL **0.576**. The paired standardization-minus-RF difference averages +0.133 R² but is mixed across dates (bootstrap date-resampling 95% interval **[−0.029, 0.338]**, exact six-date sign-flip p=.438). No adaptation superiority is established. Standardization/CORAL often worsens **absolute** target scores.

Mean absolute RMSE reduction from three-weather ridge date-baseline plus anomaly versus raw absolute RF is **0.919°C** (six-date resampled bootstrap 95% interval **[−0.004, 1.831]°C**; exact sign-flip p=.188). Absolute RMSE decreases on four of six dates, notably **7.177→4.977°C for 2026**, but worsens on 2020 and 2021; 2026 absolute R² is still **−10.489**. With five training dates, these are hypothesis-generating results, not reliable deployment.

### 5.4 Persistent hotspots and planning interpretation

On the exact **207 hexes clear in all six dates**, independent date-specific hottest-quintile sets identify **42** units hot in ≥3/6 dates (~**8,546** WorldPop-2020 modelled residents) and 33 hot in ≥4/6 (~**6,821**). Four ≥3/6 hotspots also have poor cached network access (~219 modelled residents). Five units were hot only in 2026 (~722 modelled residents). These are *observed historical persistence*, not successful predicted interventions.

Across all original 537 hexes, cached OSMnx multi-source Dijkstra nearest-service distances imply 2.162% of modelled 2020 residents can access all five categories in 15 min (assumed 4.8 km/h), accessibility Moran I ~0.744 (p=.001), population-weighted Gini ~0.345. A Euclidean-vs-network paired misclassification estimate **cannot** be computed without underlying POI geometries and the network graph, absent from available archives. These exposure and topology claims are limited by the unvalidated OSM source, dated modelled population and highly uncertain boundary registration; no parcel- or street-level intervention list is validated.

## 6. Discussion

The consistent failure of raw absolute LST under calendar-date withholding and usually positive relative-anomaly performance supports the operationally important distinction between *absolute thermal state* and *intra-urban thermal contrast*. However, the latter target requires target-date mean LST to define its **true** evaluation labels; this mean cannot be substituted into an operational predictor without independent measured weather/rural reference or legitimate observations. Reanalysis baseline modelling is a first nonleaking attempt but is empirically unreliable across six dates. Our data cannot establish a causal effect of any road, vegetation or mitigation intervention. The local Kundu et al. (2026) competitor already integrates morphology/road predictors and explainable ML, making novelty in multi-modal integration untenable. A fully new method claim would require demonstrably robust cross-acquisition performance over matched baselines and a formal distinct algorithm with strong date-level confidence.

## 7. Conclusion and submission assessment

This work establishes an empirically reproducible, geographically audited **failure mode** for urban LST absolute transfer and identifies relative thermal anomaly as a more stable—but still spatially dependent and imperfect—retrospective prediction target. It extends from three to six actual same-platform acquisitions and explicitly attempts weather-conditioned reconstruction. Strong IEEE full-paper readiness is **not established**: date-level n=6, uncertain geographic boundary, missing independent POI validation, mixed adaptation results and significant residual Moran remain material. The defensible contribution is a careful negative/relative-target benchmark and planning-data integrity audit, rather than an original high-performing algorithm or operational urban cooling recommendation.

## Reproduction and evidence index

`run_round7_research.py` replays cached-input experiments; `--acquire` rechecks deterministic STAC rules, source downloads and weather. Exact tables include `leave_one_date_out.csv`, `spatiotemporal_holdout.csv`, `unsupervised_domain_alignment.csv`, `meteorology_aware_transfer.csv`, `six_date_persistent_exposure.csv`, `boundary_translation_sensitivity.csv`, `euclidean_vs_network_access.csv`; source limitations in `docs/ROUND7_EVIDENCE.md`, `docs/TEAMMATE_CONCEPTUAL_MERGE_AUDIT.md`, `docs/ACCESSIBILITY_VALIDATION.md`.

## References (selected, verified where possible)

Kundu, A., Mukherjee, S., and Mukhopadhyay, S. (2026). Seasonal drivers of urban heat and their implications for sustainable spatial planning: A case study from a rapidly developing city of eastern India. *Sustainable Cities and Society*, 140, 107246. DOI: 10.1016/j.scs.2026.107246.

Roberts, D. R. et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography* 40:913–929. DOI: 10.1111/ecog.02881.

Hengl, T. et al. (2018). Random forest as a generic framework for predictive modeling of spatial and spatio-temporal variables. *PeerJ* 6:e5518. DOI: 10.7717/peerj.5518.

Sun, B., Feng, J., and Saenko, K. (2016). Return of Frustratingly Easy Domain Adaptation. *AAAI Conference on Artificial Intelligence*.

Boeing, G. (2017). OSMnx: New methods for acquiring, constructing, analyzing, and visualizing complex street networks. *Computers, Environment and Urban Systems*.

Gupta, N., and Aithal, B. H. (2024). Urban land surface temperature forecasting: a data-driven approach using regression and neural network models. *Geocarto International*. DOI: 10.1080/10106049.2023.2299145.
