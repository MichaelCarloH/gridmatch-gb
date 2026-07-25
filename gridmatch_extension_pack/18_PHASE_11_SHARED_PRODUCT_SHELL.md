# Phase 11 — Shared Product Shell

## Goal

Turn the existing frontend into a reliable multi-workspace platform without changing Phase 3–10 outputs.

## Routes

```text
/business/*
/generator/*
/operations/*
/models/*
/research/*
/admin/*
```

## Required shell

- workspace switcher;
- primary and secondary navigation;
- route breadcrumbs;
- demo-period badge;
- persistent public/simulated-data disclosure;
- global loading, empty and error states;
- artifact/API availability indicator;
- static fallback mode;
- direct-route support;
- working `/research`.

## Shared components

```text
WorkspaceSwitcher
PrimaryNav
SecondaryNav
MetricCard
MetricExplanation
HowCalculatedDrawer
ActionCard
DataOriginBadge
ScenarioBadge
ArtifactStatus
LoadingSkeleton
ErrorState
EmptyState
```

## Reliability requirements

- no P0 route returns 404;
- no false zero or em-dash KPI before hydration;
- compact bundled artifacts render without FastAPI;
- direct navigation works;
- all existing calculations remain unchanged.

## Acceptance

- routes exist;
- workspace selection persists;
- static fallback works;
- build and route tests pass;
- no Phase 12 detail pages are started.

## Execution prompt

```text
Read 18_PHASE_11_SHARED_PRODUCT_SHELL.md and PROGRESS.md. Implement only Phase 11. Preserve Phase 3–10 artifacts and logic. Fix /research, direct routes, false first-render values, fallback mode and the shared shell. Run tests and npm run build. Update PROGRESS.md and stop before Phase 12.
```
