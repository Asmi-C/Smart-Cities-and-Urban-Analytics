"""Unsupervised source-to-target spectral-domain baselines on fixed three dates.

Only unlabeled target NDVI/NDBI/MNDWI are used to adapt predictors.
Absolute target LST and target date mean never enter training or adaptation.
"""
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error,r2_score
from scipy.linalg import fractional_matrix_power
R=Path(__file__).resolve().parents[1];D=R/'external_case/data'
dates={'2021':'20210324','2024':'20240401','2026':'20260322'}
f=['NDVI','NDBI','MNDWI'];d=None
for y,date in dates.items():
    t=pd.read_csv(D/f'landsat_hex_LC08_{date}.csv')
    t=t[['hex_id','LST']+f].rename(columns={v:f'{v}_{y}' for v in ['LST']+f})
    d=t if d is None else d.merge(t,on='hex_id')
d=d.loc[np.isfinite(d[[f'{v}_{y}' for y in dates for v in ['LST']+f]]).all(axis=1)]
def rf():return RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1)
def coral(xs,xt,reg=.05):
    # CORAL: whiten source spectral covariance then recolor with target unlabeled covariance.
    ms=xs.mean(0);mt=xt.mean(0);cs=np.cov(xs,rowvar=False)+reg*np.eye(xs.shape[1]);ct=np.cov(xt,rowvar=False)+reg*np.eye(xt.shape[1])
    return np.real((xs-ms)@fractional_matrix_power(cs,-.5)@fractional_matrix_power(ct,.5)+mt)
rows=[]
for held in dates:
    train=[y for y in dates if y!=held]
    src=np.vstack([d[[f'{v}_{y}' for v in f]].to_numpy() for y in train]); test=d[[f'{v}_{held}' for v in f]].to_numpy()
    sy=np.concatenate([d[f'LST_{y}'].to_numpy() for y in train]);yt=d[f'LST_{held}'].to_numpy()
    src_an=np.concatenate([d[f'LST_{y}'].to_numpy()-d[f'LST_{y}'].mean() for y in train]); y_an=yt-yt.mean()
    source_sc=StandardScaler().fit(src); target_sc=StandardScaler().fit(test)
    transforms={'raw':(src,test),
                'source_scaled':(source_sc.transform(src),source_sc.transform(test)),
                'unsupervised_domain_standardize':(source_sc.transform(src),target_sc.transform(test)),
                'CORAL_unlabeled_target':(coral(src,test),test)}
    for name,(xs,xt) in transforms.items():
        for targetname,targetsrc,targettest in [('absolute_C',sy,yt),('anomaly_C',src_an,y_an)]:
            pred=rf().fit(xs,targetsrc).predict(xt)
            rows.append({'heldout_date':held,'train_dates':'+'.join(train),'alignment':name,'target':targetname,
                         'n_hex':len(d),'RMSE':np.sqrt(mean_squared_error(targettest,pred)),'R2':r2_score(targettest,pred),
                         'source_only_target_labels':True,
                         'target_unlabeled_covariates_used':name.startswith('unsupervised') or name.startswith('CORAL'),
                         'target_LST_moments_in_predictor':False})
out=pd.DataFrame(rows);out.to_csv(R/'outputs/tables/unsupervised_domain_alignment.csv',index=False)
print(out.pivot_table(index=['heldout_date','target'],columns='alignment',values='R2').round(3).to_string())
