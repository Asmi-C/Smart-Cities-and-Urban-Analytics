"""Train-only spatial cross-fit Gaussian-process residual correction experiment."""
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd
from sklearn.ensemble import RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parent;g=gpd.read_file(R/'outputs/data/hex_results.gpkg').to_crs(32643)
xy=np.c_[g.geometry.centroid.x,g.geometry.centroid.y];y=g.LST.to_numpy(float)
cols=['f_built','f_veg','f_water','NDVI','NDBI','MNDWI','d_school','d_health','d_green','d_transit','d_shop']
X=np.c_[g[cols].to_numpy(float),(xy-xy.mean(0))/1000]
blocks=np.floor((xy-xy.min(0))/1000).astype(int);groups=blocks[:,0]*10000+blocks[:,1]
def rf():return RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1)
pred=np.empty(len(y));baseline=np.empty(len(y))
for fold,(tr,te) in enumerate(GroupKFold(5).split(X,y,groups=groups)):
    p=rf().fit(X[tr],y[tr]);baseline[te]=p.predict(X[te])
    rr=np.empty(len(tr))
    for a,b in GroupKFold(4).split(X[tr],y[tr],groups=groups[tr]):
        rr[b]=y[tr[b]]-rf().fit(X[tr[a]],y[tr[a]]).predict(X[tr[b]])
    kernel=ConstantKernel(1.0,constant_value_bounds='fixed')*Matern(length_scale=.7,nu=1.5,length_scale_bounds='fixed')+WhiteKernel(noise_level=.35,noise_level_bounds='fixed')
    gp=GaussianProcessRegressor(kernel=kernel,optimizer=None,normalize_y=False,alpha=1e-6)
    gp.fit(xy[tr]/1000,rr)
    pred[te]=baseline[te]+gp.predict(xy[te]/1000)
    print('GP completed outer fold',fold,flush=True)
nb=cKDTree(xy).query(xy,k=9)[1][:,1:]
def mI(v):z=v-v.mean();return np.sum(z[:,None]*z[nb])/(8*np.sum(z*z))
rows=[]
for name,p in [('RF_coordinates_fixed',baseline),('RF_coordinates_plus_crossfit_GP',pred)]:
    rows.append({'model':name,'RMSE_C':np.sqrt(mean_squared_error(y,p)),'MAE_C':mean_absolute_error(y,p),'R2':r2_score(y,p),'residual_Moran_I':mI(y-p)})
pd.DataFrame(rows).to_csv(R/'outputs/tables/gp_spatial_residual_comparison.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
