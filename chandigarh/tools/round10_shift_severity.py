"""Exploratory source-target covariate Wasserstein distance and D3 degradation."""
from pathlib import Path
import sqlite3
import numpy as np,pandas as pd
from scipy.stats import wasserstein_distance,spearmanr
R=Path(__file__).resolve().parents[1];F=['NDVI','NDBI','MNDWI']
db=sqlite3.connect(R/'outputs/data/hex_results.gpkg')
coords=pd.read_sql_query('SELECT h.hex_id,(r.minx+r.maxx)/2 x,(r.miny+r.maxy)/2 y FROM hex_results h JOIN rtree_hex_results_geom r ON h.fid=r.id',db).set_index('hex_id');db.close()
coords['block']=(coords.x>coords.x.median()).astype(int)*2+(coords.y>coords.y.median()).astype(int)
manifest=pd.read_csv(R/'data/selected_acquisitions_final.csv');A={}
for item in manifest.item_id:
    date=item.split('_')[3];p=R/f'external_case/data/landsat_hex_LC08_{date}.csv'
    if p.exists():
        a=pd.read_csv(p);a=a[np.isfinite(a[['LST']+F]).all(axis=1)].join(coords.block,on='hex_id')
        if len(a)>=180:A[date]=a
score=pd.read_csv(R/'outputs/tables/domain_shift_model_matrix_long.csv');score=score[score.regime=='D3']
rows=[]
for (date,block),s in score.groupby(['held_date','held_quadrant']):
    src=pd.concat([a[a.block!=block] for k,a in A.items() if k!=str(date)])
    tgt=A[str(date)][A[str(date)].block==block]
    ds={f'W1_{f}':wasserstein_distance(src[f],tgt[f]) for f in F}
    for _,r in s.iterrows():rows.append({'date':date,'year':str(date)[:4],'block':block,'model':r.model,'R2':r.R2,'RMSE':r.RMSE,**ds,'mean_W1':np.mean(list(ds.values()))})
d=pd.DataFrame(rows);d.to_csv(R/'outputs/tables/domain_shift_severity.csv',index=False)
res=[]
for model,s in d.groupby('model'):
    for var in ['mean_W1']+[f'W1_{f}' for f in F]:
        rho,p=spearmanr(s[var],s.RMSE)
        res.append({'model':model,'shift_metric':var,'Spearman_rho_to_D3_RMSE':rho,'exploratory_p':p,'n_domain_folds':len(s)})
pd.DataFrame(res).to_csv(R/'outputs/tables/domain_shift_severity_correlations.csv',index=False)
print(pd.DataFrame(res).round(3).to_string(index=False))
