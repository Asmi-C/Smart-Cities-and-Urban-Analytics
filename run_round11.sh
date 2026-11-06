#!/usr/bin/env bash
# One command: replays Round-10 frozen experiments and runs Round-11 robustness, analysis and figures
# from the cached per-hexagon Landsat tables in external_case/data (no network needed).
# Raw scene re-acquisition: external_case/fetch_selected_dates.py (needs Planetary Computer access).
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-python}
$PY -I external_case/round10_domain_shift_matrix.py
$PY -I external_case/evaluate_landsat9_confirmatory.py
$PY -I external_case/round11_block_geometry.py
$PY -I tools/round11_analysis.py
$PY -I tools/round11_figures.py
$PY -I tools/round11_planning_robustness.py
sha256sum external_case/data/landsat_hex_*.csv > outputs/round11_input_checksums.sha256
echo "Round 11 replay complete"
