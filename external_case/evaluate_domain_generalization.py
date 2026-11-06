"""Source-only acquisition transfer. One score per held-out date; no test LST in fitting.

Primary endpoint frozen in docs/FINAL_METHOD_PROTOCOL.md. Domain-wise source
residuals are OUT-OF-DATE predictions from nested leave-one-source-date-out.
"""
from pathlib import Path
import os, sqlite3, time
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import spearmanr, wilcoxon
from sklearn.ensemble import RandomForestRegressor,RandomForestClassifier
from sklearn.metrics import r2_score,mean_squared_error,roc_auc_score,average_precision_score,brier_score_loss

R=Path(__file__).resolve().parents[1]; F=['NDVI','NDBI','MNDWI']
selected=R/'data/selected_acquisitions_final.csv'
if not selected.exists():selected=R/'data/selected_acquisitions.csv'
scenes=pd.read_csv(selected).item_id.tolist(); A={}
for item in scenes:
    date=item.split('_')[3]; f=R/f'external_case/data/landsat_hex_LC08_{date}.csv'
    if not f.exists():continue
    d=pd.read_csv(f); d=d[np.isfinite(d[['LST']+F]).all(axis=1)].copy()
    if len(d)>=180:A[date]=d.reset_index(drop=True)
if len(A)<5:raise ValueError('Need at least 5 acquired date domains')

# GeoPackage rtree footprint centres; does not require optional GIS packages.
con=sqlite3.connect(R/'outputs/data/hex_results.gpkg')
coords=pd.read_sql_query('SELECT h.hex_id, (r.minx+r.maxx)/2 AS x,(r.miny+r.maxy)/2 AS y FROM hex_results h JOIN rtree_hex_results_geom r ON h.fid=r.id',con).set_index('hex_id')
con.close()
def forest():return RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1)
def classification():return RandomForestClassifier(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1)
def norm(x,ref):return (x-ref.mean(0))/(ref.std(0)+1e-6)
def prep(sources, target,normalized):
    xs=np.vstack([A[k][F].to_numpy() for k in sources]); ys=np.concatenate([A[k].LST.to_numpy()-A[k].LST.mean() for k in sources]);
    xt=A[target][F].to_numpy()
    if normalized:
        xs=np.vstack([norm(A[k][F].to_numpy(),A[k][F].to_numpy()) for k in sources]);xt=norm(xt,xt)
    return xs,ys,xt
def spatial_i(residual,ids):
    c=coords.loc[ids][['x','y']].to_numpy();n=len(c)
    if n<20:return np.nan
    nn=cKDTree(c).query(c,k=9)[1][:,1:];z=np.asarray(residual)-np.mean(residual)
    return float(np.sum(z[:,None]*z[nn])/(8*np.sum(z*z))) if np.sum(z*z)>0 else np.nan
def metrics(y,p):return {'R2':r2_score(y,p),'RMSE':np.sqrt(mean_squared_error(y,p)),'Moran_I':spatial_i(y-p,ids)}

rows=[];preds=[];interval=[];stats=[];hotspot_pred=[]
for target in sorted(A):
    timer=time.perf_counter(); model_time={}
    sources=sorted(set(A)-{target});test=A[target]; ids=test.hex_id.tolist();truth=test.LST.to_numpy()-test.LST.mean()
    models={}; calibration={};
    for normal,name in [(False,'RF_raw'),(True,'RF_zsource_ztarget')]:
        start=time.perf_counter()
        xs,ys,xt=prep(sources,target,normal)
        model=forest().fit(xs,ys);models[name]=model.predict(xt)
        model_time[name]=time.perf_counter()-start
    # Strong simple spatial memory comparator, trained only on historical dates.
    anomaly_history={}
    for day in sources:
        source=A[day]; delta=source.LST.to_numpy()-source.LST.mean()
        for h,e in zip(source.hex_id,delta):anomaly_history.setdefault(h,[]).append(e)
    models['source_spatial_climatology']=np.array([np.mean(anomaly_history.get(h,[0])) for h in ids])
    model_time['source_spatial_climatology']=time.perf_counter()-timer-sum(model_time.values())
    # Cross-date source-only out-of-domain residual climatology and conformal errors.
    residuals={};date_calib=[]
    for calib in sources:
        inner=[k for k in sources if k!=calib]
        xs,ys,xv=prep(inner,calib,True)
        pv=forest().fit(xs,ys).predict(xv)
        dv=A[calib];err=(dv.LST.to_numpy()-dv.LST.mean())-pv
        for h,e in zip(dv.hex_id,err):residuals.setdefault(h,[]).append(e)
        date_calib.append(np.abs(err))
    adjustment=np.array([np.mean(residuals.get(h,[0])) for h in ids])*0.5
    models['RF_z_plus_source_spatial_bias']=models['RF_zsource_ztarget']+adjustment
    model_time['RF_z_plus_source_spatial_bias']=time.perf_counter()-timer
    for name,p in models.items():
        met=metrics(truth,p)
        threshold=np.quantile(truth,.8)
        hotspot=(truth>=threshold).astype(int)
        rows.append({'date':target,'model':name,'n_hex':len(ids),
                           'hotspot_AUROC_from_regression':roc_auc_score(hotspot,p),
                           'runtime_seconds_including_source_OOD_correction':model_time[name],**met})
        if name in ['RF_zsource_ztarget','RF_z_plus_source_spatial_bias']:
            for h,yhat,ytrue in zip(ids,p,truth):preds.append({'date':target,'hex_id':h,'model':name,'prediction_anomaly_C':yhat,'truth_anomaly_C':ytrue,'residual_C':ytrue-yhat})
    # Primary comparison is proposed spatial-bias model against best Round-7 z-transform baseline.
    # Split/date conformal are **empirical** under shift, no formal guarantee asserted.
    rawcal=np.concatenate(date_calib)
    for coverage in [.8,.9,.95]:
        for kind,width in [('pooled_source_dates',np.quantile(rawcal,coverage,method='higher')),
                           ('worst_source_date',max(np.quantile(z,coverage,method='higher') for z in date_calib))]:
            err=np.abs(truth-models['RF_zsource_ztarget'])
            interval.append({'date':target,'model':'RF_zsource_ztarget','calibration':kind,
                  'nominal':coverage,'empirical_coverage':np.mean(err<=width),'mean_interval_width_C':2*width})
    # Held-date hotspot labels are computed for evaluation only.
    hot=(test.LST.to_numpy()>=test.LST.quantile(.8)).astype(int)
    src_hot=np.concatenate([(A[k].LST.to_numpy()>=A[k].LST.quantile(.8)).astype(int) for k in sources])
    xx=np.vstack([norm(A[k][F].to_numpy(),A[k][F].to_numpy()) for k in sources]);tt=norm(test[F].to_numpy(),test[F].to_numpy())
    class_rf=classification().fit(xx,src_hot).predict_proba(tt)[:,1]
    source_freq={}
    for k in sources:
        d=A[k];h=(d.LST>=d.LST.quantile(.8)).astype(int)
        for hid,v in zip(d.hex_id,h):source_freq.setdefault(hid,[]).append(v)
    freq=np.array([np.mean(source_freq.get(hid,[np.mean(src_hot)])) for hid in ids])
    # Ranking the anomaly predictions is a label-free probability proxy via empirical source rank distribution.
    anom=models['RF_zsource_ztarget'];rank=np.argsort(np.argsort(anom)).astype(float)/(len(anom)-1)
    anom_prob=np.clip((rank-.6)/.4,0,1)
    for name,prob in [('source_hotspot_frequency',freq),('RF_hotspot_classifier',class_rf),('RF_anomaly_rank_proxy',anom_prob)]:
        stats.append({'date':target,'model':name,'n_hex':len(ids),'AUROC':roc_auc_score(hot,prob),
              'PR_AUC':average_precision_score(hot,prob),'Brier':brier_score_loss(hot,prob),
              'top20_precision':float(np.mean(hot[np.argsort(-prob)[:int(np.ceil(.2*len(hot)))]]))})
        for hid,y,pred in zip(ids,hot,prob):
            hotspot_pred.append({'date':target,'hex_id':hid,'model':name,'hotspot_truth_eval_only':y,
                                 'hotspot_probability':float(pred)})
    print('Completed held date',target,'n',len(ids),flush=True)

folder=R/'outputs/tables';df=pd.DataFrame(rows);df.to_csv(folder/'date_level_method_comparison_long.csv',index=False)
wide=df.pivot(index='date',columns='model',values=['R2','RMSE','Moran_I','hotspot_AUROC_from_regression'])
out=pd.DataFrame({'Date':wide.index,'Baseline':wide[('R2','RF_zsource_ztarget')].to_numpy(),
     'Proposed':wide[('R2','RF_z_plus_source_spatial_bias')].to_numpy(),
     'delta_R2':(wide[('R2','RF_z_plus_source_spatial_bias')]-wide[('R2','RF_zsource_ztarget')]).to_numpy(),
     'delta_RMSE':(wide[('RMSE','RF_z_plus_source_spatial_bias')]-wide[('RMSE','RF_zsource_ztarget')]).to_numpy(),
     'baseline_Moran':wide[('Moran_I','RF_zsource_ztarget')].to_numpy(),
     'proposed_Moran':wide[('Moran_I','RF_z_plus_source_spatial_bias')].to_numpy()})
out['delta_AUROC']= (wide[('hotspot_AUROC_from_regression','RF_z_plus_source_spatial_bias')]-
                     wide[('hotspot_AUROC_from_regression','RF_zsource_ztarget')]).to_numpy()
out['spatial_climatology_R2']=wide[('R2','source_spatial_climatology')].to_numpy()
out['delta_proposed_vs_climatology_R2']=out['Proposed']-out['spatial_climatology_R2']
out['spatial_climatology_RMSE']=wide[('RMSE','source_spatial_climatology')].to_numpy()
out.to_csv(folder/'date_level_method_comparison.csv',index=False)
pd.DataFrame(preds).to_csv(folder/'multi_date_residual_predictions.csv',index=False)
pd.DataFrame(interval).to_csv(folder/'date_conformal_coverage.csv',index=False)
pd.DataFrame(stats).to_csv(folder/'persistent_hotspot_prediction.csv',index=False)
pd.DataFrame(hotspot_pred).to_csv(folder/'hotspot_probability_predictions.csv',index=False)
delta=out.delta_R2.to_numpy();n=len(delta);rng=np.random.default_rng(77)
sim=np.mean(rng.choice(delta,size=(20000,n),replace=True),axis=1)
if n<=18:
    from itertools import product
    signs=np.array(list(product([-1,1],repeat=n)));p=float(np.mean(np.abs((signs*delta).mean(axis=1))>=abs(delta.mean())-1e-14))
else:p=np.nan
summary={'dates':n,'mean_delta_R2':float(np.mean(delta)),'median_delta_R2':float(np.median(delta)),
         'wins':int(np.sum(delta>0)),'bootstrap_CI_low':float(np.quantile(sim,.025)),
         'bootstrap_CI_high':float(np.quantile(sim,.975)),'exact_date_signflip_p':p,
         'wilcoxon_p':float(wilcoxon(delta).pvalue) if np.any(delta) else 1.}
summary['mean_delta_vs_spatial_climatology_R2']=float(out.delta_proposed_vs_climatology_R2.mean())
summary['wins_over_spatial_climatology']=int((out.delta_proposed_vs_climatology_R2>0).sum())
out['year']=out.Date.astype(str).str[:4]
yeardelta=out.groupby('year').delta_R2.mean().to_numpy();ny=len(yeardelta)
ysim=np.mean(rng.choice(yeardelta,size=(20000,ny),replace=True),axis=1)
summary['independent_calendar_years']=ny
summary['year_cluster_bootstrap_CI_low']=float(np.quantile(ysim,.025))
summary['year_cluster_bootstrap_CI_high']=float(np.quantile(ysim,.975))
if ny<=18:
    signs=np.array(list(product([-1,1],repeat=ny)))
    summary['year_cluster_signflip_p']=float(np.mean(np.abs((signs*yeardelta).mean(axis=1))>=abs(yeardelta.mean())-1e-14))
pd.DataFrame([summary]).to_csv(folder/'date_level_method_significance.csv',index=False)
print(out.to_string(index=False));print(summary)
