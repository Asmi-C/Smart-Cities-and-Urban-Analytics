"""Six-date LOO source-only date-baseline + spatial-anomaly models.

ERA5-Land reanalysis (Open-Meteo archive mirror) at/before Landsat UTC time is
an *ex-post available* context, not a prospective weather forecast. Six dates
provide extremely weak statistical support; report all failures.
"""
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error,r2_score
R=Path(__file__).resolve().parents[1]
items=pd.read_csv(R/'data/selected_acquisitions.csv').item_id.tolist()
weather=pd.read_csv(R/'data/acquisition_context.csv').set_index('item_id')
fields=['temperature_2m','dew_point_2m','soil_moisture_0_to_7cm']
assert (weather.loc[items,'status']=='verified_archive_response').all(),'Weather context incomplete; abort rather than silently impute'
assert np.isfinite(weather.loc[items,fields].to_numpy(float)).all()
F=['NDVI','NDBI','MNDWI'];S={}
for item in items:
    date=item.split('_')[3]
    t=pd.read_csv(R/f'external_case/data/landsat_hex_{item[:4]}_{date}.csv')
    S[item]=t.loc[np.isfinite(t[['LST']+F]).all(axis=1)]
rows=[]
for test_item in items:
    source_items=[x for x in items if x!=test_item];test=S[test_item]
    X=np.vstack([S[item][F].to_numpy() for item in source_items]);Y=np.concatenate([S[item].LST.to_numpy() for item in source_items])
    anomaly_y=np.concatenate([S[item].LST.to_numpy()-S[item].LST.mean() for item in source_items])
    anomaly=RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1).fit(X,anomaly_y).predict(test[F])
    raw=RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1).fit(X,Y).predict(test[F])
    means=np.asarray([S[item].LST.mean() for item in source_items])
    wtr=weather.loc[source_items,fields].to_numpy(float)
    wte=weather.loc[[test_item],fields].to_numpy(float)
    scaler=StandardScaler().fit(wtr);ws=scaler.transform(wtr);wt=scaler.transform(wte)
    temp=StandardScaler().fit(wtr[:,[0]])
    variants={'raw_spectral_RF':raw,
              'source_mean_plus_spatial_anomaly':np.mean(means)+anomaly,
              'temperature_ridge_baseline_plus_anomaly':Ridge(alpha=10).fit(temp.transform(wtr[:,[0]]),means).predict(temp.transform(wte[:,[0]]))[0]+anomaly,
              'three_weather_ridge_baseline_plus_anomaly':Ridge(alpha=10).fit(ws,means).predict(wt)[0]+anomaly}
    for method,p in variants.items():
        rows.append({'test_date':test_item.split('_')[3],'model':method,'n_test_hex':len(test),
                     'n_training_dates':len(source_items),'weather_fields':'+'.join(fields) if 'weather' in method else 'temperature_2m' if 'temperature_' in method else '',
                     'RMSE_C':np.sqrt(mean_squared_error(test.LST,p)),'R2':r2_score(test.LST,p),
                     'observed_date_mean_C_EVALUATION_ONLY':test.LST.mean(),'predicted_date_mean_C':p.mean(),
                     'target_LST_moment_used_in_training':False,
                     'warning':'Postprocessed reanalysis meteorology; 5 date-level training samples; no prospective deployment claim'})
out=pd.DataFrame(rows);out.to_csv(R/'outputs/tables/meteorology_aware_transfer.csv',index=False)
print(out.pivot_table(index='test_date',columns='model',values='RMSE_C').round(3).to_string())
