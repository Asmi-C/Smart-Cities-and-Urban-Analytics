# Generalization experiment and honest scope

## Data availability decision

The current package contains one year of hex-level pre-monsoon LST/covariates (2026) and classified LULC rasters for 2016, 2021 and 2026. The LULC rasters are **not** compatible LST/feature stacks, and their reference validation is weak. The original Google Earth Engine workflow needs a working authenticated environment to retrieve additional harmonized Landsat LST and satellite covariates; this workspace does not contain that authenticated pipeline or a second independent city's matching data. Accordingly, neither temporal nor external-area validation has been completed. We did not substitute 2016/2021 class maps as fake thermal observations.

## Internal spatial transfer stress test

We instead trained on the western 80% of the existing NKDA hexes (423) and evaluated on the geographically contiguous easternmost 20% (114). The cutoff is based on projected centroid x-coordinate and no eastern target labels are used in training. These hexes have nevertheless belonged to earlier research and feature-selection explorations, so this is **not an untouched final holdout**.

| Model | Transfer RMSE °C | MAE °C | R² |
|---|---:|---:|---:|
| RF | 1.000 | 0.856 | 0.360 |
| RF + coordinates | 0.844 | 0.689 | 0.544 |
| RF + 750-m covariate context | 1.010 | 0.870 | 0.346 |
| RF + context + coordinates | 0.866 | 0.717 | 0.520 |

The ranking is informative for *within-town* extrapolation, not external validation. No confidence is claimed in time transfer or transfer to a different city. Results and exact counts are in `outputs/tables/generalization_results.csv`.

## Needed for true external evidence

One same-season second acquisition with comparable Landsat product/quality masking and independently matched predictors, or a second planned township with the same schema and verified administrative study boundary. Freeze model and decision hyperparameters before access to those external targets; compare within-period spatial, cross-period and spatiotemporal holdouts. If this cannot be obtained, any submitted paper must explicitly present a single-site case study.
