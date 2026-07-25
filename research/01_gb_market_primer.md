# GB market and settlement primer

## Verified public facts

Great Britain electricity delivery is settled in half-hourly periods. A normal Europe/London delivery day has 48 periods, the spring clock-change day has 46, and the autumn clock-change day has 50. Generators and consumers create physical injections and withdrawals; suppliers contract and settle customer energy, NESO operates the system, and Elexon administers the Balancing and Settlement Code arrangements.

## Observed data findings

The deterministic worked table verifies 48 periods on 2025-01-15, 46 on 2025-03-30, and 50 on 2025-10-26. UTC boundaries remain unambiguous across both clock changes. The illustrative imbalance table uses `metered_mwh - contracted_mwh`: positive is long, negative is short. These rows are examples, not public or simulated customer observations.

## Modelling assumptions

Later research may compare point forecasts with calibrated q10/q50/q90 forecasts. Issue time, delivery time, contracted volume, and metered volume must remain distinct. No forecasting model or trading rule is introduced in this phase.

## Prototype limitations

The primer does not reproduce the complete BSC calculation, settlement charges, credit arrangements, or licensed participant processes. The deterministic volumes are for explanation only and must not be read as market advice.

## Production recommendations

Test every time conversion on normal and DST days, keep UTC as the storage timestamp, and present Europe/London delivery labels to operators. Apply an explicitly governed sign convention and only use probabilistic forecasts after calibration and risk-policy approval.
