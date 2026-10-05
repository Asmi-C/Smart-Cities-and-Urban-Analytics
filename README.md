# Smart Cities and Urban Analytics Using Spatial Data — New Town Kolkata

Term project for the **Geographic Information Systems** course at **IIT Kharagpur**.

An open-data GIS framework that measures how liveable a planned Indian smart city is,
using **New Town Kolkata** as the case. It combines satellite remote sensing,
street-network analysis and spatial statistics on a common 250 m hexagonal grid and
condenses them into a **Smart Liveability Index (SLI)**.

## Research questions

1. **RQ1:** How much has built-up area grown since 2016, and what land covers did it replace?
2. **RQ2:** How strongly is land surface temperature associated with built-up density and vegetation?
3. **RQ3:** What share of residents can reach five essential services within a 15-minute walk?
4. **RQ4:** Are liveability deficits spatially clustered, and where are the hot spots?

## Workflow

```mermaid
flowchart TD
    S2[Sentinel-2<br/>10 m, dry season] --> A
    DW[Dynamic World<br/>training labels] --> A
    L[Landsat 8/9<br/>thermal, pre-monsoon] --> B
    OSM[OpenStreetMap<br/>walk network + services] --> C
    WP[WorldPop<br/>100 m population] --> C
    A[A. Land cover<br/>Random Forest, built-up growth] --> G
    B[B. Heat island<br/>LST, SUHI, regression] --> G
    C[C. 15-minute accessibility<br/>network shortest paths] --> G
    G[250 m hexagonal grid<br/>zonal statistics] --> SLI[Smart Liveability Index<br/>AHP weights + sensitivity]
    SLI --> D[D. Spatial clustering<br/>Moran's I, LISA, Gi*]
    D --> O[Maps, tables and<br/>priority zones]
```

| Module | Method | Data |
| --- | --- | --- |
| A — Land cover | Random Forest (100 trees) on Sentinel-2 bands + NDVI/NDBI/MNDWI, trained on high-confidence Dynamic World pixels; transition matrix | Sentinel-2, Dynamic World, ESA WorldCover (check) |
| B — Heat island | Landsat C2 L2 surface temperature, surface UHI intensity, UTFVI, OLS of LST on spectral indices | Landsat 8/9 |
| C — Accessibility | OSMnx walk network, multi-source Dijkstra to schools, health, parks, transit and shops; 15 min = 1,200 m | OpenStreetMap, WorldPop |
| D — Index and clustering | AHP-weighted SLI (CR < 0.10), ±20% weight sensitivity, Global Moran's I, LISA and Getis-Ord Gi* with FDR control | Outputs of A–C |

## Study area: the NKDA area (29.34 km²)

The study area is the **New Town Kolkata Development Authority (NKDA) area**, 29.34 km²,
which is the statutory area defined in Schedule I Part A of the New Town, Kolkata
Development Authority Act, 2007 (24 mouza parts). The boundary is committed at
[`data/newtown_boundary.geojson`](data/newtown_boundary.geojson) and is already set as
`BOUNDARY_FILE` in the configuration cell.

It was digitised from the only published drawing of that area, the official NKDA
plan-area sheet (`maps-of-new-town-planning-area.pdf` on nkdamar.org), by
[`tools/nkda_boundary.py`](tools/nkda_boundary.py):

```bash
python tools/nkda_boundary.py --report     # regenerate + print scale and registration
```

| Step | Result |
| --- | --- |
| Boundary style | blue `(0, 0, 1)` width 19, layer 6, confirmed against the sheet's own legend swatch |
| Extraction | 3,977 usable dashes (3,976 zero-length parser artefacts discarded), chained in stream order into one closed ring of 4,931 points, closure gap 4.12 units |
| Scale | **1.5663 m per PDF unit**, from `sqrt(29.34 × 10⁶ / 11,959,630 units²)` |
| Registration | rotation **89.36°**, translation solved against 5 OpenStreetMap ground-control points |
| Registration residuals | RMS **640 m**, max 962 m |
| Area check | **29.242 km²** on the UTM 45N grid, −0.33 % against the statutory 29.34 km² |
| Extent | 8.59 × 10.42 km |
| Spot checks | Eco Park inside; Rajarhat, Baguiati, Dum Dum, Ultadanga outside |

The scale is also probed independently of the area assumption, by asking which value
makes the OSM control points line up best: that optimum is 1.66 m/unit, 17 % above the
area-derived value, which is within the noise of label-anchor placement and confirms the
scale to roughly ±6 %.

**Known limitation.** The sheet is an unregistered CAD plot with no coordinate grid, so
ground control can only come from place labels, and the drafter placed those labels
0.5–1 km from the settlements they name. That sets a **~640 m** floor on the absolute
placement. It is a rigid transform, so area, shape and every internal metric are
unaffected; only absolute position shifts, which moves the set of edge hexes included
relative to the 250 m grid. Tightening this is future work — see
[`tools/render_sheet.py`](tools/render_sheet.py), which renders the sheet with a
1,000-unit graticule and all 351 labels for picking better control by hand in QGIS.

Earlier work on the **NTPA** and **LUDCP** boundaries was set aside as incorrect; those
modules now live in [`trashed/`](trashed/) and are not part of the analysis.

## Quick start 

1. Register a free Earth Engine Cloud project for non-commercial use:
   https://code.earthengine.google.com/register
2. Click **Open in Colab** above (or upload `notebooks/newtown_smart_city_analysis.ipynb`).
3. In the configuration cell, set `PROJECT_ID` to your Earth Engine project ID.
4. `BOUNDARY_FILE` already points at the committed NKDA boundary — nothing to upload.
5. **Runtime → Run all.** A zip of every output downloads at the end.

### Running locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
earthengine authenticate
cd notebooks && jupyter lab newtown_smart_city_analysis.ipynb
```

## Outputs

Everything is written to `outputs/`:

| Path | Contents |
| --- | --- |
| `outputs/results.md` | All results tables in the report's Section 7 layout |
| `outputs/tables/*.csv` | Accuracy, F1, areas, transition matrix, LST/UHI, OLS, accessibility, AHP, sensitivity, clustering |
| `outputs/figures/*.png` | Study area, land-cover maps, built-up change, LST, NDVI–LST scatter, service distances, 15-minute score, SLI quintiles, LISA and Gi* maps |
| `outputs/data/hex_results.gpkg` | Hexagon layer with every indicator, the SLI and cluster labels (open in QGIS) |

## Repository structure

```
newtown-smart-city-gis/
├── notebooks/
│   └── newtown_smart_city_analysis.ipynb   # run this
├── src/
│   └── newtown_smart_city_analysis.py      # same notebook as a plain script (jupytext py:percent)
├── tests/
│   └── test_helpers.py                     # offline tests for grid, AHP, SLI, FDR, clustering, maps
├── data/
│   ├── newtown_boundary.geojson            # the NKDA area, 29.34 km2 (committed)
│   └── README.md                           # boundary provenance and data licences
├── tools/
│   ├── nkda_boundary.py                    # digitise + register + validate the NKDA boundary
│   ├── pdfmap.py                           # PDF content-stream parser for the sheet
│   └── render_sheet.py                     # render the sheet with a graticule, for hand georeferencing
├── boundary/                               # cached sheet + renders (map.pdf, sheet_*.png)
├── trashed/                                # superseded NTPA / LUDCP work, kept for the record
├── outputs/                                # generated results
├── requirements.txt
└── LICENSE
```

## Development

The notebook and `src/` script are paired with jupytext. After editing either one:

```bash
jupytext --sync notebooks/newtown_smart_city_analysis.ipynb   # or edit the .py and run:
jupytext --to ipynb src/newtown_smart_city_analysis.py -o notebooks/newtown_smart_city_analysis.ipynb
pytest -q
```

The tests exercise everything that does not need network access (hexagon grid,
AHP, index, sensitivity analysis, Benjamini–Hochberg correction, spatial statistics
and map rendering) on synthetic data. Earth Engine and OpenStreetMap steps are
exercised only when the notebook runs.

## Limitations

- **Accuracy is relative to Dynamic World.** Training and validation labels come from Dynamic World, so accuracy measures agreement with that product, not field truth. ESA WorldCover 2021 is reported as an independent comparison.
- **Boundary placement carries ~640 m of registration error.** The official sheet is an unregistered CAD plot with no coordinate grid, so ground control had to come from place labels placed 0.5–1 km from the settlements they name. Area, shape and all internal metrics are unaffected because the transform is rigid, but absolute position shifts by up to ~1 km, which changes which edge hexes fall inside the 250 m grid. Better control can be hand-picked against `boundary/sheet_annotated.png`; see [`tools/render_sheet.py`](tools/render_sheet.py).
- **LST** is daytime surface temperature (~10:30 a.m. overpass) at native 100 m thermal resolution, not air temperature.
- **OSM completeness** varies, and WorldPop is modelled population.
- **AHP weights** reflect the group's judgement; the sensitivity analysis reports how much the ranking depends on them.



## Key references

- Anselin, L. (1995). Local indicators of spatial association — LISA. *Geographical Analysis*, 27(2), 93–115.
- Boeing, G. (2017). OSMnx. *Computers, Environment and Urban Systems*, 65, 126–139.
- Brown, C. F., et al. (2022). Dynamic World. *Scientific Data*, 9, 251.
- Getis, A., & Ord, J. K. (1992). *Geographical Analysis*, 24(3), 189–206.
- Gorelick, N., et al. (2017). Google Earth Engine. *Remote Sensing of Environment*, 202, 18–27.
- Moreno, C., et al. (2021). Introducing the "15-minute city". *Smart Cities*, 4(1), 93–111.
- Saaty, T. L. (1980). *The Analytic Hierarchy Process*. McGraw-Hill.
- New Town, Kolkata Development Authority Act, 2007, Schedule I Part A (definition of the NKDA area).


## License

Code: MIT (see [`LICENSE`](LICENSE)). Data remain under their original licences (see [`data/README.md`](data/README.md)).
