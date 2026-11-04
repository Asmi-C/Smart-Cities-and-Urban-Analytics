"""Round 11 planning screen: which populated hexagons are persistently hot AND poorly served by walking,
and does that conclusion survive (a) the walking threshold, (b) the heat-persistence cutoff,
(c) the boundary registration uncertainty?

Inputs (all pre-existing, no new data): 15 Landsat-8 per-hexagon LST tables; network walk distances d_*
and WorldPop-2020 pop from hex_results.gpkg; boundary-translation stable sets from Round 9/10.
Descriptive screening only: not an intervention recommendation, not validated against planning outcomes.
"""
from pathlib import Path
import sqlite3, itertools
import numpy as np, pandas as pd

R = Path(__file__).resolve().parents[1]; T = R / 'outputs/tables'
db = sqlite3.connect(R / 'outputs/data/hex_results.gpkg')
H = pd.read_sql('select hex_id,pop,d_school,d_health,d_green,d_transit,d_shop from hex_results', db).set_index('hex_id'); db.close()
D = ['d_school', 'd_health', 'd_green', 'd_transit', 'd_shop']

# persistent heat: share of valid Landsat-8 dates in which a hexagon is in that date's hottest quintile
hot = []
for item in pd.read_csv(R / 'data/selected_acquisitions_final.csv').item_id:
    day = item.split('_')[3]; p = R / f'external_case/data/landsat_hex_LC08_{day}.csv'
    if not p.exists(): continue
    d = pd.read_csv(p); d = d[np.isfinite(d[['LST', 'NDVI', 'NDBI', 'MNDWI']]).all(axis=1)]
    if len(d) < 180: continue
    hot.append(pd.DataFrame({'hex_id': d.hex_id, 'hot': d.LST >= d.LST.quantile(.8)}))
hot = pd.concat(hot).groupby('hex_id').hot.agg(['mean', 'size']).rename(columns={'mean': 'hot_freq', 'size': 'n_dates'})
assert hot.n_dates.max() == 15
H = H.join(hot)

stable = {'all_537': set(H.index),
          'stable_250m': set(pd.read_csv(T / 'boundary_stable_interior_250m.csv').hex_id),
          'stable_640m': set(pd.read_csv(T / 'boundary_stable_interior_640m.csv').hex_id),
          'stable_962m': set(pd.read_csv(T / 'boundary_stable_interior_962m.csv').hex_id)}

WALK = {'10 min (800 m)': 800, '15 min (1200 m)': 1200, '20 min (1600 m)': 1600}
HOT = [0.4, 0.5, 0.6]
rows, flags = [], {}
for (wl, wm), hc in itertools.product(WALK.items(), HOT):
    n_serv = (H[D] <= wm).sum(axis=1)
    flag = (H.hot_freq >= hc) & (H.n_dates >= 7) & (n_serv <= 1) & (H['pop'] > 0)
    flags[(wl, hc)] = set(H.index[flag])
    for b, s in stable.items():
        f = flag & H.index.isin(s)
        rows.append(dict(walk=wl, hot_cutoff=hc, boundary=b, hexes=int(f.sum()), pop=float(H.loc[f, 'pop'].sum()),
                         pop_share_of_support=float(H.loc[f, 'pop'].sum() / H.loc[H.index.isin(s), 'pop'].sum())))
S = pd.DataFrame(rows); S.to_csv(T / 'round11_planning_screen_sensitivity.csv', index=False)

core = set.intersection(*flags.values()); anyf = set.union(*flags.values())
prof = H.loc[sorted(anyf)].copy()
prof['n_variants_flagged'] = [sum(h in f for f in flags.values()) for h in prof.index]
prof['robust_all_9_variants'] = prof.n_variants_flagged == len(flags)
for b, s in stable.items(): prof[f'in_{b}'] = prof.index.isin(s)
prof['services_within_1200m'] = (prof[D] <= 1200).sum(axis=1)
prof.sort_values(['n_variants_flagged', 'pop'], ascending=False).to_csv(T / 'round11_planning_screen_profiles.csv')

# access-threshold sensitivity of the headline equity numbers (network distances)
eq = []
for wl, wm in WALK.items():
    within = H[D] <= wm
    eq.append(dict(walk=wl, pop_share_all5=float(H.loc[within.all(axis=1), 'pop'].sum() / H['pop'].sum()),
                   pop_share_le1=float(H.loc[within.sum(axis=1) <= 1, 'pop'].sum() / H['pop'].sum()),
                   **{f'pop_share_{c[2:]}': float(H.loc[within[c], 'pop'].sum() / H['pop'].sum()) for c in D}))
pd.DataFrame(eq).to_csv(T / 'round11_access_threshold_sensitivity.csv', index=False)

# persistent heat alone across boundary scenarios
ph = []
for b, s in stable.items():
    Sb = H[H.index.isin(s)]
    for hc in HOT:
        f = (Sb.hot_freq >= hc) & (Sb.n_dates >= 7)
        ph.append(dict(boundary=b, hot_cutoff=hc, support_hexes=len(Sb), hot_hexes=int(f.sum()),
                       hot_share_of_support=float(f.mean()), hot_pop=float(Sb.loc[f, 'pop'].sum()),
                       pop_share=float(Sb.loc[f, 'pop'].sum() / Sb['pop'].sum())))
pd.DataFrame(ph).to_csv(T / 'round11_persistent_heat_boundary_robustness.csv', index=False)

# heat persistence and access by planning zone
db = sqlite3.connect(R / 'outputs/data/hex_results.gpkg')
Z = pd.read_sql('select hex_id,zone,score15 from hex_results', db).set_index('hex_id'); db.close()
Z = Z.join(H[['pop', 'hot_freq']])
Z.groupby('zone').agg(hexes=('pop', 'size'), mean_score15=('score15', 'mean'), mean_hot_freq=('hot_freq', 'mean'),
                      pop=('pop', 'sum')).round(3).to_csv(T / 'round11_zone_heat_access.csv')

print(S.pivot_table(index=['walk', 'hot_cutoff'], columns='boundary', values='hexes').to_string())
print('flagged in any variant', len(anyf), 'robust in all 9', len(core), 'pop', round(H.loc[sorted(core), 'pop'].sum()))
print('robust core inside 640m-stable set', len(core & stable['stable_640m']), 'inside 962m', len(core & stable['stable_962m']))
print(pd.DataFrame(eq).round(3).to_string())
