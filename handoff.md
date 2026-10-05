# Handoff — New Town Kolkata smart liveability analysis

Read this first if you are continuing the work. It records the request, what is done,
what is known-weak, and the exact next steps.

---

## 1. The request being served

From the collaborator (quoted in the original ticket):

> "For now, it is using fallback of rough bounding box instead of the real new town
> kolkata boundary (NKDA). Can u guys include that boundary instead of the fallback in the
> .ipynb file and update the results.md and outputs if there r any changes in metrics?"

The deliverable is: **a real New Town boundary in place of the fallback bounding box,
then regenerate `results.md` and `outputs/` because every metric will move.**

**Scope decision (agreed with the collaborator):** NKDA is the *only* valid boundary.
Earlier work on NTPA and LUDCP was incorrect and is deprecated.

---

## 2. Repository and branch state

* Repo: `/home/sravant2543/GIS_TP/Smart-Cities-and-Urban-Analytics` (WSL, on Windows).
* Branch: **`nkda-implementation1`**, branched off `small-modifications`. All work here.
* Python venv at `.venv` (Python 3.12). `earthengine-api 1.7.46`, `geopandas 1.2.0`,
  `osmnx 2.1.1`, `rasterio`, `libpysal`, `esda`, `statsmodels`, `scikit-learn`,
  `jupytext 1.19.5`, `jupyterlab` + `python3` kernel. **Nothing needs installing.**
* No `.gitignore`, so `.venv/`, `__pycache__/` show as untracked. Leave them untracked.

---

## 3. Completed

### 3.1 Earth Engine access (commit `bed62c0`)

`PROJECT_ID = "newton-gis2"` in the notebook config cell and `src/…py`. `newtown-gis`
rejects calls from other Google accounts. Authentication is already done for this WSL
user (`~/.config/earthengine/credentials`). **Do not re-authenticate.**

### 3.2 PDF parser for the official sheet (commit `b319139`)

`tools/pdfmap.py` decodes the sheet's content streams into rings in PDF user space with
fill/stroke colour and line width, plus every positioned text label.

Source: `https://nkdamar.org/storage/files/maps-of-new-town-planning-area.pdf`
(1.06 MB, 1 page, MediaBox 2384×3370, `/Rotate 270`, 8 layered content streams,
42 fonts, 351 labels). Cached at `boundary/map.pdf`.

### 3.3 The NKDA boundary — **the main thing that was unblocked**

`tools/nkda_boundary.py` is a working pipeline. Run:

```bash
python tools/nkda_boundary.py --report
```

It writes `data/newtown_boundary.geojson` and prints the scale and registration reports.

**Why the earlier attempts failed, and what actually worked.** The boundary *is*
recoverable from the sheet, but not by the clustering approaches tried before:

* The sheet carries no georeference at all — no `/GPTS`, no `/LPTS`, no UTM or lat/lon
  numbers, no coordinate grid. The single `/Measure` array is the default
  `0.01389` points-per-unit viewport spec. So registration must come from named features.
* Both boundaries are drawn as **dotted** lines, not closed path objects.
* **`pdfmap` emits 3,976 zero-length "strokes"** out of the 7,953 blue marks in layer 6.
  They are degenerate and must be discarded; they break every chaining attempt.
* **Union-find over endpoint proximity cannot work here.** The dashes are so dense
  (gap ~4 u for NKDA, ~8 u for PLANNING) that clustering is *transitive* along the whole
  ring and collapses every endpoint into one node. `set_precision` grid quantisation
  fails too, since two endpoints 4 u apart can land in different cells.
* **Stream order is what works.** The CAD emits each boundary's dashes consecutively
  along the line. Concatenating the surviving strokes in order and bridging the ≤8.94 u
  inter-dash gaps reproduces the ring exactly.

Extracted and validated:

| Property | Value |
| --- | --- |
| Style | blue `(0,0,1)` width 19, layer 6 — confirmed against the sheet's own legend swatches beside the "NKDA AREA" / "PLANNING AREA" labels at y=4718 |
| Marks | 3,977 usable (3,976 degenerate dropped), 1 continuous run |
| Ring | 4,931 points, **closure gap 4.12 u**, valid simple polygon |
| Area in PDF units² | 11,959,630 |
| Perimeter in PDF units | 59,730 |
| **Scale** | **1.5663 m/unit**, `sqrt(29.34e6 / 11,959,630)` |
| **Rotation** | **89.36°** (the sheet is drawn ~90° off north) |
| **Registration RMS** | **640 m**, max 962 m, over 5 OSM GCPs |
| Measured area | **29.242 km²** (UTM 45N), −0.33 % vs statutory 29.34 |
| Extent | 8.59 × 10.42 km |
| Spot checks | Eco Park **inside**; Rajarhat, Baguiati, Dum Dum, Ultadanga **outside** |

**GCPs used** (map label anchor in PDF units → OSM lon/lat): Baguiati (8756, 14654),
Kaikhali (9934, 14342), Arjunpur (9455, 15174), Ultadanga (7626, 16992),
Tona (8593, 6122).

**Rejected as control**, recorded in `REJECTED_GCP`: Kazi Nazrul Islam Sarani (road
label, anchor ~2.7 km off), Dum Dum (junction label, ~2.4 km), Jyangra ("choumatha"
intersection, ~1.7 km). Including any of them roughly triples the RMS for no gain.

### 3.4 Boundary wired in

* `data/newtown_boundary.geojson` committed (4,932-point closed ring, properties record
  source, scale, rotation and RMS).
* `BOUNDARY_FILE = "data/newtown_boundary.geojson"` in both the notebook config cell and
  `src/newtown_smart_city_analysis.py:28`.
* `resolve_boundary_path()` added, because `nbconvert` executes with cwd = `notebooks/`
  so a bare `data/…` path does not resolve. It tries cwd, then `../`, then `../../`.
* `FALLBACK_BBOX` deleted. The OSM-geocode and bounding-box paths remain only as
  last-resort fallbacks and now prefix their source string with `WARNING`, and the
  bounding-box path raises `FileNotFoundError` if `BOUNDARY_FILE` is set but missing
  rather than silently falling back.
* `ACTION_AREAS_FILE` kept (unset). It is the three designated Action Areas, which are
  NKDA-relevant, not NTPA.
* `pytest` 12/12 green.

### 3.5 NTPA / LUDCP deprecated

`tools/ntpa_boundary.py`, `tools/ludcp_table.py` and `tools/trace_boundary.py` moved to
`trashed/` with `git mv`. Nothing in the analysis imports them. `tools/render_sheet.py`
was repointed from `ntpa_boundary` to `nkda_boundary`.

### 3.6 Repo left runnable

`outputs/` regenerated from a full headless run against the NKDA boundary; `results.md`
rewritten. `pytest` green.

---

## 4. Known weaknesses, stated plainly

1. **Registration is good to ~640 m, no better.** This is a hard floor imposed by the
   source, not a tuning failure. The sheet has no coordinate grid, so control can only
   come from place labels, and the drafter put those 0.5–1 km from the settlements they
   name. Because the transform is rigid, area, shape and every internal metric are
   unaffected — only absolute position moves, which shifts *which edge hexes* fall inside
   the 250 m grid. Acceptable for this project; documented as future work.

2. **The scale rests on a single published figure.** 1.5663 m/unit comes from assuming
   the digitised ring *is* the statutory 29.34 km² NKDA area. There is one weak
   independent check: the GCP residuals alone prefer 1.66 m/unit, 17 % higher in RMS
   terms (547 m vs 640 m), which confirms the scale to roughly ±6 % and rules out
   anything far from 1.5–1.8. A stronger check needs a citable published area for some
   other closed ring on the sheet.

   *The earlier "two-ring agreement" argument must not be reused.* It compared the NKDA
   ring against the PLANNING ring at 93.9 km², and that 93.9 figure has no traceable
   source — it came from the same discarded NTPA line of work. It happens to agree to
   1.01 %, but agreement with an unsourced number is not evidence. `scale_report()` still
   prints the PLANNING ring, labelled explicitly as a diagnostic that does **not** set
   the scale.

3. **The NKDA ring is extremely convoluted** — perimeter ≈ 93.5 km for 29.34 km², a shape
   factor ~24× a circle. The wider PLANNING ring on the same sheet is similarly ragged
   (~92 km perimeter for its area), so this is a property of how the boundaries were
   drawn, following every cadastral notch, rather than an extraction artefact. Worth a
   sanity check by eye against `boundary/sheet_plain.png`.

4. **OSM has no NKDA boundary polygon.** Overpass within a bbox around New Town returns
   only Bidhannagar (admin_level 6) and the Kolkata / 24 Parganas districts. There is no
   NKDA or New Town (Kolkata) administrative relation to shape-match against, which is
   why registration had to be point GCPs. Also note Overpass `out geom` on relation
   181473 times out (504) on all three mirrors tried — but that relation is *New Town,
   North Dakota*, not Kolkata.

---

## 5. Todo list

| # | Task | State |
|---|---|---|
| 1 | EE project `newton-gis2` wired + verified | **done** (`bed62c0`) |
| 2 | PDF content-stream parser | **done** (`b319139`) |
| 3 | Obtain a boundary polygon | **done** — NKDA, `tools/nkda_boundary.py` |
| 4 | `data/newtown_boundary.geojson` + `BOUNDARY_FILE` in notebook and `src` | **done** |
| 5 | Register to EPSG:4326, report residuals | **done** — 89.36°, RMS 640 m |
| 6 | Validate area and envelope | **done** — 29.242 km², Eco Park in, neighbours out |
| 7 | Deprecate NTPA / LUDCP | **done** — moved to `trashed/` |
| 8 | Headless re-run, regenerate `outputs/` + `results.md`, `pytest` | **done** |
| 9 | Update `handoff.md` and `README.md` | **done** |
| 10 | Improve registration below 640 m | **open — future work** |

---

## 6. Recommended next step

**Nothing is blocking.** Optional, in order of value:

1. **Tighten the registration** by hand-picking control in QGIS against
   `boundary/sheet_annotated.png`, which has a 1,000-unit graticule and all 351 labels at
   true positions. Pick *point* features, not road labels — that is what got the RMS from
   1,583 m down to 640 m. Add entries to `GCP` in `tools/nkda_boundary.py` and re-run.
2. **Find a citable published area** for another closed ring on the sheet to replace the
   unsourced 93.9 km² and give the scale a real second check.
3. **Optional `ACTION_AREAS_FILE`**: digitise Action Areas I, II, III to replace the
   distance-from-centroid terciles in the zone comparison.
4. **Simplify the ring** before publishing a map — 4,932 vertices at ~93 km perimeter is
   more detail than any figure needs. `simplify(20, preserve_topology=True)` in metres.

---

## 7. How to run things here

Regenerate the boundary:

```bash
cd /home/sravant2543/GIS_TP/Smart-Cities-and-Urban-Analytics
.venv/bin/python tools/nkda_boundary.py --report
```

Full pipeline, headless:

```bash
cd /home/sravant2543/GIS_TP/Smart-Cities-and-Urban-Analytics
.venv/bin/python -m jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=-1 \
  --output-dir=outputs/rerun notebooks/newtown_smart_city_analysis.ipynb
```

If you need it in the background, wrap it in `setsid nohup … &` — a bare `nohup … &` is
killed when the calling shell exits, which silently truncates the run.

Tests:

```bash
.venv/bin/python -m pytest tests/ -q
```

The notebook and `src/newtown_smart_city_analysis.py` are jupytext percent-format twins.
**`src/…py` is the source of truth** — `tests/test_helpers.py` execs the `.py` up to the
`# ## 2. Study area` marker. The two were kept in sync by hand here; after editing either,
check the other, or use:

```bash
.venv/bin/jupytext --sync notebooks/newtown_smart_city_analysis.ipynb
```

Note the notebook is stored as minified JSON; re-serialise with `separators=(",", ":")`,
`ensure_ascii=False` and no trailing newline, or the diff explodes to thousands of lines.

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