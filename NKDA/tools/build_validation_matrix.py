"""Evidence-only spatial/temporal matrix from executed source tables."""
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[1]
rows=[]
sp=pd.read_csv(R/'outputs/tables/spatial_model_comparison.csv')
# Round-5 benchmark values retained with same original 537-hex support.
for setting,rmse,r2 in [('random_5fold_original_537',.725,.676),('spatial_1km_original_537',.891328,.510656),
                        ('spatial_2km_original_537',.914,.485),('buffered_1km_original_537',.929,.469)]:
    rows.append({'training_regime':setting,'geographic_holdout':'random' not in setting,'temporal_holdout':False,
                 'target':'absolute_C','n_dates_tested':1,'RMSE_mean_C':rmse,'R2_mean':r2,
                 'scope':'original 537-hex same period; see original spatial test tables'})
d=pd.read_csv(R/'outputs/tables/leave_one_date_out.csv')
for target in ['absolute_C','mean_anomaly_C']:
    a=d[(d.model=='RF_raw_spectral')&(d.target==target)]
    rows.append({'training_regime':'six_date_heldout_date','geographic_holdout':False,'temporal_holdout':True,
                 'target':target,'n_dates_tested':len(a),'RMSE_mean_C':a.RMSE.mean(),'R2_mean':a.R2.mean(),
                 'scope':'variable per-date clear hex support; target mean only evaluation'})
joint=pd.read_csv(R/'outputs/tables/spatiotemporal_holdout.csv')
for target in ['absolute_C','mean_anomaly_C']:
    a=joint[joint.target==target]
    rows.append({'training_regime':'six_date_plus_1km_unseen_geo_blocks','geographic_holdout':True,'temporal_holdout':True,
                 'target':target,'n_dates_tested':len(a),'RMSE_mean_C':a.RMSE.mean(),'R2_mean':a.R2.mean(),
                 'scope':'source-date labels outside each test-date 1km test block only'})
pd.DataFrame(rows).to_csv(R/'outputs/tables/spatiotemporal_validation_matrix.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
