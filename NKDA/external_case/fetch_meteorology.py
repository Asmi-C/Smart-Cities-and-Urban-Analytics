"""Retrieve acquisition-prior hourly ERA5-Land context via Open-Meteo archive.

The mirror is a cited *secondary access route* to ERA5-Land, not a weather station.
Unavailable requests never receive fabricated values. No post-acquisition hour
is used to construct a prediction-time covariate.
"""
from pathlib import Path
import os,urllib.request,urllib.parse,json,datetime as dt
import pandas as pd
R=Path(__file__).resolve().parents[1]
ids=pd.read_csv(R/os.environ.get('NKDA_SELECTION_FILE','data/selected_acquisitions.csv')).item_id.tolist()
fields='temperature_2m,relative_humidity_2m,dew_point_2m,pressure_msl,wind_speed_10m,shortwave_radiation,precipitation,soil_moisture_0_to_7cm'.split(',')
records=[]
for item in ids:
    try:
        with urllib.request.urlopen('https://planetarycomputer.microsoft.com/api/stac/v1/collections/landsat-c2-l2/items/'+item,timeout=35) as req:
            meta=json.load(req)
        acquired=dt.datetime.fromisoformat(meta['properties']['datetime'].replace('Z','+00:00'))
    except Exception as exc:
        print('Scene datetime unavailable',item,type(exc).__name__,flush=True);continue
    start=(acquired-dt.timedelta(days=2)).date();end=acquired.date()
    params={'latitude':22.58,'longitude':88.48,'start_date':start.isoformat(),
        'end_date':end.isoformat(),'hourly':','.join(fields),'models':'era5_land','timezone':'GMT'}
    url='https://archive-api.open-meteo.com/v1/archive?'+urllib.parse.urlencode(params)
    record={'item_id':item,'acquisition_utc':acquired.isoformat(),
       'meteorology_source':'Open-Meteo historical ERA5-Land reanalysis mirror',
       'source_url_without_sensitive_credentials':url,'window':'latest hour <= acquisition UTC; precipitation prior 24h',
       'weather_observed_not_future':True,'status':'unavailable'}
    try:
        with urllib.request.urlopen(url,timeout=25) as req:data=json.load(req)
        hourly=data['hourly'];times=[dt.datetime.fromisoformat(v).replace(tzinfo=dt.timezone.utc) for v in hourly['time']]
        idx=max(i for i,t in enumerate(times) if t<=acquired)
        record['meteorology_hour_utc']=times[idx].isoformat()
        for key in fields:
            record[key]=hourly[key][idx]
            record[key+'_units']=data.get('hourly_units',{}).get(key,'unknown')
        record['precipitation_prev24h_mm']=sum(float(x or 0) for x in hourly['precipitation'][max(0,idx-23):idx+1])
        record['status']='verified_archive_response'
    except Exception as exc:
        record['retrieval_error_type']=type(exc).__name__
    records.append(record)
    print(item,record['status'],flush=True)
pd.DataFrame(records).to_csv(R/('data/acquisition_context_final.csv' if os.environ.get('NKDA_SELECTION_FILE') else 'data/acquisition_context.csv'),index=False)
