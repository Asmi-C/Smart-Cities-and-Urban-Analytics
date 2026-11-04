"""Strict chronological prediction: training acquisition < test acquisition, no future labels."""
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score,mean_squared_error,roc_auc_score,average_precision_score
R=Path(__file__).resolve().parents[1];sel=R/'data/selected_acquisitions_final.csv'
if not sel.exists():sel=R/'data/selected_acquisitions.csv'
F=['NDVI','NDBI','MNDWI'];S={}
for item in pd.read_csv(sel).item_id:
    date=item.split('_')[3];p=R/f'external_case/data/landsat_hex_LC08_{date}.csv'
    if p.exists():
        x=pd.read_csv(p);S[date]=x[np.isfinite(x[['LST']+F]).all(axis=1)]
def normalized(x):
    v=x[F].to_numpy();return (v-v.mean(0))/(v.std(0)+1e-6)
results=[]
for held in sorted(S):
    # No within-year source acquisitions: avoids same-year environmental information.
    sources=[d for d in sorted(S) if d[:4]<held[:4]]
    if len(sources)<3:continue
    test=S[held];truth=(test.LST-test.LST.mean()).to_numpy()
    xs=np.vstack([normalized(S[d]) for d in sources]);y=np.concatenate([(S[d].LST-S[d].LST.mean()).to_numpy() for d in sources]);
    pred=RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1).fit(xs,y).predict(normalized(test))
    history={};freq={}
    for day in sources:
        src=S[day];an=(src.LST-src.LST.mean()).to_numpy();hot=(src.LST>=src.LST.quantile(.8)).astype(int)
        for h,v,z in zip(src.hex_id,an,hot):history.setdefault(h,[]).append(v);freq.setdefault(h,[]).append(z)
    climatology=np.array([np.mean(history.get(h,[0])) for h in test.hex_id]);p_hot=np.array([np.mean(freq.get(h,[.2])) for h in test.hex_id]);true_hot=(truth>=np.quantile(truth,.8)).astype(int)
    for name,p in [('z_RF',pred),('historical_site_climatology',climatology)]:
        results.append({'test_date':held,'n_source_dates_prior_years':len(sources),'model':name,
          'n_test':len(test),'R2':r2_score(truth,p),'RMSE_C':np.sqrt(mean_squared_error(truth,p)),
          'hotspot_AUROC':roc_auc_score(true_hot,p)})
    results.append({'test_date':held,'n_source_dates_prior_years':len(sources),'model':'historical_hotspot_frequency',
       'n_test':len(test),'hotspot_AUROC':roc_auc_score(true_hot,p_hot),
       'hotspot_PR_AUC':average_precision_score(true_hot,p_hot)})
out=pd.DataFrame(results);out.to_csv(R/'outputs/tables/chronological_forward_transfer.csv',index=False)
print('Chronological held dates',out.test_date.nunique());print(out.groupby('model')[['R2','RMSE_C','hotspot_AUROC']].mean().round(3).to_string())
