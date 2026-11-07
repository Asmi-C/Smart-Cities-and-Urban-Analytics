"""Acquisition-level meteorological state forecasting; only source mean LST labels.

ERA5-Land is retrospectively reanalysed, not real-time forecast weather.
"""
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error,r2_score
R=Path(__file__).resolve().parents[1];F=['NDVI','NDBI','MNDWI']
sel=R/'data/selected_acquisitions_final.csv'
if not sel.exists():sel=R/'data/selected_acquisitions.csv'
ids=pd.read_csv(sel).item_id.tolist()
weatherfile=R/('data/acquisition_context_final.csv' if sel.name=='selected_acquisitions_final.csv' else 'data/acquisition_context.csv')
weather=pd.read_csv(weatherfile).set_index('item_id')
hybrid_file=R/'outputs/tables/multi_date_residual_predictions.csv'
hybrid_predictions=pd.read_csv(hybrid_file) if hybrid_file.exists() else pd.DataFrame()
vars=['temperature_2m','dew_point_2m','soil_moisture_0_to_7cm'];S={}
for item in ids:
    if item not in weather.index or weather.loc[item,'status']!='verified_archive_response':continue
    t=pd.read_csv(R/f'external_case/data/landsat_hex_LC08_{item.split("_")[3]}.csv')
    t=t[np.isfinite(t[['LST']+F]).all(axis=1)]
    if len(t)>=180 and np.isfinite(weather.loc[item,vars].to_numpy(float)).all():S[item]=t
rows=[]
for held,t in S.items():
    sources=sorted(set(S)-{held});means=np.array([S[k].LST.mean() for k in sources]);mval=t.LST.mean()
    ws=weather.loc[sources,vars].to_numpy(float);wt=weather.loc[[held],vars].to_numpy(float)
    scaler=StandardScaler().fit(ws)
    state=Ridge(alpha=10).fit(scaler.transform(ws),means).predict(scaler.transform(wt))[0]
    # Date-specific source-only climatology offsets for previously observed hexes.
    old={}
    for k in sources:
        d=S[k]; anomalies=d.LST.to_numpy()-d.LST.mean()
        for h,y in zip(d.hex_id,anomalies):old.setdefault(h,[]).append(y)
    climatology=np.array([np.mean(old.get(h,[0])) for h in t.hex_id])
    variants={'source_date_mean_only':np.full(len(t),means.mean()),
              'meteorology_only':np.full(len(t),state),
              'source_mean_plus_spatial_climatology':means.mean()+climatology,
              'meteorology_plus_spatial_climatology':state+climatology}
    if len(hybrid_predictions):
        matched=hybrid_predictions[(hybrid_predictions.date.astype(str)==held.split('_')[3]) &
                    (hybrid_predictions.model=='RF_z_plus_source_spatial_bias')]
        series=matched.set_index('hex_id').prediction_anomaly_C
        if set(t.hex_id).issubset(series.index):
            variants['meteorology_plus_hybrid']=state+t.hex_id.map(series).to_numpy()
    for name,p in variants.items():
        rows.append({'date':held.split('_')[3],'model':name,'n_source_dates':len(sources),
           'actual_mean_C_eval_only':mval,'predicted_mean_C':p.mean(),
           'date_mean_error_C':float(p.mean()-mval),
           'RMSE_C':float(np.sqrt(mean_squared_error(t.LST,p))),
           'R2':float(r2_score(t.LST,p)),
           'meteorology_reanalysis_not_forecast':True})
out=pd.DataFrame(rows);out.to_csv(R/'outputs/tables/meteorology_ablation.csv',index=False)
print(out.pivot(index='date',columns='model',values='RMSE_C').round(3).to_string())
