"""Round-8 exact replay. --acquire downloads multi-GB satellite sources."""
from pathlib import Path
import subprocess,sys,os
R=Path(__file__).resolve().parent
def run(name,env=None):
    print('RUN',name,flush=True)
    subprocess.run([sys.executable,str(R/name)],cwd=R,check=True,env=env)
if '--acquire' in sys.argv:
    run('external_case/discover_expanded_dates.py')
    state=os.environ.copy();state['NKDA_SELECTION_FILE']='data/selected_acquisitions_final_catalog.csv'
    run('external_case/fetch_selected_dates.py',state)
    run('external_case/fetch_meteorology.py',state)
run('external_case/finalize_acquisitions.py')
if not (R/'data/selected_acquisitions_final.csv').exists():
    print('WARNING: expanded cohort incomplete; replay only original six dates')
run('external_case/evaluate_domain_generalization.py')
run('external_case/residual_persistence_audit.py')
run('external_case/evaluate_weather_expanded.py')
run('tools/round8_frontier.py')
run('tools/hotspot_date_significance.py')
run('tools/hotspot_calibration.py')
run('tools/meteorology_date_significance.py')
run('external_case/evaluate_common_support.py')
run('external_case/evaluate_leave_one_year_out.py')
run('external_case/evaluate_forward_temporal.py')
run('external_case/expanded_persistent_exposure.py')
run('tools/confirmatory_new_dates.py')
run('tools/hybrid_vs_climatology_frontier.py')
run('tools/round8_moran_permutations.py')
run('tools/plot_round8.py')
print('Round-8 replay completed')
