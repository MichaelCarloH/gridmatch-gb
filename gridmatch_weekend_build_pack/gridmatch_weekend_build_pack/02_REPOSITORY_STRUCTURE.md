# Phase 2 — Generate the Repository Structure

## Goal

Create a research-to-production monorepo before writing feature code.

## Required structure

```text
gridmatch-gb/
├── app/
│   ├── page.tsx
│   ├── dashboard/
│   ├── map/
│   ├── sites/
│   ├── sites/[siteId]/
│   ├── forecasts/
│   ├── matching/
│   ├── market/
│   ├── assets/
│   ├── reports/
│   └── research/
├── components/
│   ├── charts/
│   ├── layout/
│   ├── map/
│   ├── portfolio/
│   ├── site/
│   └── ui/
├── lib/
│   ├── api.ts
│   ├── format.ts
│   ├── settlements.ts
│   └── types.ts
├── api/
│   ├── index.py
│   ├── routes/
│   └── schemas/
├── src/gridmatch/
│   ├── clients/
│   ├── data/
│   ├── features/
│   ├── models/
│   ├── portfolio/
│   ├── matching/
│   ├── market/
│   ├── monitoring/
│   ├── reporting/
│   └── simulation/
├── notebooks/
├── research/
├── scripts/
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── demo/
├── artifacts/
│   ├── models/
│   ├── forecasts/
│   ├── metrics/
│   ├── figures/
│   ├── matching/
│   └── reports/
├── tests/
│   ├── python/
│   └── web/
├── public/
│   └── demo-data/
├── .github/workflows/
├── README.md
├── ARCHITECTURE.md
├── DATA_SOURCES.md
├── MODEL_CARDS.md
├── LIMITATIONS.md
├── DEMO_SCRIPT.md
├── PLAN.md
├── PROGRESS.md
├── pyproject.toml
├── package.json
├── Makefile
└── vercel.json
```

## Initial files

Create:

- `.env.example`
- `.gitignore`
- `Makefile`
- Python package configuration
- TypeScript configuration
- Tailwind configuration
- linting configuration
- test configuration
- base README
- `PLAN.md`
- `PROGRESS.md`

## Make commands

```makefile
install:
	python -m pip install -e ".[dev]"
	npm install

demo-data:
	python scripts/build_demo_dataset.py

train:
	python scripts/train_models.py

backtest:
	python scripts/run_backtest.py

notebooks:
	python scripts/execute_notebooks.py

api:
	uvicorn api.index:app --reload

web:
	npm run dev

test:
	pytest
	npm run lint
	npm run build
```

## Acceptance criteria

- `python -c "import gridmatch"` succeeds.
- `npm run build` reaches the first compilation stage.
- all folders exist;
- no application logic is placed in `README.md`;
- `PLAN.md` contains P0, P1 and P2 tasks;
- `PROGRESS.md` records completed work.

## Codex execution prompt

```text
Inspect the current repository. Generate the exact research-to-production structure described in 02_REPOSITORY_STRUCTURE.md. Preserve useful existing code. Create configuration, Makefile, PLAN.md and PROGRESS.md. Run the Python import and frontend build, fix structural errors, and stop only when the scaffold is runnable. Do not implement feature logic yet.
```
