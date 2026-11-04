"""Descriptive crossed date, region, and interaction residual-variance ANOVA.

Not a spatially independent random-effects likelihood fit. Each pooled D3
prediction is grouped by acquisition and held geographical quadrant.
"""
from pathlib import Path
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];p=R/'outputs/tables'
d=pd.read_csv(p/'round10_joint_domain_predictions.csv')
rows=[]
for model,g in d.groupby('model'):
    e=g.residual.to_numpy();mean=e.mean();n=len(g);ss=((e-mean)**2).sum()
    day=g.groupby('held_date').residual.agg(['mean','size']);quad=g.groupby('held_quadrant').residual.agg(['mean','size'])
    # Sequential, nonorthogonal weighted decomposition: first date, then block on date-centered residuals.
    temp=g.copy();temp['date_dev']=temp.held_date.map(day['mean'])-mean
    after_date=temp.residual-mean-temp.date_dev
    quad2=after_date.groupby(temp.held_quadrant).mean();temp['region_dev']=temp.held_quadrant.map(quad2)
    after_region=after_date-temp.region_dev
    interaction=after_region.groupby([temp.held_date,temp.held_quadrant]).transform('mean')
    residual=after_region-interaction
    for source,vec in [('date',temp.date_dev),('region_given_date',temp.region_dev),('date_region_interaction',interaction),('within_domain',residual)]:
        rows.append({'model':model,'component':source,'sum_squared_component':float(np.sum(vec**2)),'fraction_of_raw_residual_SS_descriptive':float(np.sum(vec**2)/ss),'n_predictions':n})
pd.DataFrame(rows).to_csv(p/'error_variance_decomposition.csv',index=False)
print(pd.DataFrame(rows).pivot(index='model',columns='component',values='fraction_of_raw_residual_SS_descriptive').round(3))
