"""Replay Round-10 development-set domain-shift evaluation (no downloads)."""
from pathlib import Path
import os,subprocess,sys
R=Path(__file__).resolve().parent
def step(file,env=None):
    print('ROUND10',file,flush=True)
    subprocess.run([sys.executable,str(R/file)],cwd=R,env=env,check=True)
step('external_case/round10_domain_shift_matrix.py')
alt=os.environ.copy();alt['NKDA_TARGET_NORMALIZATION']='whole_scene'
step('external_case/round10_domain_shift_matrix.py',alt)
step('tools/round10_rank_shift_analysis.py')
step('tools/round10_error_decomposition.py')
step('tools/round10_shift_severity.py')
step('tools/boundary_perturbation.py')
step('tools/round10_stable_interior.py')
print('Round-10 exploratory replay complete; untouched confirmation NOT performed.')
