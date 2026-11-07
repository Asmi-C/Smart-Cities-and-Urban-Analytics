# Results — Chandigarh planned-core smart liveability analysis

Study area: Chandigarh planned core (Sectors 1-47), datameet Chandigarh_Sectors.geojson (chandigarh_boundary.geojson), 49.3 km², 906 hexagons (250 m).
Training labels: Dynamic World pixels with probability ≥ 0.6; accuracy is measured against held-out
Dynamic World labels (30%), with ESA WorldCover 2021 as an independent check.

## 7.1 Land cover change (RQ1)

| Class | 2016 area (km²) | 2021 area (km²) | 2026 area (km²) | Change 2016–2026 (%) |
| --- | --- | --- | --- | --- |
| Water / wetland | 0.10 | 0.24 | 0.08 | -18.40 |
| Vegetation | 12.18 | 12.27 | 12.25 | 0.63 |
| Cropland | 4.29 | 3.56 | 3.34 | -22.08 |
| Built-up | 32.73 | 33.23 | 33.62 | 2.72 |
| Bare / fallow | 0.00 | 0.00 | 0.00 |  |

Built-up compound annual growth 2016–2026: 0.27% per year.

**Accuracy**

| Year | Imagery | Overall accuracy (%) | Kappa | Agreement with Dynamic World (%) | Agreement with ESA WorldCover 2021 (%) |
| --- | --- | --- | --- | --- | --- |
| 2016 | 4 Sentinel-2 scenes, 2015-11-01 to 2016-03-01 (L1C top-of-atmosphere) | 93.32 | 0.91 | 72.82 |  |
| 2021 | 29 Sentinel-2 scenes, 2020-11-01 to 2021-03-01 (L2A surface reflectance) | 97.89 | 0.97 | 76.47 | 72.47 |
| 2026 | 37 Sentinel-2 scenes, 2025-11-01 to 2026-03-01 (L2A surface reflectance) | 97.14 | 0.96 | 75.96 |  |

**Per-class F1**

| Year | Water / wetland | Vegetation | Cropland | Built-up |
| --- | --- | --- | --- | --- |
| 2016 | 1.00 | 0.94 | 0.92 | 0.88 |
| 2021 | 0.99 | 0.99 | 0.98 | 0.96 |
| 2026 | 1.00 | 0.99 | 0.95 | 0.94 |

**Transition matrix 2016 → 2026 (km²; rows = 2016, columns = 2026)**

| From / to | Water / wetland (2026) | Vegetation (2026) | Cropland (2026) | Built-up (2026) | Bare / fallow (2026) |
| --- | --- | --- | --- | --- | --- |
| Water / wetland (2016) | 0.03 | 0.02 | 0.00 | 0.04 | 0.00 |
| Vegetation (2016) | 0.01 | 8.48 | 0.20 | 3.49 | 0.00 |
| Cropland (2016) | 0.00 | 0.54 | 1.27 | 2.48 | 0.00 |
| Built-up (2016) | 0.04 | 3.21 | 1.87 | 27.61 | 0.00 |
| Bare / fallow (2016) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## 7.2 Heat island (RQ2)

| Statistic | Value |
| --- | --- |
| Mean pre-monsoon LST, built-up, 2026 (°C) | 36.462 |
| Mean pre-monsoon LST, vegetated reference, 2026 (°C) | 34.269 |
| Surface UHI intensity, 2026 (°C) | 2.193 |
| Pearson r, LST vs NDVI (hexes) | -0.766 |
| Pearson r, LST vs NDBI (hexes) | 0.776 |
| OLS R², LST ~ NDVI + NDBI + MNDWI | 0.667 |
| Moran's I of OLS residuals | 0.456 |
| Pseudo p-value of residual Moran's I | 0.001 |

**Surface UHI by year**

| Year | Landsat scenes | Period | Mean LST, built-up (°C) | Mean LST, vegetated reference (°C) | Surface UHI intensity (°C) |
| --- | --- | --- | --- | --- | --- |
| 2016 | 3 | 2016-03-01 to 2016-06-01 | 42.98 | 41.85 | 1.13 |
| 2021 | 3 | 2021-03-01 to 2021-06-01 | 38.64 | 37.76 | 0.88 |
| 2026 | 9 | 2026-03-01 to 2026-06-01 | 36.46 | 34.27 | 2.19 |

OLS coefficients: const = 37.77 (p = 0.000), NDVI = -25.66 (p = 0.000), NDBI = -14.37 (p = 0.000), MNDWI = -21.98 (p = 0.000).

## 7.3 Accessibility (RQ3)

Walking threshold: 15 min at 4.8 km/h = 1200 m network distance.

| Service category | OSM features in area + buffer | Median walk distance (m) | Population within 15 min (%) |
| --- | --- | --- | --- |
| School | 214 | 428.7 | 96.6 |
| Health | 171 | 548.2 | 93.8 |
| Park / green space | 961 | 192.9 | 99.9 |
| Public transit | 25 | 1,340.3 | 42.3 |
| Daily shopping | 53 | 1,062.6 | 59.7 |
| All five categories |  |  | 30.1 |

**By zone (distance-from-centroid terciles)**

| Zone | Hexes | Mean 15-min score | Median 15-min score |
| --- | --- | --- | --- |
| Core | 302 | 0.82 | 0.80 |
| Edge | 302 | 0.69 | 0.80 |
| Middle | 302 | 0.80 | 0.80 |

Kruskal-Wallis H = 49.52, p = 0.0000.

## 7.4 Spatial clustering (RQ4)

| Variable | Global Moran's I | Pseudo p-value | High-High hexes | Low-Low hexes |
| --- | --- | --- | --- | --- |
| LST | 0.626 | 0.001 | 72 | 92 |
| 15-minute score | 0.738 | 0.001 | 183 | 80 |
| Smart Liveability Index | 0.743 | 0.001 | 155 | 119 |

Low-Low SLI hexes (priority zones): 119, covering 6.44 km²
and an estimated 57,411 residents (WorldPop 2020).

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
| Equal weights | 0.806 | 478 |
| Green cover +20% | 0.999 | 30 |
| Green cover -20% | 0.999 | 26 |
| Thermal comfort +20% | 0.999 | 28 |
| Thermal comfort -20% | 0.999 | 36 |
| Blue-green share +20% | 1.000 | 22 |
| Blue-green share -20% | 1.000 | 22 |
| 15-minute accessibility +20% | 0.998 | 42 |
| 15-minute accessibility -20% | 0.997 | 76 |
| Transit proximity +20% | 0.999 | 52 |
| Transit proximity -20% | 0.998 | 56 |
