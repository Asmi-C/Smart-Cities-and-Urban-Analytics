"""Round-7 replay; canonical Round-6 code and results remain untouched.

Without flags, runs cached-input scientific analyses. With `--acquire`, refresh
the fixed-policy STAC inventory, download any selected missing COGs, and
retrieve historical ERA5-Land context before evaluating. No speculative data.
"""
from pathlib import Path
import subprocess,sys,pandas as pd
R=Path(__file__).resolve().parent
def run(script):
    print('REPLAY:',script,flush=True)
    subprocess.run([sys.executable,str(R/script)],check=True,cwd=R)
if '--acquire' in sys.argv:
    for script in ['external_case/discover_dates.py','external_case/fetch_selected_dates.py','external_case/fetch_meteorology.py']:run(script)
run('run_round6_research.py')
for script in ['tools/boundary_perturbation.py','external_case/evaluate_domain_alignment.py']:
    run(script)
selected=pd.read_csv(R/'data/selected_acquisitions.csv').item_id.tolist()
complete=all((R/f'external_case/data/landsat_hex_{item[:4]}_{item.split("_")[3]}.csv').exists() for item in selected)
if complete:
    run('external_case/evaluate_six_date.py')
    run('external_case/evaluate_spatiotemporal_holdout.py')
    run('external_case/six_date_persistence.py')
    run('tools/build_validation_matrix.py')
    if (R/'data/acquisition_context.csv').exists():
        ctx=pd.read_csv(R/'data/acquisition_context.csv')
        if len(ctx)>=len(selected) and ctx.status.eq('verified_archive_response').all():
            run('external_case/evaluate_weather_decomposition.py')
        else:print('Weather-aware model BLOCKED: no complete independently acquired weather records',flush=True)
else:
    print('Six-date experiment BLOCKED: selected Landsat scenes not all processed; run --acquire',flush=True)
print('Round-7 replay completed',flush=True)
