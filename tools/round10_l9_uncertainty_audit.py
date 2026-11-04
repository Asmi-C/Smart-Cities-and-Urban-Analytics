"""Empirical cross-sensor D3 interval audit using frozen L8 D3 residual quantiles.

Not a mathematically guaranteed conformal interval: source D3 folds are
dependent and Landsat9 has covariate/sensor shift. Never calibrate on L9 LST.
"""
from pathlib import Path
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];P=R/'outputs/tables'
src=pd.read_csv(P/'round10_joint_domain_predictions.csv')
dst=pd.read_csv(P/'round10_landsat9_confirmatory_predictions.csv')
dst=dst[(dst.regime=='D3')&(dst.context=='held_region')]
rows=[]
for model,a in src.groupby('model'):
    b=dst[dst.model==model]
    if not len(b):continue
    for nominal in [0.8,0.9,0.95]:
        width=float(np.quantile(np.abs(a.residual),nominal,method='higher'))
        for (date,block),g in b.groupby(['date','quadrant']):
            if len(g)<15:continue
            rows.append({'model':model,'date':date,'quadrant':block,'nominal_coverage':nominal,
                         'source_absolute_error_halfwidth_C':width,'observed_L9_coverage':np.mean(np.abs(g.truth_eval_only-g.prediction)<=width),
                         'full_interval_width_C':2*width,'n':len(g),'caveat':'Empirical L8 D3 residual quantiles; cross-sensor coverage not guaranteed'})
out=pd.DataFrame(rows);out.to_csv(P/'round10_l9_D3_uncertainty_coverage.csv',index=False)
print(out.groupby(['model','nominal_coverage']).observed_L9_coverage.agg(['mean','min','max']).round(3).to_string())
