# Data

Satellite imagery, land-cover labels and
population come from Google Earth Engine, and the street network and services from
OpenStreetMap, at run time.

## Study boundary

`newtown_boundary.geojson` is the **NKDA area**, 29.34 km² — the statutory area in
Schedule I Part A of the New Town, Kolkata Development Authority Act, 2007 (24 mouza
parts). It is committed here and `BOUNDARY_FILE` in the notebook already points at it,
so nothing needs uploading.

Regenerate it from the official plan-area sheet with:

```bash
python tools/nkda_boundary.py --report
```

| Field | Value |
| --- | --- |
| Source drawing | `maps-of-new-town-planning-area.pdf`, nkdamar.org (unregistered CAD, no coordinate grid) |
| Boundary style | blue `(0, 0, 1)` width 19, layer 6 |
| Scale | 1.5663 m per PDF unit, solved from the statutory 29.34 km² |
| Registration | rotation 89.36°, solved on 5 OSM ground-control points |
| Registration RMS | 640 m (max 962 m) — see the boundary's `registration_rms_m` property |
| Measured area | 29.242 km² on the UTM 45N grid (−0.33 % vs statutory) |

The 640 m registration uncertainty is inherent: the sheet carries no coordinate grid, so
control can only come from place labels, which the drafter placed 0.5–1 km from the
settlements they name. See README → Limitations.

## Optional inputs

| File | Used for | How to make it |
| --- | --- | --- |
| `action_areas.geojson` | Comparing accessibility across Action Areas I, II and III | Digitise the three designated Action Areas with a `name` column, then set `ACTION_AREAS_FILE`. |

`ACTION_AREAS_FILE` is unset by default, in which case zones are distance-from-centroid
terciles instead.

## Deprecated

The **NTPA** and **LUDCP** boundaries were pursued earlier and set aside as incorrect.
Only the NKDA area is used.

## Licences

Copernicus Sentinel-2 (free and open), Landsat (public domain, USGS), Dynamic World
(CC BY 4.0), ESA WorldCover (CC BY 4.0), WorldPop (CC BY 4.0), OpenStreetMap
(ODbL, © OpenStreetMap contributors). The NKDA plan-area sheet is a public
government publication of the New Town Kolkata Development Authority.