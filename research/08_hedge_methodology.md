# Hedge-decision methodology

## Scope and interpretation

The Phase 9 engine converts an out-of-sample portfolio forecast distribution
into a signed day-ahead net-volume decision. Positive MWh means forward
procurement; negative MWh represents a forward sale for forecast net
generation. This is a research prototype, not a licensed-supplier settlement
engine, trading recommendation, or reproduction of a private commercial
system.

The volume forecasts cover 626 June 2025 settlement periods. The cached public
Elexon price artifact is a July 2026 snapshot: it has a complete 48-period
system-price curve but only five positive-volume APX market-index points.
There is no contemporaneous overlap. The engine therefore uses the APX
volume-weighted price and the public system-price shape as an explicitly
labelled scenario reference mapped by settlement period. Reported GBP values
are scenario costs, not realised historical costs or supplier savings.

## Simplified cost convention

For realised signed net demand \(Y_t\), hedge \(H_t\), market reference
\(P^{ref}_t\), short price \(P^{short}_t\), and long recovery price
\(P^{long}_t\):

\[
C_t = H_tP^{ref}_t
      + \max(Y_t-H_t,0)P^{short}_t
      - \max(H_t-Y_t,0)P^{long}_t.
\]

The base scenario uses a minimum short price of 1.35 times the market
reference and a maximum long recovery of 0.65 times the reference. The public
system-price curve can make short settlement more expensive or long recovery
lower. All assumptions and source dates are stored on every recommendation.

When short and long values are asymmetric, the newsvendor cost ratio implies:

\[
\tau =
\frac{P^{short}-P^{ref}}
     {P^{short}-P^{long}}.
\]

The lightweight `scenario_recommendation` function recalculates this quantile,
the interpolated hedge, and deterministic expected short/long exposures for
new multipliers and risk preference without retraining a model.

## Forecast distribution and policies

The default forecast is Phase 7's bottom-up net-position q10/q50/q90
distribution because it had the strongest net-position MAE in that phase.
Intermediate quantiles use monotonic piecewise-linear interpolation. Expected
exposure uses fixed split-normal quantile samples, never random draws.

The historical comparison includes no hedge, q50, q60, q70, q80,
validation-optimised, and perfect foresight. Perfect foresight sets the signed
hedge equal to realised net demand, uses information unavailable at decision
time, and is retained only as an unattainable lower-bound benchmark.

## Leakage-safe validation

Fold 1 has no earlier out-of-sample forecast evidence, so it uses the nearest
quantile on the asymmetric-cost grid. Each later fold evaluates q10 through
q90 only on earlier-fold outcomes whose delivery timestamp is strictly before
the current fold's earliest forecast issue time. The current delivery outcome
never selects its own quantile. Training cutoffs, issue times, evidence end
times and selection source remain in the recommendation artifact.

## Risk and sensitivity

Policy metrics include total scenario cost, cost difference versus no hedge,
short and long exposure, standard deviation, p95 cost, CVaR95 and worst-period
cost. A 3×3 sensitivity grid varies short-cost and long-value multipliers.
Risk preference in the scenario function moves the cost-implied quantile
toward q90, making its direction explicit.

## Production limitations

A production implementation needs contemporaneous day-ahead price forecasts
and realised imbalance prices, tradable product shapes, liquidity and market
impact, gate-closure timing, fees, credit and collateral, supplier and BSC
settlement rules, metering corrections, contract constraints, position limits,
approval controls and live audit trails. The prototype does not claim actual
financial savings or affiliation with Volter.
