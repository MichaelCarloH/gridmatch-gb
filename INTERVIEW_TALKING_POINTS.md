# Interview talking points

## What problem does the product solve?

Half-hour electricity data is fragmented across meter quality, forecasts,
renewable output, commercial allocation and residual procurement. GridMatch GB
joins those decisions with one traceable settlement-period model, then presents
the same evidence for a business customer, generator, operator, modeller and
data administrator.

## What is public versus simulated?

Public evidence includes REPD operational assets and cached GB market
references. The 12 operational sites, observations, forecasts, allocations,
contracts and commercial scenarios are deterministic and simulated. CSV
uploads are user-supplied, validated in memory and not retained.

## Why site and portfolio models?

Site models preserve local load and technology behaviour and support error
attribution. Bottom-up aggregation makes the portfolio explainable. A direct
portfolio model remains an independent challenger. Reconciliation enforces the
identity `demand - generation = net` while retaining the site evidence.

## Why did bottom-up win, and why keep direct models?

Bottom-up provides traceable site contributions and competitive temporal
metrics. Direct models can capture portfolio-level cancellation and are useful
challengers. MAE and procurement cost can disagree because signed, tail and
price-weighted errors matter differently from absolute error.

## Why probabilistic forecasts?

A point forecast cannot describe short/long risk. q10, q50 and q90 allow
empirical coverage checks and support bounded contract-volume scenarios. The
intervals are evaluated, not treated as guarantees.

## How does matching work?

For each GB settlement period, renewable generator MWh is allocated to
consumer demand under maximum-match or local-preference modes. Conservation
tests ensure allocations do not exceed demand or generation. These are
commercial links, not physical grid paths.

## Who executes procurement?

A licensed supplier or utility partner. The application provides scenario
decision support and never executes a trade.

## What changes with real Volter data?

Replace simulated sites with governed meter and contract masters; use
forecast-at-issue weather; align contemporaneous prices and tariffs; add
identity, authorization, audit logging, private storage, monitoring and
licensed execution integration; retrain and revalidate under an agreed model
risk policy.

## What did I decide?

I specified the settlement/DST rules, data-quality score and auditability,
temporal validation, site-versus-portfolio hierarchy, reconciliation,
probabilistic outputs, commercial matching conservation, scenario boundaries,
API artifact controls and audience-specific product flow.

## How did coding agents help?

I used coding agents to accelerate implementation, but I specified the
architecture, data rules, validation design, modelling choices, acceptance
criteria and product flow. I reviewed outputs, ran tests and can explain the
core methods and trade-offs.

## How was correctness verified?

Tests cover 46/48/50-period settlement days, conversion, validation,
duplicates, missing data, physical limits, forecasting constraints, matching
conservation, API boundaries, static fallback, routes and upload validation.
Notebooks execute from a controlled runner; the frontend is type-checked and
production-built; direct routes are smoke-tested in static and local API modes.
