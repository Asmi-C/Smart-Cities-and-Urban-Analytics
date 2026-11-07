"""Date-level 999-permutation residual Moran test on OOD model predictions."""
from pathlib import Path
import sqlite3
import numpy as np,pandas as pd
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1];T=R/'outputs/tables'
d=pd.read_csv(T/'multi_date_residual_predictions.csv')
with sqlite3.connect(R/'outputs/data/hex_results.gpkg') as con:
    xy=pd.read_sql_query('SELECT h.hex_id,(r.minx+r.maxx)/2 AS x,(r.miny+r.maxy)/2 AS y FROM hex_results h JOIN rtree_hex_results_geom r ON h.fid=r.id',con).set_index('hex_id')
rows=[]
for (date,model),group in d.groupby(['date','model']):
    ids=group.hex_id.to_list();c=xy.loc[ids][['x','y']].to_numpy();nn=cKDTree(c).query(c,k=9)[1][:,1:]
    z=group.residual_C.to_numpy();z=z-z.mean();den=8*np.dot(z,z)
    value=np.sum(z[:,None]*z[nn])/den
    rng=np.random.default_rng(1009);null=[]
    for _ in range(999):
        q=rng.permutation(z);null.append(np.sum(q[:,None]*q[nn])/(8*np.dot(q,q)))
    null=np.array(null);p=(1+np.sum(abs(null-null.mean())>=abs(value-null.mean())))/1000
    rows.append({'date':date,'model':model,'n_hex':len(z),'residual_Moran_I':value,
                 'permutation_p_two_sided':p,'permutations':999,'neighbors':8})
pd.DataFrame(rows).to_csv(T/'round8_residual_Moran_permutations.csv',index=False)
print(pd.DataFrame(rows).groupby('model')[['residual_Moran_I','permutation_p_two_sided']].mean().round(3))
