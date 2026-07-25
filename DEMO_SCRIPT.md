# Demo script

Open `/demo` and use the guided controls. The complete client path is designed
for about two minutes; the condensed interview path below takes 90 seconds.

## 90-second walkthrough

1. **Business overview — 15 seconds.** Open `/business`. Explain forecast
   consumption, commercial renewable coverage, residual grid exposure,
   scenario cost and the artifact-backed action centre. State that the
   portfolio is simulated.
2. **Renewable coverage — 10 seconds.** Open `/business/renewables`. Read the
   disclosure: matching is commercial same-half-hour allocation, not physical
   routing.
3. **Tomorrow's energy plan — 15 seconds.** Open `/business/energy-plan`. Show
   expected demand, generation, residual need, uncertainty and recommended
   contracted volume. Procurement is executed by a licensed partner, not this
   application.
4. **Generator — 10 seconds.** Switch to `/generator`. Show output, offtake,
   unused generation and scenario revenue. State that values are not invoices
   or contract terms.
5. **Control room — 15 seconds.** Open `/operations/portfolio`. Point out the
   half-hour plan, recommendation and realised result are separate columns.
6. **Diversification — 10 seconds.** Open `/operations/diversification`, then
   `/operations/stress-tests`. Show error contribution and one fixed,
   reproducible stress ID.
7. **Model operations — 10 seconds.** Open `/models`. Explain site, fallback,
   bottom-up, direct and reconciled models, then open incidents or calibration.
8. **Methodology — 5 seconds.** Expand “How calculated” on a KPI and show the
   full meter-to-report lineage.

## Full guided client demo

The `/demo` route links these ten steps:

1. Non-persistent supermarket onboarding and CSV validation.
2. Site consumption, peak, baseload, anomalies and quality.
3. Day-ahead demand.
4. Renewable supply.
5. Commercial matching.
6. Residual requirement.
7. Recommended contracted volume.
8. Printable business report.
9. Generator and operator perspectives.
10. Model methodology.

## Presenter guardrails

- Always state unit, period, data origin and whether a value is forecast,
  realised or scenario.
- Do not describe allocation as physical electricity routing.
- Do not describe scenario cost or revenue as a bill, saving or invoice.
- Do not imply live trading, production model status or permanent data storage.
