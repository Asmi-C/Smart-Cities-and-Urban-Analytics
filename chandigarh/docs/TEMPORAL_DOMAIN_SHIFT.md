# Thermal-domain shift and relative-anomaly evidence (3 independent Landsat 8 dates)

Executed `python external_case/evaluate_relative_transfer.py` on the **same 207 hexagons valid in all three acquisitions**. Train data comprise two dates; the third date's thermal observations are never used for training, hyperparameters, or predictions. All three use the same Landsat 8 Collection 2 Level-2 sensor family/thermal scaling and NDVI/NDBI/MNDWI covariates. The RF uses fixed hyperparameters (120 trees, min leaf 5, max features 0.8). Each source date's per-hex mean and standard deviation are computed from training observations and used for source-centering/source-standardization. Target date's mean/SD are used **only to define the target's observed relative anomaly for retrospective evaluation**; they are unavailable in unlabeled deployment.

| Held-out date | Absolute RMSE °C | Absolute R² | Mean-centered RMSE °C | Mean-centered R² | z-score R² | Anomaly Spearman | Hot-quintile AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 1.641 | −0.181 | 1.593 | −0.113 | −0.099 | 0.578 | 0.554 |
| 2024 | 7.281 | −21.672 | 0.928 | **0.632** | 0.637 | 0.754 | 0.802 |
| 2026 | 7.373 | −24.220 | 1.239 | **0.288** | 0.304 | 0.621 | 0.767 |

**Meaning and limits:** relative spatial anomaly is substantially more transferable than absolute degrees Celsius in 2024 and 2026 (R² changes from below −20 to above zero). The 2021 holdout still fails. The raw and centered RMSE are **not directly comparable operational errors**, because their targets have different definitions. The same-period actual target mean is *not* available at inference: absolute predictions **cannot** simply be recovered as anomaly prediction plus an unknown target mean. The finding supports a scientific separation of acquisition offset and spatial pattern, *not* an operational fix for absolute temporal prediction. There is no learned acquisition-meteorology model, no proof of causal offset magnitude, and no independent city.

**Conditional block-bootstrap uncertainty:** 1,500 resamples of 24 geographic blocks over frozen transfer predictions give anomaly R² 95% percentile ranges **[−0.836, 0.288]** (2021), **[0.468, 0.725]** (2024), and **[−0.003, 0.398]** (2026). The 2026 interval touches zero: a confidently positive transfer claim is unwarranted at this resampling unit. These are *not* date-level replication or retraining confidence intervals. See `outputs/tables/relative_transfer_spatial_bootstrap.csv`.

Observed top quintile hotspots by actual thermal measurements (k=42 per date): 37 hexagons are hot in at least two of the three dates. Six are hot in 2026 but not in 2021/2024; 20 were hot in 2021 only. Some of the remaining hexagons may be hot only in 2024 or in none. Those latter categories are conservatively grouped as "other/unstable", not falsely declared cool. See `outputs/tables/persistent_heat_hexes.csv` and `observed_hotspot_persistence.csv`.

On the common three-date clear subset, the cached 2020 WorldPop estimate is ~32,669 persons; **~6,802** reside in 37 persistent-hot hexagons and **~219** in the four persistent-hot *and* low-accessibility hexagons. These are population proxies only and cannot represent the entire NKDA population or a 2026 census. The accessibility layer is cached OSM, and boundary registration is uncertain (~640 m RMS fitted-anchor residual). These limitations preclude street/parcel-scale intervention prescriptions.

## Meteorological/context hypothesis

The difference of period means and the strong anomaly/absolute contrast are consistent with an acquisition-level thermal component in (LST_{it}=\alpha_t+f(X_{it})+\epsilon_{it}\). But neither the satellite preprocessing nor three dates identifies whether \(\alpha_t\) represents air temperature, humidity, wind, rainfall, atmospheric residual, phenology, viewing geometry or clear-pixel selection. No verified contemporaneous ERA5/ERA5-Land fields were acquired in this run, so `data/acquisition_context.csv` records those fields as missing rather than inventing weather. A date fixed effect can be estimated for *seen* training dates but gives no value for an unseen date; an oracle target-mean adjustment would leak thermal labels. An operational meteorology-conditioned model remains a future required experiment.

## Prior art / novelty restraint

Standardized and mean-centered thermal anomalies are already used in urban-LST research (e.g. the primary 2026 Chennai temporal-SUHI study discussed in the literature audit). Our new evidence is a three-date, fixed-sensor **failure analysis with an anomaly-vs-absolute contrast and geographically explicit planning consequence**, not invention of normalization. A transferable method advantage needs multiple independent scenes/cities, comparison to prior temporal baselines and calibrated uncertainty. The negative 2021 holdout and weak hotspot top-set Jaccard must not be hidden.
