"""One-time cross-sensor test after dates/method are predeclared.

Use --acquire only for absent raw Landsat9 COGs (multiple gigabytes).
Never tune against the confirmatory outcomes.
"""
from pathlib import Path
import subprocess,sys,os
R=Path(__file__).resolve().parent
if '--acquire' in sys.argv:
    env=os.environ.copy();env['NKDA_SELECTION_FILE']='data/round10_landsat9_confirmatory_frozen.csv'
    subprocess.run([sys.executable,str(R/'external_case/fetch_selected_dates.py')],cwd=R,env=env,check=True)
subprocess.run([sys.executable,str(R/'external_case/evaluate_landsat9_confirmatory.py')],cwd=R,check=True)
subprocess.run([sys.executable,str(R/'tools/round10_l9_uncertainty_audit.py')],cwd=R,check=True)
