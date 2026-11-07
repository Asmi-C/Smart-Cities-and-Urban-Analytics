"""Advanced, fully offline NKDA GeoAI evaluations; no new claims of ground truth.

Usage: python run_ieee_experiments.py
Existing: outputs/data/hex_results.gpkg (the previous branch's 537 hexes).
"""
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
from sklearn.base import clone
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import KFold, GroupKFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs';TAB=OUT/'tables';FIG=OUT/'PPT_FIGURES';DOC=ROOT/'docs'
for q in (TAB,FIG,DOC):q.mkdir(parents=True,exist_ok=True)
g=gpd.read_file(OUT/'data/hex_results.gpkg').to_crs(32643)
xy=np.column_stack([g.geometry.centroid.x,g.geometry.centroid.y]);y=g.LST.to_numpy(float);n=len(g)
assert n==906 and np.isfinite(y).all()
feat={
 'morphology':['f_built','f_veg','f_water'],
 'morphology+spectral':['f_built','f_veg','f_water','NDVI','NDBI','MNDWI'],
 'morphology+access':['f_built','f_veg','f_water','d_school','d_health','d_green','d_transit','d_shop'],
 'combined':['f_built','f_veg','f_water','NDVI','NDBI','MNDWI','d_school','d_health','d_green','d_transit','d_shop']}
base={'Mean':DummyRegressor(),
      'Ridge':make_pipeline(SimpleImputer(strategy='median'),Ridge(alpha=10)),
      'RF':make_pipeline(SimpleImputer(strategy='median'),RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1)),
      'HGB':make_pipeline(SimpleImputer(strategy='median'),HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=12,l2_regularization=5,random_state=42))}
def spatial_groups(width):
    q=np.floor((xy-xy.min(axis=0))/width).astype(int)
    return q[:,0]*10000+q[:,1]
def folds_for(mode):
    if mode=='random':return list(KFold(5,shuffle=True,random_state=42).split(y))
    if mode.startswith('block_'):
        width=float(mode.split('_')[1])*1000
        return list(GroupKFold(5).split(y,groups=spatial_groups(width)))
    if mode=='region_x':
        # Each geographic strip is a contiguous leave-region-out fold.
        region=np.minimum(np.digitize(xy[:,0],np.quantile(xy[:,0],[.2,.4,.6,.8])),4)
        return [(np.where(region!=i)[0],np.where(region==i)[0]) for i in range(5)]
    if mode=='region_y':
        region=np.minimum(np.digitize(xy[:,1],np.quantile(xy[:,1],[.2,.4,.6,.8])),4)
        return [(np.where(region!=i)[0],np.where(region==i)[0]) for i in range(5)]
    raise ValueError(mode)

def buffered(folds,buffer_m):
    for tr,te in folds:
        distance,_=cKDTree(xy[te]).query(xy[tr],k=1)
        new=tr[distance>buffer_m]
        if len(new)<100:raise ValueError('Insufficient training after buffer')
        yield new,te

def predict_cv(estimator,cols,folds,spatial_knn=False):
    X=g[cols].replace([np.inf,-np.inf],np.nan).to_numpy(float)
    p=np.full(n,np.nan);err=[]
    for tr,te in folds:
        if spatial_knn:
            # Only coordinates of *training* points, with no test-target leakage.
            m=KNeighborsRegressor(n_neighbors=min(8,len(tr)),weights='distance')
            m.fit(xy[tr],y[tr]);p[te]=m.predict(xy[te])
        else:
            m=clone(estimator);m.fit(X[tr],y[tr]);p[te]=m.predict(X[te])
        err.append(np.sqrt(mean_squared_error(y[te],p[te])))
    assert np.isfinite(p).all()
    return p,np.std(err,ddof=1)

schemes=['random','block_1','block_1.5','block_2','region_x','region_y','block_1_buffer250','block_2_buffer250']
rows=[];pred={}
for mode in schemes:
    folds=folds_for(mode.split('_buffer')[0]); folds=list(buffered(folds,250)) if 'buffer' in mode else folds
    for model,est in base.items():
        p,sd=predict_cv(est,feat['combined'],folds)
        rows.append([mode,model,'combined',r2_score(y,p),np.sqrt(mean_squared_error(y,p)),mean_absolute_error(y,p),sd])
        pred[(mode,model,'combined')]=p
    k,sd=predict_cv(None,[],folds,True)
    rows.append([mode,'SpatialKNN8','coordinates',r2_score(y,k),np.sqrt(mean_squared_error(y,k)),mean_absolute_error(y,k),sd]);pred[(mode,'SpatialKNN8','coordinates')]=k
    for name in ('morphology','morphology+spectral','morphology+access'):
        p,sd=predict_cv(base['RF'],feat[name],folds)
        rows.append([mode,'RF',name,r2_score(y,p),np.sqrt(mean_squared_error(y,p)),mean_absolute_error(y,p),sd]);pred[(mode,'RF',name)]=p
res=pd.DataFrame(rows,columns=['scheme','model','features','R2','RMSE_C','MAE_C','fold_RMSE_sd_C'])
res.to_csv(TAB/'ieee_validation_matrix.csv',index=False)

# Moran I for kNN graph; permutation null conditional on fixed adjacency.
neighbors=cKDTree(xy).query(xy,k=9)[1][:,1:]
def moran(residual,seed=42,permutations=999):
    z=residual-np.mean(residual)
    value=np.sum(z[:,None]*z[neighbors])/(8*np.sum(z*z))
    rng=np.random.default_rng(seed)
    null=np.empty(permutations)
    for i in range(permutations):
        q=rng.permutation(z);null[i]=np.sum(q[:,None]*q[neighbors])/(8*np.sum(q*q))
    p=(1+np.sum(np.abs(null-np.mean(null))>=abs(value-np.mean(null))))/(permutations+1)
    return value,p
diagnostics=[]
for mode in ['random','block_1','block_2','region_x']:
    for model in ('Ridge','RF','HGB','SpatialKNN8'):
        key=(mode,model,'coordinates' if model=='SpatialKNN8' else 'combined')
        m,p=moran(y-pred[key]);diagnostics.append([mode,model,m,p])
pd.DataFrame(diagnostics,columns=['scheme','model','residual_Moran_I','permutation_p_two_sided']).to_csv(TAB/'residual_spatial_diagnostics.csv',index=False)

# Paired geographic-block bootstrap of OOF errors. It measures uncertainty conditional
# on the fixed OOF predictions, not uncertainty across repeated model refits.
groups=spatial_groups(1000); uniq=np.unique(groups)
a=pred[('block_1','RF','morphology')];b=pred[('block_1','RF','combined')]
rng=np.random.default_rng(2026);delta=[]
for _ in range(3000):
    sampled=rng.choice(uniq,len(uniq),replace=True)
    ix=np.concatenate([np.where(groups==u)[0] for u in sampled])
    delta.append(np.sqrt(np.mean((y[ix]-b[ix])**2))-np.sqrt(np.mean((y[ix]-a[ix])**2)))
lo,hi=np.quantile(delta,[.025,.975]); observed=np.sqrt(np.mean((y-b)**2))-np.sqrt(np.mean((y-a)**2))
pd.DataFrame([{'contrast':'RF combined minus RF morphology','scheme':'block_1',
               'delta_RMSE_C':observed,'bootstrap_95_low_C':lo,'bootstrap_95_high_C':hi,
               'n_groups':len(uniq),'method':'paired block bootstrap of fixed OOF predictions'}]).to_csv(TAB/'paired_model_uncertainty.csv',index=False)

# Spatial split-conformal-like diagnostic: groupwise calibration selected *within*
# each outer training fold; coverage is reported empirically, not guaranteed under shift.
X=g[feat['combined']].replace([np.inf,-np.inf],np.nan).to_numpy(float)
outer=folds_for('block_1');lower=np.full(n,np.nan);upper=np.full(n,np.nan);pt=np.full(n,np.nan)
for fold,(train,test) in enumerate(outer):
    gu=np.unique(groups[train]);rr=np.random.default_rng(103+fold);rr.shuffle(gu)
    ncal=max(2,int(np.ceil(.2*len(gu))))
    cal=train[np.isin(groups[train],gu[:ncal])]; fit=train[~np.isin(groups[train],gu[:ncal])]
    m=clone(base['RF']).fit(X[fit],y[fit]);cal_error=np.abs(y[cal]-m.predict(X[cal]))
    q=np.quantile(cal_error,min(1.,np.ceil((len(cal)+1)*.9)/len(cal)),method='higher')
    pt[test]=m.predict(X[test]);lower[test]=pt[test]-q;upper[test]=pt[test]+q
coverage=np.mean((y>=lower)&(y<=upper));width=np.mean(upper-lower)
pd.DataFrame([{'scheme':'1km spatial outer CV; inner group calibration','nominal_coverage':.9,
               'empirical_coverage':coverage,'mean_interval_width_C':width,
               'n_test':n,'guarantee':'No finite-sample guarantee under spatial distribution shift'}]).to_csv(TAB/'prediction_uncertainty.csv',index=False)

# Rank acceptability under policy preference scenarios and nondominated fronts.
# Each dimension is a benefit of intervention: high heat, service deficit,
# and blue-green deficit. These are screening proxies, not treatment effects.
def norm(v):
    v=np.asarray(v,float);return (v-v.min())/(v.max()-v.min())
Z=np.column_stack([norm(y),1-norm(g.score15),1-norm(g.f_bluegreen)])
w=np.vstack([np.ones(3)/3,np.random.default_rng(2027).dirichlet([2,2,2],size=500)])
S=Z@w.T
rank=np.argsort(np.argsort(-S,axis=0),axis=0)+1 # 1 = most severe
p20=(rank<=int(np.ceil(.2*n))).mean(axis=1)
meanrank=rank.mean(axis=1);medrank=np.median(rank,axis=1);rank_sd=rank.std(axis=1)
entropy=[]
for row in rank:
    q=np.histogram(row,bins=np.linspace(1,n+1,11))[0].astype(float);q/=q.sum();q=q[q>0]
    entropy.append(-np.sum(q*np.log(q))/np.log(10))

# For three 'more concern' objectives, dominance is defined by being at least
# as severe on all three and strictly more severe on one. Pareto front 1 =
# no other unit dominates it. Dominance is not a welfare ranking.
remaining=np.ones(n,bool);front=np.zeros(n,int);layer=1
while remaining.any():
    ids=np.where(remaining)[0];v=Z[ids]
    nondom=np.ones(len(ids),bool)
    for i in range(len(ids)):
        dominates=np.all(v>=v[i]-1e-12,axis=1)&np.any(v>v[i]+1e-12,axis=1)
        if dominates.any():nondom[i]=False
    front[ids[nondom]]=layer;remaining[ids[nondom]]=False;layer+=1

# Avoid collapsing preference and measurement confidence into a false-precision score.
# A candidate can be robust to policy weights yet have uncertain heat estimates.
g['priority_probability']=p20;g['mean_priority_rank']=meanrank;g['median_priority_rank']=medrank
g['rank_sd']=rank_sd;g['rank_entropy']=entropy;g['pareto_front']=front
g['heat_pred_C']=pt;g['heat_pi_low_C']=lower;g['heat_pi_high_C']=upper
g['heat_interval_width_C']=upper-lower
width_threshold=np.median(upper-lower)
g['priority_class']=np.select([
    (p20>=.8)&(upper-lower<=width_threshold),
    (p20>=.8)&(upper-lower>width_threshold),
    (p20>=.2)&(p20<.8)],
    ['Robust candidate / lower uncertainty','Robust candidate / heat uncertain','Preference-sensitive candidate'],default='Lower-consensus concern')
g['intervention_candidate']=np.select([
    (Z[:,0]>=.7)&(Z[:,1]>=.7),
    (Z[:,0]>=.7)&(Z[:,2]>=.7),
    Z[:,1]>=.7,Z[:,0]>=.7],
    ['Joint heat and service evaluation','Green-shade feasibility evaluation','Service access audit','Urban cooling feasibility evaluation'],default='Targeted local assessment')
g.to_file(OUT/'data/ieee_priority_results.gpkg',driver='GPKG')
g.drop(columns='geometry').to_csv(TAB/'rank_uncertainty_pareto.csv',index=False)
pd.DataFrame([{'scenarios':len(w),'n_high_consensus':int(np.sum(p20>=.8)),
               'n_high_consensus_lower_uncertainty':int(np.sum((p20>=.8)&(upper-lower<=width_threshold))),
               'n_preference_sensitive':int(np.sum((p20>=.2)&(p20<.8))),
               'n_pareto_front1':int(np.sum(front==1)),
               'rank_sd_median':float(np.median(rank_sd)),
               'heat_interval_width_median_C':float(width_threshold)}]).to_csv(TAB/'priority_summary.csv',index=False)

# Limited aggregation test: geographic fixed square neighborhoods, showing MAUP
# sensitivity without pretending these squares are new independent observations.
scales=[]
for meter in (250,500,750,1000):
    ids=spatial_groups(meter);groups_df=pd.DataFrame({'block':ids,'heat':y,'access':g.score15,'green':g.f_bluegreen,'p':p20})
    agg=groups_df.groupby('block').agg(heat=('heat','mean'),access=('access','mean'),green=('green','mean'),p=('p','mean'),n=('p','size'))
    scales.append({'square_grid_m':meter,'units':len(agg),'heat_sd_C':agg.heat.std(),
                   'access_sd':agg.access.std(),'share_mean_priority_prob_gt_0.8':(agg.p>=.8).mean()})
pd.DataFrame(scales).to_csv(TAB/'scale_sensitivity.csv',index=False)

plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
v=res[(res.model=='RF')&(res.features=='combined')]
fig,ax=plt.subplots(figsize=(10,4.5));ax.bar(v.scheme,v.RMSE_C,color='#287e91');ax.set(ylabel='Out-of-fold RMSE (°C)',title='Geographic independence stress test: combined RF');ax.tick_params(axis='x',rotation=34);fig.tight_layout();fig.savefig(FIG/'05_geographic_stress_test.png',dpi=200);plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4));a=res[(res.scheme=='block_1')&(res.model=='RF')&(res.features.isin(feat))];ax.bar(a.features,a.RMSE_C,color='#377f91');ax.set(ylabel='Spatial RMSE (°C)',title='Nested ablation: no guaranteed benefit of additional data');ax.tick_params(axis='x',rotation=20);fig.tight_layout();fig.savefig(FIG/'06_nested_ablation.png',dpi=200);plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(13,4.6))
for ax,col,title,cmap in zip(axs,['priority_probability','pareto_front','heat_interval_width_C'],['Top-quintile acceptability','Pareto severity layer','Heat PI width (°C)'],['YlOrRd','viridis_r','magma']):
    g.plot(column=col,cmap=cmap,ax=ax,legend=True,legend_kwds={'shrink':.66});ax.set_title(title);ax.axis('off')
fig.tight_layout();fig.savefig(FIG/'07_rank_pareto_uncertainty.png',dpi=190,bbox_inches='tight');plt.close(fig)

summary=f'''# Advanced experiment results (3 November 2026)

- The original 537-hex dataset was reused without relabeling.
- **RF 1 km block RMSE:** {res.query("scheme=='block_1' and model=='RF' and features=='combined'").RMSE_C.iloc[0]:.3f}°C. Full eight-scheme validation matrix includes spatial KNN and three statistical/ML baselines.
- **RF contiguous x-strip holdout RMSE:** {res.query("scheme=='region_x' and model=='RF' and features=='combined'").RMSE_C.iloc[0]:.3f}°C; **2 km block holdout:** {res.query("scheme=='block_2' and model=='RF' and features=='combined'").RMSE_C.iloc[0]:.3f}°C.
- **Combined minus morphology RF RMSE:** {observed:+.4f}°C, geographic-block bootstrap 95% CI [{lo:+.4f}, {hi:+.4f}]°C. A zero-crossing interval does not support superiority.
- **Combined RF block-1 residual Moran I:** {next(q[2] for q in diagnostics if q[0]=='block_1' and q[1]=='RF'):.3f}, permutation p={next(q[3] for q in diagnostics if q[0]=='block_1' and q[1]=='RF'):.3f}.
- **Nominal 90% prediction interval:** observed coverage {coverage:.1%}, mean width {width:.3f}°C. This is empirical; no guaranteed coverage under spatial shift.
- **Priority acceptability:** {int(np.sum(p20>=.8))} hexes in the most severe quintile in at least 80% of 501 policy weighting scenarios, among which {int(np.sum((p20>=.8)&(upper-lower<=width_threshold)))} have lower-than-median model interval widths.
- **Pareto front 1:** {int(np.sum(front==1))} nondominated hexes under heat, service-access deficit and blue-green deficit. Pareto position does not establish optimal intervention or causal benefit.

Sources: `outputs/tables/ieee_validation_matrix.csv`, `residual_spatial_diagnostics.csv`, `paired_model_uncertainty.csv`, `prediction_uncertainty.csv`, `rank_uncertainty_pareto.csv`, `priority_summary.csv` and `scale_sensitivity.csv`.
'''
(ROOT/'ppt/IEEE_CURRENT_RESULTS.md').write_text(summary)
print(summary)
