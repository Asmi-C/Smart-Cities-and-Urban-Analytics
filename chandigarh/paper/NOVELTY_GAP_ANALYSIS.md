# Prior-art audit before developing a new thermal transfer method

Scope: unseen-date Landsat LST prediction within the NKDA region, using **no LST labels from the held-out acquisition**. A study's failure to mention a validation scheme in its abstract is **not evidence that it did not use one**; full-text checks are required before asserting uniqueness.

| Closest work/method | Assumptions and inputs | Target labels at adaptation? | Confirmed spatial CV? | Confirmed unseen-date test? | Explicit meteo baseline? | Relative thermal target? | Remaining question for our task |
|---|---|---|---|---|---|---|---|
| Kundu, Mukherjee & Mukhopadhyay (2026), New Town/Rajarhat, *Sustainable Cities and Society* 140, 107246, DOI 10.1016/j.scs.2026.107246 | Landsat temperature, built/road/green features, LightGBM/CatBoost/SHAP | Training labels yes; transfer setting unavailable from abstract | Not established from available text | Not established from available text | Not established | LST target | Evaluate a matched strong tree model under geographic and held-acquisition splits; avoid incomparable R² |
| Pseudo-invariant feature linear normalization for Changsha (2021), *Atmosphere* 12,1540 | Multitemporal Landsat LST, invariant surface anchors | Historical observations used to calibrate | Not established | Five images analyzed; no zero-label future-date transfer verified | Not established | Normalized multitemporal LST | Check if target-date invariant anchors require target LST; compare only if zero-label input rules match |
| Rao et al. (2025), GTWR urban surface-heat drivers in Wuhan, *Transactions in GIS* | Time-stamped multi-date urban covariates and geographic-temporal regression weighting | Observed multitemporal LST for regression fitting; unseen-date inference protocol not verified | Not established from abstract | Not established as zero-label acquisition extrapolation | Not established | Urban heat-island intensity studied | Explicitly establishes that spatial + temporal LST regression itself is prior art |
| LST spatial lag/error regression, *MethodsX* 2023, DOI 10.1016/j.mex.2023.102022 | Spatial weights and observed urban LST | Source LST yes | Not established | No zero-label date transfer verified | No | No | Spatial residual modelling is prior art, not a standalone novelty claim |
| Sun, Feng & Saenko, CORAL, AAAI 2016 | Unlabeled target covariate distribution; covariance alignment | No | Not a geospatial paper | Held-out domains yes, not satellite dates | No | No | Already tested, not novel |
| GeoMultiTaskNet (Marsocci et al., CVPR EarthVision 2023) | Geographical coordinates for unsupervised remote-sensing domain adaptation | No target annotation | Study-specific; not established here | Cross-domain segmentation, not thermal acquisition holdout | No | No | Spatial structure may help covariate alignment, but ours must test spatially blocked dates |
| Seasonal Domain Shift in the Global South (Voulgaris et al., CVPR EarthVision 2023) | Wet/dry aerial imagery, scene classification | Labels for reference data; held-domain setup differs | Not established | Seasonal domain evaluation | No | No | Evidence of seasonal appearance shift; no direct thermal baseline |
| CoDEx (Kuriyal et al., CVPR EarthVision 2025) | Multiple source-domain experts and domain-similarity gating | No target fine-tune | Spatial-generalization focus | Multiple satellite benchmarks | No | No | Source-domain expert gating is established; cannot rename this as new |
| Invariant risk minimization games (Ahuja et al., ICML 2020) and IRM critique (Kamath et al., AISTATS 2021) | Environment-labeled sources, invariance assumptions | No | Not satellite-specific | Unseen environments | No | No | Few dates, strong environmental confounding, IRM may fail; do not assert guarantees |
| Weighted conformal under covariate shift (Tibshirani et al., NeurIPS 2019) | Covariate-density ratio and conditional label-mechanism assumptions | No labels, target covariates yes | Not spatial-specific | Shifted-domain evaluations | No | No | May not cover acquisition-level label shift; test empirical coverage and state assumptions |
| Our Round-7 six-date RF spectral transfer | Landsat NDVI/NDBI/MNDWI, ERA5 context; 207–309 valid hexes/date | No | Separate + joint geographic tests | Six date holdouts | Ridge preliminary | Yes | Residual Moran persists; zero-label absolute state fails; no demonstrated new method advantage |

## Gap decision

The **evaluation gap** is clear: directly contrast target-free absolute and relative LST temporal transfer under both held-date and geographic exclusion while testing meteorological state estimation and spatially persistent bias. However this combination does **not automatically constitute a novel algorithm**. The decomposition `LST_{it}=g(M_t)+f(X_{it})+h(s_i)+epsilon_{it}` is an additive mixed/spatiotemporal model form with established precedents; novelty requires a specific new estimator or justified constraint and date-level superiority over strong counterparts.

## Sources and verification status

- Kundu et al. (2026): https://doi.org/10.1016/j.scs.2026.107246 (abstract-level only)
- Atmosphere normalization: https://www.mdpi.com/2073-4433/12/11/1540
- GTWR surface heat: https://doi.org/10.1111/tgis.70013
- Spatial lag/error urban LST: https://doi.org/10.1016/j.mex.2023.102022
- CORAL: https://doi.org/10.1609/aaai.v30i1.10306
- GeoMultiTaskNet: https://openaccess.thecvf.com/content/CVPR2023W/EarthVision/html/Marsocci_GeoMultiTaskNet_Remote_Sensing_Unsupervised_Domain_Adaptation_Using_Geographical_Coordinates_CVPRW_2023_paper.html
- Seasonal shift: https://openaccess.thecvf.com/content/CVPR2023W/EarthVision/html/Voulgaris_Seasonal_Domain_Shift_in_the_Global_South_Dataset_and_Deep_CVPRW_2023_paper.html
- CoDEx: https://openaccess.thecvf.com/content/CVPR2025W/EarthVision/papers/Kuriyal_CoDEx_Combining_Domain_Expertise_for_Spatial_Generalization_in_Satellite_Image_CVPRW_2025_paper.pdf
- IRM games: https://proceedings.mlr.press/v119/ahuja20a ; critical analysis: https://proceedings.mlr.press/v130/kamath21a
- Conformal covariate shift: https://proceedings.neurips.cc/paper_files/paper/2019/file/8fb21ee7a2207526da55a679f0332de2-Paper.pdf

Status: conceptual gap *identified*, a new method *not established*. Strongest honest contribution may remain an evaluation/protocol paper.
