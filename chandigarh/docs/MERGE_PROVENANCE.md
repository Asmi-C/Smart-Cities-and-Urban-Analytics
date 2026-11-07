# Round-6 teammate merge provenance

| Imported concept/source | Original teammate location | Implemented canonical location | Transformation |
|---|---|---|---|
| Walking-network accessibility | `research/decision_support.py`, team audit; originally `src/newtown_smart_city_analysis.py` | `tools/merge_access_exposure.py`; `outputs/tables/network_accessibility.csv` | New computations from canonical `d_school,d_health,d_green,d_transit,d_shop`; no unverified graph copied |
| WorldPop 2020 overlay | Teammate audit and original Earth Engine `WorldPop/GP/100m/pop` | `tools/merge_access_exposure.py`; `outputs/tables/final_population_exposure.csv` | Weighted overlay on current 537 hexes and 207 clear-three-period subset; label proxy limitations |
| Spatial clustering/access equity | Teammate `spatial_clustering.csv` and audit | `outputs/tables/accessibility_equity.csv` | Nearest-eight permutation Moran re-estimated, unweighted and population-weighted Gini added |
| Heat-access trade-off | Teammate `objective_correlations.csv` | `outputs/tables/accessibility_equity.csv` | Recomputed Spearman with canonical LST and `1-score15` |
| Boundary caveat | Teammate audit / original registration code | `docs/BOUNDARY_VALIDATION.md`; `outputs/tables/boundary_validation.csv` | Loaded both extant GeoJSONs, corrected invalid topology solely for equality comparison; **no fabricated positional correction** |
| Historical LULC caution | `EXISTING_PROJECT_AUDIT.md` | `docs/TEAMMATE_BRANCH_MERGE_AUDIT.md` | Preserve negative data-quality finding; do not import historical trend into claims |

All thermal transfer code remains independent under `external_case/`; older RF and Pareto implementations remain background only. The ZIP's older research scripts are **not** promoted to the canonical execution path.
