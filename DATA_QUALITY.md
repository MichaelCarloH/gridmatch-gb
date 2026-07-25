# Data-quality score

Phase 4 assigns every site a bounded score from 0 to 100. Invalid observations are never removed: `data/quality/annotated_observations.parquet` retains every input row and adds a pipe-delimited `quality_flag`.

| Component | Weight | Calculation |
|---|---:|---|
| Completeness | 30 | Unique valid half-hours divided by expected GB settlement periods across the covered local dates |
| Consistency | 20 | Reduced by duplicate timestamps, non-30-minute intervals and DST-period errors |
| Physical validity | 25 | Reduced by negative demand/generation, generation above capacity and night-time solar |
| Recency | 10 | Full credit when the latest value is within the configured stale-data threshold |
| Anomaly rate | 15 | Reduced by rows in long zero runs or containing robust extreme spikes |

Each component is clipped to its weight and the final score is clipped to `[0, 100]`. A site is `ready` at a score of at least 80 when it has no invalid timestamp or physical-value flags. Completeness, stale thresholds and zero-run lengths remain visible in each site report.

CSV uploads require `timestamp,consumption_kwh,generation_kwh`. Values are preserved, converted to explicit MWh columns and labelled `data_origin=uploaded`; invalid rows remain present with audit flags.
