"""Re-evaluate cached OSM walking-distance and WorldPop proxy columns.

This DOES NOT requery OSM, nor assert independent verification of historical
POIs or raster pixel semantics. The original Earth Engine procedure uses
WorldPop/GP/100m/pop 2020 EE Reducer.sum at scale 100 m.
"""
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd
from scipy.stats import spearmanr
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

R=Path(__file__).resolve().parents[1]
g=gpd.read_file(R/'outputs/data/hex_results.gpkg').to_crs(32643)
p=np.maximum(g['pop'].to_numpy(float),0)
types=['school','health','green','transit','shop']
dist=np.column_stack([g[f'd_{t}'].to_numpy(float) for t in types])
walk=80.0 # metres/minute exactly 4.8 km/h from original protocol
rows=[]
for j,t in enumerate(types):
    d=dist[:,j]; finite=np.isfinite(d)
    row={'category':t,'n_hex':len(g),'finite_nearest_n':int(finite.sum()),
         'median_nearest_m':float(np.median(d[finite])) if finite.any() else np.nan,
         'population_2020_proxy_total':p.sum(),
         'population_weighted_nearest_m':float(np.average(d[finite],weights=p[finite])) if finite.any() else np.nan}
    for minutes in [5,10,15]:
        within=d<=walk*minutes
        row[f'hexes_within_{minutes}min']=int(within.sum())
        row[f'population_within_{minutes}min']=float(p[within].sum())
        row[f'population_pct_within_{minutes}min']=100*float(p[within].sum()/p.sum())
    rows.append(row)
all15=np.all(dist<=1200,axis=1)
rows.append({'category':'all_five','n_hex':len(g),
             'population_2020_proxy_total':p.sum(),
             'hexes_within_15min':int(all15.sum()),
             'population_within_15min':float(p[all15].sum()),
             'population_pct_within_15min':100*float(p[all15].sum()/p.sum())})
pd.DataFrame(rows).to_csv(R/'outputs/tables/network_accessibility.csv',index=False)

score=np.mean(dist<=1200,axis=1)
assert np.allclose(score,g['score15'].to_numpy(float)),'Cached 15min fraction incompatible with source distances'
xy=np.c_[g.geometry.centroid.x,g.geometry.centroid.y]
nb=cKDTree(xy).query(xy,k=9)[1][:,1:]
def moran(z):
    z=z-z.mean(); I=np.sum(z[:,None]*z[nb])/(8*np.sum(z*z))
    rng=np.random.default_rng(2468); null=np.asarray([np.sum(q[:,None]*q[nb])/(8*np.sum(q*q)) for q in (rng.permutation(z) for _ in range(999))]);
    return I,(1+np.sum(abs(null-null.mean())>=abs(I-null.mean())))/1000
def gini(v,weights):
    order=np.argsort(v); x=v[order];w=weights[order]; w=w/w.sum(); mean=np.sum(w*x)
    if mean<=0:return np.nan
    return np.sum(w[:,None]*w[None,:]*np.abs(x[:,None]-x[None,:]))/(2*mean)

equity={'n_hex':len(g),'population_2020_proxy_total':p.sum(),
        'moran_I_nearest8':moran(score)[0],'moran_permutation_p':moran(score)[1],
        'unweighted_gini_service_fraction':gini(score,np.ones(len(g))),
        'population_weighted_gini_service_fraction':gini(score,p),
        'population_with_zero_of_five_15min':p[score==0].sum(),
        'population_with_all_five_15min':p[score==1].sum(),
        'population_weighted_service_fraction':np.average(score,weights=p),
        'spearman_LST_vs_access_deficit':spearmanr(g.LST.to_numpy(),1-score).statistic,
        'scope':'CACHED OSM network distances and modelled WorldPop 2020 counts; source POIs not revalidated'}
pd.DataFrame([equity]).to_csv(R/'outputs/tables/accessibility_equity.csv',index=False)

persist=pd.read_csv(R/'outputs/tables/persistent_heat_hexes.csv')
merged=persist.merge(g[['hex_id','pop','score15','f_bluegreen','LST']+['d_'+t for t in types]],on='hex_id',validate='one_to_one')
cut=np.quantile(g.score15,.2)
merged['low_access']=merged.score15<=cut
merged['joint_persistent_low_access']=(merged.hotspot_type=='persistent_hot')&merged.low_access
merged['priority_type']=np.select([merged.joint_persistent_low_access,
     merged.hotspot_type=='persistent_hot',merged.low_access],
     ['persistent_heat_low_access','persistent_heat_only','access_deficit_only'],default='other')
merged['pop_2020_proxy']=merged['pop']
merged['boundary_registration_uncertainty_m_RMS']=640
high_pop_cut=float(np.quantile(merged['pop'],.75))
merged['high_population_proxy']=merged['pop']>=high_pop_cut
merged['blue_green_deficit_proxy']=1-merged['f_bluegreen']
merged['planning_typology']=np.select([
    (merged.hotspot_type=='persistent_hot')&merged.high_population_proxy&merged.low_access,
    (merged.hotspot_type=='persistent_hot')&merged.high_population_proxy&~merged.low_access,
    (merged.hotspot_type!='persistent_hot')&merged.low_access],
    ['A_persistent_heat_high_pop_poor_access','B_persistent_heat_high_pop_better_access',
     'C_other_heat_poor_access'],default='D_other_or_lower_burden')
merged.to_csv(R/'outputs/tables/planning_candidate_profiles.csv',index=False)
sens=[]
for a_pct in [.2,.4]:
    for pop_pct in [.5,.75]:
        poor=merged.score15<=np.quantile(g.score15,a_pct)
        high=merged['pop']>=np.quantile(merged['pop'],pop_pct)
        sel=(merged.hotspot_type=='persistent_hot')&poor&high
        sens.append({'access_quantile':a_pct,'population_quantile':pop_pct,
                     'n_type_A':int(sel.sum()),'estimated_population_2020_type_A':merged.loc[sel,'pop'].sum(),
                     'note':'Threshold sensitivity only; no verified intervention feasibility'})
pd.DataFrame(sens).to_csv(R/'outputs/tables/planning_typology_sensitivity.csv',index=False)

hottest=g.LST.to_numpy()>=np.quantile(g.LST.to_numpy(),.8)
low=g.score15.to_numpy()<=cut
ind=g.set_index('hex_id').loc[merged.hex_id]
def poprow(name,mask,values):return {'group':name,'n_hex':int(np.sum(mask)),'estimated_population_2020':float(np.asarray(values)[mask].sum()),'population_source':'original WorldPop 2020 hex proxy'}
poprows=[poprow('all_537_2020_original_hexes',np.ones(len(g),bool),p),
         poprow('2026_original_composite_hottest_quintile',hottest,p),
         poprow('2026_original_low_access_quintile',low,p),
         poprow('2026_original_joint_heat_access',hottest&low,p)]
pm=merged['pop'].to_numpy(float)
for name,mask in [('2021_2024_2026_common_clear_hexes',np.ones(len(merged),bool)),
                  ('persistent_hot_2of3',merged.hotspot_type=='persistent_hot'),
                  ('persistent_hot_plus_low_access',merged.joint_persistent_low_access),
                  ('2026_new_hot_only',merged.hotspot_type=='emerging_2026_hot')]:
    poprows.append(poprow(name,mask,pm))
pd.DataFrame(poprows).to_csv(R/'outputs/tables/final_population_exposure.csv',index=False)
fig,axs=plt.subplots(1,2,figsize=(12,6))
g.assign(service_coverage=score).plot(column='service_coverage',ax=axs[0],cmap='viridis',legend=True,edgecolor='none')
axs[0].set_title('Five-category OSM network access (15 min)')
g.assign(population_proxy=p).plot(column='population_proxy',ax=axs[1],cmap='magma',legend=True,edgecolor='none')
axs[1].set_title('WorldPop 2020 modelled population by hex')
for ax in axs:ax.set_axis_off()
fig.suptitle('Exploratory NKDA overlay • boundary registration RMS ~640 m • POIs unverified')
fig.tight_layout(); (R/'outputs/figures').mkdir(parents=True,exist_ok=True)
fig.savefig(R/'outputs/figures/network_access_population_audit.png',dpi=170);plt.close(fig)
print(pd.DataFrame(rows)[['category','population_pct_within_15min']].to_string(index=False))
print(pd.DataFrame([equity]).to_string(index=False))
print(pd.DataFrame(poprows).to_string(index=False))
