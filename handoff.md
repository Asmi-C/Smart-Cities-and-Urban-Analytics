# Handoff — New Town Kolkata smart liveability analysis

Read this first if you are continuing the work. It records the request, what is done,
what is blocked and why, and the exact next steps.

---

## 1. The request being served

From the collaborator (quoted in the original ticket):

> "For now, it is using fallback of rough bounding box instead of the real new town
> kolkata boundary (NKDA). Can u guys include that boundary instead of the fallback in the
> .ipynb file and update the results.md and outputs if there r any changes in metrics?"

So the deliverable is: **a real New Town boundary in place of the fallback bounding box,
then regenerate `results.md` and `outputs/` because every metric will move.**

---

## 2. Repository and branch state

* Repo: `/home/sravant2543/GIS_TP/Smart-Cities-and-Urban-Analytics` (WSL, on Windows).
* Branches: `main` is **untouched and must stay that way.** All work is on
  `small-modifications`.
  ```
  main (d124d82)
    └── small-modifications   bed62c0, b319139   <- current work
  ```
* A second branch `nkda-impementation1` was requested for the NKDA 29.34 km² attempt.
  It has **not** been created yet — it should branch off `small-modifications` once a
  boundary actually exists.
* `git` needed `git config --global --add safe.directory ...` for this WSL path. Already done.
* Python venv at `.venv` (Python 3.12). `earthengine-api 1.7.46`, `geopandas 1.2.0`,
  `osmnx 2.1.1`, `rasterio`, `libpysal`, `esda`, `statsmodels`, `scikit-learn`,
  `jupytext 1.19.5`, `jupyterlab` + `python3` kernel. **Nothing needs installing.**
* No `.gitignore` exists, so `.venv/`, `__pycache__/` show as untracked. Leave them
  untracked; do not commit them.

---

## 3. Completed

### 3.1 Earth Engine access fixed and verified (commit `bed62c0`)

`PROJECT_ID` was the collaborator's Cloud project `newtown-gis`, which rejects every call
from another Google account:

```
EEException: Caller does not have required permission to use project newtown-gis.
Grant ... roles/serviceUsageConsumer ...
```

Changed to **`newton-gis2`** (project the user registered) in
`notebooks/newtown_smart_city_analysis.ipynb` cell 3 and
`src/newtown_smart_city_analysis.py:25`.

Verified live: `ee.Initialize(project="newton-gis2")` succeeds and real `getInfo()` calls
return data for `COPERNICUS/S2_SR_HARMONIZED`, `COPERNICUS/S2_HARMONIZED`,
`GOOGLE/DYNAMICWORLD/V1`, `ESA/WorldCover/v200`, `LANDSAT/LC08/C02/T1_L2`,
`LANDSAT/LC09/C02/T1_L2`, `WorldPop/GP/100m/pop`.

Authentication for this WSL user is done — credentials at
`~/.config/earthengine/credentials`, `project: newton-gis2`. Do not re-authenticate.

### 3.2 PDF parser for the official NKDA map (commit `b319139`)

`tools/pdfmap.py` — decodes PDF content streams into closed rings in PDF user space with
fill/stroke colour and line width, plus every text label with anchor, rotation and font
size. Built because the official boundary is published only as a vector CAD plot.

The source document is `https://nkdamar.org/storage/files/maps-of-new-town-planning-area.pdf`
(1.06 MB, 1 page, MediaBox 2384x3370, `/Rotate 270`, 8 layered content streams,
~27,000 path constructions, 42 fonts, 351 positioned labels).

### 3.3 LUDCP 2012 authoritative mouza schedule (working code, `tools/ludcp_table.py`)

`tools/ludcp_table.py` fetches `https://www.wbhidcoltd.com/upload_file/report_publication/report11.pdf`
and decodes its text through the subset fonts' ToUnicode CMaps.

It recovers **Table 2**: the schedule of the **45 mouzas** of the New Town Planning Area
land-use plan, each with a J.L. (Jote/Lot) number and an area, summing to exactly
**60.354 km²**. Cross-checked: rows 1–22 sum to 20.847 and rows 23–45 to 39.507.

41 distinct J.L. numbers label the 45 mouzas, because two police stations reuse four of
them (12, 13, 24, 25):

```
2, 3, 9, 10, 11, 12, 13, 15, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32,
33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 49, 53, 54, 55, 69, 71
```

Also useful and already extracted: the LUDCP's written boundary description, and
Table 4 (a mouza population profile, `TOTAL AREA 185060` — not an area column).

This table is worth keeping in the report regardless of how the boundary is obtained.

### 3.4 Repo left runnable

`BOUNDARY_FILE` is back to `None` on purpose — it must not point at a file that does not
exist. `pytest` is **12/12 green**. `outputs/` still holds the collaborator's original
fallback-bbox run (77.4 km², 1442 hexes).

---

## 4. Blocked, and why

**The boundary geometry is the only thing standing between the current state and the
finish line. Everything after it is mechanical.**

Three independent dead ends were verified, not assumed:

1. **The official map carries no georeference.** No `/GPTS`, no `/LPTS`, no
   UTM-magnitude numbers, no lat/lon text. The one `/Measure` array is the default
   `0.01389` points-per-unit viewport spec. The `22.xx` values that look like latitudes are
   Bézier control coordinates. There is no coordinate grid to register on.

2. **OSM does not carry the map's settlements.** Of ~41 map-labelled place names,
   Nominatim returned nothing for 37 — Bhojerhat, Hatgachha, Raigacchi, Langalpota,
   Panapukhuria, Arbelia, Tona, Chakmaricha, Panapukhuria, Bagjola Khal, Chowreswar Canal
   and more. So the labels cannot georeference the sheet. (Overpass also went down /
   rate-limited during the session; the coverage gap is real, not transient.)

3. **The map does not draw the 45 mouzas as identifiable polygons.** Across the whole
   sheet the largest *filled* polygon is 13,299 units². The large features are ~930
   closed rings, but the big ones are containers, not units: a 5,536,952-unit² ring
   contains the labels for J.L. 23, 25, 26, 27, 32 and 43 at once, and a
   1,545,166-unit² ring holds J.L. 40, 41 and 42.

   The intended method was to solve the scale from the official 60.354 km² and union the
   matched polygons. It does not work, because label→polygon assignment fails. Measured:
   the implied scale per mouza, `sqrt(area_km2e6 / ring_units2)`, has median 1.517 m/unit,
   IQR 0.687–2.067, outliers to 13.9, and **only 9% of mouzas fall within 5% of the
   median**. A correct extraction would cluster tightly.

   A plausible sheet scale is about **2.3 m/unit** (content spans roughly 30 x 29 km), at
   which that 5,536,952-unit² ring would be ~29.3 km² — close to the NKDA statutory
   29.34 km². **This is a coincidence worth checking by hand, not evidence.** It rests on
   a scale estimated from one area match.

`tools/ntpa_boundary.py` keeps this investigation, with the failure written down in its
docstring. **It is not a working pipeline — do not build on it as if it were.**

SHRUG / OpenFTSL were also checked as alternative village-boundary sources; both were
unreachable (404 on the GitHub paths tried, DNS failure for `api.opentrustf.org`).

---

## 5. Todo list

| # | Task | State |
|---|---|---|
| 1 | EE project `newton-gis2` wired + verified | **done** (`bed62c0`) |
| 2 | PDF content-stream parser | **done** (`b319139`) |
| 3 | LUDCP Table 2 (45 mouzas, 60.354 km²) | **done**, code works |
| 4 | Obtain a boundary polygon | **BLOCKED — needs a human decision** |
| 5 | Write `data/newtown_boundary.geojson`, set `BOUNDARY_FILE` in notebook + `src`, keep tests green | pending 4 |
| 6 | Full headless re-run, regenerate all `outputs/` + `results.md` | pending 4 |
| 7 | Diff `results.md`; fix README inaccuracies (this branch only) | pending 6 |
| 8 | Create `nkda-impementation1` for the NKDA 29.34 km² attempt | pending 4 |
| 9 | Commit remaining work on `small-modifications` | pending |

Also outstanding from earlier, independent of the boundary: `README.md` references
`docs/README.md` and `.github/workflows/tests.yml`, neither of which exists; it claims
`outputs/` is git-ignored when it is not; and it describes the study area as ~30 km² when
the executed run used the 77.4 km² fallback. There is no CI.

---

## 6. Recommended next step

**Get the boundary from a human, then everything else is straightforward.**

Best option, in order:

1. **Digitise in QGIS.** I can render the official sheet to a high-res PNG from
   `tools/pdfmap.py` (all vectors are already parsed; no poppler needed) and hand you a GCP
   table built from the OSM features that *do* resolve — Eco Park (22.60224, 88.46474),
   Rajarhat admin boundary (22.60202, 88.47799), Kazi Nazrul Islam Sarani
   (22.58759, 88.41932), Krishnapur Canal (22.51219, 88.52055), Tona PHC (22.60188,
   88.57489), Eastern Metropolitan Bypass (~22.53, 88.40). ~45 min of clicking; gives an
   accurate boundary with a statable RMSE, which is the most defensible thing to put in a
   report.
2. **Ask the collaborator or course staff for the shapefile.** One message, cleanest result.
3. **Trace the LUDCP written boundary** (Nowai/Bidyadhari Canal NE; Maricha Gram and
   Bhojerhat S; Chowreswar and Bagjola Canal W). Fully automatic but ±500 m–1 km, and note
   the **eastern side is never described**, so the fourth side would have to be invented.
   Weakest option.

Worth doing alongside, whichever route is chosen: verify by hand whether that
5,536,952-unit² ring really is the NKDA 29.34 km² boundary. If it is, the extraction
becomes tractable and 1b can be finished.

---

## 7. How to run things here

Notebook is executed headless with the venv's own kernel:

```bash
cd /home/sravant2543/GIS_TP/Smart-Cities-and-Urban-Analytics
.venv/bin/python -m jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=-1 \
  --output-dir=outputs/rerun notebooks/newtown_smart_city_analysis.ipynb
```

The notebook and `src/newtown_smart_city_analysis.py` are jupytext percent-format twins.
`tests/test_helpers.py` execs the `.py` up to the `# ## 2. Study area` marker, so **the
script is the source of truth** — keep them in sync. Note the notebook is stored as
minified JSON; re-serialise with `separators=(",", ":")`, `ensure_ascii=False` and no
trailing newline, or the diff explodes to thousands of lines.

When you write throwaway bash from Windows PowerShell into WSL, pipe the script via stdin
with CRLF stripped, otherwise bash does not recognise the heredoc terminator:

```powershell
$s = @'
cd /path && .venv/bin/python - <<'PY'
...
PY
'@
($s -replace "`r`n", "`n") | wsl.exe -e bash -s
```

Also: `wsl.exe -e bash -lc '...python -c "..."...'` mangles nested quotes. Use the
stdin-piping form above instead.