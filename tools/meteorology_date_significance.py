"""Acquisition-level paired weather ablation; distinguish biases from forecast skill."""
from pathlib import Path
from itertools import product
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];F=R/'outputs/tables'
d=pd.read_csv(F/'meteorology_ablation.csv');pv=d.pivot(index='date',columns='model',values=['RMSE_C','date_mean_error_C'])
rmse_base=pv[('RMSE_C','source_mean_plus_spatial_climatology')].to_numpy()
rmse_new=pv[('RMSE_C','meteorology_plus_spatial_climatology')].to_numpy()
gain=rmse_base-rmse_new;n=len(gain);rng=np.random.default_rng(3)
byyear=pd.DataFrame({'year':pv.index.astype(str).str[:4], 'gain':gain}).groupby('year').gain.mean().to_numpy()
b=np.mean(rng.choice(byyear,size=(15000,len(byyear)),replace=True),axis=1)
sign=np.array(list(product([-1,1],repeat=len(byyear)))) if len(byyear)<=18 else None
record={'dates':n,'calendar_years':len(byyear),'mean_RMSE_reduction_C':gain.mean(),
        'dates_better':int((gain>0).sum()),'year_cluster_boot_CI_low_C':np.quantile(b,.025),
        'year_cluster_boot_CI_high_C':np.quantile(b,.975),
        'year_cluster_signflip_p':float(np.mean(np.abs((sign*byyear).mean(axis=1))>=abs(byyear.mean())-1e-14)) if sign is not None else np.nan,
        'mean_abs_date_bias_meteorology_C':np.mean(np.abs(pv[('date_mean_error_C','meteorology_plus_spatial_climatology')]))}
pd.DataFrame([record]).to_csv(F/'meteorology_date_significance.csv',index=False)
print(record)
