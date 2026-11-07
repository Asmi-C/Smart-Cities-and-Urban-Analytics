"""Observed six-date hotspot persistence on the EXACT 207 fully clear hexes.

Date-specific hot quintiles defined solely by observed date-specific LST;
these retrospective labels are never predictor features.
"""
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd
R=Path(__file__).resolve().parents[1];items=pd.read_csv(R/'data/selected_acquisitions.csv').item_id.tolist()
data=None;dates=[]
for item in items:
    date=item.split('_')[3];dates.append(date)
    t=pd.read_csv(R/f'external_case/data/landsat_hex_{item[:4]}_{date}.csv')[['hex_id','LST']].rename(columns={'LST':date})
    data=t if data is None else data.merge(t,on='hex_id',validate='one_to_one')
d=data.dropna(subset=dates).copy();assert len(d)==207
hot=np.zeros((len(d),len(dates)),bool);k=int(np.ceil(.2*len(d)))
for j,date in enumerate(dates):hot[np.argsort(-d[date].to_numpy(),kind='stable')[:k],j]=True
n=hot.sum(axis=1)
d['hot_count_six_dates']=n
d['persistent_3of6']=n>=3
d['persistent_4of6']=n>=4
d['emerging_last_date']=hot[:,-1]&(n==1)
d['frequency']=n/len(dates)
g=gpd.read_file(R/'outputs/data/hex_results.gpkg').set_index('hex_id')
d['population_2020_proxy']=d.hex_id.map(g['pop'])
d['score15_cached_OSM']=d.hex_id.map(g['score15'])
d['low_access_cached_OSM']=d['score15_cached_OSM']<=g.score15.quantile(.2)
d.to_csv(R/'outputs/tables/six_date_hotspot_persistence.csv',index=False)
rows=[]
for name,mask in [('common_six_date_clear',np.ones(len(d),bool)),('persistent_at_least_3_of_6',d.persistent_3of6),
                  ('persistent_at_least_4_of_6',d.persistent_4of6),
                  ('persistent_3of6_plus_poor_access',d.persistent_3of6&d.low_access_cached_OSM),
                  ('2026_only_hot',d.emerging_last_date)]:
    rows.append({'category':name,'hexes':int(mask.sum()),
                 'population_2020_proxy':float(d.loc[mask,'population_2020_proxy'].sum()),
                 'warning':'WorldPop 2020 model; OSM cache; unregistered boundary'})
pd.DataFrame(rows).to_csv(R/'outputs/tables/six_date_persistent_exposure.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
