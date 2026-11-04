"""Round 11: robustness of D2->D3 optimism to the geographic holdout geometry.

Sensitivity analysis to the frozen Round-10 primary endpoint (quadrant D3).
Models, hyperparameters, features, normalization rules and the >=180-hex scene
QA are unchanged from Round 10. New here: D3 geographic holdouts are square
grid blocks (1 km, 2 km), with two grid origins and with/without an exclusion
buffer, assigned to 5 folds. D2 and D3 are scored on the SAME hexagons, so the
per-date gap is a paired difference. No test-date LST enters fitting, scaling
or tuning; the test-date scene mean is used only to form evaluation anomalies.

Domains: 15 Landsat-8 dates (development; leave-one-date-out sources) and 5
frozen Landsat-9 dates (trained on all 15 Landsat-8 dates). The Landsat-9 dates
were already scored once in Round 10 under quadrant D3; these block-geometry
results on them are a second look and are labelled as such.
"""
from pathlib import Path
import sqlite3, sys
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor

R = Path(__file__).resolve().parents[1]
F = ['NDVI', 'NDBI', 'MNDWI']
MODELS = ['ridge_z', 'RF_z', 'HGB_z', 'RF_z_coords']
db = sqlite3.connect(R / 'outputs/data/hex_results.gpkg')
xy = pd.read_sql_query('SELECT h.hex_id,(r.minx+r.maxx)/2 x,(r.miny+r.maxy)/2 y FROM hex_results h '
                       'JOIN rtree_hex_results_geom r ON h.fid=r.id', db).set_index('hex_id'); db.close()
c = xy[['x', 'y']].to_numpy(); mu = c.mean(0); sig = c.std(0)
X0, Y0 = xy.x.min(), xy.y.min()


def load(sensor, date):
    d = pd.read_csv(R / f'external_case/data/landsat_hex_{sensor}_{date}.csv')
    d = d[np.isfinite(d[['LST'] + F]).all(axis=1)].join(xy, on='hex_id')
    return d.reset_index(drop=True) if len(d) >= 180 else None


L8 = {}
for item in pd.read_csv(R / 'data/selected_acquisitions_final.csv').item_id:
    day = item.split('_')[3]
    if (R / f'external_case/data/landsat_hex_LC08_{day}.csv').exists():
        d = load('LC08', day)
        if d is not None: L8[day] = d
L9 = {}
for item in pd.read_csv(R / 'data/round10_landsat9_confirmatory_frozen.csv').item_id:
    day = item.split('_')[3]; d = load('LC09', day)
    if d is not None: L9[day] = d
assert len(L8) == 15 and len(L9) == 5, (len(L8), len(L9))


def feat(d, geo):
    f = d[F].to_numpy(float); f = (f - f.mean(0)) / (f.std(0) + 1e-6)
    if geo: f = np.column_stack([f, (d[['x', 'y']].to_numpy() - mu) / (sig + 1e-6)])
    return f


def est(k):
    if k == 'ridge_z': return Ridge(alpha=10.0)
    if k == 'HGB_z': return HistGradientBoostingRegressor(max_iter=80, min_samples_leaf=10, learning_rate=.07, random_state=42)
    return RandomForestRegressor(n_estimators=45, min_samples_leaf=5, max_features=.8, random_state=42, n_jobs=2)


def fit_predict(sources, target_view, test_ids, excl_ids=None):
    """Train on source dates (minus excluded hexes), predict test hexes.
    Source anomalies are centred on each source date's *retained* units only."""
    tr = []
    for s in sources:
        if excl_ids is not None: s = s[~s.hex_id.isin(excl_ids)]
        if len(s) >= 15: tr.append(s)
    y = np.concatenate([s.LST.to_numpy() - s.LST.mean() for s in tr])
    lookup = {h: i for i, h in enumerate(target_view.hex_id)}
    rows = [lookup[h] for h in test_ids]
    out = {}
    for m in MODELS:
        g = m.endswith('coords')
        Xtr = np.vstack([feat(s, g) for s in tr])
        Xte = feat(target_view, g)[rows]
        out[m] = est(m).fit(Xtr, y).predict(Xte)
    return out


CONFIGS = [(size, shift, buf) for size in (1000, 2000) for shift in (0.0, 0.5) for buf in (0, 500)]
recs = []
domains = [('Landsat8', d, L8[d], [L8[s] for s in L8 if s != d]) for d in sorted(L8)] + \
          [('Landsat9', d, L9[d], list(L8.values())) for d in sorted(L9)]
for sensor, day, tgt, sources in domains:
    truth_all = tgt.LST.to_numpy() - tgt.LST.mean()          # evaluation only
    hot_thr = tgt.LST.quantile(.8)
    # D2: unseen date, familiar geography (whole-scene normalisation, frozen rule)
    d2 = fit_predict(sources, tgt, tgt.hex_id.tolist())
    for m in MODELS:
        for hid, t, p in zip(tgt.hex_id, truth_all, d2[m]):
            recs.append((sensor, day, 'D2', 'none', m, hid, t, p, int(tgt.LST[tgt.hex_id == hid].iloc[0] >= hot_thr), -1))
    for size, shift, buf in CONFIGS:
        cfg = f'{size//1000}km_o{int(shift*10)}_b{buf}'
        bx = np.floor((tgt.x - X0 + shift * size) / size).astype(int)
        by = np.floor((tgt.y - Y0 + shift * size) / size).astype(int)
        block = (bx * 100 + by).to_numpy()
        ub = np.unique(block); rng = np.random.default_rng(42 + size + int(shift * 10))
        fold_of = dict(zip(ub, rng.permutation(len(ub)) % 5))
        fold = np.array([fold_of[b] for b in block])
        for k in range(5):
            te = tgt[fold == k]
            if len(te) < 15: continue
            excl = set(te.hex_id)
            if buf > 0:   # also exclude source units within buf metres of any test unit
                tree = cKDTree(te[['x', 'y']].to_numpy())
                allc = xy[['x', 'y']].to_numpy()
                near = tree.query(allc, k=1)[0] <= buf
                excl |= set(xy.index[near])
            # held-region-only unlabeled spectral normalisation (frozen Round-10 primary rule)
            p = fit_predict(sources, te, te.hex_id.tolist(), excl_ids=excl)
            tt = te.LST.to_numpy() - tgt.LST.mean()
            hot = (te.LST.to_numpy() >= hot_thr).astype(int)
            for m in MODELS:
                for hid, t, pr, h, b in zip(te.hex_id, tt, p[m], hot, block[fold == k]):
                    recs.append((sensor, day, 'D3', cfg, m, hid, t, pr, h, b))
    print('done', sensor, day, flush=True)

out = pd.DataFrame(recs, columns=['sensor', 'date', 'regime', 'config', 'model', 'hex_id', 'truth_eval_only',
                                  'prediction', 'hot', 'block'])
out.to_csv(R / 'outputs/tables/round11_block_geometry_predictions.csv.gz', index=False, compression='gzip')
print('rows', len(out))
