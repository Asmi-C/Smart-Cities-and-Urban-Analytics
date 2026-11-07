"""Frozen spectral-only RF temporal transfer on two independently acquired Landsat scenes."""
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1];DATA=R/'external_case/data'
a=pd.read_csv(DATA/'landsat_hex_LC08_20210324.csv');b=pd.read_csv(DATA/'landsat_hex_LC08_20260322.csv')
d=a.merge(b,on='hex_id',suffixes=('_2021','_2026'))
cols=['NDVI','NDBI','MNDWI'];needed=[f'{x}_{y}' for y in ('2021','2026') for x in cols+['LST']]
d=d.loc[np.isfinite(d[needed]).all(axis=1)].copy()
assert len(d)>=100,f'Insufficient independent matched data ({len(d)} hexes)'
g=gpd.read_file(R/'outputs/data/hex_results.gpkg').to_crs(32643).set_index('hex_id').loc[d.hex_id]
xy=np.c_[g.geometry.centroid.x,g.geometry.centroid.y]
blocks=np.floor((xy-xy.min(0))/1000).astype(int);grp=blocks[:,0]*10000+blocks[:,1]
def RF():return RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1)
def moran(res):
    nb=cKDTree(xy).query(xy,k=min(9,len(xy)))[1][:,1:]
    z=res-res.mean();I=np.sum(z[:,None]*z[nb])/(nb.shape[1]*np.sum(z*z))
    rng=np.random.default_rng(13);null=[]
    for i in range(999):
        q=rng.permutation(z);null.append(np.sum(q[:,None]*q[nb])/(nb.shape[1]*np.sum(q*q)))
    null=np.array(null);return I,(1+np.sum(abs(null-null.mean())>=abs(I-null.mean())))/1000
def record(label,target,pred,year,train,valid):
    I,p=moran(target-pred)
    return {'evaluation':label,'train_period':train,'test_period':year,'n_hex':len(target),'RMSE_C':np.sqrt(mean_squared_error(target,pred)),
            'MAE_C':mean_absolute_error(target,pred),'R2':r2_score(target,pred),'residual_Moran_I':I,'Moran_p':p,
            'mean_target_C':target.mean(),'mean_prediction_C':pred.mean(),'spatially_independent_time':valid}
rows=[];predictions={};spatial_oof={}
for year in ('2021','2026'):
    X=d[[f'{x}_{year}' for x in cols]].to_numpy();target=d[f'LST_{year}'].to_numpy()
    folds=list(GroupKFold(5).split(X,target,groups=grp));p=np.empty(len(d))
    for tr,te in folds:p[te]=RF().fit(X[tr],target[tr]).predict(X[te])
    spatial_oof[year]=p
    rows.append(record('same_period_spatial_cv',target,p,year,year,False))
for train,test in [('2021','2026'),('2026','2021')]:
    Xtr=d[[f'{x}_{train}' for x in cols]].to_numpy();Xte=d[[f'{x}_{test}' for x in cols]].to_numpy()
    yt=d[f'LST_{test}'].to_numpy();p=RF().fit(Xtr,d[f'LST_{train}']).predict(Xte)
    predictions[(train,test)]=p
    rows.append(record('true_cross_acquisition_transfer',yt,p,test,train,True))
results=pd.DataFrame(rows);results.to_csv(R/'outputs/tables/temporal_validation_detailed.csv',index=False)
coverage=[]
for (train,test),pred in predictions.items():
    source_y=d[f'LST_{train}'].to_numpy();target_y=d[f'LST_{test}'].to_numpy()
    abs_errors=np.abs(source_y-spatial_oof[train])
    for alpha in (.2,.1,.05):
        q=np.quantile(abs_errors,min(1,np.ceil((len(abs_errors)+1)*(1-alpha))/len(abs_errors)),method='higher')
        coverage.append({'train_period':train,'test_period':test,'nominal_coverage':1-alpha,
                         'empirical_coverage':np.mean(np.abs(target_y-pred)<=q),
                         'mean_width_C':2*q,'calibration':'spatial OOF errors in source period',
                         'guarantee':'No formal exchangeability under temporal shift'})
pd.DataFrame(coverage).to_csv(R/'outputs/tables/temporal_interval_coverage.csv',index=False)
transfer_rank=[]
for (train,test),p in predictions.items():
    observed=d[f'LST_{test}'].to_numpy();k=int(np.ceil(.2*len(d)))
    predicted_top=set(np.argsort(-p)[:k]);observed_top=set(np.argsort(-observed)[:k])
    intersection=len(predicted_top&observed_top)
    transfer_rank.append({'train_period':train,'test_period':test,'n_hex':len(d),'k':k,
                          'predicted_observed_topk_Jaccard':intersection/(2*k-intersection),
                          'predicted_observed_topk_recall':intersection/k,
                          'Spearman_predicted_observed':pd.Series(p).corr(pd.Series(observed),method='spearman'),
                          'label':'exploratory rank-transfer test; not preregistered primary endpoint'})
pd.DataFrame(transfer_rank).to_csv(R/'outputs/tables/temporal_rank_transfer.csv',index=False)
# Measured spatial hotspot overlap is a descriptive temporal-change metric,
# not a claimed transfer of the older intervention policy index.
q1=d.LST_2021.to_numpy();q2=d.LST_2026.to_numpy();k=int(np.ceil(.2*len(d)))
set1=set(np.argsort(-q1)[:k]);set2=set(np.argsort(-q2)[:k]);inter=len(set1&set2)
pd.DataFrame([{'n_matched':len(d),'top20_k':k,'overlap_count':inter,'Jaccard':inter/len(set1|set2),
               'retention_2021_top_in_2026':inter/k,
               'mean_LST_2021_C':q1.mean(),'mean_LST_2026_C':q2.mean(),
               'note':'Two independent March scenes; weather differences not controlled'}]).to_csv(R/'outputs/tables/temporal_hotspot_overlap.csv',index=False)
print(results.to_string(index=False));print('Temporal hotspot overlap',inter,'/',k)
