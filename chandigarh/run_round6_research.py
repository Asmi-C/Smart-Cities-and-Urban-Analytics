"""One-command replay of Round-6 incremental analyses from cached canonical data.

`python run_round6_research.py` recomputes nested spatial selection, GP residuals,
relative transfer and planning audit. Set NKDA_FETCH_LANDSAT=1 to perform
cached/verified-HTTPS satellite acquisition before replay (large downloads).
The original broader GEE/OSM extraction remains a separately authenticated step.
"""
from pathlib import Path
import subprocess,sys,os
R=Path(__file__).resolve().parent
jobs=[]
if os.environ.get('NKDA_FETCH_LANDSAT')=='1':jobs+=['external_case/temporal_landsat.py']
jobs+=['run_nested_spatial.py','run_gp_residual.py','external_case/evaluate_temporal.py',
       'external_case/evaluate_three_periods.py','external_case/evaluate_relative_transfer.py',
       'external_case/spatial_bootstrap_relative.py',
       'tools/merge_access_exposure.py']
for job in jobs:
    print('REPLAY',job,flush=True)
    subprocess.run([sys.executable,str(R/job)],cwd=R,check=True)
print('Round-6 cached-input replay succeeded:',len(jobs),'stages')
