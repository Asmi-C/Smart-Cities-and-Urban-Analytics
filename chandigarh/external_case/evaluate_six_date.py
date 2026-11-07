"""Predeclared leave-one-acquisition-out benchmark for six selected Landsat dates.

All model settings frozen; no target LST is used in any fit, date selection,
adaptation, hyperparameter selection or reconstructed absolute forecast.
Target label moments are computed solely to SCORE retrospective anomalies.
"""
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd
from scipy.stats import spearmanr,rankdata
from scipy.spatial import cKDTree
from scipy.linalg import fractional_matrix_power
from sklearn.ensemble import RandomForestRegressor,RandomForestClassifier,HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score,roc_auc_score,average_precision_score
R=Path(__file__).resolve().parents[1]
scene_ids=pd.read_csv(R/'data/selected_acquisitions.csv').item_id.tolist()
F=['NDVI','NDBI','MNDWI']
arrays={}
for item in scene_ids:
    date=item.split('_')[3]
    t=pd.read_csv(R/f'external_case/data/landsat_hex_{item[:4]}_{date}.csv')
    valid=np.isfinite(t[['LST']+F]).all(axis=1)
    arrays[date]=t.loc[valid,['hex_id','LST']+F].reset_index(drop=True)
def reg():return RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1)
def cls():return RandomForestClassifier(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1)
def coral(xs,xt,penalty=.05):
    ms=xs.mean(0);mt=xt.mean(0)
    cs=np.cov(xs,rowvar=False)+penalty*np.eye(xs.shape[1]);ct=np.cov(xt,rowvar=False)+penalty*np.eye(xt.shape[1])
    return np.real((xs-ms)@fractional_matrix_power(cs,-.5)@fractional_matrix_power(ct,.5)+mt)
def rank01(y):return (rankdata(y,method='average')-.5)/len(y)
def moran(y,hexes):
    if len(y)<20:return np.nan,np.nan
    geom=gg.loc[hexes];xy=np.c_[geom.geometry.centroid.x,geom.geometry.centroid.y]
    nb=cKDTree(xy).query(xy,k=9)[1][:,1:];z=y-y.mean()
    if z.var()==0:return np.nan,np.nan
    I=np.sum(z[:,None]*z[nb])/(8*np.sum(z*z));rng=np.random.default_rng(32)
    null=[]
    for _ in range(499):
        q=rng.permutation(z);null.append(np.sum(q[:,None]*q[nb])/(8*np.sum(q*q)))
    null=np.asarray(null);pv=(1+np.sum(abs(null-null.mean())>=abs(I-null.mean())))/500
    return I,pv
gg=gpd.read_file(R/'outputs/data/hex_results.gpkg').to_crs(32643).set_index('hex_id')
rows=[];preds=[]
for held,test in arrays.items():
    sources=[v for date,v in arrays.items() if date!=held]
    xt=test[F].to_numpy(); yt=test.LST.to_numpy()
    ys=np.concatenate([s.LST.to_numpy() for s in sources]);xs=np.vstack([s[F].to_numpy() for s in sources])
    mean_y=np.concatenate([s.LST.to_numpy()-s.LST.mean() for s in sources])
    med_y=np.concatenate([s.LST.to_numpy()-s.LST.median() for s in sources])
    z_y=np.concatenate([(s.LST.to_numpy()-s.LST.mean())/s.LST.std(ddof=0) for s in sources])
    rank_y=np.concatenate([rank01(s.LST.to_numpy()) for s in sources])
    hot_y=np.concatenate([(s.LST.to_numpy()>=s.LST.quantile(.8)).astype(int) for s in sources])
    target_defs={'absolute_C':(ys,yt),'mean_anomaly_C':(mean_y,yt-yt.mean()),
        'median_anomaly_C':(med_y,yt-np.median(yt)),
        'standardized_anomaly':(z_y,(yt-yt.mean())/yt.std(ddof=0)),
        'within_date_percentile':(rank_y,rank01(yt))}
    # Unlabeled target covariates can be used by an unsupervised feature transform.
    scsrc=(xs-xs.mean(0))/(xs.std(0)+1e-6);sctgt=(xt-xt.mean(0))/(xt.std(0)+1e-6)
    variants={'RF_raw_spectral':(xs,xt),
              'HGB_raw_spectral':(xs,xt),
              'RF_unsupervised_feature_standardization':(scsrc,sctgt),
              'RF_CORAL_unlabeled_target':(coral(xs,xt),xt)}
    for variant,(xx,xxte) in variants.items():
        for target_type,(train_y,truth) in target_defs.items():
            est=HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=12,l2_regularization=5,random_state=42) if variant=='HGB_raw_spectral' else reg()
            p=est.fit(xx,train_y).predict(xxte)
            I,pv=moran(truth-p,test.hex_id)
            m=len(yt);k=max(1,int(np.ceil(.2*m)))
            top_actual=set(np.argsort(-truth,kind='stable')[:k]);top_pred=set(np.argsort(-p,kind='stable')[:k]);shared=len(top_actual&top_pred)
            rows.append({'test_date':held,'source_dates':'+'.join(sorted(arrays.keys()-{held})),
                'n_test_hex':m,'n_train_records':len(ys),'model':variant,'target':target_type,
                'RMSE':np.sqrt(mean_squared_error(truth,p)),'MAE':mean_absolute_error(truth,p),
                'R2':r2_score(truth,p),'Spearman':spearmanr(truth,p).statistic,
                'top20_Jaccard':shared/(2*k-shared),'top20_recall':shared/k,
                'residual_Moran_I':I,'residual_Moran_p':pv,
                'target_LST_used_for_fit':False,'target_moments_only_for_retrospective_label':target_type!='absolute_C'})
            if variant=='RF_raw_spectral' and target_type=='mean_anomaly_C':
                for hid,true,pr in zip(test.hex_id,truth,p):preds.append({'test_date':held,'hex_id':hid,'actual_anomaly_C':true,'predicted_anomaly_C':pr})
        if variant=='HGB_raw_spectral':continue
        p=cls().fit(xx,hot_y).predict_proba(xxte)[:,1]
        truth=(yt>=np.quantile(yt,.8)).astype(int);k=max(1,int(np.ceil(.2*len(yt))))
        truth_top=set(np.where(truth==1)[0]);pred_top=set(np.argsort(-p,kind='stable')[:k]);shared=len(truth_top&pred_top)
        rows.append({'test_date':held,'source_dates':'+'.join(sorted(arrays.keys()-{held})),
            'n_test_hex':len(yt),'n_train_records':len(ys),'model':variant,'target':'hot_quintile_classifier',
            'AUROC':roc_auc_score(truth,p),'PR_AUC':average_precision_score(truth,p),
            'top20_Jaccard':shared/(len(truth_top|pred_top)), 'top20_recall':shared/len(truth_top),
            'target_LST_used_for_fit':False,'target_moments_only_for_retrospective_label':True})
out=pd.DataFrame(rows)
out.to_csv(R/'outputs/tables/leave_one_date_out.csv',index=False)
pd.DataFrame(preds).to_csv(R/'outputs/tables/six_date_anomaly_predictions.csv',index=False)
print('Held-out dates',len(arrays),'records', {date:len(df) for date,df in arrays.items()})
print(out[(out.model=='RF_raw_spectral')&(out.target.isin(['absolute_C','mean_anomaly_C','hot_quintile_classifier']))]
      [['test_date','target','n_test_hex','RMSE','R2','Spearman','AUROC','top20_Jaccard']].to_string(index=False))
