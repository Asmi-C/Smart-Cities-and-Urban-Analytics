"""Join pre-existing scene metadata and model test scores; descriptive QA audit."""
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import spearmanr
R=Path(__file__).resolve().parents[1]
m=pd.read_csv(R/'data/acquisition_manifest_final.csv')
m=m[m.quality_status.astype(str).str.contains('pass|included|accepted',case=False,regex=True)].copy()
if not len(m):m=pd.read_csv(R/'data/acquisition_manifest_final.csv').query('n_valid_hex >= 180').copy()
s=pd.read_csv(R/'outputs/tables/date_level_method_comparison.csv');s.Date=s.Date.astype(str)
rows=[]
for _,item in m.iterrows():
    date=str(item.date).replace('-','')[:8]
    f=R/f'external_case/data/landsat_hex_LC08_{date}.csv'
    if not f.exists():continue
    d=pd.read_csv(f)
    v=d[np.isfinite(d[['LST','NDVI','NDBI','MNDWI']]).all(axis=1)]
    rows.append({'date':date,'item_id':item.item_id,'scene_cloud_pct':item.scene_cloud_pct,
                 'n_valid_hex':len(v),'median_clear_pixels_per_hex':v.n_clear_pixels.median(),
                 'mean_LST_C':v.LST.mean(),'fraction_hex_complete':len(v)/len(d)})
out=pd.DataFrame(rows).merge(s,left_on='date',right_on='Date',how='left')
out.to_csv(R/'outputs/tables/round9_scene_quality_audit.csv',index=False)
cr=[]
for target in ['Baseline','Proposed','delta_R2']:
    for attr in ['scene_cloud_pct','fraction_hex_complete','mean_LST_C','median_clear_pixels_per_hex']:
        x=out[[target,attr]].dropna()
        if len(x)>3:
            rho,p=spearmanr(x[target],x[attr]);cr.append({'metric':target,'acquisition_attribute':attr,'n_dates':len(x),'Spearman_rho':rho,'exploratory_p':p})
pd.DataFrame(cr).to_csv(R/'outputs/tables/round9_scene_quality_associations.csv',index=False)
print('Scene QA',len(out),'dates; minimum complete-hex fraction',out.fraction_hex_complete.min())
