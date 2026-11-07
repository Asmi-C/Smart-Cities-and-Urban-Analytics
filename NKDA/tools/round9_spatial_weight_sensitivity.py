"""Permutation Moran sensitivity; 199 random permutations per date/model/weights."""
from pathlib import Path
import sqlite3
import numpy as np,pandas as pd
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1]
pred=pd.read_csv(R/'outputs/tables/multi_date_residual_predictions.csv')
c=sqlite3.connect(R/'outputs/data/hex_results.gpkg')
xy=pd.read_sql_query('SELECT h.hex_id,(r.minx+r.maxx)/2 x,(r.miny+r.maxy)/2 y FROM hex_results h JOIN rtree_hex_results_geom r ON h.fid=r.id',c).set_index('hex_id');c.close()
rng=np.random.default_rng(3301);rows=[]
for (date,model),g in pred.groupby(['date','model']):
    p=xy.loc[g.hex_id][['x','y']].to_numpy();z=g.residual_C.to_numpy();z=z-z.mean();ss=float(z@z)
    if ss<1e-12:continue
    tree=cKDTree(p);n=len(z)
    for k in [4,8,12]:
        idx=tree.query(p,k=min(k+1,n))[1][:,1:]
        def stat(v):return float(np.sum(v[:,None]*v[idx])/(idx.shape[1]*ss))
        val=stat(z);null=np.array([stat(rng.permutation(z)) for _ in range(199)])
        rows.append({'date':date,'model':model,'weights':f'kNN_{k}','n':n,'Moran_I':val,'permutation_two_sided_p':(1+np.sum(np.abs(null)>=abs(val)))/200})
    neighbors=tree.query_ball_point(p,r=550)
    pairs=[(i,j) for i,ns in enumerate(neighbors) for j in ns if j!=i]
    if pairs:
        ii,jj=np.array(pairs).T;S=len(pairs)
        def stat(v):return float(n*np.sum(v[ii]*v[jj])/(S*ss))
        val=stat(z);null=np.array([stat(rng.permutation(z)) for _ in range(199)])
        rows.append({'date':date,'model':model,'weights':'distance_550m','n':n,'Moran_I':val,'permutation_two_sided_p':(1+np.sum(np.abs(null)>=abs(val)))/200})
out=pd.DataFrame(rows);out.to_csv(R/'outputs/tables/residual_weights_sensitivity.csv',index=False)
print(out.groupby(['model','weights'])[['Moran_I','permutation_two_sided_p']].mean().round(3))
