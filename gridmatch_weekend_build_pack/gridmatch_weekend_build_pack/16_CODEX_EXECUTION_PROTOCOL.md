# Phase 16 — Codex Execution Protocol

## Why the first attempt became a toy

A large product prompt can cause a coding agent to:

- compress requirements;
- generate a conceptual scaffold;
- use placeholders;
- stop after one pass;
- optimise for showing breadth rather than implementation depth.

The remedy is phased execution with acceptance criteria.

## Rule

Give Codex one phase at a time.

Do not paste all phases repeatedly.

## Initial command

```text
Audit the current repository. Read 00_README.md through 02_REPOSITORY_STRUCTURE.md. Implement only the repository structure phase. Preserve useful code, run the initial build and tests, fix errors, and update PROGRESS.md. Do not begin later phases.
```

## Phase continuation template

```text
Read [PHASE_FILE]. Implement every P0 requirement in that file directly in the repository. Do not return only a plan. Run the relevant commands, fix failures, update PROGRESS.md with completed items and evidence, and stop only when the phase acceptance criteria pass.
```

## Verification prompt

After every phase:

```text
Audit the phase you just completed against its Markdown acceptance criteria. List missing items in PROGRESS.md, implement them now, run tests, and provide the exact commands and outputs proving completion.
```

## Anti-placeholder prompt

```text
Search the repository for TODO, placeholder, mock, lorem, hardcoded KPI, fake metric and static demo response. Replace every P0 placeholder with artifact-backed logic or explicitly documented deterministic fixture data. Run tests and the production build.
```

## Model-phase prompt

```text
Do not return model pseudocode. Train the models, save loadable artifacts, export forecasts and metrics, verify q10 <= q50 <= q90, verify physical bounds and show the exact artifact paths.
```

## Frontend-phase prompt

```text
Open every P0 route, connect it to generated outputs, remove placeholder cards, add loading/error/empty states, run npm run build and fix every error. Do not stop at component scaffolding.
```

## Final audit prompt

```text
Perform a final repository audit against 01_PRODUCT_SCOPE.md. Run make test, execute notebooks, run the frontend production build, inspect all routes, verify demo artifacts and update README, DEMO_SCRIPT.md and PROGRESS.md. Fix all P0 gaps before summarising.
```

## Working style

Use Codex as an implementation loop:

```text
specify phase
→ implement
→ run
→ inspect
→ fix
→ verify
→ commit
```

Do not use:

```text
huge prompt
→ one-shot generation
→ accept summary
```

## Commit strategy

Suggested commits:

```text
chore: scaffold research and product monorepo
data: add GB public and synthetic pipelines
feat: add settlement validation and data quality
model: add site-level probabilistic forecasts
model: add portfolio reconciliation
feat: add renewable matching and hedge engine
api: expose forecasts and decisions
web: add portfolio and site experience
test: add invariants and integration coverage
docs: add research, model cards and demo
deploy: prepare production demo
```
