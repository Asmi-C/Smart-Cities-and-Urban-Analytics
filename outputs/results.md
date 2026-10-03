# Results — New Town Kolkata smart liveability analysis

Study area: fallback bounding box, 77.4 km², 1442 hexagons (250 m).
Training labels: Dynamic World pixels with probability ≥ 0.6; accuracy is measured against held-out
Dynamic World labels (30%), with ESA WorldCover 2021 as an independent check.

## 7.1 Land cover change (RQ1)

| Class | 2016 area (km²) | 2021 area (km²) | 2026 area (km²) | Change 2016–2026 (%) |
| --- | --- | --- | --- | --- |
| Water / wetland | 9.51 | 7.96 | 8.88 | -6.63 |
| Vegetation | 20.14 | 17.24 | 14.15 | -29.78 |
| Cropland | 0.00 | 0.00 | 0.00 |  |
| Built-up | 47.74 | 52.23 | 54.41 | 13.97 |
| Bare / fallow | 0.04 | 0.00 | 0.00 | -100.00 |

Built-up compound annual growth 2016–2026: 1.32% per year.

**Accuracy**

| Year | Imagery | Overall accuracy (%) | Kappa | Agreement with Dynamic World (%) | Agreement with ESA WorldCover 2021 (%) |
| --- | --- | --- | --- | --- | --- |
| 2016 | 4 Sentinel-2 scenes, 2015-11-01 to 2016-03-01 (L1C top-of-atmosphere) | 99.44 | 0.99 | 42.51 |  |
| 2021 | 41 Sentinel-2 scenes, 2020-11-01 to 2021-03-01 (L2A surface reflectance) | 100.00 | 1.00 | 70.32 | 56.45 |
| 2026 | 53 Sentinel-2 scenes, 2025-11-01 to 2026-03-01 (L2A surface reflectance) | 99.17 | 0.99 | 72.55 |  |

**Per-class F1**

| Year | Water / wetland | Vegetation | Cropland | Built-up | Bare / fallow |
| --- | --- | --- | --- | --- | --- |
| 2016 | 1.00 | 1.00 | 0.00 | 0.99 | 0.86 |
| 2021 | 1.00 | 1.00 | 0.00 | 1.00 |  |
| 2026 | 1.00 | 0.99 | 0.00 | 0.99 |  |

**Transition matrix 2016 → 2026 (km²; rows = 2016, columns = 2026)**

| From / to | Water / wetland (2026) | Vegetation (2026) | Cropland (2026) | Built-up (2026) | Bare / fallow (2026) |
| --- | --- | --- | --- | --- | --- |
| Water / wetland (2016) | 7.37 | 0.88 | 0.00 | 1.26 | 0.00 |
| Vegetation (2016) | 0.29 | 10.02 | 0.00 | 9.83 | 0.00 |
| Cropland (2016) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| Built-up (2016) | 1.22 | 3.24 | 0.00 | 43.28 | 0.00 |
| Bare / fallow (2016) | 0.00 | 0.00 | 0.00 | 0.04 | 0.00 |

## 7.2 Heat island (RQ2)

| Statistic | Value |
| --- | --- |
| Mean pre-monsoon LST, built-up, 2026 (°C) | 35.194 |
| Mean pre-monsoon LST, vegetated reference, 2026 (°C) | 33.602 |
| Surface UHI intensity, 2026 (°C) | 1.592 |
| Pearson r, LST vs NDVI (hexes) | 0.062 |
| Pearson r, LST vs NDBI (hexes) | 0.760 |
| OLS R², LST ~ NDVI + NDBI + MNDWI | 0.706 |
| Moran's I of OLS residuals | 0.639 |
| Pseudo p-value of residual Moran's I | 0.001 |

**Surface UHI by year**

| Year | Landsat scenes | Period | Mean LST, built-up (°C) | Mean LST, vegetated reference (°C) | Surface UHI intensity (°C) |
| --- | --- | --- | --- | --- | --- |
| 2016 | 6 | 2016-03-01 to 2016-06-01 | 42.96 | 40.83 | 2.13 |
| 2021 | 7 | 2021-03-01 to 2021-06-01 | 38.61 | 36.72 | 1.89 |
| 2026 | 15 | 2026-03-01 to 2026-06-01 | 35.19 | 33.60 | 1.59 |

OLS coefficients: const = 34.26 (p = 0.000), NDVI = -21.91 (p = 0.000), NDBI = -16.38 (p = 0.000), MNDWI = -22.51 (p = 0.000).

## 7.3 Accessibility (RQ3)

Walking threshold: 15 min at 4.8 km/h = 1200 m network distance.

| Service category | OSM features in area + buffer | Median walk distance (m) | Population within 15 min (%) |
| --- | --- | --- | --- |
| School | 51 | 1,849.3 | 39.5 |
| Health | 72 | 1,738.5 | 64.2 |
| Park / green space | 331 | 904.8 | 82.8 |
| Public transit | 133 | 1,492.2 | 67.0 |
| Daily shopping | 45 | 2,057.1 | 36.8 |
| All five categories |  |  | 18.8 |

**By zone (distance-from-centroid terciles)**

| Zone | Hexes | Mean 15-min score | Median 15-min score |
| --- | --- | --- | --- |
| Core | 481 | 0.33 | 0.20 |
| Edge | 481 | 0.37 | 0.40 |
| Middle | 480 | 0.36 | 0.40 |

Kruskal-Wallis H = 4.21, p = 0.1220.

## 7.4 Spatial clustering (RQ4)

| Variable | Global Moran's I | Pseudo p-value | High-High hexes | Low-Low hexes |
| --- | --- | --- | --- | --- |
| LST | 0.812 | 0.001 | 123 | 119 |
| 15-minute score | 0.835 | 0.001 | 274 | 357 |
| Smart Liveability Index | 0.840 | 0.001 | 317 | 341 |

Low-Low SLI hexes (priority zones): 341, covering 18.46 km²
and an estimated 44,266 residents (WorldPop 2020).

## 7.5 AHP weights and robustness

| Indicator | Column | AHP weight |
| --- | --- | --- |
| Green cover | NDVI | 0.137 |
| Thermal comfort | LST | 0.137 |
| Blue-green share | f_bluegreen | 0.079 |
| 15-minute accessibility | score15 | 0.403 |
| Transit proximity | d_transit_cap | 0.244 |

Consistency ratio: 0.007.

| Variant | Spearman rho vs baseline | Hexes changing quintile |
| --- | --- | --- |
| Equal weights | 0.823 | 811 |
| Green cover +20% | 1.000 | 30 |
| Green cover -20% | 1.000 | 32 |
| Thermal comfort +20% | 1.000 | 38 |
| Thermal comfort -20% | 1.000 | 22 |
| Blue-green share +20% | 1.000 | 48 |
| Blue-green share -20% | 1.000 | 38 |
| 15-minute accessibility +20% | 0.999 | 56 |
| 15-minute accessibility -20% | 0.998 | 88 |
| Transit proximity +20% | 0.999 | 66 |
| Transit proximity -20% | 0.999 | 68 |
