# Final audit

Audit date: 25 July 2026.

## Scope

Extension Phases 11–20 were audited against
`gridmatch_extension_pack/18_PHASE_11_SHARED_SHELL.md` through
`27_PHASE_20_INTERVIEW_PACKAGING.md`. The quantitative outputs from Phases
3–10 were preserved; no request-time training or trading path was introduced.

## Acceptance evidence

| Area | Evidence | Result |
|---|---|---|
| Shared shell | Six persisted workspaces, breadcrumbs, responsive navigation, data-origin disclosure and global states | Pass |
| Business portal | Consumption, matching, residual, scenario cost, actions, site detail, energy plan and print report | Pass |
| Generator portal | Output, probabilistic forecast, offtake, unused generation, performance, scenario revenue and incidents | Pass |
| Operations | Half-hour position, planned/realised separation, tail risk and bounded scenarios | Pass |
| Diversification | Saved correlation/attribution, contribution proxies, HHI, eight stress IDs and four additions | Pass |
| Model operations | Hierarchy, metrics, aggregate calibration, registry, incidents and drift evidence | Pass |
| Admin | Non-persistent onboarding, simulated contracts, data operations and CSV validation | Pass |
| Explainability | Ten-step demo, full calculation lineage and three print-safe reports | Pass |
| Integration | Direct routes, static fallback, local API mode, responsive/print CSS, chart labels and bounded API responses | Pass locally |
| Packaging | Required documents, 90-second script, honest claims and tooling statement | Pass |

## Claims audit

- Public, simulated and uploaded origins are visible in the shared shell.
- Planned, realised and scenario values use distinct labels.
- Renewable matching is disclosed as commercial allocation, not physical
  routing.
- Costs and revenue disclose their public scenario reference and are not called
  invoices, savings or contract terms.
- Procurement ownership is assigned to a licensed supplier or utility partner.
- No emissions saving is asserted.
- No live production, retraining, payment, legal execution or permanent upload
  storage is implied.

## Verification record

The authoritative command results are recorded in `PROGRESS.md`. The final
verification set includes:

```powershell
py -3 -m uv run python scripts/build_frontend_fallback.py
py -3 -m uv run python -m pytest -q
py -3 -m uv run python scripts/execute_notebooks.py
cmd /c npm test
cmd /c npm run build
```

Direct route checks cover every extension route in public static-fallback mode
and representative health/API calls in local technical mode.

## Deployment status

Extension commit `6a2cdcc` was pushed to
`agent/publish-gridmatch-vercel`. Vercel deployment
`dpl_8duajTPhV7amAvTucs69uhhAPqSo` reached `READY`, was promoted to production
and was aliased to `https://gridmatch-gb.vercel.app`. Public route and API
checks returned HTTP 200 after deployment. Draft PR #1 remains open against
`master`.
