"""Reproducible, offline research extension on the existing NKDA hexagon dataset.

Run from repository root: python run_research_pipeline.py
Does not replace the original Google Earth Engine pipeline or claim independent ground truth.
"""
from pathlib import Path
import csv
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.base import clone
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.model_selection import KFold, GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs'
FIG = OUT / 'PPT_FIGURES'
TAB = OUT / 'tables'
PPT = ROOT / 'ppt'
for d in (FIG, TAB, PPT): d.mkdir(parents=True, exist_ok=True)

g = gpd.read_file(OUT / 'data/hex_results.gpkg')
assert len(g) == 906, 'Expected 906 Chandigarh hexagons; inspect boundary before using'
g = g.to_crs(32643)
xy = np.column_stack([g.geometry.centroid.x, g.geometry.centroid.y])
y = g['LST'].to_numpy(dtype=float)
features = {'spectral':['NDVI','NDBI','MNDWI'],
            'morphology':['f_built','f_veg','f_water'],
            'accessibility':['d_school','d_health','d_green','d_transit','d_shop'],
            'combined':['NDVI','NDBI','MNDWI','f_built','f_veg','f_water','d_school','d_health','d_green','d_transit','d_shop']}
models = {'Mean':DummyRegressor(strategy='mean'),
          'Ridge':make_pipeline(SimpleImputer(strategy='median'),Ridge(alpha=10.)),
          'RF':make_pipeline(SimpleImputer(strategy='median'),RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=0.8,n_jobs=-1,random_state=42)),
          'HGB':make_pipeline(SimpleImputer(strategy='median'),HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=12,l2_regularization=5,random_state=42))}

# Fixed 1km geographic blocks, assigned to five folds: a genuine unseen-block test.
blocks = np.floor((xy-xy.min(axis=0))/1000).astype(int)
groups = blocks[:,0] * 10000 + blocks[:,1]
assert len(np.unique(groups)) >= 5
splitters = {'random':list(KFold(n_splits=5,shuffle=True,random_state=42).split(y)),
             'spatial_1km':list(GroupKFold(n_splits=5).split(y,groups=groups))}
rows=[]
preds={}
for name,cols in features.items():
    X=g[cols].replace([np.inf,-np.inf],np.nan).to_numpy(dtype=float)
    for method,estimator in models.items():
        for split,folds in splitters.items():
            p=np.full(len(y),np.nan)
            fold_rmse=[]
            for train,test in folds:
                model=clone(estimator)
                model.fit(X[train],y[train]); p[test]=model.predict(X[test])
                fold_rmse.append(np.sqrt(mean_squared_error(y[test],p[test])))
            rows.append({'features':name,'model':method,'validation':split,'R2_oof':r2_score(y,p),
                         'RMSE_oof_C':np.sqrt(mean_squared_error(y,p)), 'fold_RMSE_sd_C':np.std(fold_rmse,ddof=1),
                         'n_hex':len(y),'n_spatial_blocks':len(np.unique(groups))})
            preds[(name,method,split)]=p
cv=pd.DataFrame(rows).sort_values(['features','model','validation'])
cv.to_csv(TAB/'spatial_cv_results.csv',index=False)
best=cv[(cv.features=='combined')&(cv.validation=='spatial_1km')].sort_values('RMSE_oof_C').iloc[0]
best_model=best['model']

# Stability of lowest liveability quintile under a continuum of AHP/equal weights.
# These are derived from existing index columns, so they are a screening tool, not validated harm outcomes.
cols=['NDVI','LST','f_bluegreen','score15','d_transit_cap']
positive=[True,False,True,True,False]
Z=[]
for col,pos in zip(cols,positive):
    v=g[col].to_numpy(float); z=(v-np.min(v))/(np.max(v)-np.min(v))
    Z.append(z if pos else 1-z)
Z=np.array(Z).T
ahp=np.array([0.137,0.137,0.079,0.403,0.244]); ahp/=ahp.sum()
rng=np.random.default_rng(42)
weights=[ahp,np.repeat(0.2,5)]
weights.extend(rng.dirichlet(ahp*25,300))
scores=np.stack([Z@w for w in weights],axis=1)
priority=scores <= np.quantile(scores,0.2,axis=0)
g['priority_stability']=priority.mean(axis=1)
g['priority_ahp']=priority[:,0].astype(int)
g['priority_equal']=priority[:,1].astype(int)
g['intervention_type']=np.where((Z[:,1]<0.3)&(Z[:,3]<0.4),'Cooling + services',
                         np.where(Z[:,1]<0.3,'Heat mitigation',
                         np.where(Z[:,3]<0.4,'Service access','Mixed improvement')))
g[['hex_id','priority_stability','priority_ahp','priority_equal','intervention_type']].to_csv(TAB/'intervention_priority.csv',index=False)
g.to_file(OUT/'data/research_extension.gpkg',driver='GPKG')

# Portable slides figures.
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(figsize=(8,4.5))
t=cv[cv.features=='combined'].pivot(index='model',columns='validation',values='RMSE_oof_C').reindex(list(models))
t.plot(kind='bar',ax=ax,color=['#29a5a0','#ec8b50'],width=.7)
ax.set(ylabel='Out-of-fold RMSE (°C)',xlabel='',title='Heat prediction: random vs 1 km spatial CV')
ax.legend(title='Validation');ax.tick_params(axis='x',rotation=0)
fig.tight_layout();fig.savefig(FIG/'01_spatial_cv.png',dpi=190);plt.close(fig)

fig,ax=plt.subplots(figsize=(8,4.5))
t=cv[(cv.model==best_model)&(cv.validation=='spatial_1km')].set_index('features').loc[list(features)]
ax.bar(t.index,t.RMSE_oof_C,color='#327e9c')
ax.set(ylabel='Spatial CV RMSE (°C)',title=f'Feature-group ablation: {best_model}')
fig.tight_layout();fig.savefig(FIG/'02_ablation.png',dpi=190);plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(11,4.5))
g.plot(column='priority_stability',ax=axs[0],cmap='YlOrRd',vmin=0,vmax=1,legend=True,legend_kwds={'label':'Share of weighting schemes in lowest quintile'})
g.plot(column='intervention_type',ax=axs[1],categorical=True,legend=True,legend_kwds={'loc':'lower center','bbox_to_anchor':(.5,-.23),'ncol':2,'fontsize':7})
for ax,title in zip(axs,['Priority stability','Indicative intervention type']):ax.set_title(title);ax.axis('off')
fig.tight_layout();fig.savefig(FIG/'03_intervention_map.png',dpi=190,bbox_inches='tight');plt.close(fig)

fig,ax=plt.subplots(figsize=(6.5,4.5));p=preds[('combined',best_model,'spatial_1km')]
ax.scatter(y,p,s=15,alpha=.6,c='#27879d');ax.plot([y.min(),y.max()],[y.min(),y.max()],'--',color='#d87148')
ax.set(xlabel='Existing satellite-derived LST (°C)',ylabel='Spatially held-out prediction (°C)',title=f'{best_model} spatial CV: R²={r2_score(y,p):.3f}')
fig.tight_layout();fig.savefig(FIG/'04_predicted_vs_observed.png',dpi=190);plt.close(fig)

stable=int((g.priority_stability>=.8).sum())
overlap=int((g.priority_ahp & g.priority_equal).sum())
baseline=int(g.priority_ahp.sum())
rho=spearmanr(scores[:,0],scores[:,1]).statistic
summary=f'''# Current presentable results (automatically generated)

All results below are **VERIFIED computations on the existing exported 537 hexagons**, not independent field validation.

- Spatial CV: 1 km geographic groups, 5 held-out folds, {len(np.unique(groups))} unique blocks; random 5-fold comparison.
- Best combined-feature model under spatial CV: **{best_model}**, RMSE **{best.RMSE_oof_C:.3f} °C**, out-of-fold R² **{best.R2_oof:.3f}**.
- Baseline mean, Ridge, RF, HGB, and four feature groups were evaluated. Full matrix: `outputs/tables/spatial_cv_results.csv`.
- Intervention screening: **{stable}** hexagons are in the bottom liveability quintile under at least 80% of {len(weights)} weighting schemes.
- Equal weights and original AHP overlap: **{overlap} / {baseline}** original priority hexagons. Full-rank Spearman rho **{rho:.3f}**.

## Slide figures

1. `outputs/PPT_FIGURES/01_spatial_cv.png`
2. `outputs/PPT_FIGURES/02_ablation.png`
3. `outputs/PPT_FIGURES/03_intervention_map.png`
4. `outputs/PPT_FIGURES/04_predicted_vs_observed.png`

## Important safeguards

- LST target and spectral predictors share remote-sensing acquisition context; this is spatial interpolation evaluation, **not causal attribution or independent forecast skill**.
- The original 2016 Dynamic World agreement (21.21%) and ESA WorldCover 2021 agreement (43.79%) raise substantial concerns for temporal land-cover change claims.
- Intervention labels are exploratory rules, not independently validated policy recommendations.
- Spatial block size is fixed at 1 km; further buffer / block-size robustness is needed before publication.
'''
(PPT/'CURRENT_PRESENTABLE_RESULTS.md').write_text(summary)
(OUT/'PPT_RESULTS.md').write_text(summary)
ledger=[['claim','claim_type','source','script','dataset','result_file','figure','verified','notes'],
        ['Best spatial-CV RMSE','VERIFIED RESULT','existing NKDA hex export','run_research_pipeline.py','hex_results.gpkg','outputs/tables/spatial_cv_results.csv','outputs/PPT_FIGURES/01_spatial_cv.png','true','1 km GroupKFold, target satellite-derived LST'],
        ['Priority weight stability','VERIFIED RESULT','existing NKDA hex export','run_research_pipeline.py','hex_results.gpkg','outputs/tables/intervention_priority.csv','outputs/PPT_FIGURES/03_intervention_map.png','true','Scenario analysis, not intervention effectiveness'],
        ['Temporal LULC trends','LIMITED RESULT','existing GEE run','src/newtown_smart_city_analysis.py','lulc_2016/2021/2026.tif','outputs/tables/lulc_areas.csv','outputs/figures/03_lulc_areas.png','false','Independent reference disagreement and differing Sentinel processing levels']]
with (OUT/'EVIDENCE_LEDGER.csv').open('w',newline='') as f:csv.writer(f).writerows(ledger)
print(summary)
