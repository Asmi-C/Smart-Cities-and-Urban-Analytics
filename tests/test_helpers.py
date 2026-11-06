"""Offline tests for the notebook's helper functions (no Earth Engine or OSM needed).

The helpers are loaded straight from src/newtown_smart_city_analysis.py, from the top of
the file up to the "Study area" section, so the notebook stays the single source of truth.
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import pytest
from shapely.geometry import box

SRC = Path(__file__).resolve().parents[1] / "src" / "newtown_smart_city_analysis.py"


@pytest.fixture(scope="module")
def nb(tmp_path_factory):
    cwd = os.getcwd()
    os.chdir(tmp_path_factory.mktemp("run"))   # helpers create outputs/ folders
    try:
        ns = {}
        exec(SRC.read_text().split("# ## 2. Study area")[0], ns)
    finally:
        os.chdir(cwd)
    return ns


@pytest.fixture(scope="module")
def grid(nb):
    b = gpd.GeoDataFrame(geometry=[box(640000, 2495000, 645000, 2501000)], crs=nb["CRS"])
    return b, nb["make_hex_grid"](b, 250)


@pytest.fixture(scope="module")
def synthetic(nb, grid):
    _, h = grid
    rng = np.random.default_rng(0)
    c = h.centroid
    x = (c.x - c.x.min()) / 5000
    y = (c.y - c.y.min()) / 6000
    H = h.copy()
    H["NDVI"] = 0.2 + 0.4 * x + rng.normal(0, 0.05, len(h))
    H["LST"] = 38 - 6 * x + rng.normal(0, 0.5, len(h))
    H["f_bluegreen"] = np.clip(0.3 + 0.5 * x + rng.normal(0, 0.1, len(h)), 0, 1)
    H["score15"] = np.round(np.clip(1 - y + rng.normal(0, 0.2, len(h)), 0, 1) * 5) / 5
    H["d_transit_cap"] = np.clip(200 + 2000 * y + rng.normal(0, 100, len(h)), 0, 3000)
    return H.reset_index(drop=True)


def test_hex_grid_geometry(nb, grid):
    b, h = grid
    expected_area = np.sqrt(3) / 2 * 250 ** 2
    assert len(h) > 400
    assert np.allclose(h.area, expected_area, rtol=1e-6)
    assert h.centroid.within(b.geometry.iloc[0]).all()
    assert h["hex_id"].is_unique


def test_hex_grid_contiguity(nb, grid):
    _, h = grid
    w = nb["build_weights"](h.reset_index(drop=True))
    assert max(w.cardinalities.values()) == 6
    assert not w.islands


def test_ahp_default_matrix_is_consistent(nb):
    w, cr = nb["ahp_weights"](nb["AHP_MATRIX"])
    assert np.isclose(w.sum(), 1)
    assert cr < 0.10
    assert np.argmax(w) == 3          # 15-minute accessibility gets the largest weight


def test_ahp_perfectly_consistent_matrix(nb):
    v = np.array([4, 2, 1.0])
    w, cr = nb["ahp_weights"](np.outer(v, 1 / v))
    assert np.allclose(w, v / v.sum())
    assert abs(cr) < 1e-9


def test_minmax_direction_and_constant(nb):
    assert np.allclose(nb["minmax"]([1, 2, 3]), [0, 0.5, 1])
    assert np.allclose(nb["minmax"]([1, 2, 3], reverse=True), [1, 0.5, 0])
    assert np.allclose(nb["minmax"]([5, 5, 5]), 0.5)


def test_sli_bounds_and_direction(nb, synthetic):
    w, _ = nb["ahp_weights"](nb["AHP_MATRIX"])
    sli = nb["compute_sli"](synthetic, nb["SLI_SPEC"], w)
    assert sli.min() >= 0 and sli.max() <= 1
    better = synthetic.copy()
    better["LST"] -= 5                # cooler everywhere, but min-max rescales: ranks unchanged
    assert np.allclose(nb["compute_sli"](better, nb["SLI_SPEC"], w), sli)


def test_sensitivity_table(nb, synthetic):
    w, _ = nb["ahp_weights"](nb["AHP_MATRIX"])
    s = nb["sensitivity"](synthetic, nb["SLI_SPEC"], w)
    assert len(s) == 1 + 2 * len(w)
    assert (s["Spearman rho vs baseline"].iloc[1:] > 0.95).all()


def test_bh_fdr(nb):
    rng = np.random.default_rng(1)
    p = np.r_[np.full(20, 1e-4), rng.uniform(0.2, 1, 500)]
    sig = nb["bh_fdr"](p)
    assert sig[:20].all() and not sig[20:].any()
    assert not nb["bh_fdr"](np.full(10, 0.5)).any()


def test_cluster_stats_detects_gradient(nb, synthetic):
    w = nb["build_weights"](synthetic)
    summary, lisa, hot = nb["cluster_stats"](synthetic, "LST", w)
    assert summary["Global Moran's I"] > 0.5
    assert summary["Pseudo p-value"] <= 0.01
    assert {"High-High", "Low-Low"} <= set(lisa)
    assert {"Hot spot", "Cold spot"} <= set(hot)


def test_cluster_stats_random_field(nb, grid):
    _, h = grid
    g = h.reset_index(drop=True).copy()
    g["noise"] = np.random.default_rng(3).normal(size=len(g))
    w = nb["build_weights"](g)
    summary, lisa, _ = nb["cluster_stats"](g, "noise", w)
    assert abs(summary["Global Moran's I"]) < 0.1
    assert (lisa != "Not significant").mean() < 0.05


def test_md_table(nb):
    t = nb["md_table"](pd.DataFrame({"a": ["x"], "b": [1.23456]}), 2)
    assert t.splitlines() == ["| a | b |", "| --- | --- |", "| x | 1.23 |"]


def test_hex_map_writes_png(nb, synthetic, grid, tmp_path):
    b, _ = grid
    out = tmp_path / "map.png"
    nb["hex_map"](synthetic, "LST", "test", str(out), b, cmap="inferno")
    assert out.stat().st_size > 10_000
