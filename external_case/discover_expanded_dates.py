"""Frozen expanded cohort; selection only from STAC metadata, never LST outcomes."""
from pathlib import Path
import json, urllib.parse, urllib.request
import pandas as pd

R = Path(__file__).resolve().parents[1]
old = pd.read_csv(R/'data/selected_acquisitions.csv').item_id.tolist()
url = 'https://planetarycomputer.microsoft.com/api/stac/v1/search?' + urllib.parse.urlencode({
    'collections':'landsat-c2-l2', 'bbox':'88.43,22.54,88.54,22.64',
    'datetime':'2018-02-15/2026-05-15', 'limit':500})
rows=[];seen=set()
while url and url not in seen:
    seen.add(url)
    with urllib.request.urlopen(url,timeout=120) as stream: data=json.load(stream)
    for v in data.get('features',[]):
        name=v['id'];part=name.split('_');date=part[3] if len(part)>3 else ''
        cloud=v['properties'].get('eo:cloud_cover')
        try:cloud=float(cloud)
        except (ValueError,TypeError):cloud=float('nan')
        okay=(name.startswith('LC08_L2SP_138045_') and '_02_T1' in name and
              '0215'<=date[4:]<='0515' and cloud<=25)
        rows.append({'item_id':name,'date':date,'year':date[:4],
             'scene_cloud_pct':cloud,'catalog_eligible':okay,'already_selected_round7':name in old})
    pages=[x for x in data.get('links',[]) if x.get('rel')=='next' and x.get('method','GET')=='GET']
    url=pages[0]['href'] if pages else None
df=pd.DataFrame(rows).drop_duplicates('item_id').sort_values(['year','scene_cloud_pct','item_id'])
chosen=set(old)
for year, group in df[df.catalog_eligible].groupby('year'):
    dates=[pd.to_datetime(s.split('_')[3]) for s in chosen if s.split('_')[3][:4]==year]
    for _,r in group.iterrows():
        day=pd.to_datetime(r.date)
        if r.item_id in chosen:continue
        if len(dates)>=2:break
        if all(abs((day-d).days)>=16 for d in dates):
            chosen.add(r.item_id);dates.append(day)
df['selected_catalog']=df.item_id.isin(chosen)
df['rejection_reason']=df.apply(lambda x: 'selected' if x.selected_catalog else
                ('eligible but per-year limit/separation' if x.catalog_eligible else
                 'outside frozen sensor/season/scene-cloud criteria'),axis=1)
df.to_csv(R/'data/acquisition_manifest_final.csv',index=False)
pd.DataFrame({'item_id':sorted(chosen)}).to_csv(R/'data/selected_acquisitions_final_catalog.csv',index=False)
print('catalog',len(df),'eligible',int(df.catalog_eligible.sum()),
      'selected',len(chosen),'new',len(chosen-set(old)),flush=True)
print('\n'.join(sorted(chosen)),flush=True)
