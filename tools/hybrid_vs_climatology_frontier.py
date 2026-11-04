"""Strongest-baseline paired test; prediction error vs residual Moran are separate endpoints."""
from pathlib import Path
from itertools import product
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];T=R/'outputs/tables'
d=pd.read_csv(T/'date_level_method_comparison_long.csv');pivot=d.pivot(index='date',columns='model',values=['R2','RMSE','Moran_I','hotspot_AUROC_from_regression'])
old=set(pd.read_csv(R/'data/selected_acquisitions.csv').item_id.str.split('_').str[3]);rng=np.random.default_rng(71);rows=[]
for subset in ['all_15_dates','new_additions_only']:
    ids=pivot.index.astype(str);which=np.ones(len(ids),bool) if subset=='all_15_dates' else ~ids.isin(old)
    selected=pivot.iloc[which]
    if len(selected)<3:continue
    for metric in ['R2','RMSE','Moran_I','hotspot_AUROC_from_regression']:
        delta=(selected[(metric,'RF_z_plus_source_spatial_bias')]-selected[(metric,'source_spatial_climatology')]).to_numpy()
        year=pd.DataFrame({'year':selected.index.astype(str).str[:4],'delta':delta}).groupby('year').delta.mean().to_numpy()
        sign=np.array(list(product([-1,1],repeat=len(year))))
        boot=np.mean(rng.choice(year,size=(20000,len(year)),replace=True),axis=1)
        rows.append({'subset':subset,'metric':'hybrid_minus_climatology_'+metric,'dates':len(delta),'years':len(year),
                     'mean_delta':delta.mean(),'positive_dates':int((delta>0).sum()),
                     'year_cluster_boot_CI_low':np.quantile(boot,.025),'year_cluster_boot_CI_high':np.quantile(boot,.975),
                     'year_signflip_p':np.mean(abs((sign*year).mean(axis=1))>=abs(year.mean())-1e-14)})
out=pd.DataFrame(rows);out.to_csv(T/'hybrid_vs_climatology_pareto.csv',index=False)
print(out.round(4).to_string(index=False))
