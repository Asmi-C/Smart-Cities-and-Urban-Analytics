"""Metadata-only candidate list; NO labels downloaded or inspected.

Landsat 9 C2 L2, WRS138045, Feb15–May15, scene cloud <=25%,
at most two dates per year >=16 days apart. This does not claim sensor
harmonization, availability of valid hexes, or confirmatory testing.
"""
from pathlib import Path
import json,urllib.parse,urllib.request
import pandas as pd
R=Path(__file__).resolve().parents[1]
query={'collections':'landsat-c2-l2','bbox':'88.43,22.54,88.54,22.64','datetime':'2022-02-15/2026-05-15','limit':500}
url='https://planetarycomputer.microsoft.com/api/stac/v1/search?'+urllib.parse.urlencode(query)
rows=[];seen=set()
while url and url not in seen:
    seen.add(url)
    with urllib.request.urlopen(url,timeout=35) as r: data=json.load(r)
    for f in data.get('features',[]):
        item=f.get('id','');pieces=item.split('_');date=pieces[3] if len(pieces)>3 else ''
        if not (item.startswith('LC09_L2SP_138045_') and '_02_T1' in item and len(date)==8):continue
        cloud=f.get('properties',{}).get('eo:cloud_cover')
        eligible=cloud is not None and float(cloud)<=25 and '0215'<=date[4:]<='0515'
        rows.append({'item_id':item,'date':date,'year':date[:4],'scene_cloud_percent':cloud,'eligible_metadata':eligible})
    links=[v for v in data.get('links',[]) if v.get('rel')=='next' and v.get('method','GET')=='GET']
    url=links[0]['href'] if links else None
df=pd.DataFrame(rows).drop_duplicates('item_id').sort_values(['year','scene_cloud_percent','item_id'])
chosen=[]
for year,g in df[df.eligible_metadata].groupby('year'):
    dates=[]
    for _,r in g.iterrows():
        day=pd.Timestamp(r.date)
        if len(dates)>=2:break
        if all(abs((day-d).days)>=16 for d in dates):chosen.append(r.item_id);dates.append(day)
df['provisional_candidate']=df.item_id.isin(chosen)
df.to_csv(R/'data/untouched_landsat9_metadata_candidates.csv',index=False)
print('Metadata-only Landsat9 scenes',len(df),'eligible',df.eligible_metadata.sum(),'provisional',len(chosen))
print(df[df.provisional_candidate][['item_id','date','scene_cloud_percent']].to_string(index=False))
