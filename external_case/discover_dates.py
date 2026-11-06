"""Predefined scene inventory; catalog selection never examines model scores.

Rule: Landsat-8 C2 L2, WRS 138/045, T1 L2SP, 15 March–15 April,
scene cloud <=15%, at most one (lowest cloud) item per year; retain previous
2021/2024/2026 acquisitions for comparison even if not yearly cloud minima.
"""
from pathlib import Path
import urllib.request,urllib.parse,json
import pandas as pd
R=Path(__file__).resolve().parents[1]
URL='https://planetarycomputer.microsoft.com/api/stac/v1/search?'+urllib.parse.urlencode({
    'collections':'landsat-c2-l2','bbox':'88.43,22.54,88.54,22.64',
    'datetime':'2018-03-15/2026-04-15','limit':500})
items=[];next_url=URL;seen_pages=set()
while next_url and next_url not in seen_pages and len(items)<3000:
    seen_pages.add(next_url)
    with urllib.request.urlopen(next_url,timeout=120) as response:body=json.load(response)
    items.extend(body.get('features',[]))
    links=[l for l in body.get('links',[]) if l.get('rel')=='next' and l.get('method','GET')=='GET']
    next_url=links[0]['href'] if links else None
rows=[]
for v in items:
    item=v['id'];props=v['properties'];date=item.split('_')[3] if len(item.split('_'))>=4 else ''
    pathrow=item.split('_')[2] if len(item.split('_'))>=3 else ''
    try:cloud=float(props.get('eo:cloud_cover'))
    except (TypeError,ValueError):cloud=float('nan')
    year=date[:4];cal=date[4:]
    eligible=(item.startswith('LC08_L2SP_138045_') and '_02_T1' in item and
              '0315'<=cal<='0415' and cloud<=15)
    rows.append({'item_id':item,'year':year,'date':date,'cloud_cover_scene_percent':cloud,
                 'wrs_path_row':pathrow,'predeclared_eligible':eligible,
                 'reason':'eligible' if eligible else 'outside season/sensor/path/quality threshold'})
df=pd.DataFrame(rows).sort_values(['year','cloud_cover_scene_percent','item_id'])
chosen=df[df.predeclared_eligible].drop_duplicates('year').item_id.tolist()
existing=['LC08_L2SP_138045_20210324_02_T1','LC08_L2SP_138045_20240401_02_T1','LC08_L2SP_138045_20260322_02_T1']
chosen=sorted(set(chosen+existing))
df['selected']=df.item_id.isin(chosen)
df.to_csv(R/'data/thermal_acquisition_manifest.csv',index=False)
pd.DataFrame({'item_id':chosen}).to_csv(R/'data/selected_acquisitions.csv',index=False)
print('Catalog candidates',len(df),'eligible',df.predeclared_eligible.sum(),
      'unique years selected',len(chosen),'selection:',chosen)
