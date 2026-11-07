"""Train-only inner geographic model selection on existing 537 NKDA hexes."""
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd
from scipy.spatial import cKDTree
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score

R=Path(__file__).resolve().parent;g=gpd.read_file(R/'outputs/data/hex_results.gpkg').to_crs(32645)
xy=np.c_[g.geometry.centroid.x,g.geometry.centroid.y];y=g.LST.to_numpy(float)
basecols=['f_built','f_veg','f_water','NDVI','NDBI','MNDWI','d_school','d_health','d_green','d_transit','d_shop']
X=np.c_[g[basecols].to_numpy(float),(xy-xy.mean(0))/1000]
blk=np.floor((xy-xy.min(0))/1000).astype(int);groups=blk[:,0]*10000+blk[:,1]
configs=[{'min_samples_leaf':l,'max_features':mf,'max_depth':depth} for l in (3,8) for mf in (.6,1.0) for depth in (8,None)]
def fit(config,xx,yy):return RandomForestRegressor(n_estimators=120,random_state=42,n_jobs=-1,**config).fit(xx,yy)
out=np.full(len(y),np.nan);fixed=np.full(len(y),np.nan);selection=[]
for k,(tr,te) in enumerate(GroupKFold(5).split(X,y,groups=groups)):
    inner=list(GroupKFold(3).split(X[tr],y[tr],groups=groups[tr]))
    errors=[]
    for config in configs:
        scores=[]
        for a,b in inner:
            m=fit(config,X[tr[a]],y[tr[a]])
            scores.append(np.sqrt(mean_squared_error(y[tr[b]],m.predict(X[tr[b]]))))
        errors.append(np.mean(scores))
    ix=int(np.argmin(errors));chosen=configs[ix]
    out[te]=fit(chosen,X[tr],y[tr]).predict(X[te])
    fixed[te]=RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1).fit(X[tr],y[tr]).predict(X[te])
    selection.append({'outer_fold':k,'chosen_config':str(chosen),'inner_mean_RMSE_C':errors[ix],
                      'outer_RMSE_C':np.sqrt(mean_squared_error(y[te],out[te]))})
    print('Nested fold',k,chosen,flush=True)
nb=cKDTree(xy).query(xy,k=9)[1][:,1:]
def Moran(r):
    z=r-r.mean();I=np.sum(z[:,None]*z[nb])/(8*np.sum(z*z))
    rng=np.random.default_rng(12);null=[]
    for _ in range(999):
        p=rng.permutation(z);null.append(np.sum(p[:,None]*p[nb])/(8*np.sum(p*p)))
    return I,(1+np.sum(abs(np.array(null)-np.mean(null))>=abs(I-np.mean(null))))/1000
rows=[]
for name,p in [('fixed_RF_coordinates',fixed),('nested_tuned_RF_coordinates',out)]:
    I,pvalue=Moran(y-p)
    rows.append({'model':name,'RMSE_C':np.sqrt(mean_squared_error(y,p)),'MAE_C':mean_absolute_error(y,p),
                 'R2':r2_score(y,p),'residual_Moran_I':I,'Moran_permutation_p':pvalue})
pd.DataFrame(rows).to_csv(R/'outputs/tables/nested_spatial_model_results.csv',index=False)
pd.DataFrame(selection).to_csv(R/'outputs/tables/nested_spatial_choices.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
