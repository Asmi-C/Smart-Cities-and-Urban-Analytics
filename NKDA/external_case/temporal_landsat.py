"""Acquire harmonized March Landsat 8 C2 L2 bands and evaluate 2021↔2026 transfer.

Same sensor/path/row/season, independent scenes. Per-scene QA mask, reflectance and
temperature scale factors. No GEE credentials. Source: Microsoft Planetary Computer
STAC API; network and Azure COG range-read access required.
"""
from pathlib import Path
import sys
import urllib.request,urllib.parse,urllib.error,json,csv,hashlib,shutil,time
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.windows import from_bounds
from rasterio.features import rasterize
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score

R=Path(__file__).resolve().parents[1];DATA=R/'external_case/data';DATA.mkdir(parents=True,exist_ok=True)
ITEMS={'2021':'LC08_L2SP_138045_20210324_02_T1',
       '2024':'LC08_L2SP_138045_20240401_02_T1',
       '2026':'LC08_L2SP_138045_20260322_02_T1'}
BASE='https://planetarycomputer.microsoft.com/api/stac/v1'
def getjson(url):
    with urllib.request.urlopen(url,timeout=35) as r:return json.load(r)
def signed(url):
    endpoint='https://planetarycomputer.microsoft.com/api/sas/v1/sign?'+urllib.parse.urlencode({'href':url})
    for attempt in range(6):
        try:return getjson(endpoint)['href']
        except urllib.error.HTTPError as err:
            if err.code!=429 or attempt==5:raise
            time.sleep(min(45,4*(2**attempt)))
def verified_local_download(href,item,band):
    """TLS-verified stdlib download, content-length checked, SHA256 recorded."""
    target=DATA/f'{item}_{band}.tif'
    if target.exists() and target.stat().st_size>1000000:
        return target
    partial=DATA/f'{item}_{band}.part'
    digest=hashlib.sha256();size=0
    with urllib.request.urlopen(href,timeout=120) as response:
        declared=int(response.headers.get('Content-Length') or 0)
        with partial.open('wb') as dest:
            while True:
                block=response.read(1024*1024)
                if not block:break
                dest.write(block);digest.update(block);size+=len(block)
    if declared and size!=declared:
        raise IOError(f'Incomplete verified download for {item}/{band}: {size} != {declared}')
    partial.replace(target)
    with (DATA/'download_manifest.csv').open('a',newline='') as f:
        csv.writer(f).writerow([item,band,target.name,size,digest.hexdigest()])
    return target
hexes=gpd.read_file(R/'outputs/data/hex_results.gpkg')
def extract(item):
    meta=getjson(f'{BASE}/collections/landsat-c2-l2/items/{item}')
    bands={}
    geom=None;shape=None;transform=None
    for band in ['green','red','nir08','swir16','lwir11','qa_pixel']:
        cached=DATA/f'{item}_{band}.tif'
        if cached.exists() and cached.stat().st_size>1000000:
            local_path=cached
        else:
            href=signed(meta['assets'][band]['href'])
            local_path=verified_local_download(href,item,band)
        print('Verified asset',item,band,round(local_path.stat().st_size/1e6,1),'MB',flush=True)
        with rasterio.open(local_path) as src:
                if geom is None:
                    hs=hexes.to_crs(src.crs)
                    bounds=hs.total_bounds
                    win=from_bounds(*bounds,transform=src.transform).round_offsets().round_lengths()
                    win=win.intersection(rasterio.windows.Window(0,0,src.width,src.height))
                    transform=src.window_transform(win);shape=(int(win.height),int(win.width))
                    labels=rasterize(((feature.geometry,i+1) for i,feature in hs.iterrows()),out_shape=shape,transform=transform,fill=0,dtype='int32')
                    geom=True
                values=src.read(1,window=win)
                assert values.shape==shape
                bands[band]=values
    # USGS C2 L2 QA_PIXEL bits 0 fill, 1 dilated cloud, 2 cirrus, 3 cloud, 4 shadow, 5 snow.
    qa=bands['qa_pixel'].astype('uint32');bad=(qa & 63)!=0
    # ST_B10 int16 DN uses scale 0.00341802, offset 149.0 Kelvin.
    lst=bands['lwir11'].astype(float)*0.00341802+149.-273.15
    spec={key:bands[key].astype(float)*0.0000275-0.2 for key in ('green','red','nir08','swir16')}
    green,red,nir,swir=(spec[x] for x in ('green','red','nir08','swir16'))
    def idx(a,b):
        den=a+b
        return np.divide(a-b,den,out=np.full_like(den,np.nan),where=np.abs(den)>=1e-5)
    arrays={'LST':lst,'NDVI':idx(nir,red),'NDBI':idx(swir,nir),'MNDWI':idx(green,swir)}
    valid=(~bad)&(bands['lwir11']>0)&np.isfinite(lst)&(lst>-10)&(lst<75)
    out={'hex_id':hexes.hex_id.to_numpy()}
    for key,v in arrays.items():
        good=valid&np.isfinite(v)&(labels>0)
        count=np.bincount(labels[good],minlength=len(hexes)+1)
        summ=np.bincount(labels[good],weights=v[good],minlength=len(hexes)+1)
        out[key]=np.where(count[1:]>=15,summ[1:]/np.maximum(count[1:],1),np.nan)
        out['n_clear_pixels']=count[1:]
    result=pd.DataFrame(out);result.to_csv(DATA/f'landsat_hex_{item[:4]}_{item.split("_")[3]}.csv',index=False)
    return result,meta

if __name__=='__main__':
    records={};metadata=[]
    for year,item in ITEMS.items():
        meta=getjson(f'{BASE}/collections/landsat-c2-l2/items/{item}')
        metadata.append({'year':year,'acquisition_date':meta['properties'].get('datetime'),
                         'satellite':'Landsat 8','sensor':'OLI/TIRS','processing_level':'Collection 2 Level-2',
                         'cloud_percentage_scene':meta['properties'].get('eo:cloud_cover'),
                         'season':'pre-monsoon March','spatial_resolution_m':30,
                         'temperature_retrieval':'USGS ST_B10 scale 0.00341802 offset 149 K; QA_PIXEL masked',
                         'source_item_id':item})
    pd.DataFrame(metadata).to_csv(R/'data/thermal_metadata.csv',index=False)
    if '--metadata-only' in sys.argv:
        print('Scene metadata saved; COG bands not retrieved or validated.')
        raise SystemExit(0)
    for year,item in ITEMS.items():
        print('Acquiring',year,item,flush=True)
        records[year],meta=extract(item)
    df=records['2021'].merge(records['2026'],on='hex_id',suffixes=('_2021','_2026'))
    features=['NDVI','NDBI','MNDWI'];rows=[]
    for trainyear,testyear in [('2021','2026'),('2026','2021')]:
        cols=[f'{x}_{trainyear}' for x in features];tcols=[f'{x}_{testyear}' for x in features]
        ok=np.isfinite(df[cols+tcols+[f'LST_{trainyear}',f'LST_{testyear}']]).all(axis=1)
        d=df.loc[ok];assert len(d)>=100,f'Only {len(d)} matched clear units'
        m=RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1)
        m.fit(d[cols].to_numpy(),d[f'LST_{trainyear}'].to_numpy());p=m.predict(d[tcols].to_numpy())
        yy=d[f'LST_{testyear}'].to_numpy()
        rows.append({'train_period':trainyear,'test_period':testyear,'n_hex':len(d),'RMSE_C':np.sqrt(mean_squared_error(yy,p)),
                     'MAE_C':mean_absolute_error(yy,p),'R2':r2_score(yy,p),
                     'mean_target_C':yy.mean(),'mean_prediction_C':p.mean()})
    pd.DataFrame(rows).to_csv(R/'outputs/tables/temporal_transfer_results.csv',index=False)
    print(pd.DataFrame(rows).to_string(index=False))
