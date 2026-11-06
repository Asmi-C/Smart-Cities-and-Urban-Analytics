"""Four distinct source-safe domain shifts across four fixed model families.

Experimental matrix on repeatedly examined development acquisitions, NOT an
untouched confirmatory evaluation. Source date means exclude held geographic
regions. Test-date mean and hotspot threshold are used for scoring only.
"""
from pathlib import Path
import os
import sqlite3
import numpy as np,pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor,HistGradientBoostingRegressor
from sklearn.metrics import r2_score,mean_squared_error,roc_auc_score
R=Path(__file__).resolve().parents[1]
F=['NDVI','NDBI','MNDWI'];rng=np.random.default_rng(42)
cx=sqlite3.connect(R/'outputs/data/hex_results.gpkg')
xy=pd.read_sql_query('SELECT h.hex_id,(r.minx+r.maxx)/2 x,(r.miny+r.maxy)/2 y FROM hex_results h JOIN rtree_hex_results_geom r ON h.fid=r.id',cx).set_index('hex_id');cx.close()
xy['quadrant']=(xy.x>xy.x.median()).astype(int)*2+(xy.y>xy.y.median()).astype(int)
scenes=pd.read_csv(R/'data/selected_acquisitions_final.csv').item_id
A={}
for name in scenes:
    day=name.split('_')[3];p=R/f'external_case/data/landsat_hex_LC08_{day}.csv'
    if p.exists():
        d=pd.read_csv(p);d=d[np.isfinite(d[['LST']+F]).all(axis=1)].join(xy,on='hex_id')
        if len(d)>=180:A[day]=d.reset_index(drop=True)
cc=xy[['x','y']].to_numpy();cmean=cc.mean(0);csd=cc.std(0)
def feature(d,coords=False):
    q=d[F].to_numpy(dtype=float);q=(q-q.mean(0))/(q.std(0)+1e-6)
    if coords:q=np.column_stack([q,((d[['x','y']].to_numpy()-cmean)/(csd+1e-6))])
    return q
def estimator(k):
    if k=='ridge_z':return Ridge(alpha=10.0)
    if k=='RF_z':return RandomForestRegressor(n_estimators=45,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=2)
    if k=='HGB_z':return HistGradientBoostingRegressor(max_iter=80,min_samples_leaf=10,learning_rate=.07,random_state=42)
    if k=='RF_z_coords':return RandomForestRegressor(n_estimators=45,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=2)
    raise ValueError(k)
MODELS=['ridge_z','RF_z','HGB_z','RF_z_coords']
WHOLE_SCENE=os.environ.get('NKDA_TARGET_NORMALIZATION','held_region')=='whole_scene'
rows=[];domainpred=[]
def eval_split(regime,day,block,train_dates,test_idx,filter_block):
    test=A[day].iloc[test_idx];n=len(test)
    if n<15:return
    datasets=[]
    for src_day in train_dates:
        ds=A[src_day]
        if filter_block is not None:ds=ds[ds.quadrant!=filter_block]
        if regime=='D0' and src_day==day:ds=ds.iloc[train_idx[day]]
        if len(ds)<15:continue
        datasets.append(ds)
    if not datasets:return
    # All source-date anomaly means are computed from source training units only.
    tr_y=np.concatenate([d.LST.to_numpy()-d.LST.mean() for d in datasets])
    truth=test.LST.to_numpy()-A[day].LST.mean() # test labels used ONLY in scoring
    hot=(test.LST.to_numpy()>=A[day].LST.quantile(.8)).astype(int)
    train_x0=np.vstack([feature(d) for d in datasets]);train_xc=np.vstack([feature(d,True) for d in datasets])
    # For genuine geographic shift, target z-statistics are based on the
    # *held geographic domain only*; otherwise full-township target context
    # would silently supply an easier transductive reference distribution.
    if regime in ('D1','D3') and not WHOLE_SCENE:
        test_x0=feature(test);test_xc=feature(test,True)
    else:
        test_x0=feature(A[day])[test_idx];test_xc=feature(A[day],True)[test_idx]
    for name in MODELS:
        usecoord=name.endswith('coords');xx=train_xc if usecoord else train_x0;tt=test_xc if usecoord else test_x0
        predict=estimator(name).fit(xx,tr_y).predict(tt)
        rr=r2_score(truth,predict);rmse=np.sqrt(mean_squared_error(truth,predict))
        auc=roc_auc_score(hot,predict) if len(np.unique(hot))==2 else np.nan
        rows.append({'regime':regime,'held_date':day,'year':day[:4],'held_quadrant':block,'model':name,'n_test':n,'R2':rr,'RMSE':rmse,'hotspot_AUROC':auc})
        if regime=='D3':
            domainpred.extend({'held_date':day,'held_quadrant':block,'hex_id':hid,'model':name,'true_anomaly':y,'prediction':p,'residual':y-p} for hid,y,p in zip(test.hex_id,truth,predict))

train_idx={}
for day,d in A.items():
    ids=np.arange(len(d));np.random.default_rng(42+int(day[-2:])).shuffle(ids);train_idx[day]=ids[:int(.8*len(ids))]
for day in sorted(A):
    # D0: same scene, random location split. Training date labels only on 80%.
    test_idx=np.setdiff1d(np.arange(len(A[day])),train_idx[day])
    eval_split('D0',day,-1,[day],test_idx,None)
    # D1: same date, unseen geo quadrant, source date is familiar.
    for b in range(4):
        ii=np.flatnonzero(A[day].quadrant.to_numpy()==b)
        eval_split('D1',day,b,[day],ii,b)
    # D2: entirely unseen date, familiar geographic support.
    eval_split('D2',day,-1,sorted(set(A)-{day}),np.arange(len(A[day])),None)
    # D3: date and geography both unseen, no historic target sites.
    for b in range(4):
        ii=np.flatnonzero(A[day].quadrant.to_numpy()==b)
        eval_split('D3',day,b,sorted(set(A)-{day}),ii,b)
    print('Finished date',day,flush=True)
suffix='_whole_scene_transductive' if WHOLE_SCENE else ''
out=pd.DataFrame(rows);out.to_csv(R/f'outputs/tables/domain_shift_model_matrix_long{suffix}.csv',index=False)
summary=out.groupby(['model','regime']).agg(R2=('R2','mean'),RMSE=('RMSE','mean'),AUROC=('hotspot_AUROC','mean'),folds=('R2','size')).reset_index()
wide=summary.pivot(index='model',columns='regime',values='R2');
for r in ['D0','D1','D2','D3']:
    if r not in wide:wide[r]=np.nan
wide=wide[['D0','D1','D2','D3']]
for metric,label in [('RMSE','D3_RMSE'),('AUROC','D3_AUROC')]:
    wide[label]=summary[summary.regime=='D3'].set_index('model')[metric]
wide['D2_minus_D3_optimism']=wide.D2-wide.D3
wide.to_csv(R/f'outputs/tables/domain_shift_model_matrix{suffix}.csv')
pd.DataFrame(domainpred).to_csv(R/f'outputs/tables/round10_joint_domain_predictions{suffix}.csv',index=False)
print(wide.round(4).to_string())
