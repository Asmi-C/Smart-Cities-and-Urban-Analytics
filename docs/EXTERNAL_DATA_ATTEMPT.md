# Independent thermal acquisition: observed technical blocker

**Date:** 3 November 2026.

The open Microsoft Planetary Computer STAC API returned independently acquired Landsat 8 Collection 2 Level-2 scenes for the same path/row (138/045):

| Period | Date (UTC) | Scene cloud fraction | Item |
|---|---|---:|---|
| T1 | 2021-03-24 04:31 UTC | 6.78% | LC08_L2SP_138045_20210324_02_T1 |
| T2 | 2026-03-22 04:31 UTC | 8.51% | LC08_L2SP_138045_20260322_02_T1 |

Both are Landsat 8 OLI/TIRS, Collection 2 Level-2, March, path/row matched. Provenance is written to `data/thermal_metadata.csv` by `python external_case/temporal_landsat.py --metadata-only`.

**Execution attempt:** `python external_case/temporal_landsat.py` correctly queried item metadata and signed asset URLs, but GDAL/rasterio HTTPS range access to the thermal/reflectance COGs failed with `SSL certificate OpenSSL verify result: self-signed certificate in certificate chain (19)`. Retrying with the system CA bundle and its installed proxy CA file did not resolve the error. TLS verification was **not disabled**. No imagery was imported and no temporal transfer metrics were produced.

**Resolution needed:** a trusted GDAL HTTP CA chain matching the runtime's TLS interception, or running the acquisition script on a machine with direct trusted access to the Planetary Computer signed Azure COG assets. Then verify AOI coverage, clear-pixel counts, cloud masks and same-scene reflectance indices before freezing and running transfer. Scene-level cloud percentage alone does not certify cloud-free NKDA coverage.

This is a real, potentially resolvable data-access blocker, not evidence of temporal generalization. Never use the item metadata as if it were measured LST.
