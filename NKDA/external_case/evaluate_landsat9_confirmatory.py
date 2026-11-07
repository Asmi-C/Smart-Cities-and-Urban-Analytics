"""One-time frozen Landsat9 test; trained on 15 pre-existing Landsat8 dates.

Do not alter models/splits/thresholds in response to these results. Test LST
used only for evaluation mean/threshold and scoring, never fitting or tuning.
"""
from pathlib import Path
import sqlite3
import numpy as np,pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor,HistGradientBoostingRegressor
from sklearn.metrics import r2_score,mean_squared_error,roc_auc_score
R=Path(__file__).resolve().parents[1];F=['NDVI','NDBI','MNDWI']
db=sqlite3.connect(R/'outputs/data/hex_results.gpkg')
xy=pd.read_sql_query('SELECT h.hex_id,(r.minx+r.maxx)/2 x,(r.miny+r.maxy)/2 y FROM hex_results h JOIN rtree_hex_results_geom r ON h.fid=r.id',db).set_index('hex_id');db.close()
xy['quad']=(xy.x>xy.x.median()).astype(int)*2+(xy.y>xy.y.median()).astype(int)
c=xy[['x','y']].to_numpy();mu=c.mean(0);sig=c.std(0)
def norm(d,geo=False):
    f=d[F].to_numpy(float);f=(f-f.mean(0))/(f.std(0)+1e-6)
    if geo:f=np.column_stack([f,(d[['x','y']].to_numpy()-mu)/(sig+1e-6)])
    return f
def forest():return RandomForestRegressor(n_estimators=45,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=2)
def fit_model(name):
    return {'ridge_z':lambda:Ridge(alpha=10.0),'RF_z':forest,
        'HGB_z':lambda:HistGradientBoostingRegressor(max_iter=80,min_samples_leaf=10,learning_rate=.07,random_state=42),
        'RF_z_coords':forest}[name]()
models=['ridge_z','RF_z','HGB_z','RF_z_coords']
src={}
for item in pd.read_csv(R/'data/selected_acquisitions_final.csv').item_id:
    date=item.split('_')[3];p=R/f'external_case/data/landsat_hex_LC08_{date}.csv'
    if p.exists():
        d=pd.read_csv(p);d=d[np.isfinite(d[['LST']+F]).all(axis=1)].join(xy,on='hex_id')
        if len(d)>=180:src[date]=d
assert len(src)==15,f'Frozen 15-source-date requirement failed: {len(src)}'
rows=[];preds=[];qa=[]
for item in pd.read_csv(R/'data/round10_landsat9_confirmatory_frozen.csv').item_id:
    date=item.split('_')[3];path=R/f'external_case/data/landsat_hex_LC09_{date}.csv'
    if not path.exists():
        qa.append({'date':date,'item_id':item,'status':'not_acquired','n_valid_hex':0});continue
    d=pd.read_csv(path);d=d[np.isfinite(d[['LST']+F]).all(axis=1)].join(xy,on='hex_id')
    if len(d)<180:
        qa.append({'date':date,'item_id':item,'status':'failed_frozen_180_hex_QA','n_valid_hex':len(d)});continue
    qa.append({'date':date,'item_id':item,'status':'passed_frozen_QA','n_valid_hex':len(d)})
    for regime in ['D2','D3']:
        for block in ([-1] if regime=='D2' else list(range(4))):
            test=d if block<0 else d[d.quad==block]
            if len(test)<15:continue
            trains=[v if block<0 else v[v.quad!=block] for v in src.values()]
            trains=[v for v in trains if len(v)>=15]
            yy=np.concatenate([v.LST.to_numpy()-v.LST.mean() for v in trains])
            truth=test.LST.to_numpy()-d.LST.mean() # evaluation only
            hot=(test.LST.to_numpy()>=d.LST.quantile(.8)).astype(int)
            for context in (['whole_scene'] if regime=='D2' else ['held_region','whole_scene']):
                view=d if context=='whole_scene' else test
                for model in models:
                    geo=model.endswith('coords')
                    xx=np.vstack([norm(v,geo) for v in trains]);tt=norm(view,geo)
                    if context=='whole_scene' and block>=0:
                        import pandas as pd
                        # d is non-reset-index after QA; align by hex_id, never by accidental row order.
                        lookup={h:i for i,h in enumerate(view.hex_id)}
                        tt=tt[[lookup[h] for h in test.hex_id]]
                    prediction=fit_model(model).fit(xx,yy).predict(tt)
                    auc=roc_auc_score(hot,prediction) if len(np.unique(hot))>1 else np.nan
                    rows.append({'date':date,'sensor':'Landsat9','regime':regime,'held_quad':block,'unlabeled_target_context':context,'model':model,'n_test':len(test),
                                 'R2':r2_score(truth,prediction),'RMSE':np.sqrt(mean_squared_error(truth,prediction)),'hotspot_AUROC':auc})
                    for hid,t,p in zip(test.hex_id,truth,prediction):preds.append({'date':date,'regime':regime,'quadrant':block,'context':context,'model':model,'hex_id':hid,'truth_eval_only':t,'prediction':p})
    print('Frozen L9 scored',date,'n',len(d),flush=True)
O=R/'outputs/tables';pd.DataFrame(qa).to_csv(O/'round10_landsat9_QA_manifest.csv',index=False)
pd.DataFrame(rows).to_csv(O/'round10_landsat9_confirmatory.csv',index=False)
pd.DataFrame(preds).to_csv(O/'round10_landsat9_confirmatory_predictions.csv',index=False)
if rows:
    z=pd.DataFrame(rows);print(z.groupby(['regime','unlabeled_target_context','model'])[['R2','RMSE','hotspot_AUROC']].mean().round(3))
print(pd.DataFrame(qa).to_string(index=False))
