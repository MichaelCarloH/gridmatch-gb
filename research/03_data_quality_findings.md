# Data quality and site-profile findings

## Verified public facts

The data-quality rules and 0–100 score are documented in `DATA_QUALITY.md`. Phase 4 validation preserves source rows and writes annotations rather than silently removing invalid observations.

## Observed data findings

The demo portfolio contains 12 simulated sites and 103,680 simulated observations. All source columns in the processed observation artifact have zero recorded missingness. The annotated artifact retains the same row count and records 5,086 rule-based flags: 4,936 extreme-spike candidates and 150 long-zero-run candidates.

All 12 sites are currently classified `ready`, with scores from 95.55 to 99.84. The two solar sites have simulated capacity factors near 13.8%; the two wind sites are near 21.8–21.9%. Office, manufacturing, solar, and wind profiles have visibly different half-hour shapes.

## Modelling assumptions

Flags identify review candidates, not automatically confirmed faults. Capacity factor is descriptive over the simulated coverage window. Readiness indicates that the documented prototype checks pass; it does not establish fitness for every downstream use.

## Prototype limitations

The portfolio is simulated, so these results do not demonstrate public generator coverage or real customer meter quality. The anomaly rules deliberately favour sensitivity and may flag legitimate ramps or operational zero periods.

## Production recommendations

Keep the original observation beside every annotation. For each later use case, explicitly decide whether flagged rows are excluded, down-weighted, repaired, or modelled, and record that decision with the rule version and reviewer outcome.
