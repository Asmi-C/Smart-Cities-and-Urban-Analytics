"""Fixed-location sensitivity test; avoids cross-date clear-mask composition changes."""
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score,mean_squared_error,roc_auc_score
R=Path(__file__).resolve().parents[1];sel=R/'data/selected_acquisitions_final.csv'
if not sel.exists():sel=R/'data/selected_acquisitions.csv'
items=pd.read_csv(sel).item_id.tolist(); F=['NDVI','NDBI','MNDWI'];A={}
for item in items:
    day=item.split('_')[3];f=R/f'external_case/data/landsat_hex_LC08_{day}.csv'
    if not f.exists():continue
    z=pd.read_csv(f).set_index('hex_id');A[day]=z[np.isfinite(z[['LST']+F]).all(axis=1)]
common=set.intersection(*(set(z.index) for z in A.values()))
if len(common)<80:print('BLOCKED: only',len(common),'common hexes across',len(A),'dates');raise SystemExit(0)
common=sorted(common);records=[]
for held in sorted(A):
    source=[k for k in A if k!=held];test=A[held].loc[common];truth=test.LST.to_numpy()-test.LST.mean()
    xs=np.vstack([(A[k].loc[common,F]-A[k].loc[common,F].mean())/(A[k].loc[common,F].std(ddof=0)+1e-6) for k in source]);
    xt=((test[F]-test[F].mean())/(test[F].std(ddof=0)+1e-6)).to_numpy()
    yy=np.concatenate([(A[k].loc[common].LST-A[k].loc[common].LST.mean()).to_numpy() for k in source])
    rf=RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1)
    pred=rf.fit(xs,yy).predict(xt)
    history=np.mean(np.vstack([(A[k].loc[common].LST-A[k].loc[common].LST.mean()).to_numpy() for k in source]),axis=0)
    hot=(truth>=np.quantile(truth,.8)).astype(int)
    for model,p in [('z_RF',pred),('historical_climatology',history)]:
        records.append({'date':held,'model':model,'common_hexes':len(common),
            'R2':r2_score(truth,p),'RMSE_C':np.sqrt(mean_squared_error(truth,p)),
            'hotspot_AUROC':roc_auc_score(hot,p)})
out=pd.DataFrame(records);out.to_csv(R/'outputs/tables/common_support_temporal_transfer.csv',index=False)
print('Common support',len(common),'dates',len(A));print(out.groupby('model')[['R2','RMSE_C','hotspot_AUROC']].mean())
