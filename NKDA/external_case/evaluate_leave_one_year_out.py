"""Stricter calendar-year transfer: no target-year LST from any acquisition."""
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score,mean_squared_error,roc_auc_score
R=Path(__file__).resolve().parents[1];F=['NDVI','NDBI','MNDWI']
sel=R/'data/selected_acquisitions_final.csv'
if not sel.exists():sel=R/'data/selected_acquisitions.csv'
S={}
for item in pd.read_csv(sel).item_id:
    day=item.split('_')[3];f=R/f'external_case/data/landsat_hex_LC08_{day}.csv'
    if not f.exists():continue
    d=pd.read_csv(f);S[day]=d[np.isfinite(d[['LST']+F]).all(axis=1)]
def rf():return RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1)
def norm(d):
    x=d[F].to_numpy();return (x-x.mean(axis=0))/(x.std(axis=0)+1e-6)
def fit(sources,test):
    x=np.vstack([norm(S[k]) for k in sources]);y=np.concatenate([(S[k].LST-S[k].LST.mean()).to_numpy() for k in sources]);return rf().fit(x,y).predict(norm(S[test]))
results=[]
for year in sorted(set(k[:4] for k in S)):
    source=[d for d in sorted(S) if d[:4]!=year];tests=[d for d in sorted(S) if d[:4]==year]
    if len(source)<3:continue
    # Source-only out-of-date residuals. Target-year sources are all excluded.
    residual={};historical={}
    for day in source:
        true=(S[day].LST-S[day].LST.mean()).to_numpy()
        for h,z in zip(S[day].hex_id,true):historical.setdefault(h,[]).append(z)
        inner=[d for d in source if d!=day];pr=fit(inner,day)
        for h,z in zip(S[day].hex_id,true-pr):residual.setdefault(h,[]).append(z)
    for day in tests:
        truth=(S[day].LST-S[day].LST.mean()).to_numpy();base=fit(source,day)
        climatology=np.array([np.mean(historical.get(h,[0])) for h in S[day].hex_id])
        hybrid=base+.5*np.array([np.mean(residual.get(h,[0])) for h in S[day].hex_id])
        hot=(truth>=np.quantile(truth,.8)).astype(int)
        for model,p in [('RF_z',base),('source_spatial_climatology',climatology),('RF_z_source_residual_hybrid',hybrid)]:
            results.append({'test_date':day,'test_year':year,'n_source_dates':len(source),
                 'model':model,'n_test':len(truth),'R2':r2_score(truth,p),
                 'RMSE_C':np.sqrt(mean_squared_error(truth,p)),
                 'AUROC':roc_auc_score(hot,p)})
    print('Held-out full year',year,'test_dates',len(tests),flush=True)
out=pd.DataFrame(results);out.to_csv(R/'outputs/tables/leave_one_year_out.csv',index=False)
print(out.groupby('model')[['R2','RMSE_C','AUROC']].mean().round(3).to_string())
