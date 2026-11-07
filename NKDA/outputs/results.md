# Results — New Town Kolkata smart liveability analysis

Study area: NKDA boundary digitised from the official plan-area sheet (newtown_boundary.geojson), 29.2 km², 537 hexagons (250 m).
Training labels: Dynamic World pixels with probability ≥ 0.6; accuracy is measured against held-out
Dynamic World labels (30%), with ESA WorldCover 2021 as an independent check.

## 7.1 Land cover change (RQ1)

| Class | 2016 area (km²) | 2021 area (km²) | 2026 area (km²) | Change 2016–2026 (%) |
| --- | --- | --- | --- | --- |
| Water / wetland | 2.09 | 1.97 | 2.33 | 11.55 |
| Vegetation | 3.24 | 4.14 | 3.94 | 21.82 |
| Cropland | 0.00 | 0.00 | 0.00 |  |
| Built-up | 23.90 | 23.13 | 22.98 | -3.85 |
| Bare / fallow | 0.03 | 0.00 | 0.00 | -100.00 |

Built-up compound annual growth 2016–2026: -0.39% per year.

**Accuracy**

| Year | Imagery | Overall accuracy (%) | Kappa | Agreement with Dynamic World (%) | Agreement with ESA WorldCover 2021 (%) |
| --- | --- | --- | --- | --- | --- |
| 2016 | 4 Sentinel-2 scenes, 2015-11-01 to 2016-03-01 (L1C top-of-atmosphere) | 99.20 | 0.99 | 21.21 |  |
| 2021 | 41 Sentinel-2 scenes, 2020-11-01 to 2021-03-01 (L2A surface reflectance) | 100.00 | 1.00 | 65.63 | 43.79 |
| 2026 | 53 Sentinel-2 scenes, 2025-11-01 to 2026-03-01 (L2A surface reflectance) | 99.72 | 1.00 | 69.25 |  |

**Per-class F1**

| Year | Water / wetland | Vegetation | Cropland | Built-up | Bare / fallow |
| --- | --- | --- | --- | --- | --- |
| 2016 | 1.00 | 1.00 | 0.00 | 0.99 | 0.75 |
| 2021 | 1.00 | 1.00 | 0.00 | 1.00 |  |
| 2026 | 1.00 | 1.00 | 0.00 | 1.00 |  |

**Transition matrix 2016 → 2026 (km²; rows = 2016, columns = 2026)**

| From / to | Water / wetland (2026) | Vegetation (2026) | Cropland (2026) | Built-up (2026) | Bare / fallow (2026) |
| --- | --- | --- | --- | --- | --- |
| Water / wetland (2016) | 1.62 | 0.19 | 0.00 | 0.28 | 0.00 |
| Vegetation (2016) | 0.09 | 1.50 | 0.00 | 1.65 | 0.00 |
| Cropland (2016) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| Built-up (2016) | 0.62 | 2.25 | 0.00 | 21.03 | 0.00 |
| Bare / fallow (2016) | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 |

## 7.2 Heat island (RQ2)

| Statistic | Value |
| --- | --- |
| Mean pre-monsoon LST, built-up, 2026 (°C) | 35.180 |
| Mean pre-monsoon LST, vegetated reference, 2026 (°C) | 33.491 |
| Surface UHI intensity, 2026 (°C) | 1.689 |
| Pearson r, LST vs NDVI (hexes) | 0.058 |
| Pearson r, LST vs NDBI (hexes) | 0.572 |
| OLS R², LST ~ NDVI + NDBI + MNDWI | 0.627 |
| Moran's I of OLS residuals | 0.490 |
| Pseudo p-value of residual Moran's I | 0.001 |

**Surface UHI by year**

| Year | Landsat scenes | Period | Mean LST, built-up (°C) | Mean LST, vegetated reference (°C) | Surface UHI intensity (°C) |
| --- | --- | --- | --- | --- | --- |
| 2016 | 6 | 2016-03-01 to 2016-06-01 | 43.61 | 40.36 | 3.25 |
| 2021 | 7 | 2021-03-01 to 2021-06-01 | 39.24 | 36.87 | 2.37 |
| 2026 | 15 | 2026-03-01 to 2026-06-01 | 35.18 | 33.49 | 1.69 |

OLS coefficients: const = 34.31 (p = 0.000), NDVI = -23.71 (p = 0.000), NDBI = -15.70 (p = 0.000), MNDWI = -24.01 (p = 0.000).

## 7.3 Accessibility (RQ3)

Walking threshold: 15 min at 4.8 km/h = 1200 m network distance.

| Service category | OSM features in area + buffer | Median walk distance (m) | Population within 15 min (%) |
| --- | --- | --- | --- |
| School | 34 | 2,082.2 | 23.8 |
| Health | 38 | 1,389.0 | 47.0 |
| Park / green space | 251 | 778.1 | 80.1 |
| Public transit | 91 | 1,377.7 | 42.8 |
| Daily shopping | 32 | 1,581.8 | 35.5 |
| All five categories |  |  | 2.2 |

**By zone (distance-from-centroid terciles)**

| Zone | Hexes | Mean 15-min score | Median 15-min score |
| --- | --- | --- | --- |
| Core | 179 | 0.50 | 0.40 |
| Edge | 179 | 0.29 | 0.20 |
| Middle | 179 | 0.49 | 0.60 |

Kruskal-Wallis H = 59.97, p = 0.0000.

## 7.4 Spatial clustering (RQ4)

| Variable | Global Moran's I | Pseudo p-value | High-High hexes | Low-Low hexes |
| --- | --- | --- | --- | --- |
| LST | 0.555 | 0.001 | 29 | 29 |
| 15-minute score | 0.768 | 0.001 | 131 | 85 |
| Smart Liveability Index | 0.797 | 0.001 | 141 | 87 |

Low-Low SLI hexes (priority zones): 87, covering 4.71 km²
and an estimated 12,649 residents (WorldPop 2020).

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
| Equal weights | 0.857 | 278 |
| Green cover +20% | 1.000 | 14 |
| Green cover -20% | 1.000 | 12 |
| Thermal comfort +20% | 1.000 | 18 |
| Thermal comfort -20% | 1.000 | 16 |
| Blue-green share +20% | 1.000 | 12 |
| Blue-green share -20% | 1.000 | 14 |
| 15-minute accessibility +20% | 0.999 | 34 |
| 15-minute accessibility -20% | 0.997 | 36 |
| Transit proximity +20% | 0.999 | 18 |
| Transit proximity -20% | 0.999 | 34 |
