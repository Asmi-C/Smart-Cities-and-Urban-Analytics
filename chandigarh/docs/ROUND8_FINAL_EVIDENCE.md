# Round 8 evidence ledger (2026-11-03)

## Independent acquisition accounting

Landsat-8 Collection-2 Level-2; WRS 138/045; 15 February–15 May; scene-level cloud cap 25%; 2018–2026. STAC candidates 695, preselected scenes 16, complete-scene hex quality passes **15**, excluded 2025-05-06 after imagery QA (28 valid observations, minimum 180). The accepted 15 span **eight calendar years** and have 189–311 valid hexagons per date; **180** shared spatial hexagons remain observed across every date. Six dates had been inspected during model development; the **nine new dates** are separately tested under the frozen protocol `docs/FINAL_METHOD_PROTOCOL.md`. No 2022 acquisition passed selection. All 16 acquired dates have ERA5-Land historical context; missing weather fields are left missing.

## Locked primary endpoint: leave-one-acquisition-out anomaly transfer

| Model | Mean anomaly R², 15 dates | RMSE °C | Mean residual Moran I |
|---|---:|---:|---:|
| Raw spectral RF | 0.450 | 1.141 | 0.422 |
| Target-unlabeled feature z-score spectral RF | 0.602 | 0.971 | 0.396 |
| Source-only cross-date RF residual correction (fixed shrink 0.5) | **0.737** | **0.785** | **0.385** |
| Historical site anomaly climatology | 0.723 | 0.803 | 0.565 |

The hybrid beats the z-RF on **15/15 dates**, mean paired ΔR² **+0.1347**; exact **calendar-year** clustered sign-flip p **0.0078125**, 95% cluster-bootstrap CI **[+0.1138,+0.1674]**. On **nine newly acquired dates only**, ΔR² **+0.1409** (9/9), year-cluster p **0.0078125**, CI **[+0.1138,+0.1737]**. These results do not establish superiority over the stronger site climatology: nine-new-date ΔR² **+0.0446**, 6/9 wins, year-cluster p **0.34375**, CI **[−0.0362,+0.1444]**. All 15 climatology comparisons likewise fail to establish a meaningful R² advantage (mean +0.0135, p 0.8828).

**Independent spatial property:** hybrid minus climatology mean residual Moran I **−0.1787 on nine added dates**, 8/9 lower, clustered p **0.0078125**, year-bootstrap CI **[−0.2559,−0.1210]**. Across all 15 dates reduction **−0.1798** (p **0.0078125**). However all tested hybrid residual fields still have significant positive autocorrelation at 999 permutations (minimum Monte Carlo p **0.001**); **the underlying spatial problem is not solved**.

## Other transfer stress tests

| Test | Major observed result | Caution |
|---|---|---|
| 180-hex common support (15 dates) | Site climatology R² 0.745, z-RF 0.632 | Both require same township; prevents changing QA footprint from creating a false gain |
| Leave-one-calendar-year-out, 8 years | Hybrid anomaly R² 0.727; historical climatology 0.709; z-RF 0.596 | Same geography, not external city |
| Strict chronological prior-year-only, 11 dates | Historical climatology anomaly R² 0.626; z-RF 0.557; site-hotspot frequency AUROC 0.860 | Later acquisition information unavailable; historical climatology requires observed sites |
| Original joint geographic/date block, 2021 | Anomaly R² about −0.014 | Geographically novel sites remain an unresolved failure |
| Weather ridge + site climatology absolute LST | Mean RMSE 1.803°C, mean R² **−0.441** | Reanalysis is retrospective; *not* forecast-ready |
| Weather-only absolute LST | Mean RMSE 2.345°C, mean R² −1.204 | Source history only 14 dates per held-date fit |
| Meteorology + site climatology versus source-date mean + site climatology | Mean RMSE benefit 1.998°C, 13/15 dates, year p 0.0078 | Explains acquisition-level offset, not absolute transfer success |

## Predictive uncertainty and hotspot ranking

Historical **source-only site hotspot frequency**: fifteen-date mean AUROC **0.902**, PR-AUC **0.726**, Brier **0.094**, calibration ECE ~**0.061**. Spectral RF classifier: AUROC **0.801**, PR-AUC **0.500**, Brier **0.131**, ECE ~**0.062**. Nine-addition AUROC gain site frequency vs RF **+0.0778**, 8/9 wins, year-cluster p **0.0234**; Brier gain −0.0248, year-cluster p **0.1406** (uncertain).

Source-date conformal-style 90% intervals: pooled mean observed coverage **89.8%** but worst date **70.7%**; most conservative worst-source-date calibration mean **96.8%**, worst **82.8%** with larger intervals. No new-date distribution-free guarantee is claimed.

Early vs late acquisition residual site-bias means correlate **0.585** over 283 shared units; geographic 1-km block bootstrap CI **[0.454,0.726]**, 30 blocks. Spatial residual persistence and static built/green context are descriptive associations, not demonstrated causes.

## Planning screen and irreducible access constraints

Across 15 dates, **46** hexagons are observed hot in at least half their valid dates and have ≥7 valid dates, containing ~**7,993** WorldPop-2020 modelled people. **Six** also have lowest-quintile *cached* OSM access scores (~**288** modelled people). The polygon has ~**640-m** anchor registration error; no independently authenticated boundary, raw source OSM graph or POIs, ground-truthed accessibility, refreshed population product, or validated Euclidean-versus-network test is present. These are screens, **not planning recommendations or measured human exposure**.

## What is and is not new

Quantified claim: a strictly source-only hybrid has **comparable anomaly accuracy to strong historical-site climatology yet materially lower residual Moran's I on independent newly acquired dates**. This is a measurable methodological *tradeoff* and a robust evaluation protocol, not a new estimator in the machine-learning literature. The spectral comparison alone is insufficient; the stronger baseline remains essential in every table. No claim of causal intervention, external-area validation, universal transfer, or new-city performance is justified.

## Reproduction pointers

`run_round8.py` replays included per-date hex features; `--acquire` retrieves original COG inputs (multi-GB, supported service required). `data/acquisition_manifest_final.csv` contains QA outcome and source provenance; `outputs/tables/addition_only_confirmatory_tests.csv`, `hybrid_vs_climatology_pareto.csv`, `round8_residual_Moran_permutations.csv`, `leave_one_year_out.csv`, `chronological_forward_transfer.csv`, `meteorology_ablation.csv`, `hotspot_calibration_ECE.csv`, `date_conformal_coverage.csv` contain the corresponding individual metrics. Raw scene COG files are intentionally omitted from the portable package; harmonized per-scene CSVs are supplied.
