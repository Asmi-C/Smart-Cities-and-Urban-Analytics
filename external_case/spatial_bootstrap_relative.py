"""Conditional geographic-block bootstrap on frozen temporal predictions.

Not independent date sampling; no claims of population-level temporal certainty.
"""
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd
from sklearn.metrics import r2_score
from scipy.stats import spearmanr
R=Path(__file__).resolve().parents[1]
z=pd.read_csv(R/'outputs/tables/temporal_relative_predictions.csv')
g=gpd.read_file(R/'outputs/data/hex_results.gpkg').to_crs(32643).set_index('hex_id')
rows=[]
for year in sorted(z.test_year.unique()):
    d=z[z.test_year==year].reset_index(drop=True)
    gg=g.loc[d.hex_id];xy=np.c_[gg.geometry.centroid.x,gg.geometry.centroid.y]
    blocks=np.floor((xy-xy.min(0))/1000).astype(int);grp=blocks[:,0]*10000+blocks[:,1]
    unique=np.unique(grp);ix={b:np.where(grp==b)[0] for b in unique};rng=np.random.default_rng(1412)
    r2=[];rho=[]
    for _ in range(1500):
        draws=rng.choice(unique,len(unique),replace=True)
        ii=np.concatenate([ix[b] for b in draws])
        if len(ii)<20 or np.var(d.actual_anomaly_C.iloc[ii])<1e-5:continue
        yy=d.actual_anomaly_C.to_numpy()[ii]; pp=d.pred_anomaly_C.to_numpy()[ii]
        r2.append(r2_score(yy,pp));rho.append(spearmanr(yy,pp).statistic)
    rows.append({'test_year':year,'n_hex':len(d),'n_geographic_blocks':len(unique),
                 'block_bootstrap_draws':len(r2),
                 'anomaly_R2':r2_score(d.actual_anomaly_C,d.pred_anomaly_C),
                 'conditional_bootstrap_R2_lower_95':np.quantile(r2,.025),
                 'conditional_bootstrap_R2_upper_95':np.quantile(r2,.975),
                 'anomaly_Spearman':spearmanr(d.actual_anomaly_C,d.pred_anomaly_C).statistic,
                 'conditional_bootstrap_Spearman_lower_95':np.quantile(rho,.025),
                 'conditional_bootstrap_Spearman_upper_95':np.quantile(rho,.975),
                 'warning':'Frozen-prediction geography bootstrap; not uncertainty across unseen dates'})
pd.DataFrame(rows).to_csv(R/'outputs/tables/relative_transfer_spatial_bootstrap.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
