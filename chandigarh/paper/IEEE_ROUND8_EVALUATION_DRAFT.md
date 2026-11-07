# Domain shift in satellite-derived urban heat: a multi-acquisition evaluation and spatial persistence audit

**Status:** completed 15-date experimental manuscript with new exploratory joint held-geography/date negative test; **not submission-ready under the four-reviewer gate**. The original six acquisitions are exploratory for method selection; the nine newly acquired dates supply a separately reported frozen-protocol test for *date-only transfer*. All absolute-temperature, unseen-geography and spatial-autocorrelation failures remain explicit.

## Abstract

Urban land-surface-temperature (LST) regressors can appear accurate within one satellite acquisition yet fail when transferred across acquisitions. We test source-only acquisition-state and location-persistent thermal models in New Town–Rajarhat on **15 Landsat-8 Collection-2 Level-2 acquisitions (eight calendar years)** screened before outcome evaluation. We distinguish retrospective mean-centered thermal anomalies from prospective absolute LST. Held-date spectral RF averages anomaly R² 0.450; unsupervised datewise feature-normalized RF reaches 0.602, a source-only spatial residual-correction hybrid 0.737, and simple historical per-site anomaly climatology 0.723. On **nine newly added acquisitions**, the hybrid improves over feature-normalized RF by mean ΔR² 0.141 (calendar-year-clustered sign-flip p=0.0078), but its ΔR² of 0.045 relative to historical climatology is not significant (p=0.344). The hybrid instead reduces residual Moran's I versus historical climatology by about 0.179 on the new dates (year-clustered p=0.0078), while **its own residuals remain significantly autocorrelated**. Historical hotspot-frequency predicts unseen-date high-heat status better than a spectral RF (15-date AUROC 0.902 versus 0.801). Leave-one-calendar-year-out hybrid anomaly R² averages 0.727; stricter chronological site-climatology transfer falls to 0.626. ERA5-Land retrospective weather plus spatial anomaly reduces absolute RMSE but mean absolute R² remains negative. The principal contribution is a reproducible spatial/temporal transfer and strong-baseline study showing which aspects of urban heat persist across domains—not a proven state-of-the-art forecasting algorithm.

## 1. Research question and prior work

Can models preserving site-specific thermal structure generalize to an unseen satellite acquisition without using its LST labels? Closest local work includes Kundu, Mukherjee and Mukhopadhyay (2026), DOI 10.1016/j.scs.2026.107246, which studies New Town/Rajarhat LST with tree-based explainable models. Its available abstract does not support a directly comparable validation protocol; no relative performance claim is made. Additional relevant precedents are pseudo-invariant Landsat LST normalization, CORAL target-covariate alignment, remote-sensing domain generalization with coordinate-aware alignment, multi-domain experts and conformal prediction under covariate shift (details in `paper/NOVELTY_GAP_ANALYSIS.md`). No claim of uniqueness is made based on inaccessible full-text methodological details.

## 2. Acquisition cohort and leakage protocol

The original six acquisitions were March 2019, April 2020, March 2021, April 2023, April 2024 and March 2026. Expansion used Landsat-8 WRS 138/045 C2L2 (no intersensor mixing), 15 February–15 May 2018–2026, scene cloud ≤25%, at most two sufficiently separated acquisitions/year, with the six original dates retained. Of 695 STAC catalog items, 16 were selected for download using metadata alone. **Fifteen passed the predefined ≥180 complete-case hex criterion** (189–311 hexes/date); 2025-05-06 was excluded after QA because only **28** hexes were valid, not because of model results. The final corpus consists of **15 independent acquisitions from eight calendar years** (2018, 2019, 2020, 2021, 2023, 2024, 2025, 2026). Exact per-scene inclusion and exclusions are in `data/acquisition_manifest_final.csv`. The 15-date study includes six originally inspected dates and nine addition-only confirmatory test domains. Adjacent scenes from one year are correlated, hence all significance claims include **calendar-year-clustered** inference. Only *source acquisitions* provide LST labels; unlabeled target spectra are available for transductive covariate alignment. Target date LST mean and quintiles are **retrospective scoring labels only**, never inference features.

## 3. Targets and models

Let `Y_it` be Landsat LST in place `i` at acquisition `t`; `X_it` three source-harmonized spectral indices. Relative anomaly is `A_it=Y_it−mean_j(Y_jt)`. This definition uses the actual test mean only to *score retrospective predictions*: prospective temperature level is not inferred by subtracting it.

- Raw spectral Random Forest `f(X)` trained to source-date anomalies.
- Unsupervised per-domain z-scored spectral Random Forest `f_z(z(X))`, using unlabeled target spectral distribution only.
- Cross-date source-only residual-bias correction `f_z(z(X_it)) + 0.5 mean_{u != t}(A_iu−f_{-u}(X_iu))`, where each source residual is generated by a model trained on other source acquisitions, with correction set to zero for unknown hexagons.
- Simple historical spatial climatology `mean_{u != t}(A_iu)` as a strong source-only baseline. This method requires previous observations at the same location and therefore does not represent generalization to newly developed or geographically unseen units.
- Source-date hotspot frequency, RF hotspot classifier, and spectral anomaly rank-based proxy; hot-quintile truth defined retrospectively per acquisition.
- Source-date meteorology-ridge estimate of the absolute acquisition state, optionally plus a historical spatial anomaly. ERA5 historical reanalysis is retrospective and not a tested real-time forecast.

All hyperparameters are frozen in `docs/FINAL_METHOD_PROTOCOL.md`. The newly proposed hybrid is a *candidate integration of established estimators*, not an asserted novel algorithm.

## 4. Completed 15-date anomaly-transfer and hotspot results

| Model | Mean leave-date-out anomaly R² | Mean anomaly RMSE (°C) | Mean residual Moran I |
|---|---:|---:|---:|
| Raw RF spectral | 0.450 | 1.141 | 0.422 |
| Unsupervised spectral z-score RF | 0.602 | 0.971 | 0.396 |
| Source-only cross-date residual correction + spectral z-score RF | **0.737** | **0.785** | **0.385** |
| Source-only historical anomaly climatology | 0.723 | 0.803 | 0.565 |

The hybrid improves anomaly R² versus spectral z-score RF in **15/15** held acquisitions (mean Δ+0.135, year-clustered bootstrap 95% CI [+0.114,+0.167], year-clustered exact sign flip p=0.0078). Crucially, on **the nine acquisition dates never inspected in prior research rounds**, its mean ΔR² versus z-scored RF is **+0.141**, with eight calendar-year clusters and p=0.0078. Against the *stronger* historical-site climatology, the hybrid's nine-addition mean ΔR² is **+0.045, p=0.344**, and all-date mean ΔR² is +0.013, p=0.883; neither supports an accuracy-superiority claim. However, relative to the historical climatology, the hybrid decreases mean residual Moran I by **0.179 on the new dates** (year-clustered p=0.0078, clustered 95% CI approximately [−0.256,−0.121]) while preserving similar RMSE. Moran remains significant at p≈0.001 by 999 permutations in each tested model/date; the effect is *partial reduction*, not successful residual whitening. Moran was a secondary endpoint; multiplicity and shared source folds remain qualifications.

Across 15 held-date tests, the historical site-hotspot-frequency baseline yields mean AUROC **0.902**, PR-AUC **0.726**, and Brier **0.094**, compared with RF classifier **0.801**, **0.500**, and **0.131**. On the nine newly acquired dates the mean AUROC gain is **+0.078**, with eight-year-cluster sign-flip p=0.0234. The new-only Brier improvement is not significant under year clusters (p=0.141). Ten-bin ECE across dates averages approximately 0.061 for source frequency and 0.062 for RF; classification probability calibration is not uniformly dominant. Historical site frequency cannot score unseen sites without an additional geographic model.

Source-date residual means exhibit repeated local structure: early/late date-group mean residual correlation **0.585** over 283 comparable hexes, with a 1-km geographic-block bootstrap 95% CI **[0.454,0.726]** over 30 blocks. Some residual biases correlate descriptively with cached built-distance and vegetation morphology; static source layers cannot be treated as historically validated covariates or causal explanations. Date-wise semivariograms, local cluster diagnostics, residual maps, and 999-permutation Moran checks are retained with the executable code.

Source-only conformal-style intervals are not uniformly valid under acquisition shift: pooled source-date 90% intervals achieve mean observed coverage **89.8%** but worst-date **70.7%**; worst-source-date calibration reaches mean **96.8%** and worst-date **82.8%** at nominal 90%, with wider intervals. This is an empirical audit, not a finite-sample coverage guarantee under unseen acquisition shift.

## 5. Meteorology and absolute LST

All 16 catalog-selected acquisitions received acquisition-time historical ERA5-Land data via a documented archive mirror, but unavailable wind, solar, pressure and precipitation-series fields are not invented. The 15 usable scenes have 14 source-date means for each leave-one-date-out Ridge fit. Absolute-transfer meteorology-only RMSE averages **2.345°C** (mean R² −1.204). Meteorology plus site climatology averages **1.803°C** (mean R² **−0.441**), compared with meteorology plus hybrid **1.813°C** (mean R² −0.452). Against the *non-meteorological* site-climatology intercept, weather reduces mean RMSE by **1.998°C** in 13/15 dates (eight-year-cluster p=0.0078). However **negative mean absolute R² persists**, source weather is retrospective reanalysis, and the effective number of meteorological training regimes remains only 14 per fold. This is progress in explaining acquisition-state bias, **not reliable prospective absolute-temperature forecasting**.

## 6. Geographical separation and planning

Round-7 independently withheld geographic blocks AND entire acquisitions. The 2021 mean-centered anomaly joint holdout returned negative R² (about −0.014), despite date-only improvements. The new stricter **leave-one-calendar-year-out** analysis (eight test years, 15 date-level scores) yields mean anomaly R² **0.727** for the hybrid, **0.709** for site climatology, and **0.596** for z-RF. Chronological forward-only testing across 11 acquisition dates gives mean anomaly R² **0.626** for site climatology versus **0.557** for z-RF; historical hotspot-frequency AUROC averages 0.860. On the fixed **180 hexagons valid in all 15 dates**, site-climatology mean anomaly R² is **0.745** versus z-RF **0.632**, reducing concern about variation in clear-mask sample composition. **Historical site climatology is not a model for genuinely unobserved geography**, and neither year/date tests establish new-city transfer.

Descriptive expanded 15-date observation profiles identify **46** hexagons hot in ≥half their observed dates with ≥7 valid observations, totaling approximately **7,993 WorldPop-2020 modelled residents**; **six** also meet the lowest-quintile cached-access criterion (~**288** modelled people). Their hotspot frequencies reflect the available clear-scene sample; they are not climatological probabilities or causal policy effects. The boundary has no survey-registered confirmation (five-anchor fit RMS ~640 m), the OSM source graph/POI audit and Euclidean/network pairing remain blocked, and exposure uses a 2020 population proxy. No parcel-level planning conclusion follows.

## 7. Contributions and limitations

Defensible contributions: (1) rigorous **15-acquisition** absolute-vs-relative transfer audit across eight calendar years and 180-hex common support; (2) nine-addition, source-only evidence that temporal residual corrections outperform a spectral RF; (3) stronger-baseline test showing the hybrid retains accuracy close to historical climatology while reducing residual Moran by approximately 0.18; (4) date/year/chronological splits, meteorology ablation, hotspot frequency and conformal failure analysis; (5) auditable quality-screening manifest and derived imagery. The work does **not** establish algorithmic priority over all methods, prospective absolute LST forecasting, spatially white residuals, true external-area generalization, or audited boundary/OSM/population planning outputs. Its current strongest identity is an **evaluation-methodology / domain-shift evidence paper**, with the hybrid as a carefully qualified secondary methodological component.

## Round-9 stricter geographic stress test and spatial-weight sensitivity

To investigate the potential for memorization, a new exploratory joint geographic/time test froze centroid-median quadrant blocks and held out **both all historical LST for the test quadrant and the entire test acquisition**. Only three quadrants possessed at least 15 complete target hexes; **40** eligible quadrant×date folds were scored. The strong same-site historical climatology was made comparable by spatial interpolation (fixed eight-neighbor inverse-distance weighting) from other-quadrant source observations, and the hybrid spatial residual estimate used identically restricted source information.

| Model | Held-quadrant/date anomaly R² | RMSE (°C) | Hotspot AUROC |
|---|---:|---:|---:|
| Normalized spectral RF | **0.080** | **1.251** | 0.742 |
| Source-only residual-corrected RF | 0.027 | 1.284 | **0.745** |
| Historical-site climatology spatially interpolated | −0.418 | 1.708 | 0.553 |

Relative to the strongest new-site baseline, normalized spectral RF, the proposed hybrid's R² **decreases by 0.053** across paired folds (eight-year clustered exact sign-flip p=0.0078; 95% year-bootstrap CI [−0.077,−0.043]) and RMSE increases by 0.032°C. It does outperform the interpolated historical-site climatology, but that is not the strongest benchmark. Thus the original source-only correction **does not solve** geographic extrapolation; its date-only gains are primarily at previously observed locations. Because all fifteen acquisition domains were previously studied, these joint tests are exploratory design stress tests, not untouched confirmation.

For residual-spatial dependence, a new 15-date 199-permutation sensitivity check over kNN4/8/12 and a 550-m distance band yields hybrid mean Moran I **0.447, 0.385, 0.339, 0.331** respectively, versus normalized spectral RF **0.463, 0.396, 0.339, 0.331**. All residual fields are significantly dependent at p=0.005 (permutation resolution). The prior improvement of about 0.179 relative to site-climatology residuals is real for that comparator but **cannot be generalized** into substantial spatial whitening against the normalized RF baseline. Both scientific limitations are retained in the final reviewer-gated assessment `docs/REVIEWER_GATE_FINAL.md`.

Authoritative NKDA materials corroborate approximately 29.34 sq km / 24 mouzas and a 2018 published zoning map but no coordinate-authenticated study-boundary polygon. Translating the existing reconstructed polygon by hypothetical 640 m in eight directions retains 351–408 original sample hexes versus the unshifted 537, showing material support sensitivity without identifying the true boundary. OSM source graph/POI validation and independent population sensitivity remain unavailable; detailed evidence is in `docs/PLANNING_ROUND9_ACCESS_AUDIT.md`. There is no defensible parcel-level intervention conclusion.

## Replication files

- Selection, quality and conditions: `external_case/discover_expanded_dates.py`, `external_case/finalize_acquisitions.py`, `data/acquisition_manifest_final.csv`, `data/acquisition_context_final.csv`.
- Date-transfer models: `external_case/evaluate_domain_generalization.py`, `outputs/tables/date_level_method_comparison.csv`, `persistent_hotspot_prediction.csv`.
- Calibration: `outputs/tables/date_conformal_coverage.csv`.
- Stable residual diagnostics and map: `external_case/residual_persistence_audit.py`, `outputs/tables/residual_persistence.csv`, `outputs/figures/persistent_residual_bias.png`.
- Meteorology ablation: `external_case/evaluate_weather_expanded.py`, `outputs/tables/meteorology_ablation.csv`.
- Addition-only and strongest-baseline tests: `outputs/tables/addition_only_confirmatory_tests.csv`, `outputs/tables/hybrid_vs_climatology_pareto.csv`.
- Independent-year and chronology tests: `outputs/tables/leave_one_year_out.csv`, `outputs/tables/chronological_forward_transfer.csv`.
- Permutation Moran, hotspot calibration, frontier and expanded exposure: `outputs/tables/round8_residual_Moran_permutations.csv`, `hotspot_calibration_ECE.csv`, `model_selection_frontier.csv`, `expanded_planning_exposure.csv`.
- Joint geographic/date evaluation and year-cluster paired inference: `external_case/evaluate_unseen_sites_dates.py`, `tools/round9_unseen_site_inference.py`, `outputs/tables/unseen_site_unseen_date.csv`, `unseen_site_inference.csv`.
- Spatial weight sensitivity, scene QA and boundary scenarios: `tools/round9_spatial_weight_sensitivity.py`, `round9_scene_quality_audit.py`, `boundary_perturbation.py`; output tables in `outputs/tables/`.

**Manuscript status:** evaluated as an evidence-focused *domain-shift / methodology-validation* paper. Critically, joint geography/date tests show that the spatial correction's date-transfer advantage does not survive unseen-site extrapolation versus normalized RF. The empirical advantages of relative monitoring do not justify a 5/5 novelty rating or submission readiness under all four reviewer gates.
