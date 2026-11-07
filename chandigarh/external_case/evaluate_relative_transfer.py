"""Three-way leave-one-date-out temperature domain-shift audit.

Source dates only fit models. Target-date mean/std are used solely to DEFINE
held-out anomaly/z-score truth for evaluation, NEVER for model adaptation.
Consequently anomaly evaluation is diagnostic, not an operationally available
absolute LST forecast. Persistent hotspot maps are observed-data retrospection.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor,RandomForestClassifier
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score,roc_auc_score,average_precision_score
from scipy.stats import spearmanr

R=Path(__file__).resolve().parents[1]
D=R/'external_case/data'
F=['NDVI','NDBI','MNDWI']
dates={'2021':'20210424','2024':'20240502','2026':'20260422'}
joined=None
for year,date in dates.items():
    t=pd.read_csv(D/f'landsat_hex_LC08_{date}.csv')
    t=t[['hex_id','LST']+F].rename(columns={col:f'{col}_{year}' for col in ['LST']+F})
    joined=t if joined is None else joined.merge(t,on='hex_id',validate='one_to_one')
required=[f'{c}_{y}' for y in dates for c in ['LST']+F]
d=joined.loc[np.isfinite(joined[required]).all(axis=1)].copy().reset_index(drop=True)
assert len(d)>=100
n=len(d);k=int(np.ceil(n*.2))
X={y:d[[f'{f}_{y}' for f in F]].to_numpy() for y in dates}
Y={y:d[f'LST_{y}'].to_numpy() for y in dates}
mu={y:float(Y[y].mean()) for y in dates}
sd={y:float(Y[y].std(ddof=0)) for y in dates}
def rf():return RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1)
def clf():return RandomForestClassifier(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1)
def topk(v):return set(np.argsort(-v,kind='stable')[:k])
def score(target,pred):
    a=topk(target);b=topk(pred);inter=len(a&b)
    return {'RMSE':float(np.sqrt(mean_squared_error(target,pred))),
            'MAE':float(mean_absolute_error(target,pred)),
            'R2':float(r2_score(target,pred)),
            'Spearman':float(spearmanr(target,pred).statistic),
            'top20_Jaccard':inter/(2*k-inter), 'top20_recall':inter/k}
rows=[];predictions={};det=[]
for target_year in dates:
    sources=[y for y in dates if y!=target_year]
    xx=np.vstack([X[y] for y in sources]);xt=X[target_year]
    yt=Y[target_year]
    # Neither model nor hyperparameters ever access target-date thermal labels.
    raw=rf().fit(xx,np.concatenate([Y[y] for y in sources])).predict(xt)
    an=rf().fit(xx,np.concatenate([Y[y]-mu[y] for y in sources])).predict(xt)
    zn=rf().fit(xx,np.concatenate([(Y[y]-mu[y])/sd[y] for y in sources])).predict(xt)
    class_y=np.concatenate([np.isin(np.arange(n),list(topk(Y[y]))).astype(int) for y in sources])
    hot=clf().fit(xx,class_y).predict_proba(xt)[:,1]
    ishot=np.isin(np.arange(n),list(topk(yt))).astype(int)
    for name,true,pred in [('absolute_C',yt,raw),('mean_centered_anomaly_C',yt-mu[target_year],an),
                           ('zscore_anomaly', (yt-mu[target_year])/sd[target_year],zn)]:
        rows.append({'train_years':'+'.join(sources),'test_year':target_year,'target_type':name,
                     'n_hex':n,'source_only_fit':True,'target_moments_used_for_prediction':False,
                     'target_date_mean_C_for_evaluation':mu[target_year],
                     'target_date_sd_C_for_evaluation':sd[target_year],**score(true,pred)})
    rows.append({'train_years':'+'.join(sources),'test_year':target_year,'target_type':'hot_quintile_classifier',
                 'n_hex':n,'source_only_fit':True,'target_moments_used_for_prediction':False,
                 'target_date_mean_C_for_evaluation':mu[target_year],
                 'target_date_sd_C_for_evaluation':sd[target_year],
                 'AUROC':roc_auc_score(ishot,hot),'PR_AUC':average_precision_score(ishot,hot),
                 'top20_Jaccard':score(yt,hot)['top20_Jaccard'],
                 'top20_recall':score(yt,hot)['top20_recall']})
    for i,hid in enumerate(d.hex_id):
        det.append({'hex_id':hid,'test_year':target_year,'actual_LST_C':yt[i],
                    'actual_anomaly_C':yt[i]-mu[target_year],'actual_hot':ishot[i],
                    'pred_absolute_C':raw[i],'pred_anomaly_C':an[i],
                    'pred_zscore':zn[i],'pred_hot_probability':hot[i]})
results=pd.DataFrame(rows)
results.to_csv(R/'outputs/tables/relative_temporal_transfer.csv',index=False)
pd.DataFrame(det).to_csv(R/'outputs/tables/temporal_relative_predictions.csv',index=False)

heat=np.column_stack([np.isin(np.arange(n),list(topk(Y[y]))) for y in dates])
count=heat.sum(axis=1)
types=np.where(count>=2,'persistent_hot',np.where(heat[:,2] & (count==1),'emerging_2026_hot',
         np.where(heat[:,0] & (count==1),'historical_2021_only_hot','other_or_unstable')))
persist=pd.DataFrame({'hex_id':d.hex_id,'hot_count_3dates':count,
                       'hot_2021':heat[:,0],'hot_2024':heat[:,1], 'hot_2026':heat[:,2],
                       'hotspot_type':types})
persist.to_csv(R/'outputs/tables/persistent_heat_hexes.csv',index=False)
overlaps=[]
for i,year1 in enumerate(dates):
    for year2 in list(dates)[i+1:]:
        a=topk(Y[year1]);b=topk(Y[year2]);overlaps.append({'year_a':year1,'year_b':year2,
            'n_hex':n,'top_k':k,'shared_hot_hexes':len(a&b), 'hotspot_Jaccard':len(a&b)/len(a|b),
            'observed_Spearman':spearmanr(Y[year1],Y[year2]).statistic})
pd.DataFrame(overlaps).to_csv(R/'outputs/tables/observed_hotspot_persistence.csv',index=False)
print(results[['train_years','test_year','target_type','RMSE','R2','Spearman','top20_Jaccard','AUROC','PR_AUC']].to_string(index=False))
print('Hotspot class counts:',persist.hotspot_type.value_counts().to_dict())
