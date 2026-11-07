"""Retrospective repeated-heat profiles; not an intervention optimization model."""
from pathlib import Path
import numpy as np,pandas as pd,sqlite3
R=Path(__file__).resolve().parents[1];src=R/'data/selected_acquisitions_final.csv'
if not src.exists():src=R/'data/selected_acquisitions.csv'
dates=[];data={}
for item in pd.read_csv(src).item_id:
    day=item.split('_')[3];f=R/f'external_case/data/landsat_hex_LC08_{day}.csv'
    if not f.exists():continue
    df=pd.read_csv(f).set_index('hex_id').LST.dropna();dates.append(day);data[day]=df
ids=sorted(set.union(*(set(v.index) for v in data.values())))
tbl=pd.DataFrame({'hex_id':ids}).set_index('hex_id');top={}
for day,v in data.items():
    thr=v.quantile(.8)
    tbl[day+'_observed']=tbl.index.isin(v.index)
    tbl[day+'_hot']=tbl.index.isin(v.index[v>=thr])
tbl['observed_dates']=tbl[[x+'_observed' for x in dates]].sum(axis=1)
tbl['hot_dates']=tbl[[x+'_hot' for x in dates]].sum(axis=1)
tbl['hot_frequency_observed']=tbl.hot_dates/tbl.observed_dates.replace(0,np.nan)
with sqlite3.connect(R/'outputs/data/hex_results.gpkg') as con:
    context=pd.read_sql_query('select hex_id,pop,score15,f_built,f_veg,f_water from hex_results',con).set_index('hex_id')
tbl=tbl.join(context);tbl['poor_access_cached_OSM']=tbl.score15<=context.score15.quantile(.2)
tbl['persistent_high_frequency']=((tbl.observed_dates>=max(6,len(dates)//2)) &
                                  (tbl.hot_frequency_observed>=.5))
tbl['boundary_robust']=pd.NA  # no independently registered administrative polygon
tbl.reset_index().to_csv(R/'outputs/tables/expanded_planning_profiles.csv',index=False)
summary=[]
for name,mask in [('all_observed_units',tbl.observed_dates>0),
                  ('persistent_hot_over_half_dates',tbl.persistent_high_frequency),
                  ('persistent_hot_and_cached_poor_access',tbl.persistent_high_frequency&tbl.poor_access_cached_OSM)]:
    summary.append({'group':name,'n_hex':int(mask.sum()),'worldpop_2020_model_people':float(tbl.loc[mask,'pop'].sum()),
      'source_dates':len(dates),'warning':'Only modelled 2020 population, unverified OSM cache, ~640m boundary fit RMS'})
pd.DataFrame(summary).to_csv(R/'outputs/tables/expanded_planning_exposure.csv',index=False)
print(pd.DataFrame(summary).to_string(index=False))
