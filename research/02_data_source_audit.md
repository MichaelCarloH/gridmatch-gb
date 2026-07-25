# Public asset data source audit

## Verified public facts

The cached Renewable Energy Planning Database extract is public project metadata. It includes operational status, technology, capacity, region, and source coordinates; it does not guarantee public half-hourly meter output, availability, curtailment, a usable BM Unit mapping, or commercial terms.

## Observed data findings

The processed artifact contains 3,100 operational projects. Of those, 3,096 have valid converted coordinates and four retain an invalid-coordinate flag, giving a 99.87% map-ready rate. Solar photovoltaics has 1,393 projects and 10,918.06 MW; onshore wind has 778 projects and 15,271.45 MW; offshore wind has 48 projects and 15,129 MW. Counts and installed MW therefore tell different stories.

The separate 12-site business portfolio is simulated and is not presented as REPD project output.

## Modelling assumptions

Technology, project size, region, and coordinate validity are descriptive research inputs only. No public asset is matched to a simulated site, and no generation history is inferred from installed capacity.

## Prototype limitations

Operational status and coordinates may be stale or incomplete. Missing project capacity and invalid coordinates are retained. The map is a reproducible diagnostic scatter, not a production geospatial product.

## Production recommendations

Version every public extract, preserve raw identifiers and coordinate-quality flags, independently validate candidate assets, and acquire permissioned meter and availability histories before asset-level forecasting.
