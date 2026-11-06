# Reproducibility and data availability

This repository contains the complete project: the base smart-liveability pipeline
(Google Earth Engine, modules A–D) and the NKDA GeoAI research extension (spatial and
temporal generalization of the urban-heat model).

## Layout

- `notebooks/` — the base analysis notebook (Google Colab / JupyterLab)
- `src/` — the same pipeline as a plain script (kept in sync with `jupytext`)
- `tests/` — offline unit tests (synthetic data; no network)
- `data/` — the NKDA boundary GeoJSON, scene manifests, thermal metadata
- `boundary/` — the official NKDA plan-area sheet (`map.pdf`) and renders
- `outputs/` — committed results: `results.md`, 134 tables, 12+12 figures, geopackages
- `tools/` — boundary digitiser, audits, Round-specific scripts
- `external_case/` — Landsat acquisition and every multi-date experiment
- `run_*.py`, `run_round11.sh` — one-command replays
- `paper/` — IEEE drafts, claims/evidence maps, references.bib
- `docs/` — validation notes, evidence ledgers, protocols

## Environment

Python 3.12. Create a virtualenv and install the base requirements:

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`requirements-lock-round11.txt` pins the exact Round-11 analysis environment
(numpy, pandas, scikit-learn, scipy, matplotlib).

## What runs offline (verified 2026-11-05)

```bash
python -m pytest tests/ -q          # 12 passed
python run_research_pipeline.py     # spatial CV matrix, ablations, priority stability
python run_ieee_experiments.py      # validation matrix, spatial diagnostics, uncertainty
python run_submission_tests.py      # residual structure, geographic transfer, rank robustness
bash run_round11.sh                 # full replay from the cached per-hexagon tables
```

All five exit 0. `run_round11.sh` (~25 min on 2 CPUs; ~11 min on 12) rebuilds every
Round-10/11 table and the two figures embedded in the final deck from
`external_case/data/landsat_hex_*.csv` (15 Landsat-8 development scenes + 5 frozen
Landsat-9 confirmation scenes). Round-11 statistics reproduce to **≤ 0.0025 R²/gap**
vs the committed tables; Landsat-9 means change by **≤ 0.003 R²**; D3 interval
coverage matches exactly (0.899/0.937 leave-one-year-out; 0.887/0.929 Landsat-8→9).

Committed outputs are the frozen package the deck quotes; fresh replays differ only
by library patch drift. After replaying, `git diff` will show small drift — restore
with `git restore .` unless you intend to re-freeze the tables.

## What is not re-runnable without extra inputs

- Raw Landsat/ERA5 downloads (`external_case/fetch_selected_dates.py`): ~3–5 GB of
  COGs from Planetary Computer (open, no credentials). Not needed — the cached
  per-hexagon tables are committed.
- The Google Earth Engine notebook from scratch: requires an EE project
  (registration at https://earthengine.google.com/). Dynamic World and OSM are live
  collections, so a fresh run will not match the committed Stage-1 numbers exactly;
  the committed `outputs/` are the reference record.
- `tools/nkda_boundary.py --report` rewrites the committed boundary; do not re-run it.

## What is deliberately not in this repository

Internal review and scoring material (reviewer simulations, rubrics,
submission-readiness notes) is not part of the public repository. The scientific
content — code, data manifests, cached tables, all output tables and figures, the
IEEE drafts and validation documents — is complete and reproducible.
