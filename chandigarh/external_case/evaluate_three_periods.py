"""Three same-sensor acquisition transfer with frozen RF hyperparameters.

Evaluates 2021+2024→2026 on hexes clear in all three, no 2026 labels in fitting.
"""
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1];D=R/'external_case/data'
years={'2021':'20210324','2024':'20240401','2026':'20260322'}
tables={year:pd.read_csv(D/f'landsat_hex_LC08_{date}.csv') for year,date in years.items()}
df=None
for year,t in tables.items():
    t=t.rename(columns={c:c+'_'+year for c in t.columns if c!='hex_id'})
    df=t if df is None else df.merge(t,on='hex_id')
features=['NDVI','NDBI','MNDWI']
needed=[c+'_'+y for y in years for c in features+['LST']]
df=df.loc[np.isfinite(df[needed]).all(axis=1)].copy()
assert len(df)>=100,f'Only {len(df)} three-period clear hexes; withhold claims'
def model():return RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1)
def data(year):return df[[c+'_'+year for c in features]].to_numpy(),df['LST_'+year].to_numpy()
X21,y21=data('2021');X24,y24=data('2024');X26,y26=data('2026')
pred=model().fit(np.vstack([X21,X24]),np.r_[y21,y24]).predict(X26)
pred21=model().fit(X21,y21).predict(X26)
pred24=model().fit(X24,y24).predict(X26)
g=gpd.read_file(R/'outputs/data/hex_results.gpkg').to_crs(32643).set_index('hex_id').loc[df.hex_id]
xy=np.c_[g.geometry.centroid.x,g.geometry.centroid.y];nb=cKDTree(xy).query(xy,k=9)[1][:,1:]
def moran(err):
    z=err-err.mean();I=np.sum(z[:,None]*z[nb])/(8*np.sum(z*z))
    rng=np.random.default_rng(924);null=[]
    for _ in range(999):
        t=rng.permutation(z);null.append(np.sum(t[:,None]*t[nb])/(8*np.sum(t*t)))
    nu=np.asarray(null);return I,(1+np.sum(abs(nu-nu.mean())>=abs(I-nu.mean())))/1000
rows=[]
for name,p in [('2021_to_2026',pred21),('2024_to_2026',pred24),('2021plus2024_to_2026',pred)]:
    I,pval=moran(y26-p)
    rows.append({'experiment':name,'n_hex':len(df),'RMSE_C':np.sqrt(mean_squared_error(y26,p)),
                 'MAE_C':mean_absolute_error(y26,p),'R2':r2_score(y26,p),
                 'residual_Moran_I':I,'Moran_p':pval,'n_training_records':len(y21)*2 if 'plus' in name else len(y21)})
pd.DataFrame(rows).to_csv(R/'outputs/tables/three_period_transfer.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
