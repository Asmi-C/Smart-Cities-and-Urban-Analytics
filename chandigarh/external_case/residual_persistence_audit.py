"""Diagnostic of unseen-date residual persistence, never fed into held-date models."""
from pathlib import Path
import sqlite3
import numpy as np,pandas as pd
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import pearsonr,spearmanr
from scipy.spatial import cKDTree,distance
R=Path(__file__).resolve().parents[1];F=R/'outputs/tables'
d=pd.read_csv(F/'multi_date_residual_predictions.csv');d=d[d.model=='RF_zsource_ztarget']
dates=sorted(d.date.unique());early=set(dates[:len(dates)//2]);late=set(dates[len(dates)//2:])
piv=d.pivot(index='hex_id',columns='date',values='residual_C')
records=[]
for h,z in piv.iterrows():
    a=z[list(early)].dropna();b=z[list(late)].dropna()
    if len(a)<2 or len(b)<2:continue
    records.append({'hex_id':h,'early_mean_residual_C':a.mean(),'late_mean_residual_C':b.mean(),
       'overall_bias_C':z.mean(),'n_observed_dates':int(z.notna().sum()),
       'same_sign_between_periods':bool(np.sign(a.mean())==np.sign(b.mean()))})
q=pd.DataFrame(records);q.to_csv(F/'residual_persistence.csv',index=False)
with sqlite3.connect(R/'outputs/data/hex_results.gpkg') as con:
    xy=pd.read_sql_query('SELECT h.hex_id,(r.minx+r.maxx)/2 AS x,(r.miny+r.maxy)/2 AS y FROM hex_results h JOIN rtree_hex_results_geom r ON h.fid=r.id',con)
    context=pd.read_sql_query('SELECT hex_id,f_built,f_veg,f_water,d_built,NDBI,NDVI,MNDWI FROM hex_results',con)
plot=q.merge(xy,on='hex_id');fig,ax=plt.subplots(figsize=(8,7));
variogram=[];local=[];rng_local=np.random.default_rng(143)
for acquisition,group in d.groupby('date'):
    g=group.merge(xy,on='hex_id');points=g[['x','y']].to_numpy();res=g.residual_C.to_numpy()
    if len(g)<20:continue
    D=distance.pdist(points);sem=distance.pdist(res[:,None],metric='sqeuclidean')/2
    edges=np.arange(0,5500,500)
    for low,high in zip(edges[:-1],edges[1:]):
        mask=(D>=low)&(D<high)
        if mask.any():variogram.append({'date':acquisition,'distance_low_m':low,'distance_high_m':high,
                            'n_pairs':int(mask.sum()),'semivariance_C2':float(sem[mask].mean())})
    nb=cKDTree(points).query(points,k=9)[1][:,1:];z=res-res.mean();z/=max(res.std(),1e-9)
    lag=z[nb].mean(axis=1);observed=z*lag
    # Per-unit local permutation p-values; exploratory, unadjusted for multiplicity.
    null=np.empty((199,len(z)))
    for j in range(199):
        perm=rng_local.permutation(z);null[j]=z*perm[nb].mean(axis=1)
    pv=(1+(np.abs(null)>=np.abs(observed)).sum(axis=0))/200
    for hid,value,p,zi,li in zip(g.hex_id,observed,pv,z,lag):
        cls='high_high' if zi>0 and li>0 else 'low_low' if zi<0 and li<0 else 'discordant'
        local.append({'date':acquisition,'hex_id':hid,'local_Moran_proxy':value,'permutation_p_unadjusted':p,
                      'cluster':cls if p<=.05 else 'not_significant'})
pd.DataFrame(variogram).to_csv(F/'multidate_residual_semivariogram.csv',index=False)
pd.DataFrame(local).to_csv(F/'multidate_local_residual_clusters.csv',index=False)
assoc=[]
for col in context.columns.drop('hex_id'):
    z=q.merge(context[['hex_id',col]],on='hex_id').dropna(subset=[col,'overall_bias_C'])
    if len(z)>=30:
        coef=spearmanr(z.overall_bias_C,z[col])
        assoc.append({'feature':col,'n_hex':len(z),'Spearman_residual_bias':coef.statistic,
         'naive_p_not_spatially_valid':coef.pvalue,'warning':'2026-era original static layers; descriptive only, not verified historical morphology'})
pd.DataFrame(assoc).to_csv(F/'residual_morphology_correlations.csv',index=False)
v=np.abs(plot.overall_bias_C).quantile(.95);v=max(v,.01)
scatter=ax.scatter(plot.x,plot.y,c=plot.overall_bias_C,s=40,cmap='RdBu_r',vmin=-v,vmax=v)
ax.set_aspect('equal');ax.set_title('Cross-acquisition mean held-date residual bias\nRetrospective diagnostic; not a learned correction')
ax.set_xlabel('Projected eastings (m)');ax.set_ylabel('Projected northings (m)');fig.colorbar(scatter,ax=ax,label='LST anomaly residual (°C)')
fig.tight_layout();out=R/'outputs/figures';out.mkdir(parents=True,exist_ok=True)
fig.savefig(out/'persistent_residual_bias.png',dpi=180);plt.close(fig)
if len(q)>=10:
    co=pearsonr(q.early_mean_residual_C,q.late_mean_residual_C)
    print('Residual early/late correlation',co.statistic,'p',co.pvalue,'same signs',q.same_sign_between_periods.mean())
    # Geographic blocks, not individual hexes, are the resampling unit.
    plot['block']=((plot.x//1000).astype(int)).astype(str)+'_'+((plot.y//1000).astype(int)).astype(str)
    blocks=list(plot.groupby('block'));rng=np.random.default_rng(19);boot=[]
    for _ in range(3000):
        sampled=rng.integers(0,len(blocks),len(blocks));z=pd.concat([blocks[i][1] for i in sampled])
        if z.early_mean_residual_C.std()>0 and z.late_mean_residual_C.std()>0:
            boot.append(np.corrcoef(z.early_mean_residual_C,z.late_mean_residual_C)[0,1])
    summary={'n_hex':len(q),'n_dates':len(dates),'n_spatial_blocks':len(blocks),
             'early_late_residual_correlation':co.statistic,'naive_hex_p_not_valid_spatially':co.pvalue,
             'block_bootstrap_CI_low':float(np.quantile(boot,.025)),
             'block_bootstrap_CI_high':float(np.quantile(boot,.975)),
             'matching_bias_sign_fraction':q.same_sign_between_periods.mean()}
    pd.DataFrame([summary]).to_csv(F/'residual_persistence_summary.csv',index=False)
print('Analyzed',len(q),'hexagons across',len(dates),'dates')
