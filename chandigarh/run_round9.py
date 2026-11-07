"""Round-9 reviewer-gate replay on packaged Round-8 processed satellite features.

Exploratory joint spatial/time test can take several minutes; no raw downloads.
"""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parent
for script in [
    'external_case/evaluate_unseen_sites_dates.py',
    'tools/round9_unseen_site_inference.py',
    'tools/round9_spatial_weight_sensitivity.py',
    'tools/round9_scene_quality_audit.py',
    'tools/boundary_perturbation.py',
]:
    print('REPLAY',script,flush=True)
    subprocess.run([sys.executable,str(R/script)],cwd=R,check=True)
print('Round-9 reviewer-gated exploratory replay complete')
