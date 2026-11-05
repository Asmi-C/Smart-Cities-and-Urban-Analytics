# Teammate package merge audit — 3 November 2026

Canonical baseline: Round-5 NKDA, including 2021/2024/2026 independent thermal tests, 24 shifted geographic validations, inner-tuned RF, residual GP and its negative decision comparison. The uploaded teammate ZIP contains two research scripts, previously generated summary CSVs, figures and manuscript notes. **It contains neither raw OSM network/POI extracts nor WorldPop raster**, so some source-level validations cannot be repeated from that ZIP alone.

| Component | Teammate result | Round-5 equivalent | Decision | Reason |
|---|---|---|---|---|
| 537 250-m analysis units | EPSG:32645 hexes over ~29.2 km² | Same exact canonical hex layer | MERGE | Reuse IDs/geometry; no alternate independent boundary |
| 5-category OSMnx accessibility | Cached Dijkstra nearest walking distances; 15-min all-five ~2.2% population | Original `hex_results.gpkg` has five network distances | RECOMPUTE | Recomputed 5/10/15-min distance and weighted coverage; 2.162% all five; old POI graph cannot be independently regenerated from ZIP |
| WorldPop population | Earth Engine `WorldPop/GP/100m/pop`, 2020 `Reducer.sum` at scale 100 m | Preexisting `pop` per same hex | RECOMPUTE | Overlay with final persistent heat and service distances; raster unavailable for independent pixel/edge checks; 2020 modelled proxy |
| Accessibility Moran / equity | Moran ~0.768 | Recomputed nearest-eight Moran 0.744, p=.001; weighted Gini 0.345 | RECOMPUTE | Different weight-matrix definition; don't silently equate statistics |
| Heat vs deficit | Spearman ~−0.29 | Recomputed Spearman **−0.287** on 537 cached hexes | RECOMPUTE | Correlation descriptive, spatially confounded; not causal |
| Pareto / random weights | Previously estimated rank stability | Strict Round-5 equal-weight and AHP comparators | SUPERSEDED | Proposed selector trails equal weights on matched perturbations |
| Random-vs-spatial CV and RF importance | Earlier single-configuration RF | 24 shifted, buffered, nested RF and GP | SUPERSEDED | Stronger leakage-aware geographic evaluation |
| Historical LULC and 99–100% accuracy | Built decreases, circular random holdout | Prior independent LULC disagreements | REJECT | Invalid accuracy/generalization and implausible trends |
| Historical UHI cooling | Different composite scenes/sensors | Same-sensor three independent thermal dates | REJECT | Acquisition-condition shifts make trend claim unidentifiable |
| OLS LST coefficients | Collinearity, Moran residual ~0.49 | Nested RF plus spatial residual testing | SUPERSEDED | OLS inferential assumptions violated |
| Official-paper-derived boundary | 640-m RMS fitted-label residual and 962-m max | Same digitized boundary is canonical | RECOMPUTE | Exact geometry self-consistency measured, independent geographic truth absent; preserve warning |
| Planning service and population layers | Service categories, heat/access tradeoffs | Round-5 planning exposure proxy | MERGE | Integrated into transparent candidate profiles with uncertainty flags |
| Presentation figures and styling | Numerous previous images | Round-5 research figures | REJECT | No new scientific evidence; excluded from scientific merge choices |

**No raw teammate source replaces the canonical Round-5 record.** The only merged scientific components are recomputed cached-network/accessibility and population/exposure analyses, and explicit data-quality/boundary warnings. Results in `network_accessibility.csv`, `accessibility_equity.csv`, `final_population_exposure.csv` and `planning_candidate_profiles.csv` are derivatives of current canonical hex records.
