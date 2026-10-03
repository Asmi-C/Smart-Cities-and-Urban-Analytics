# Data

Satellite imagery, land-cover labels and
population come from Google Earth Engine, and the street network and services from
OpenStreetMap, at run time.

## Optional inputs

| File | Used for | How to make it |
| --- | --- | --- |
| `newtown_boundary.geojson` | Exact NKDA study boundary (recommended) | Digitise in QGIS over satellite imagery; much of the NKDA boundary follows the Periphery Canal and Bagjola Canal. Save as GeoJSON in EPSG:4326. |
| `action_areas.geojson` | Comparing accessibility across Action Areas I, II and III | Digitise the three Action Areas with a `name` column. |

Set `BOUNDARY_FILE` and `ACTION_AREAS_FILE` in the notebook's configuration cell
(e.g. `"../data/newtown_boundary.geojson"` when running locally from `notebooks/`,
or upload the file to Colab and use its file name). Without a boundary file the
notebook tries an OpenStreetMap polygon, then falls back to a bounding box, and
reports which it used.

## Licences

Copernicus Sentinel-2 (free and open), Landsat (public domain, USGS), Dynamic World
(CC BY 4.0), ESA WorldCover (CC BY 4.0), WorldPop (CC BY 4.0), OpenStreetMap
(ODbL, © OpenStreetMap contributors).
