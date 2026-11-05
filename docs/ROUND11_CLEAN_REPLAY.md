# Clean-environment replay (Round 11)

- **Environment:** fresh Python 3.13 virtualenv, with only numpy 2.5.4, pandas 3.1.0, scikit-learn 1.9.1, scipy 1.18.1 and matplotlib installed (`requirements-lock-round11.txt`). Linux, 2 CPUs.
- **Inputs:** the cached per-hexagon Landsat tables `external_case/data/landsat_hex_*.csv` (15 LC08 + 5 LC09 + 1 excluded LC08). SHA-256 hashes are in `outputs/round11_input_checksums.sha256`.
- **Commands:** `external_case/round10_domain_shift_matrix.py` took 41 s; `external_case/evaluate_landsat9_confirmatory.py` took 14 s.

## Agreement with the shipped Round-10 tables

- **Development matrix** (`domain_shift_model_matrix.csv`): largest absolute cell difference 0.0053 (in D1). For D2 and D3 the largest differences are 0.0014 and 0.0007; the D2−D3 gap differs by at most 0.0021.
- **Landsat-9 confirmation:** all 108 rows match. Ridge, RF and RF+coords are identical. HGB rows differ by up to 0.065 R² on single small folds, which moves HGB model means by at most 0.004. This is attributed to version-dependent histogram binning in HistGradientBoosting, and no conclusion changes.

## Not replayed here

Raw Landsat scene download and ERA5 retrieval. Planetary Computer and USGS were not reachable from this session (proxy-blocked); `external_case/fetch_selected_dates.py` is the route on a machine with access.

## One command

`bash run_round11.sh` reruns everything from the cached tables, then writes the Round-11 tables and figures.

## File convention

Shipped Round-10 tables are kept unchanged, and the paper cites them. Replay outputs sit beside them as `*_r11replay.csv`. Running `run_round11.sh` regenerates the Round-10 tables in place; expect the HGB third-decimal drift described above.
