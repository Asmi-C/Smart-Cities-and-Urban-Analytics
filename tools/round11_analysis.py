"""Round 11 analysis of round11_block_geometry_predictions.csv.gz.

Outputs (outputs/tables/):
  round11_paired_optimism.csv      per date x model x config: paired D2/D3 R2 on identical hexes
  round11_optimism_summary.csv     per sensor x model x config: mean gap, two-way cluster CI, sign test
  round11_residual_moran.csv       D3 residual Moran's I (kNN8, 499 perms) + effective n
  round11_interval_coverage.csv    D3 intervals: pooled vs date-cluster conformal; LOYO on L8, applied to L9
Inference units: calendar year (dates within a year are correlated) and geographic block.
Hexagons are never treated as independent units for model comparison.
"""
from pathlib import Path
import sqlite3
import numpy as np, pandas as pd
from itertools import product
from scipy.spatial import cKDTree

R = Path(__file__).resolve().parents[1]; O = R / 'outputs/tables'
P = pd.read_csv(O / 'round11_block_geometry_predictions.csv.gz', dtype={'date': str})
P['year'] = P.date.str[:4]
db = sqlite3.connect(R / 'outputs/data/hex_results.gpkg')
xy = pd.read_sql_query('SELECT h.hex_id,(r.minx+r.maxx)/2 x,(r.miny+r.maxy)/2 y FROM hex_results h '
                       'JOIN rtree_hex_results_geom r ON h.fid=r.id', db).set_index('hex_id'); db.close()
rng = np.random.default_rng(2026)


def r2(t, p):
    t = np.asarray(t); p = np.asarray(p)
    return 1 - ((t - p) ** 2).sum() / ((t - t.mean()) ** 2).sum()


d2 = P[P.regime == 'D2'][['sensor', 'date', 'year', 'model', 'hex_id', 'truth_eval_only', 'prediction']]
d3 = P[P.regime == 'D3']
pair = d3.merge(d2, on=['sensor', 'date', 'year', 'model', 'hex_id'], suffixes=('', '_d2'))
assert np.allclose(pair.truth_eval_only, pair.truth_eval_only_d2)

# ---------- paired optimism per date ----------
rows = []
for (s, dt, yr, cfg, m), g in pair.groupby(['sensor', 'date', 'year', 'config', 'model']):
    rows.append(dict(sensor=s, date=dt, year=yr, config=cfg, model=m, n=len(g),
                     R2_D2=r2(g.truth_eval_only, g.prediction_d2), R2_D3=r2(g.truth_eval_only, g.prediction)))
po = pd.DataFrame(rows); po['gap'] = po.R2_D2 - po.R2_D3
po.to_csv(O / 'round11_paired_optimism.csv', index=False)


def twoway_boot(g, B=2000):
    """Resample calendar years, then geographic blocks within each sampled date; recompute paired gap."""
    unit = 'year' if g.sensor.iloc[0] == 'Landsat8' else 'date'
    g = g.assign(t2=g.truth_eval_only ** 2, e2=(g.truth_eval_only - g.prediction_d2) ** 2,
                 e3=(g.truth_eval_only - g.prediction) ** 2)
    stats = {dt: gg.groupby('block')[['truth_eval_only', 't2', 'e2', 'e3']].agg(['sum', 'size']).to_numpy()
             for dt, gg in g.groupby('date')}
    # columns: t_sum,t_n,t2_sum,_,e2_sum,_,e3_sum,_
    units = g[unit].unique(); dates_of = g.groupby(unit).date.unique().to_dict(); out = []
    for _ in range(B):
        gaps = []
        for u in rng.choice(units, len(units)):
            for dt in dates_of[u]:
                st = stats[dt][rng.integers(0, len(stats[dt]), len(stats[dt]))]
                n = st[:, 1].sum(); tss = st[:, 2].sum() - st[:, 0].sum() ** 2 / n
                gaps.append((st[:, 6].sum() - st[:, 4].sum()) / tss)   # R2_D2 - R2_D3
        out.append(np.mean(gaps))
    return np.percentile(out, [2.5, 97.5])


def signflip_years(gaps_by_year):
    v = np.array(list(gaps_by_year.values())); obs = abs(v.mean()); k = len(v)
    signs = np.array(list(product([-1, 1], repeat=k)))
    return float((np.abs((signs * v).mean(1)) >= obs - 1e-12).mean())


summ = []
for (s, cfg, m), g in pair.groupby(['sensor', 'config', 'model']):
    pg = po[(po.sensor == s) & (po.config == cfg) & (po.model == m)]
    unit = 'year' if s == 'Landsat8' else 'date'
    byu = pg.groupby(unit).gap.mean().to_dict()
    lo, hi = twoway_boot(g, B=2000)
    summ.append(dict(sensor=s, config=cfg, model=m, n_dates=len(pg), n_units=len(byu), inference_unit=unit,
                     mean_R2_D2=pg.R2_D2.mean(), mean_R2_D3=pg.R2_D3.mean(), mean_gap=pg.gap.mean(),
                     dates_gap_positive=int((pg.gap > 0).sum()), CI95_low_twoway=lo, CI95_high_twoway=hi,
                     exact_signflip_p_two_sided=signflip_years(byu)))
S = pd.DataFrame(summ)
# one-sided exact sign-flip p (direction pre-stated in Round-10 primary endpoint: D2 > D3)
def one_sided(row):
    pg = po[(po.sensor == row.sensor) & (po.config == row.config) & (po.model == row.model)]
    unit = 'year' if row.sensor == 'Landsat8' else 'date'
    v = pg.groupby(unit).gap.mean().to_numpy(); k = len(v)
    signs = np.array(list(product([-1, 1], repeat=k)))
    return float(((signs * v).mean(1) >= v.mean() - 1e-12).mean())
S['exact_signflip_p_one_sided'] = S.apply(one_sided, axis=1)
S.to_csv(O / 'round11_optimism_summary.csv', index=False)

# ---------- residual Moran's I of D3 residuals (primary config) ----------
def moran(vals, coords, k=8, perms=499):
    tree = cKDTree(coords); _, nb = tree.query(coords, k=k + 1); nb = nb[:, 1:]
    z = vals - vals.mean(); den = (z ** 2).sum()
    I = (z[:, None] * z[nb]).sum() / k / den * 1.0
    sims = []
    for _ in range(perms):
        zz = rng.permutation(z); sims.append((zz[:, None] * zz[nb]).sum() / k / den)
    p = (1 + np.sum(np.array(sims) >= I)) / (perms + 1)
    return I, p

mor = []
prim = pair[pair.config == '1km_o0_b0']
for (s, dt, m), g in prim.groupby(['sensor', 'date', 'model']):
    cc = xy.loc[g.hex_id, ['x', 'y']].to_numpy(); res = (g.truth_eval_only - g.prediction).to_numpy()
    I, p = moran(res, cc); n = len(g)
    mor.append(dict(sensor=s, date=dt, model=m, n=n, moran_I_knn8=I, perm_p=p,
                    n_eff_AR1_approx=n * (1 - I) / (1 + I)))
M = pd.DataFrame(mor); M.to_csv(O / 'round11_residual_moran.csv', index=False)

# ---------- D3 interval calibration ----------
# Calibration uses only Landsat-8 D3 residuals. Two rules, fixed before scoring:
#  pooled  : q-quantile of all calibration |residuals| (Round-10 rule)
#  cluster : q-quantile across calibration dates of each date's q-quantile (date-cluster conformal,
#            guards against acquisition-level shift by calibrating to between-date spread)
cov = []
l8 = prim[prim.sensor == 'Landsat8'].copy(); l8['ae'] = (l8.truth_eval_only - l8.prediction).abs()
l9 = prim[prim.sensor == 'Landsat9'].copy(); l9['ae'] = (l9.truth_eval_only - l9.prediction).abs()
for m, q in product(l8.model.unique(), (0.8, 0.9, 0.95)):
    a = l8[l8.model == m]
    # (i) leave-one-calendar-year-out within Landsat-8
    for yr in sorted(a.year.unique()):
        cal = a[a.year != yr]; te = a[a.year == yr]
        hw = {'pooled': cal.ae.quantile(q), 'date_cluster': cal.groupby('date').ae.quantile(q).quantile(q)}
        for rule, h in hw.items():
            for dt, td in te.groupby('date'):
                cov.append(dict(test='L8_leave_one_year_out', model=m, nominal=q, rule=rule, date=dt,
                                halfwidth=h, coverage=(td.ae <= h).mean(), n=len(td)))
    # (ii) all Landsat-8 -> Landsat-9 (second look at L9; exploratory)
    hw = {'pooled': a.ae.quantile(q), 'date_cluster': a.groupby('date').ae.quantile(q).quantile(q)}
    for rule, h in hw.items():
        for dt, td in l9[l9.model == m].groupby('date'):
            cov.append(dict(test='L8_to_L9_second_look', model=m, nominal=q, rule=rule, date=dt,
                            halfwidth=h, coverage=(td.ae <= h).mean(), n=len(td)))
C = pd.DataFrame(cov); C.to_csv(O / 'round11_interval_coverage.csv', index=False)

pd.set_option('display.width', 200)
print(S.round(3).to_string())
print(M.groupby(['sensor', 'model'])[['moran_I_knn8', 'perm_p', 'n', 'n_eff_AR1_approx']].mean().round(3))
print(C.groupby(['test', 'rule', 'nominal']).agg(mean_cov=('coverage', 'mean'), min_cov=('coverage', 'min'),
                                                 width=('halfwidth', lambda x: 2 * x.mean())).round(3))
