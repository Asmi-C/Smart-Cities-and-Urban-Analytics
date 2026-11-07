"""Prespecified 12-origin, 2-seed spatial-validation stress test."""
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd
from sklearn.model_selection import GroupKFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from scipy.spatial import cKDTree

R=Path(__file__).resolve().parent;g=gpd.read_file(R/'outputs/data/hex_results.gpkg').to_crs(32645)
xy=np.c_[g.geometry.centroid.x,g.geometry.centroid.y];y=g.LST.to_numpy(float)
cols=['f_built','f_veg','f_water','NDVI','NDBI','MNDWI','d_school','d_health','d_green','d_transit','d_shop']
X=g[cols].to_numpy(float);xc=(xy-xy.mean(0))/1000
nb=cKDTree(xy).query(xy,k=9)[1][:,1:]
def moran(v):
    z=v-v.mean();return np.sum(z[:,None]*z[nb])/(8*np.sum(z*z))
offsets=[(0,0),(.25,0),(.5,0),(.75,0),(0,.25),(0,.5),(0,.75),(.25,.25),(.5,.5),(.75,.75),(.25,.75),(.75,.25)]
rows=[]
for seed in (42,2026):
    for j,(ox,oy) in enumerate(offsets):
        blk=np.floor((xy-xy.min(0))/1000+np.array([ox,oy])).astype(int)
        grp=blk[:,0]*10000+blk[:,1]
        folds=list(GroupKFold(5).split(X,y,groups=grp))
        for name,features in [('RF',X),('RF + coordinates',np.c_[X,xc])]:
            pred=np.empty(len(y))
            for tr,te in folds:
                m=RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=seed,n_jobs=-1)
                m.fit(features[tr],y[tr]);pred[te]=m.predict(features[te])
            rows.append({'seed':seed,'origin_id':j,'offset_x_fraction':ox,'offset_y_fraction':oy,
                         'model':name,'RMSE_C':np.sqrt(mean_squared_error(y,pred)),
                         'MAE_C':mean_absolute_error(y,pred),'R2':r2_score(y,pred),
                         'residual_Moran_I':moran(y-pred),'unique_blocks':len(np.unique(grp))})
        print('Completed',seed,j,flush=True)
d=pd.DataFrame(rows);out=R/'outputs/tables/shifted_block_validation.csv';d.to_csv(out,index=False)
p=d.pivot(index=['seed','origin_id'],columns='model',values='RMSE_C')
delta=p['RF + coordinates']-p['RF']
per_origin=delta.groupby(level='origin_id').mean().to_numpy()
rng=np.random.default_rng(902);boot=np.array([rng.choice(per_origin,len(per_origin),replace=True).mean() for _ in range(5000)])
mp=d.pivot(index=['seed','origin_id'],columns='model',values='residual_Moran_I')
summary=pd.DataFrame([{'n_comparisons':len(delta),'n_offsets':len(offsets),'n_seeds':2,
                       'mean_delta_RMSE_C':delta.mean(),'median_delta_RMSE_C':delta.median(),
                       'offset_bootstrap_low_95_C':np.quantile(boot,.025),'offset_bootstrap_high_95_C':np.quantile(boot,.975),
                       'n_coordinate_better':int((delta<0).sum()),'fraction_coordinate_better':(delta<0).mean(),
                       'n_coordinate_lower_Moran':int((mp['RF + coordinates']<mp['RF']).sum()),
                       'mean_RF_RMSE_C':p['RF'].mean(),'mean_RF_coordinates_RMSE_C':p['RF + coordinates'].mean()}])
summary.to_csv(R/'outputs/tables/shifted_block_summary.csv',index=False)
print(summary.to_string(index=False))
