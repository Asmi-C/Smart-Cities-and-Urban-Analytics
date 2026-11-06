# Round-7 research evidence: acquisition-domain shift, meteorology and competitors

## Fixed acquisition selection

`external_case/discover_dates.py` scanned all 683 returned Planetary Computer STAC items in the date/bbox query and applied **Landsat-8 C2 L2 / WRS 138045 / Tier-1 / 15 March–15 April / scene cloud ≤15%**, keeping the lowest-cloud qualifying scene per year and retaining the three previous independent dates. Six preselected years (2019, 2020, 2021, 2023, 2024, 2026) passed; 2022/2025 had no qualifying item under this query. Complete accepted/rejected inventory and reasons: `data/thermal_acquisition_manifest.csv`. The six scene items were downloaded with verified HTTPS, cached, QA-masked, radiometrically scaled and aggregated using **the same canonical hex polygons**. Valid sample counts vary by acquisition (207–309); the six-date experiment does **not** silently restrict to only the original 207 complete cases. Consequently numeric comparisons with Round 6's fixed-207 three-date subset answer a *related but different* estimand. Earlier results remain intact.

## True leave-one-date-out, no target thermal adaptation

Five source periods train a fixed 120-tree RF using NDVI/NDBI/MNDWI and the sixth date is entirely held out. A period-centered anomaly model trains on each source's centered values and is evaluated against the held period's centered *observed truth*. **The held date's mean is not used in predictions or feature transforms.** Source date means may be estimated from source training observations; the held date mean is unknown at deployment. Domain-normalized labels do **not** constitute operational absolute forecasts.

| Held date | Valid hexes | Absolute R² | Anomaly R² | Anomaly Spearman | Hot-quintile AUROC | Anomaly residual Moran I |
|---|---:|---:|---:|---:|---:|---:|
| 2019-03-19 | 309 | −1.876 | 0.301 | 0.729 | 0.763 | 0.289 |
| 2020-04-06 | 273 | −3.676 | 0.647 | 0.797 | 0.777 | 0.569 |
| 2021-03-24 | 298 | −0.189 | 0.067 | 0.724 | 0.697 | 0.429 |
| 2023-04-15 | 283 | −2.881 | 0.627 | 0.772 | 0.800 | 0.441 |
| 2024-04-01 | 255 | −0.840 | 0.654 | 0.767 | 0.762 | 0.333 |
| 2026-03-22 | 207 | −22.896 | 0.372 | 0.593 | 0.753 | 0.265 |

All six relative-model residual Moran statistics are **significant (permutation p=.002)**. Better temporal target transfer **does not resolve spatial dependence**.

**Joint geographic + temporal holdout:** We further trained on the five other acquisition dates while excluding every 1-km geographic block assigned to the held-out test fold **from all source-date training observations**. The six held-out anomaly R² values were **0.304, 0.626, −0.014, 0.614, 0.651 and 0.361** in chronological order. Raw absolute R² remains negative in all six folds, including **−23.066** for held-out 2026. The 2021 anomaly negative case returns under geographic exclusion; simple leave-one-date-out scores should therefore not be misrepresented as geographic generalization. Exact table: `outputs/tables/spatiotemporal_holdout.csv`.

**Observed six-date hotspot persistence:** All six acquisitions happen to share **207** complete-case hexes (other dates each have more valid individual hexes). Within that fixed 207-hex subset, 42 units were in the hottest quintile in at least 3 of 6 independent acquisitions, containing **~8,546 WorldPop-2020 modelled residents**. Of these, 33 hexes (~6,821 modelled residents) were hot in at least 4 dates, and 4 persistent-hot units (~219 residents) also have low cached access scores. Five are hot only in 2026 (~722 modelled residents). These are descriptive **observed**, not predicted, hotspots; dates are selectively clear and not independent annual climatologies. `outputs/tables/six_date_hotspot_persistence.csv` and `six_date_persistent_exposure.csv`.

## Unsupervised spectral-domain alignment (6 date-level units)

We compared unadapted RF, target-unlabeled spectral standardization and classic CORAL feature covariance alignment (Sun, Feng & Saenko, AAAI 2016), as well as an HGB spectral baseline. Mean R² across six held dates for the *relative anomaly target* was **0.445** (raw RF), **0.578** (unlabeled per-date feature standardization), **0.576** (CORAL) and **0.451** (HGB). Differences change sign by year. The mean paired standardization-minus-raw date-level R² difference is **+0.133** but 10,000 resampled-date bootstrap percentile 95% interval **[−0.029, 0.338]**, exact six-date sign-flip p = **0.438**. No statistically established superiority; no novel adaptation algorithm is claimed. For the absolute target, feature alignment is often harmful.

## Meteorological context and date-baseline model

Independent Landsat timestamp metadata was paired with **hourly ERA5-Land reanalysis returned by Open-Meteo's documented archive mirror** (22.58N, 88.48E). The latest weather hour **at or before** each overpass (usually 04:00 UTC vs 04:31 UTC acquisition) and preceding 24-hour rainfall were requested. Retrieved temperature (°C), dew point (°C), relative humidity, near-surface soil moisture (units in CSV) and other source fields are in `data/acquisition_context.csv`; some requested variables are unavailable in ERA5-Land mirror and intentionally remain blank. **Reanalysis is retrospectively generated, not contemporaneous actual weather-forecast availability.** Only temperature, dew point and soil moisture (complete fields) entered the fixed ridge(α=10) date-baseline estimator trained on **five date-level means**; it was added to a separately trained relative RF predictor. No held-date Landsat target values or date mean were used in the estimate.

| Test date | Raw absolute RF RMSE °C | Three-weather ridge baseline + anomaly RMSE °C |
|---|---:|---:|
| 2019-03-19 | 2.672 | **1.107** |
| 2020-04-06 | **5.113** | 5.381 |
| 2021-03-24 | **1.735** | 2.374 |
| 2023-04-15 | 3.294 | **0.970** |
| 2024-04-01 | 2.148 | **1.820** |
| 2026-03-22 | 7.177 | **4.977** |

Average paired RMSE reduction **0.919°C**; date-level 95% resampled bootstrap interval **[−0.004, 1.831]°C**, exact sign-flip p=**0.188**. Hence the weather model is directionally promising on four dates but **not convincingly superior** with six independent acquisitions. It still fails in 2026 (R² **−10.489**) and in 2020. All weather fields are coarse reanalysis for one point, not per-hex microclimate or local observed station measurements.

## Closest competitor and boundary caveat

Kundu, Mukherjee & Mukhopadhyay (2026), *Sustainable Cities and Society* 140:107246, DOI `10.1016/j.scs.2026.107246`, examine **the same New Town–Rajarhat region**, seasonal summer/winter Landsat LST with LightGBM/CatBoost, SHAP, road proximity and bare-soil/vegetation/moisture drivers; abstract reports R² up to **0.99 summer, 0.96 winter**. Its accessible abstract does not establish a matched geographical heldout or leave-one-date-out test. The R² scores cannot be directly compared with ours (different data, target, area/support, model and validation); no invalidity of their study is asserted. The paper's existence significantly weakens any claim that spectral/morphology/explainability integration is new for New Town.

The original official-PDF-derived NKDA boundary has fitted-label registration RMS ~640 m. `tools/boundary_perturbation.py` translates the boundary in 8 directions at 0/250/640/962 m **without inventing source measurements in newly included geography**. At 640 m, only 351–408 existing original 537 centroid locations remain, depending on direction; this is *exposure to registration sensitivity*, not an estimate of true edge error or corrected population. The lack of an independent survey-registered statutory boundary prevents legitimate fine-scale planning claims. HIDCO public layouts are useful comparison documents but do not supply a verified machine-readable correction in this run.

## Blockers and scope

The requested Euclidean-vs-network paired experiment is **not executed** because the original POI coordinates and full OSM graph are absent from both ZIPs and the canonical GeoPackage; nearest-network distances alone cannot identify Euclidean distances. We report this blocker in `docs/ACCESSIBILITY_VALIDATION.md`, not a fictional circuity ratio. The 2020 WorldPop and old OSM overlays remain conditional. No causal intervention benefit, validated boundary fix, universally reliable hotspot model or superiority over the 2026 close competitor is claimed.
