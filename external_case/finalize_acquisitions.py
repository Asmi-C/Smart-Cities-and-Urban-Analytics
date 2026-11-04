"""Apply predeclared >=180 valid hex criterion to *all* selected catalog scenes.

Do not run the main expanded evaluation until all selected catalog items are
either processed or explicitly marked inaccessible.
"""
from pathlib import Path
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1]
manifest=pd.read_csv(R/'data/acquisition_manifest_final.csv')
manifest=manifest.drop(columns=['n_valid_hex','quality_status'],errors='ignore')
selected=manifest[manifest.selected_catalog].copy()
valid=[]
for _,r in selected.iterrows():
    date=r.date;path=R/f'external_case/data/landsat_hex_LC08_{date}.csv'
    if not path.exists():
        n=0;status='not_acquired'
    else:
        data=pd.read_csv(path);n=int(np.isfinite(data[['LST','NDVI','NDBI','MNDWI']]).all(axis=1).sum())
        status='included' if n>=180 else 'excluded_insufficient_valid_hex'
    valid.append({'item_id':r.item_id,'n_valid_hex':n,'quality_status':status})
rec=pd.DataFrame(valid);manifest=manifest.merge(rec,on='item_id',how='left')
manifest.loc[manifest.quality_status=='excluded_insufficient_valid_hex','rejection_reason']='FROZEN_QA_EXCLUSION: fewer than 180 complete-case NKDA hexagons'
manifest.loc[manifest.quality_status=='not_acquired','rejection_reason']='selected_catalog: acquisition not yet completed; outcome not assessed'
manifest.to_csv(R/'data/acquisition_manifest_final.csv',index=False)
rec.to_csv(R/'data/acquisition_coverage_audit.csv',index=False)
print(rec.to_string(index=False));print('Complete',sum(rec.quality_status!='not_acquired'),'/',len(rec),flush=True)
if (rec.quality_status=='not_acquired').any():
    print('INCOMPLETE: do not label this a final expanded sample')
else:
    rec.loc[rec.quality_status=='included',['item_id']].to_csv(R/'data/selected_acquisitions_final.csv',index=False)
