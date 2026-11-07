"""Sensitivity of EXISTING geo-referenced hex records to uncertain boundary translation.

No data exist for new hexes outside original survey; hence retained-sample-only,
not a corrected population estimate or an alternative legal boundary.
"""
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd
from shapely.affinity import translate
from shapely.validation import make_valid
R=Path(__file__).resolve().parents[1]
g=gpd.read_file(R/'outputs/data/hex_results.gpkg').to_crs(32643)
poly=make_valid(gpd.read_file(R/'data/chandigarh_boundary.geojson').to_crs(32643).geometry.union_all())
xy=g.geometry.centroid
persist=pd.read_csv(R/'outputs/tables/persistent_heat_hexes.csv').set_index('hex_id')
g['persistent_hot']=g.hex_id.map(persist.hotspot_type=='persistent_hot').fillna(False).astype(bool)
pop=np.maximum(g['pop'].to_numpy(float),0)
rows=[];stable=np.ones(len(g),bool)
stable_by_radius={250:np.ones(len(g),bool),640:np.ones(len(g),bool),962:np.ones(len(g),bool)}
for radius in (0,250,640,962):
    for deg in (0,45,90,135,180,225,270,315):
        theta=np.deg2rad(deg)
        shifted=translate(poly,xoff=radius*np.cos(theta),yoff=radius*np.sin(theta))
        inside=np.array([shifted.covers(c) for c in xy])
        if radius in (640,962):stable&=inside
        if radius in stable_by_radius:stable_by_radius[radius]&=inside
        rows.append({'translation_radius_m':radius,'azimuth_deg':deg,'retained_original_hexes':int(inside.sum()),
                     'retained_original_population_2020_proxy':float(pop[inside].sum()),
                     'retained_original_persistent_hot_hexes':int((inside&g.persistent_hot.to_numpy()).sum()),
                     'retained_original_persistent_hot_pop_2020_proxy':float(pop[inside&g.persistent_hot.to_numpy()].sum()),
                     'excluded_original_hexes':int((~inside).sum()),
                     'newly_included_geography_unmeasured':True})
pd.DataFrame(rows).to_csv(R/'outputs/tables/boundary_translation_sensitivity.csv',index=False)
pd.DataFrame([{'n_original_hexes':len(g),'stable_inside_every_640m_and_962m_direction':int(stable.sum()),
               'stable_original_population_2020_proxy':float(pop[stable].sum()),
               'stable_original_persistent_hot_hexes':int((stable&g.persistent_hot.to_numpy()).sum()),
               'warning':'Only preexisting hexes observed; no shifted-area source data'}]).to_csv(R/'outputs/tables/boundary_stable_interior.csv',index=False)
g.loc[stable,['hex_id','pop']].to_csv(R/'outputs/tables/boundary_stable_interior_hexes.csv',index=False)
for radius,mask in stable_by_radius.items():
    g.loc[mask,['hex_id','pop']].to_csv(R/f'outputs/tables/boundary_stable_interior_{radius}m.csv',index=False)
print(pd.DataFrame(rows).groupby('translation_radius_m')[['retained_original_hexes','retained_original_population_2020_proxy']].agg(['min','max']).to_string())
