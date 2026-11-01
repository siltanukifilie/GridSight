# GridSight third party notices

The hosted demo also uses **Gunicorn 26.2.0**, Gunicorn contributors,
MIT licence. [Source and licence](https://github.com/benoitc/gunicorn).
The published package includes its upstream licence.

GridSight uses open-source dependencies installed into an isolated Python environment. Their versions are listed in `requirements-lock.txt`. No third-party source repository has been copied into the application source tree.

- **RAMP 0.5.0**, RAMP contributors, EUPL-1.2-or-later. Used directly by `build_profiles.py` to generate appliance-based daily shapes. Preserve applicable upstream license and attribution when redistributing it. [Source and license](https://github.com/RAMP-project/RAMP), [project](https://rampdemand.org/).
- **Flask**, Pallets contributors, BSD-3-Clause. Local web server and templates. [Project](https://flask.palletsprojects.com/).
- **scikit-learn**, scikit-learn contributors, BSD-3-Clause. Regression, model selection, and evaluation. [Project](https://scikit-learn.org/).
- **NumPy**, NumPy contributors, BSD-3-Clause. Numerical computation. [Project](https://numpy.org/).
- **pandas**, pandas contributors, BSD-3-Clause. Dataset construction and processing. [Project](https://pandas.pydata.org/).
- **pytest**, pytest contributors, MIT. Automated testing. [Project](https://docs.pytest.org/).

Transitive dependencies retain their own licenses. The installed distribution metadata contains their full notices. RAMP is used through its published API without modifying the package. Appliance configurations, monthly generator, frontend, scenario calculations and integration code in this project are newly authored work.

External references provide methodology and context. The generated dataset does not contain copied operator data. AI assistance was used in implementation and documentation; the later submission disclosure should include this work and its actual timing.
## Public context services (v1.2)

- **World Bank, World Development Indicators:** national population `SP.POP.TOTL` and electricity access `EG.ELC.ACCS.ZS`. The indicator pages identify CC BY 4.0 licensing: [population](https://data.worldbank.org/indicator/SP.POP.TOTL), [electricity access](https://data.worldbank.org/indicator/EG.ELC.ACCS.ZS). The app retains the latest non-null value per series, source year/URL and retrieval time; it does not alter values or use them as local demand labels. [API documentation](https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures).
- **Open-Meteo / GeoNames:** on-demand country-filtered place-name and coordinate lookup. [Geocoding documentation](https://open-meteo.com/en/docs/geocoding-api); [GeoNames dataset licence](https://download.geonames.org/export/dump/readme.txt), CC BY 4.0. Place labels are combined with administrative names; no customer/financial inputs are sent. The free hosted endpoint is for non-commercial prototyping. A paid/commercial release needs an appropriate provider arrangement or replacement; no subscription was purchased. [Provider terms/pricing](https://open-meteo.com/en/pricing).
- **OpenStreetMap contributors:** opt-in embedded map, visibly attributed and linked to [copyright/ODbL](https://www.openstreetmap.org/copyright). No tiles are prefetched or downloaded for offline use. Map requests are made by the visitor only after choosing to load/open the map. [Service policy](https://operations.osmfoundation.org/policies/tiles/).

Public context is not consumed by the prediction model. The synthetic dataset and model retain their original provenance. Internet/provider availability is not guaranteed; failures are surfaced without fabricated replacement data.

## Default EAC location selector (v1.3)

The new default selector reads locally imported **GeoNames Gazetteer** country extracts, downloaded from `https://download.geonames.org/export/dump/{CC}.zip` for RW, UG, KE, TZ, BI, SS, SO and CD on 31 October 2026. GeoNames contributors; **Creative Commons Attribution 4.0**. [Dataset README and licence](https://download.geonames.org/export/dump/readme.txt), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), [feature definitions](https://www.geonames.org/export/codes.html).

This derivative keeps selected administrative and populated-place fields, excludes seats/historical features, maps zero population to unknown, constructs code-based hierarchy and applies disclosed rural-first search filters. Each country JSON carries its source URL, fetch time and source ZIP checksum; each record keeps its modification date. Geographic data is provided as-is with no accuracy, timeliness or completeness warranty. Preserve this attribution and transformation notice with redistribution.

The default selector does not use the hosted Open-Meteo endpoint; that legacy API remains available for compatibility with its original provider restrictions. Map tiles are still loaded only on a visitor's explicit action. Country scope follows the user's eight-country choice and the [EAC partner-state list](https://www.eac.int/eac-partner-states); geographic naming is not an assertion about disputed jurisdiction.

## Rwanda local evidence (v1.4)

- Google Research **Open Buildings v3**, May 2023 inference: [source/licences](https://sites.research.google/gr/open-buildings/). This project chooses **CC BY 4.0**, not the alternative ODbL licence. Point tile 19d is filtered at confidence >= 0.738 and clipped to the Rwanda outline. Coordinates, area and confidence retained; household estimates are newly derived assumptions, not source attributes. Preserve attribution and transformation notices with redistribution.
- **geoBoundaries gbOpen**, William & Mary geoLab and boundary contributors: [Rwanda ADM0 metadata](https://www.geoboundaries.org/api/current/gbOpen/RWA/ADM0/), boundary ID RWA-ADM0-41251308, 2021 representation, CC BY 4.0. Used for spatial clipping; no assertion of authoritative cadastral coverage.
- **OpenStreetMap contributors**, retrieved through public Overpass: ODbL 1.0, [copyright and attribution](https://www.openstreetmap.org/copyright). This independent extract keeps object IDs, coordinates and amenity/shop categories only. It is not a WRI Energy Access Explorer dataset. Preserve attribution and applicable database share-alike obligations when redistributing or combining databases. Numerical detections and OSM extracts remain separate source assets.
- **MININFRA**, Bugesera Connection to electricity layer, 2022 description: [public service](https://infrastructure.space.gov.rw/server/rest/services/Connection_to_electricity/MapServer/0). Reuse licence is not stated by the service. Raw records are retained locally for review but deliberately omitted from downloadable public-source packs pending terms verification. No current site grid-access or household-count assertion is derived.
- **Shapely 2.2.0**, Shapely contributors, BSD-3-Clause, and bundled GEOS with its own licence. Used to clip point detections and check the imported country geometry; distribution metadata retains full notices.

VIIRS, GridFinder, WRI EAE, MTF, ESMAP/AMDA cost tables and GEP settlement/scenario data are references or pending inputs, not included collected datasets. No meter data is present. The original synthetic model remains unchanged. The v1.4 source/proxy distinction supersedes the earlier blanket statement that public context never affects inputs; only explicit local proxies initialize a new preliminary screen.
