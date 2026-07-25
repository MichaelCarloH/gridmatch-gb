# Renewable matching methodology

## Interpretation

GridMatch's renewable-matching output is a commercial and accounting
allocation between simulated renewable generators and simulated business
consumers. It does not model grid topology, power flows or the path travelled
by physical electricity. A shorter allocation distance is a configurable
commercial preference only; it is not evidence that electrons travelled
locally.

## Inputs and timing

The engine uses the 626 common rolling-origin periods produced in Phases 6 and
7. Forecast allocations use only each site's day-ahead point forecast.
Realised allocations use only the corresponding out-of-sample actual energy.
The files and `allocation_type` field keep these modes separate. The forecast
issue time is retained on both outputs so planned and realised outcomes share
an auditable decision context.

Each period contains four renewable generators and eight demand consumers.
No site or portfolio period is silently discarded. Zero availability or zero
demand remains visible in the period summaries even when it produces no
positive allocation arc.

## Optimisation objective and constraints

For matched energy \(x_{g,c,t}\), generator availability \(G_{g,t}\), and
consumer demand \(D_{c,t}\), the model enforces:

\[
x_{g,c,t} \ge 0,\qquad
\sum_c x_{g,c,t} \le G_{g,t},\qquad
\sum_g x_{g,c,t} \le D_{c,t}.
\]

All generator-consumer pairs are eligible in the prototype, so the exact
maximum match is \(\min(\sum_g G_g,\sum_c D_c)\). The SciPy HiGHS linear
programme fixes total allocation to that maximum and then minimises only a
secondary tie-break cost. This lexicographic construction means preferences
cannot reduce renewable volume.

The `maximum_match` mode uses deterministic site ordering as its geography-
neutral tie-break. The `local_preference` mode uses a normalized score of 80%
great-circle distance, 15% same-region preference, 4.9% deterministic
technology preference, and 0.1% site ordering. The score is transparent and
repeatable, with no random tie-breaking. A deterministic greedy fallback is
available if SciPy cannot be imported, although SciPy is an explicit project
dependency and the generated artifacts record the solver used.

## Metrics and outputs

Period metrics report demand, generation, matched energy, residual grid
demand, unused generation, renewable match rate and matched-MWh-weighted
distance. Consumer summaries report renewable coverage and residual demand.
Generator summaries report offtake coverage and unused generation. Zero
denominators produce a zero coverage ratio.

Positive generator-consumer matches are exported as audit records and compact
map arcs. Period summaries preserve all periods, including any zero-match
period. `allocation_comparison.parquet` defines allocation error as realised
matched MWh minus forecast matched MWh.

## Production limitations

The prototype uses simulated sites, energy and weather. A production matching
problem would need contractual eligibility and volume terms, supplier and
balancing-party constraints, certificate ownership and retirement rules such
as REGOs, generation and demand prices, credit and settlement terms, temporal
granularity rules, and potentially fairness or concentration limits. Network
constraints would require a separate physical power-system model. Financial
valuation and hedge optimisation belong to Phase 9 and are intentionally not
included here.

This work is an independent prototype and does not claim affiliation with
Volter or reproduction of any private Volter system, contract or methodology.
