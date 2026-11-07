"""Minimal data provenance and coverage audit; never substitutes for validation."""
from pathlib import Path
import geopandas as gpd,pandas as pd,numpy as np
R=Path(__file__).resolve().parents[1];g=gpd.read_file(R/'outputs/data/hex_results.gpkg')
rows=[]
for col in ('LST','NDVI','NDBI','MNDWI','f_built','f_veg','f_water','score15','pop','d_school','d_health','d_green','d_transit','d_shop'):
    a=pd.to_numeric(g[col],errors='coerce');rows.append({'field':col,'n_records':len(g),'n_missing':int(a.isna().sum()),
       'pct_missing':float(a.isna().mean()*100),'min':a.min(),'max':a.max(),
       'source':'existing Landsat/Sentinel/OSM/WorldPop NKDA analysis (see original src)',
       'year':'mixed; see original pipeline','CRS':str(g.crs),
       'spatial_unit':'250m nominal hex','independent_validation':'none for hex outcome; LULC independent agreement weak',
       'bias_note':'Source-date mismatch, spatial autocorrelation, POI incompleteness; not ground-truth observations'})
pd.DataFrame(rows).to_csv(R/'outputs/tables/data_quality.csv',index=False)
print('Audited',len(rows),'fields')
