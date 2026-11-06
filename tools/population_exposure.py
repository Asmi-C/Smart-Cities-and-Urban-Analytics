"""Descriptive population exposure using existing, unvalidated WorldPop 2020 hex counts."""
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd
R=Path(__file__).resolve().parents[1]
g=gpd.read_file(R/'outputs/data/hex_results.gpkg')
pop=np.maximum(g['pop'].to_numpy(float),0)
heat=g.LST.to_numpy(float);access=g.score15.to_numpy(float)
high_heat=heat>=np.quantile(heat,.8);low_access=access<=np.quantile(access,.2)
priority=gpd.read_file(R/'outputs/data/ieee_priority_results.gpkg')
stable=priority.priority_probability.to_numpy(float)>=.8
rows=[]
for name,mask in [('All analyzed hexes',np.ones(len(g),bool)),('Top-quintile satellite LST',high_heat),
                  ('Bottom-quintile access score',low_access),('Both high heat and low access',high_heat&low_access),
                  ('High policy-acceptability priority',stable)]:
    rows.append({'class':name,'n_hex':mask.sum(),'estimated_population_2020':pop[mask].sum(),
                 'population_share':pop[mask].sum()/max(pop.sum(),1),
                 'population_weighted_mean_LST_C':np.average(heat[mask],weights=np.maximum(pop[mask],1e-8)) if mask.any() else np.nan,
                 'data_limitation':'WorldPop 2020 proxy, not independently calibrated against 2026 residents'})
pd.DataFrame(rows).to_csv(R/'outputs/tables/population_exposure.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
