# Chandigarh replication — run notes

Independent replication of the New Town–Rajarhat (NKDA) project on the **Chandigarh
planned core** (Sectors 1–47), used for the E12 "does the method transfer to another
city?" question. **NKDA was not modified**; everything here is a sibling copy.

## Study area and data

- Boundary: `data/chandigarh_boundary.geojson` — datameet/Municipal_Spatial_Data
  `Chandigarh_Sectors.geojson` (CC BY-SA 2.5 IN), filtered to sectors ≤ 47, dissolved
  to a single polygon. 49.3 km² (published core), **906 hexagons** of 250 m,
  EPSG:32643. (NKDA polygon kept at `data/newtown_boundary_nkda.geojson`.)
- Landsat: 15 Landsat-8 scenes (2018–2026 Feb–May, cloud ≤ 25%, ≤2/yr ≥16 days apart,
  pre-declared rule) + **5 frozen Landsat-9 scenes** (one per year 2022–2026,
  lowest cloud; metadata only). **Every scene: 906/906 valid hexagons.**
- ERA5-Land context re-fetched at Chandigarh's coordinates (30.73, 76.77).
- WorldPop 2020; OSM (walk network + POIs).

## What was reproduced (all from this folder, all exit 0)

- `pytest tests/ -q` → 12 passed
- `run_research_pipeline.py` — spatial CV RMSE **0.623 °C** (R² 0.630); 144 stable
  priority hexagons; AHP-vs-equal overlap 135/182 (ρ = 0.806)
- `run_ieee_experiments.py` — combined-minus-morphology RMSE −0.073 °C,
  bootstrap 95% CI [−0.109, −0.037] (unlike NKDA, **combined features help here**);
  residual Moran's I 0.411 (p = 0.001); nominal 90% interval coverage 91.5%
- `run_submission_tests.py` — RF+coords RMSE **0.563 °C** (R² 0.698), Moran's I 0.337;
  equal weights still beat the proposed shortlist (Jaccard 0.331 vs 0.506)
- `bash run_round11.sh` — full replay; `outputs/round11_input_checksums.sha256`
  (20 Chandigarh files); Round-11 statistics reproduce identically in structure:
  **all 64 holdout-shape CIs > 0** (thinnest lower bound 0.005); Landsat-9 D2→D3
  gap 0.315–0.477 — the date-only-optimism result **replicates**; mean anomaly R²
  0.45→0.78; interval coverage L8 LOYO pooled 0.898 / date-cluster 0.937 (matches
  NKDA almost exactly); L8→L9 date-cluster coverage 0.968 (worst date 0.939)
- Base notebook re-run end-to-end on Chandigarh (EE `newton-gis2`); outputs regenerated
  (Modules A–D), results.md rewritten with honest Chandigarh numbers:
  built-up +2.7% (2016–2026); surface UHI 2.19 °C; r(LST, NDVI) = −0.766;
  **30.1%** reach all five services in 15 min (transit weakest, 42.3%);
  SLI Moran's I 0.743 (p = 0.001); 119 Low-Low SLI hexagons (~57,411 modelled residents)

## One-line setup changes made in this copy only

Boundary file path + name (`data/chandigarh_boundary.geojson`); `CRS` 32645→32643
(script, notebook + docs/comments); `PLACE_QUERY`; figure title; `results.md` heading;
`BOUNDARY_SOURCE` string; `fetch_meteorology.py` coordinates; `evaluate_relative_transfer.py`
three dates (2021-04-24 / 2024-05-02 / 2026-04-22); `boundary_perturbation.py` boundary path.
CRS comment corrected to zone 43N. No algorithm, threshold, or model change.

## Caveats (read before reuse)

1. **The Overpass (OSM) API was flaky/overloaded during this run.** School and health
   queries intermittently returned 502s and were silently zeroed by the pipeline's
   `try/except` on the first two attempts; the third attempt (with the responses in
   the OSMnx cache) succeeded, and the final `accessibility.csv` is complete
   (School 214 features / 96.6% in 15 min). If OSM 502s return in a fresh re-run,
   cache the POI responses before re-running (or the pipeline silently produces 0s).
2. **EE re-runs do not reproduce bit-exact outputs** (live Dynamic World/Sentinel-2);
   this folder's outputs are the honest, current-vintage Chandigarh numbers.
3. Land-cover accuracy vs ESA WorldCover is high (72.5%) but 2021 agreement is still
   the operative check; DW-circular 99–100% values are not evidence.
4. Boundary is **CC BY-SA 2.5 IN** — reuse with attribution and share-alike.
   OSM data is ODbL (attribute © OpenStreetMap contributors).
5. Modelled (WorldPop 2020), not enumerated, population; access metrics inherit
   OSM mapping completeness; only three pre-monsoon dates used for the
   3-way transfer check (2021/2024/2026 design), matching NKDA's protocol.
6. `docs/`, `README.md`, `paper/`, `presentation/`, `ppt/` in this folder are still
   the NKDA project's documents and were left as reference; they do **not** describe
   Chandigarh. NKDA's cached scenes are preserved under `external_case/data_nkda_reference/`,
   `data/*_nkda.csv`, `data/newtown_boundary_nkda.geojson`, `outputs_nkda_reference/`.
7. `run_research_pipeline.py` prints a hard-coded "537 hexagons" line (its data here
   is 906) — cosmetic, code left unchanged by policy.
