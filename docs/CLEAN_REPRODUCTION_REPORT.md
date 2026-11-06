# Round-9 reproduction report

**Scope achieved:** existing Round-8 full replay previously completed with its included processed Landsat hex CSVs; Round-9 scripts executed successfully in the current scientific Python environment:

```bash
python external_case/evaluate_unseen_sites_dates.py
python tools/round9_unseen_site_inference.py
python tools/round9_spatial_weight_sensitivity.py
python tools/round9_scene_quality_audit.py
python tools/boundary_perturbation.py
```

Verified outputs: `outputs/tables/unseen_site_unseen_date.csv` (40 block/date folds × three methods), `unseen_site_inference.csv`, `residual_weights_sensitivity.csv` (15 dates × 2 RF models × 4 weights), `round9_scene_quality_audit.csv` (15 dates), `round9_scene_quality_associations.csv`, `boundary_translation_sensitivity.csv` and `boundary_stable_interior.csv`.

**NOT passed as a clean, from-zero, one-command reproduction:** multi-gigabyte Landsat TIFF reacquisition requires external signed asset availability; an entirely fresh Docker/Conda environment has not been independently rebuilt; official boundary, verified raw OSM road graph/POIs and second-population layer are unavailable. The archive provides processed public-derived hex data and methods, not an authenticated raw-data supply chain for planning evidence. No 5/5 reproducibility claim is made.

Scientific caveat: the new geographic/date test uses 15 dates already explored in earlier rounds. It is a new blocking design but is **not an untouched independently confirmed model-selection endpoint**.
