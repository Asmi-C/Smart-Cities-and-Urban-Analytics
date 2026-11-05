# OSM network data audit

The canonical `src/newtown_smart_city_analysis.py` uses OSMnx `graph_from_polygon(network_type='walk')`, projects the walking network to EPSG:32645, maps hex centroids and OSM service geometries to nearest nodes, then applies NetworkX multi-source Dijkstra with edge length and 4.8 km/h (80 m/min) walking speed.

Five source categories are **school, health, green, transit, shop**. Network-distance columns in `outputs/data/hex_results.gpkg` preserve the resulting nearest distance for all 537 hexes. We recomputed 5/10/15-minute coverage, population-weighted accessibility, Moran's I and inequality **from these existing network-distance columns** in `tools/merge_access_exposure.py`.

This is a defensible re-derivation of **cached** distances and not an independent current OSM extraction. The teammate ZIP contains summary files and no separate live network graph or original OSM snapshot; a fresh OSM requery was not demonstrated in this round. The provenance and time of the actual POI snapshot, routing graph completeness, correctness of centroid snapping, permissions and individual POI existence have **not** been independently checked against government listings or field data. Consequently all service-availability findings must be qualified as OSM-derived coverage proxies.

Only nearest-service distance is stored; the number of *distinct* services reachable within 5, 10 or 15 minutes cannot be reconstructed. `network_accessibility.csv` counts reachable **service categories**, not opportunities. It does not invent cumulative POI counts or accessibility routes.

The reported 2.2% all-five coverage is reproduced as **2.162%** of modelled WorldPop 2020 residents (2,119 / 98,028), conditional on the cached network and source assumptions. The 640-m boundary registration error is especially serious for street-level nearest-service estimates.
