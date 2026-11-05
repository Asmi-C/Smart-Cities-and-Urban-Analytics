# Smart Cities and Urban Analytics using Spatial Data — New Town Kolkata (NKDA)

Term project for the **Geographic Information Systems** course at **IIT Kharagpur**.
**Group 9:** Choudhary Asmi Aashay (23CS30061) · Maddipatla Sai Sravan (23CS10041) ·
Pachva Shiva Rama Krishna (23CS30037)

An open-data GIS framework that measures how liveable a planned Indian smart city is —
**New Town–Rajarhat (the NKDA statutory area, 29.34 km², Kolkata)** — using satellite
remote sensing, walk-network analysis and spatial statistics on a common 250 m hexagonal
grid (537 cells, EPSG:32645), condensed into a **Smart Liveability Index (SLI)**. The
repository also contains the **NKDA GeoAI research extension**: a rigorous test of
whether the urban-heat model survives unseen dates and unseen areas.

> **The one-line result:** date-only validation overstates model transfer by
> **0.10–0.40 R²** — the same direction on **Landsat-8 and Landsat-9** and in
> **all 64 holdout-shape combinations** tried; confirmed on five Landsat-9 dates
> fixed before their temperatures were read. Full evidence in `outputs/tables/`,
> the IEEE draft in `paper/`, and the write-up of what does and does not work.

---

## Research questions

| # | Question | Short answer |
|---|---|---|
| RQ1 | How much skill survives a geographic holdout within one date? | Tree models lose 0.09–0.10 R² vs random CV; OLS loses 0.03 |
| RQ2 | Does absolute LST transfer across dates — and is a relative (anomaly) target better? | Absolute LST: negative R² on every held-out date. Anomaly: positive on all 15 |
| RQ3 | How much does date-only testing overstate joint (date + area) transfer? | 0.10–0.40 R² depending on model and holdout shape |
| RQ4 | Does the gap hold on a second sensor and other holdout shapes? | Yes — 5/5 frozen Landsat-9 dates; every one of 64 CIs excludes 0 |
| RQ5 | Which planning conclusions survive boundary and threshold uncertainty? | Persistent heat in the boundary-stable core survives; joint hot-+-poor-access targeting is withheld |

## Project layout

```text
notebooks/ + src/     the base pipeline as notebook (Colab/Jupyter) and plain script
tests/                12 offline unit tests (synthetic data)
data/                 NKDA boundary GeoJSON; scene manifests; ERA5-Land context
boundary/             official NKDA plan-area sheet (PDF) + renders
outputs/              results.md; 134 tables; figures (maps + PPT figures); geopackages
external_case/        Landsat STAC discovery/fetch + every multi-date experiment
tools/                boundary digitiser, audits, Round-specific scripts
run_*.py, run_round11.sh   one-command replays (offline)
docs/                 validation notes, evidence ledgers, protocols
paper/                IEEE drafts, claim→evidence maps, references.bib
```

## 1) The base pipeline (Stage 1)

A → B → C → D, from free open data:

```text
Sentinel-2 (dry season) ─┐
Dynamic World (labels) ──┼─► A. Random-Forest land cover (100 trees) ─► maps, areas
Landsat C2 L2 (T1_L2) ───┤
                         ├─► B. LST + surface UHI + OLS (R² = 0.627) ─► heat map
OpenStreetMap (walk) ────┤
                         ├─► C. multi-source Dijkstra to 5 services ──► 15-min scores
WorldPop 2020 (100 m) ───┤
                         └─► D. AHP Smart Liveability Index (CR = 0.007) ─► clusters
```

| Module | Method | Outputs |
|---|---|---|
| A — Land cover | RF on 9 bands + NDVI/NDBI/MNDWI; trained on high-confidence Dynamic World; transitions vs 2016/2021/2026 | lulc_*.csv, 04–06 figures |
| B — Heat | Landsat-8/9 C2 L2 `ST_B10` (scale 0.00341802, offset 149 K), QA_PIXEL mask | heat_statistics.csv, 05 figure |
| C — Access | OSMnx walk graph; 1,200 m = 15 min @ 4.8 km/h | accessibility*.csv, 07–08 figures |
| D — Index & clusters | AHP weights, ±20 % sensitivity, Moran's I / LISA / Gi* with BH-FDR | sli_*.csv, spatial_clustering.csv, 09–12 figures |

Headline numbers (see `outputs/results.md`): surface UHI 1.69 °C (2026); 2.2% of
residents reach all five services in 15 minutes (11.9% at 20 min; 0.0% at 10 min);
walk-access deficit is concentrated at the edge (mean score 0.29 vs ~0.5 core);
87 Low-Low SLI hexagons (~12,649 residents, WorldPop modelled).

**Stage-1 metrics are committed** — the raw Sentinel-2/Dynamic World inputs are live
collections, so a fresh run will not reproduce them exactly (see "Reproducibility").

## 2) The research extension (Stages 2–6)

The extension challenges the naive use of the base layer for planning claims:

1. **Within one date, random CV flatters.** Spatial CV (1 km blocks, 5 folds over 52
   geographic blocks): tree models lose ~0.09–0.10 R²; coordinates-only falls
   0.47 → 0.08. (`spatial_cv_results.csv`, deck slide 11)
2. **Absolute LST does not transfer across dates.** Negative R² on every held-out
   date; anomaly (relative) heat does better. (`date_level_method_comparison.csv`, slide 12)
3. **Date-only testing overstates joint transfer.** D0–D3 regimes (random / new-area /
   new-date / new-date-and-new-area). Landsat-8: D2→D3 drops 0.515–0.687 R² (sign-flip
   p = 0.0078). Landsat-9 (5 dates, frozen in advance): drops 0.315–0.477 on all five
   dates; p = 0.0625 (smallest possible at n = 5). (`domain_shift_model_matrix.csv`,
   `round10_landsat9_confirmatory.csv`, slides 13–14)
4. **The gap is not an artefact of how the map is cut.** Eight holdout shapes
   (1/2 km blocks × 2 grid origins × ±500 m buffer) × 4 models × 2 sensors =
   **64 CIs, all positive**; 639/640 single-date gaps positive. (`round11_optimism_summary.csv`, slide 15)
5. **Residual spatial structure persists.** Moran's I 0.22–0.63 across all
   dates/models/weights; accounted for by block resampling in the statistics, never
   "modelled away" (all p ≤ 0.002). (`round11_residual_moran.csv`, slide 19)
6. **Intervals are approximate.** Nominal 90% conformal intervals cover 0.899
   (pooled) / 0.937 (date-cluster) on average; worst date 0.667 / 0.711. (slide 20)
7. **Planning survives only partly.** Persistent heat (≥ half of 15 dates): 46
   hexagons, ~7,993 residents — 18 hexagons (~3,635 residents, 18.7%) inside the
   640 m boundary-stable core. Joint hot + poor-access targeting is **withheld** until
   an authoritative boundary exists. (`round11_planning_screen_sensitivity.csv`, slide 21)

Everything the deck reports maps to committed tables — see
`docs/REPRODUCIBILITY_AND_DATA.md` for the table→slide map and the exclusion list
(reviewer material is not published here).

## How to run

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# offline checks
python -m pytest tests/ -q          # 12 passed
python run_research_pipeline.py     # spatial CV, ablations, priority stability
python run_ieee_experiments.py      # validation matrix, diagnostics, uncertainty
python run_submission_tests.py      # residual structure, geographic transfer

# full replay from the committed cached satellite tables (~25 min on 2 CPUs)
bash run_round11.sh
```

For the base notebook (needs a Google Earth Engine project — register at
<https://earthengine.google.com/> for non-commercial use, then set `PROJECT_ID` in
the configuration cell):

```bash
jupyter lab notebooks/newtown_smart_city_analysis.ipynb   # Runtime → Run all
```

See **docs/REPRODUCIBILITY_AND_DATA.md** for what is and is not re-runnable, the
frozen-outputs policy, and the 2026-11-05 verification log.

## Study area and boundary (honesty notice)

The NKDA boundary is the statutory 29.34 km² planning area (Schedule I Part A, NKDA
Act 2007). It was digitised from the official (unregistered, no coordinate grid)
plan-area sheet via `tools/nkda_boundary.py`; registration RMS ≈ **640 m** (max 962 m;
rigid transform — internal metrics are unaffected, edge membership is not; see
`docs/BOUNDARY_VALIDATION.md`). Hexagons whose membership depends on the boundary are
treated as uncertain everywhere in the planning analysis.

## Limitations

- LST ≠ air temperature; anomaly (relative) heat is the transferable target, and it
  needs the observed scene mean — **not** absolute forecasting.
- One township only; no independent second city yet; only 5 confirmation dates.
- Residual spatial dependence is not modelled; intervals undercover the worst date.
- Dynamic-World-circular land-cover accuracy; ESA WorldCover agreement ≈ 44% —
  land-cover trend claims were dropped accordingly.
- Screening indicators only — no intervention effects, no parcel-level advice.

## Licences

Code: MIT (see `LICENSE`). Data keep their original licences: Sentinel-2 (Copernicus),
Landsat (USGS, public domain), Dynamic World & ESA WorldCover & WorldPop (CC BY 4.0),
OpenStreetMap (ODbL, © OpenStreetMap contributors), NKDA plan-area sheet (public
government publication).
