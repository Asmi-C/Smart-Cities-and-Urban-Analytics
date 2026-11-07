"""Year-clustered exploratory inference for joint geography/date results."""
from itertools import product
from pathlib import Path
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1]
d=pd.read_csv(R/'outputs/tables/unseen_site_unseen_date.csv')
p=d.pivot_table(index=['held_date','year','held_quadrant'],columns='model',values=['R2','RMSE','hotspot_AUROC'])
rng=np.random.default_rng(41);rows=[]
for metric in ['R2','RMSE','hotspot_AUROC']:
    for b in ['normalized_RF','historical_climatology_IDW']:
        t=p[metric][['RF_plus_spatial_residual_IDW',b]].dropna()
        delta=t['RF_plus_spatial_residual_IDW']-t[b]
        y=delta.groupby(level='year').mean().to_numpy()
        signs=np.array(list(product([-1,1],repeat=len(y))))
        null=np.abs((signs*y).mean(1));obs=np.abs(y.mean())
        bootstrap=rng.choice(y,size=(20000,len(y)),replace=True).mean(1)
        rows.append({'endpoint':metric,'comparison':'hybrid_minus_'+b,'n_geo_date_folds':len(delta),
                     'n_years':len(y),'mean_paired_delta_folds':delta.mean(),
                     'mean_paired_delta_equal_years':y.mean(),'year_cluster_signflip_p':np.mean(null>=obs-1e-14),
                     'year_cluster_boot_CI_low':np.quantile(bootstrap,.025),
                     'year_cluster_boot_CI_high':np.quantile(bootstrap,.975),
                     'n_folds_hybrid_better':int((delta>0).sum()) if metric!='RMSE' else int((delta<0).sum())})
out=pd.DataFrame(rows);out.to_csv(R/'outputs/tables/unseen_site_inference.csv',index=False)
print(out.to_string(index=False))
