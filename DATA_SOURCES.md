# Data sources

Phase 3 separates public source records from simulated portfolio data. Every collection writes an immutable raw cache, a processed artifact and a machine-readable file under `data/manifests/`.

| Dataset | Official source | Demonstration scope | Terms / attribution |
|---|---|---|---|
| DESNZ REPD | `https://www.gov.uk/government/publications/renewable-energy-planning-database-quarterly-extract` | April 2026 CSV; operational sites | Open Government Licence v3.0 |
| Elexon BMRS | `https://data.elexon.co.uk/bmrs/api/v1` | BM Units, B1610, Market Index Data and system prices | Elexon Insights Solution API terms |
| NESO CKAN | `https://api.neso.energy/api/3/action` | Historic-demand package/resource discovery and 96 datastore records | NESO data portal terms |
| Open-Meteo | `https://archive-api.open-meteo.com/v1/archive` | 48 hourly London records with issue and valid times | CC BY 4.0 |
| Carbon Intensity | `https://api.carbonintensity.org.uk` | 48 national half-hourly records | Carbon Intensity API terms |
| UK calendar | `https://www.gov.uk/bank-holidays.json` | England and Wales bank holidays plus computed Europe/London DST transitions | Open Government Licence v3.0 |
| Synthetic portfolio | `gridmatch.data.synthetic` | 12 simulated sites and 180 days of half-hourly observations | Generated demonstration data; no real customers |

## Provenance contract

Each manifest retains `dataset_name`, `source_url`, `retrieved_at`, `raw_path`, `processed_path`, `schema_version`, `data_origin`, `license_or_terms` and `retrieval_mode`. Public fixtures are compact snapshots derived from successful official responses. They retain `data_origin=public` and explicitly use `retrieval_mode=fixture` when selected.

## Known source limitations

- Public endpoints and schemas can change; boundary validation intentionally fails loudly when required structure disappears.
- The REPD source CSV currently requires Windows-1252 decoding. Its raw response is retained unchanged.
- Elexon demonstrations use a fixed compact date window and are not a complete settlement history.
- The NESO demonstration selects a relevant historic-demand result through CKAN discovery rather than hard-coding a resource ID.
- Open-Meteo’s demonstration uses ERA5 archive data; it is not a stored operational forecast vintage.
- DST dates are computed from the installed IANA `Europe/London` timezone rules rather than downloaded as a separate dataset.
