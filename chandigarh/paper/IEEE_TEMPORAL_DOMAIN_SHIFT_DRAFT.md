# When Spatially Accurate Urban Heat Models Fail Across Dates: A Three-Acquisition Landsat-8 Audit in New Town Kolkata

**Research draft — not yet suitable for submission without further validation**

## Abstract

Urban land-surface-temperature (LST) models are frequently evaluated by spatial cross-validation within one image, potentially obscuring acquisition-level domain shift. We examine a 537-hexagon New Town Kolkata urban planning dataset with 1-km geographically blocked, buffered, shifted and nested model tests, then construct three independently acquired Landsat 8 Collection 2 Level-2 observations (24 March 2021, 1 April 2024, 22 March 2026). Under nested spatial validation, a coordinate-aware random forest attains RMSE 0.790°C but retains significant spatial residual autocorrelation (Moran's I 0.369, permutation p=.001). In 207 hexagons cloud-clear in all dates, leave-one-acquisition-out absolute LST models fail severely on 2024 (R² −21.67) and 2026 (R² −24.22). Training on source-period centered spatial thermal anomalies instead yields corresponding R² values 0.632 and 0.288; the 2021 holdout remains negative (−0.113). Target-period means are used only to define retrospective anomaly truth, never for model fitting or operational prediction. In observed hot-quintile maps, 37 hexagons are hot in at least two acquisitions and about 6,802 modelled WorldPop-2020 residents lie within them. Network-derived accessibility remains markedly unequal, but boundary registration (~640-m fitted-label RMS), unvalidated OSM completeness and noncontemporaneous population make these screening outputs exploratory. Our contribution is a documented failure and target-definition audit—not a novel thermal normalization algorithm or an operational absolute LST forecasting method.

## 1. Introduction and research questions

Satellite LST is acquisition- and weather-dependent. High within-scene performance does not demonstrate that absolute temperature can be predicted at a different acquisition. The questions are: (RQ1) how much spatial model skill survives stringent geographic withholding? (RQ2) does an absolute-temperature model transfer across matched Landsat-8 acquisitions? (RQ3) is relative intra-township spatial heat anomaly more stable and predictable across acquisitions? (RQ4) where do persistent observed hotspots coincide with modelled population and network accessibility deficits? We explicitly test negative hypotheses and distinguish prediction, descriptive retrospective thermal persistence and planning screening.

## 2. Prior work and positioning

Roberts et al. (2017) established the necessity of separation appropriate to spatially structured data. Hengl et al. (2018) investigated random forests with spatial predictors. Surface-UHI studies have already employed mean and standard-deviation normalization of satellite temperatures for cross-period comparison; a 2026 Chennai Landsat study explicitly uses standardized relative-SUHI values. SMAA-2 literature predates the former project's preference-acceptability component. We therefore do **not** claim to invent spatial cross-validation, coordinate features, date-centering, z-scoring, stochastic ranking, or the use of population and accessibility indicators. The intended contribution is a paired, reproducible case-study test of **which target is temporally defensible**, together with an explicit demonstration of cases where even anomaly transfer fails.

## 3. Data and validation

The primary 537 units are the pre-existing 250-m hexagon NKDA layer (EPSG:32643). Its digitized official-PDF-derived boundary is not independently registered: five label-based anchors yielded ~640 m RMS (~962 m maximum). The independently obtained thermal observations use Landsat 8 C2 L2 WRS 138/045 on 2021-03-24, 2024-04-01 and 2026-03-22. Identical band scaling, QA flags and hex aggregation were applied; a restrictive intersection gives **207 complete-case hexes**. Model features for temporal transfer are satellite NDVI, NDBI and MNDWI; no target-date LST is used as feature. Scene means, weather, cloud support and atmospheric corrections can differ; our three-date design cannot remove those confounders. Original WorldPop/GP/100m/pop 2020 and cached OSMnx walk-network service distances serve only descriptive planning overlays.

Within the original period, geographic GroupKFold uses 1/1.5/2-km blocks, buffers and 24 shifted-block origin/seed paired comparisons; nested RF hyperparameter selection uses only geographically separated inner training groups. Train-residual GP correction uses inner out-of-fold residuals, never withheld outer targets. Temporal experiments train RF on two of three dates with fixed hyperparameters and hold out the third date entirely. We evaluate absolute LST, period-mean-centered anomaly, period-z standardized anomaly and source-trained top-quintile classification. **Target-period means and standard deviations enter only the retrospective *evaluation labels* for anomalies, not any predictor.** Raw and anomaly RMSE are not directly comparable as forecasts of the same physical quantity.

## 4. Main results

### 4.1 Spatial predictability and remaining residual dependence

Original 1-km RF: RMSE 0.891°C, R² 0.511, Moran I 0.439 (p=.001). Coordinate RF: RMSE 0.820°C, Moran I 0.383. Nested RF plus coordinates: RMSE **0.790°C**, R² **0.616**, Moran I **0.369** (p=.001). Inner-crossfit Matern GP correction reduces Moran I to **0.304**, but RMSE worsens to **0.831°C**. The 24 shifted geographical evaluations support the direction of the coordinate-model improvement, not external-city independence. Residual spatial structure persists.

### 4.2 Cross-date failure and relative-target evaluation

| Test date; train on other two | Absolute RMSE °C | Absolute R² | Anomaly RMSE °C | Anomaly R² | z-score R² | Anomaly Spearman | Hot-quintile AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 1.641 | −0.181 | 1.593 | −0.113 | −0.099 | 0.578 | 0.554 |
| 2024 | 7.281 | −21.672 | 0.928 | **0.632** | 0.637 | 0.754 | 0.802 |
| 2026 | 7.373 | −24.220 | 1.239 | **0.288** | 0.304 | 0.621 | 0.767 |

The earlier single-date frozen 2021→2026 absolute model had RMSE 4.436°C, R² −8.128; 2026→2021 had RMSE 5.422°C, R² −11.887, and 2024→2026 RMSE 7.921°C, R² −28.105. These findings are not replaced by the two-source leave-one-date-out comparison. Source-spatially calibrated nominal 90% predictive intervals had only **1.45%** coverage on 2021→2026 and **0%** reverse, a severe failure of temporal calibration. Temporal normalization improves the *evaluated relative target* in 2024/2026 but cannot recover the unknown absolute date-level offset without an independent meteorological/reference estimate; 2021 is a negative transfer case.

For geographic dependence-aware uncertainty, 1,500 resamples of the 24 spatial blocks on **frozen predictions** yield anomaly R² conditional 95% ranges [−0.836, 0.288] in 2021, [0.468, 0.725] in 2024 and **[−0.003, 0.398] in 2026**. Thus only 2024 retains a clearly positive anomaly R² under this *conditional* bootstrap; no date-level or retraining inference is justified from three acquisitions.

### 4.3 Observed hotspot persistence and unequal service access

In 207 matched hexes, observed 2021/2024 top-quintile sets overlap by 18/42 (Jaccard 0.273), 2021/2026 by 21/42 (0.333), and 2024/2026 by 32/42 (0.615). **37 hexagons** enter the hottest quintile in at least two dates; six are 2026-only emergent hotspots. The cached WorldPop 2020 estimate for the 207 matched hexes is ~32,669 residents; persistent-hot hexes contain ~6,802, and the four persistent-hot/low-access hexes ~219. The complete canonical study hexes hold ~98,028 modelled 2020 people; 2.162% reach all five cached OSM service categories within 15 minutes at assumed 4.8-km/h walking speed. The original 537-hex accessibility score has nearest-eight Moran I **0.744**, p=.001, population-weighted Gini **0.345**, and LST-versus-accessibility-deficit Spearman **−0.287**. A transparent four-type screening typology additionally distinguishes persistent-hot/high-population/poor-access units from persistent-hot/high-population/better-access units, other poor-access units and lower-burden residual units; sensitivity of Type A counts to thresholds is reported rather than assumed. OSM features and source WorldPop raster were not independently reacquired here; planning numbers remain conditional proxies. The negative association demonstrates that environmental and service burdens are distinct descriptive dimensions, not causal substitutes.

### 4.4 Ranking-method negative result

The prior Pareto/rank-acceptability/interval gating method retained top-quintile status 0.886 under perturbations versus 0.942 for equal-weight selection; its Jaccard 0.319 was worse than equal weights 0.506. This is **not** the paper's novel method claim and remains a documented negative ablation. Accessibility is intentionally a downstream planning layer, not a proxy temperature predictor.

## 5. Discussion and threats to validity

The large acquisition-level mean changes and the relative-target benefit are consistent with the hypothesis (LST_{it}=\alpha_t+f(X_{it})+\epsilon_{it}\). But three scenes cannot isolate meteorological variability, cloud-selection bias, sensor residuals, land changes or atmospheric effects. No verified ERA5 variables were available; `data/acquisition_context.csv` explicitly marks them missing. Date fixed effects are unidentifiable for unseen future dates. Anomaly targets require knowing the actual period mean to construct observed labels; using the test mean in a predictor would be leakage. Source-trained hotspot AUROC 0.767/0.802 for 2026/2024 is encouraging but only moderate, with modest top-quintile Jaccard, and it fails substantially on 2021. Population vintage mismatch and boundary and OSM uncertainty especially preclude fine-grained resource allocation. This is a **single-township case study**, not universal transfer or evidence that interventions causally lower temperatures.

## 6. Conclusion

Stringent spatial CV reveals measurable within-period RF skill, yet significant spatially structured error. Independently acquired Landsat scenes expose catastrophic absolute transfer failure; period-centered relative heat patterns are markedly more transferable on two of three held-out years, but not all. Persistent observed heat can be overlaid with explicitly uncertain walking-network and population proxies for preliminary screening. A wider set of independent same-season acquisitions, acquisition-weather normalization, authoritative boundary registration, source-level OSM audits and a clean-environment replay are prerequisites for an IEEE-strength contribution. No new algorithmic novelty or temporal operational capability is claimed from three scenes.

## Reproducible materials

`external_case/temporal_landsat.py`, `external_case/evaluate_temporal.py`, `external_case/evaluate_three_periods.py`, `external_case/evaluate_relative_transfer.py`, `tools/merge_access_exposure.py`; machine-readable exact results are in `outputs/tables/`, with source-level warnings in `docs/BOUNDARY_VALIDATION.md`, `docs/OSM_DATA_VALIDATION.md`, `docs/TEMPORAL_DOMAIN_SHIFT.md` and `docs/MERGE_PROVENANCE.md`.

## Selected references

Roberts, D. R. et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography*, 40, 913–929. DOI: 10.1111/ecog.02881.

Hengl, T. et al. (2018). Random forest as a generic framework for predictive modeling of spatial and spatio-temporal variables. *PeerJ*, 6:e5518. DOI: 10.7717/peerj.5518.

*Examining urban heat island progression in Chennai: temporal insights from 2014 to 2024.* (2026). *Scientific Reports*. https://www.nature.com/articles/s41598-026-57905-4 (uses normalized relative thermal maps; prior art, not proof of our method's novelty).
