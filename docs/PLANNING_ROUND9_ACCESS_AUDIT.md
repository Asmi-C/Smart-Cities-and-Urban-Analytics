# Boundary, street network, population: hard-gated planning audit

An authoritative NKDA source describes a jurisdiction of **29.34 sq km and 24 mouzas**, and an NKDA-issued annexure map exists at `https://nkdamar.org/storage/files/map-new.pdf` (2018 notice). These corroborate the *general study area* but the PDF image is not an authenticated georeferenced GIS polygon; do not treat it as coordinate ground truth.

The existing digitized ~29.24-sq-km polygon is still registered using five approximate feature/place anchors (reported RMS 640 m, largest 962 m). This is an anchor-fit residual, **not** a measured positional uncertainty probability distribution. We therefore ran a **scenario sensitivity**, not a corrected boundary: shift the existing polygon 0, 250, 640 and 962 m in eight directions, re-test only *originally observed* hex centers (`tools/boundary_perturbation.py`).

| Hypothetical rigid translation | Retained original hexes, min–max | Retained original WorldPop-2020 model population, min–max |
|---|---:|---:|
| 0 m | 537 | 98,028 |
| 250 m | 442–465 | 79,203–86,094 |
| 640 m | 351–408 | 64,306–77,435 |
| 962 m | 296–374 | 52,688–72,525 |

These are **retained-source-sample** numbers, not true replacement polygon population or a scientifically justified uncertainty posterior. Unobserved land brought inside shifted boundaries cannot be evaluated. Output tables: `boundary_translation_sensitivity.csv`, `boundary_stable_interior.csv`.

No authentic source graph of OSM pedestrian edges and facility POIs was acquired and audited in Round 9; cached service values are not sufficient to compute validated network vs Euclidean distances. No second gridded population raster was downloaded, aligned or cross-checked against WorldPop 2020. These outputs are **blocked**, and the urban-planning gate cannot be passed.

Current valid practical question is limited to a *descriptive screen*: which previously observed hexes were repeatedly warm within the available fifteen clear scenes? The broader question of high-population heat plus poor network access **cannot** yet be answered with validated data. No intervention recommendation is drawn.
