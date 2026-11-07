# NKDA urban heat study — code

Code only. Data tables and outputs are in the full package (NKDA_GeoAI_Round11_Submission.zip).
To run, extract this folder over the full package (same folder layout).

Main entry points
- `run_round11.sh` — rebuilds all tables and figures from the cached per-hexagon Landsat tables
- `external_case/round10_domain_shift_matrix.py` — D0–D3 tests on 15 Landsat-8 dates
- `external_case/evaluate_landsat9_confirmatory.py` — Landsat-9 confirmation
- `external_case/round11_block_geometry.py` — holdout-shape robustness (1 km / 2 km blocks, origins, buffers)
- `tools/round11_analysis.py` — paired gaps, cluster bootstrap CIs, residual Moran's I, prediction intervals
- `tools/round11_planning_robustness.py` — planning check (boundary, walking threshold, heat persistence)
- `tools/round11_figures.py` — figures
- `external_case/fetch_selected_dates.py` — raw Landsat download (needs Planetary Computer access)
- `presentation/` — scripts that build the slide deck and its figures (`fig.py`). The two deck scripts are saved as `head.js.txt` and `body.js.txt` because Gmail blocks `.js` files; to use them, run `cat head.js.txt body.js.txt > build.js && node build.js` (needs pptxgenjs)

Python: see `requirements-lock-round11.txt` (numpy, pandas, scikit-learn, scipy, matplotlib).
