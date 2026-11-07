"""Focused submission blockers: spatial residual correction, geographic transfer, and rank robustness.
Run: python run_submission_tests.py  (offline, reads existing NKDA hex export).
"""
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree, distance
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

P=Path(__file__).resolve().parent;T=P/'outputs/tables';F=P/'outputs/PPT_FIGURES';D=P/'docs'
for x in (T,F,D):x.mkdir(parents=True,exist_ok=True)
g=gpd.read_file(P/'outputs/data/hex_results.gpkg').to_crs(32643)
xy=np.c_[g.geometry.centroid.x,g.geometry.centroid.y];y=g.LST.to_numpy(float);n=len(g)
cols=['f_built','f_veg','f_water','NDVI','NDBI','MNDWI','d_school','d_health','d_green','d_transit','d_shop']
X=g[cols].to_numpy(float);assert np.isfinite(X).all()
q=np.floor((xy-xy.min(0))/1000).astype(int);groups=q[:,0]*10000+q[:,1]
folds=list(GroupKFold(5).split(y,groups=groups))
def RF(seed=42):return RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,n_jobs=-1,random_state=seed)
neighbors=cKDTree(xy).query(xy,k=9)[1][:,1:]
def moran(v,perm=999):
    z=v-v.mean();I=np.sum(z[:,None]*z[neighbors])/(8*np.sum(z*z))
    rng=np.random.default_rng(230);null=np.empty(perm)
    for k in range(perm):
        r=rng.permutation(z);null[k]=np.sum(r[:,None]*r[neighbors])/(8*np.sum(r*r))
    return I,(1+np.sum(abs(null-null.mean())>=abs(I-null.mean())))/(perm+1)
def kernel_predict(train_xy,res,test_xy,bandwidth):
    dist=distance.cdist(test_xy,train_xy)
    w=np.exp(-.5*(dist/bandwidth)**2)
    return w@res/np.maximum(w.sum(axis=1),1e-12)

# Context features derive exclusively from covariates, not held-out responses.
# Every point's neighborhood excludes itself; neighborhood radius 750 m.
dist=distance.cdist(xy,xy);mask=(dist<=750)&(dist>0)
context=np.column_stack([mask@g[c].to_numpy(float)/np.maximum(mask.sum(axis=1),1) for c in ('f_built','f_veg','f_water')])
coords=(xy-xy.mean(0))/1000
datasets={'RF':X,'RF + coordinates':np.c_[X,coords],
          'RF + 750m covariate context':np.c_[X,context],
          'RF + context + coordinates':np.c_[X,context,coords]}
pred={name:np.full(n,np.nan) for name in datasets}
pred['RF + cross-fit residual kernel']=np.full(n,np.nan)
pred['RF + cross-fit residual KNN']=np.full(n,np.nan)
foldrows=[]
for k,(train,test) in enumerate(folds):
    for name,x in datasets.items():
        m=RF().fit(x[train],y[train]);pred[name][test]=m.predict(x[test])
    # Inner OOF residuals across training-only spatial blocks prevent in-sample RF bias.
    inners=list(GroupKFold(4).split(train,groups=groups[train]));inner_res=np.full(len(train),np.nan)
    for itr,iva in inners:
        model=RF().fit(X[train[itr]],y[train[itr]])
        inner_res[iva]=y[train[iva]]-model.predict(X[train[iva]])
    assert np.isfinite(inner_res).all()
    base=pred['RF'][test]
    pred['RF + cross-fit residual kernel'][test]=base+kernel_predict(xy[train],inner_res,xy[test],700)
    kd=cKDTree(xy[train]);dd,ii=kd.query(xy[test],k=8);wt=1/np.maximum(dd,100)
    pred['RF + cross-fit residual KNN'][test]=base+np.sum(wt*inner_res[ii],axis=1)/wt.sum(axis=1)
    for name in pred:foldrows.append({'fold':k,'model':name,'n_test':len(test),
                                      'RMSE_C':np.sqrt(mean_squared_error(y[test],pred[name][test])),
                                      'mean_residual_C':np.mean(y[test]-pred[name][test])})
pd.DataFrame(foldrows).to_csv(T/'residual_fold_summary.csv',index=False)
comparison=[]
for name,p in pred.items():
    I,pval=moran(y-p)
    comparison.append({'Model':name,'RMSE':np.sqrt(mean_squared_error(y,p)),'MAE':mean_absolute_error(y,p),
                       'R2':r2_score(y,p),'Residual Moran I':I,'p':pval})
pd.DataFrame(comparison).sort_values('RMSE').to_csv(T/'spatial_model_comparison.csv',index=False)
np.savez_compressed(T/'submission_oof_predictions.npz',y=y,xy=xy,**{'p'+str(i):p for i,p in enumerate(pred.values())})
# Block bootstrap the paired coordinate-feature improvement, conditional on the
# fixed OOF predictions. Geographic groups, not individual pixels, are sampled.
unique=np.unique(groups);boot_rng=np.random.default_rng(970);deltas=[]
for _ in range(3000):
    drawn=boot_rng.choice(unique,len(unique),replace=True)
    ids=np.concatenate([np.where(groups==b)[0] for b in drawn])
    a=np.sqrt(np.mean((y[ids]-pred['RF'][ids])**2))
    b=np.sqrt(np.mean((y[ids]-pred['RF + coordinates'][ids])**2))
    deltas.append(b-a)
pd.DataFrame([{'comparison':'RF + coordinates minus RF','delta_RMSE_C':np.sqrt(mean_squared_error(y,pred['RF + coordinates']))-np.sqrt(mean_squared_error(y,pred['RF'])),
               'bootstrap_low_95_C':np.quantile(deltas,.025),'bootstrap_high_95_C':np.quantile(deltas,.975),
               'method':'1km geographic-block bootstrap of fixed out-of-fold predictions'}]).to_csv(T/'spatial_model_gain_ci.csv',index=False)

# Residual diagnostics for original RF, all OOF (no in-sample target leakage).
res=y-pred['RF'];lag=res[neighbors].mean(axis=1)
pairdist=distance.pdist(xy);semivar=.5*distance.pdist(res[:,None],metric='sqeuclidean')
bins=np.arange(0,5001,250);mid=(bins[:-1]+bins[1:])/2
vario=pd.DataFrame([{'distance_m':mid[i],'n_pairs':int(np.sum((pairdist>=bins[i])&(pairdist<bins[i+1]))),
    'semivariance_C2':float(np.mean(semivar[(pairdist>=bins[i])&(pairdist<bins[i+1])])) if np.any((pairdist>=bins[i])&(pairdist<bins[i+1])) else np.nan} for i in range(len(mid))])
vario.to_csv(T/'residual_semivariogram.csv',index=False)
rho=[]
pairproduct=(res[:,None]*res[None,:])[np.triu_indices(n,1)]
for i in range(len(mid)):
    ix=(pairdist>=bins[i])&(pairdist<bins[i+1]);rho.append(float(np.mean(pairproduct[ix])/np.var(res)) if ix.sum()>0 else np.nan)
pd.DataFrame({'distance_m':mid,'residual_correlation_proxy':rho}).to_csv(T/'residual_distance_correlation.csv',index=False)

# Local Moran with per-site permutation and BH-FDR control (descriptive clustering).
z=(res-res.mean())/res.std();local=z*z[neighbors].mean(axis=1)
rng=np.random.default_rng(97);null=np.empty((999,n))
for j in range(999):
    zz=rng.permutation(z);null[j]=zz*zz[neighbors].mean(axis=1)
pvals=(1+(abs(null)>=abs(local)).sum(axis=0))/1000
order=np.argsort(pvals);cut=.05*np.arange(1,n+1)/n;passed=np.where(pvals[order]<=cut)[0]
sig=np.zeros(n,bool)
if len(passed):sig=pvals<=pvals[order[passed[-1]]]
cluster=np.where(sig& (z>0)&(lag>0),'High-high',np.where(sig&(z<0)&(lag<0),'Low-low','Not FDR-significant'))
g['rf_oof_residual']=res;g['residual_cluster']=cluster
g.to_file(P/'outputs/data/residual_diagnostics.gpkg',driver='GPKG')
fig,ax=plt.subplots(2,2,figsize=(11,9))
g.plot(column='rf_oof_residual',ax=ax[0,0],cmap='RdBu_r',legend=True);ax[0,0].set_title('Out-of-fold RF residual (°C)')
ax[0,1].plot(mid,vario.semivariance_C2,'o-');ax[0,1].set(xlabel='Pair separation (m)',ylabel='Semivariance (°C²)',title='Empirical semivariogram')
ax[1,0].scatter(res,lag,s=13,alpha=.5);ax[1,0].axhline(0,color='gray');ax[1,0].axvline(0,color='gray');ax[1,0].set(xlabel='Residual (°C)',ylabel='8-neighbor spatial lag (°C)',title='Moran scatterplot')
g.plot(column='residual_cluster',categorical=True,legend=True,ax=ax[1,1]);ax[1,1].set_title('Local Moran clusters (BH-FDR 5%)')
for a in (ax[0,0],ax[1,1]):a.axis('off')
fig.tight_layout();fig.savefig(F/'08_residual_diagnostics.png',dpi=180);plt.close(fig)

# Pseudo-external internal geographic transfer, predeclared easternmost 20%.
# Not truly independent external/time validation; compare simple feature ablations.
cutoff=np.quantile(xy[:,0],.8);test=np.where(xy[:,0]>=cutoff)[0];train=np.where(xy[:,0]<cutoff)[0]
transfer=[]
for name,x in datasets.items():
    m=RF().fit(x[train],y[train]);q=m.predict(x[test])
    transfer.append({'transfer_test':'eastmost_20_percent_INTERNAL','model':name,
                     'n_train':len(train),'n_test':len(test),'RMSE_C':np.sqrt(mean_squared_error(y[test],q)),
                     'MAE_C':mean_absolute_error(y[test],q),'R2':r2_score(y[test],q),
                     'external_validation':False})
pd.DataFrame(transfer).to_csv(T/'generalization_results.csv',index=False)

# Rank robustness benchmark. Selection uses design scenarios, evaluation uses
# disjoint policy weights and independent input perturbations. Same budget K=37.
def normalize(z):return (z-z.min(axis=0))/(z.max(axis=0)-z.min(axis=0))
baseZ=np.c_[normalize(y[:,None]).ravel(),1-normalize(g.score15.to_numpy()[:,None]).ravel(),1-normalize(g.f_bluegreen.to_numpy()[:,None]).ravel()]
dir_rng=np.random.default_rng(441);design=dir_rng.dirichlet([2,2,2],size=501)
def priority_probs(z,ww,K=108):
    vals=z@ww.T;return (np.argsort(np.argsort(-vals,axis=0),axis=0)<K).mean(axis=1)
accept=priority_probs(baseZ,design);K=37
# Proposed policy shortlist requires (i) stable top-quintile acceptance,
# (ii) below-median independently calibrated heat interval width, and
# (iii) severity ordering by Pareto front (from earlier research extension).
# Select fixed K for fair comparison. A fall-back is recorded if the gate lacks K.
old=gpd.read_file(P/'outputs/data/ieee_priority_results.gpkg')
heat_width=old.heat_interval_width_C.to_numpy(float)
pareto=old.pareto_front.to_numpy(int)
eligible=np.where((accept>=.8)&(heat_width<=np.median(heat_width)))[0]
eligible=eligible[np.lexsort((-accept[eligible],pareto[eligible]))]
if len(eligible)<K:
    remainder=np.setdiff1d(np.argsort(-accept),eligible,assume_unique=False)
    proposed=np.r_[eligible,remainder[:K-len(eligible)]]
else:proposed=eligible[:K]
methods={'Proposed_Pareto_acceptability_interval':proposed,
         'Equal_weight':np.argsort(-(baseZ@np.ones(3)/3))[:K],
         'AHP_proxy':np.argsort(-(baseZ@np.array([.137,.403,.079])/.619))[:K],
         'Fixed_weight_0.5_0.3_0.2':np.argsort(-(baseZ@np.array([.5,.3,.2])))[:K]}
eval_rng=np.random.default_rng(987);eval_w=eval_rng.dirichlet([.7,.7,.7],size=300)
scores=baseZ@eval_w.T;evaltop=np.argsort(np.argsort(-scores,axis=0),axis=0)<108
bench=[]
for name,ids in methods.items():
    # Evaluate candidate recall/retention under unseen preference scenarios.
    retention=evaltop[ids].mean(axis=0)
    # Every scenario has an independently perturbed input, not reused for selection.
    pert=[]
    for j in range(300):
        noise=eval_rng.normal(0,.04,size=baseZ.shape)
        z=np.clip(baseZ+noise,0,1)
        top=np.argsort(-(z@eval_w[j]))[:K]
        pert.append(len(set(ids)&set(top))/len(set(ids)|set(top)))
    bench.append({'method':name,'selected_K':K,'mean_top20_retention':retention.mean(),
                  'retention_95_low':np.quantile(retention,.025),'mean_topK_Jaccard_perturbed':np.mean(pert),
                  'mean_false_high_confidence_fraction':1-retention.mean(),
                  'eligible_count_before_budget':len(eligible) if name.startswith('Proposed') else np.nan})
pd.DataFrame(bench).to_csv(T/'ranking_baseline_comparison.csv',index=False)

print(pd.read_csv(T/'spatial_model_comparison.csv').to_string(index=False))
print(pd.read_csv(T/'ranking_baseline_comparison.csv').to_string(index=False))
