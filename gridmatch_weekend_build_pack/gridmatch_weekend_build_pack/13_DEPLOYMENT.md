# Phase 13 — Deployment

## Goal

Deploy a stable demo without moving research workloads into serverless requests.

## Deployment split

### Offline build pipeline

Run locally or in CI:

- data downloads;
- data cleaning;
- simulation;
- feature generation;
- training;
- backtesting;
- notebook execution;
- artifact exports.

### Deployed runtime

Serve:

- frontend;
- compact API;
- saved predictions;
- small model inference;
- upload validation;
- hedge scenarios;
- cached maps and reports.

## Vercel

Use Vercel for:

- Next.js frontend;
- lightweight API route or FastAPI function if bundle size permits;
- static artifacts;
- environment variables.

Do not rely on Vercel cron for hourly model refresh.

## Fallback deployment

When Python serverless deployment is difficult:

- export JSON/Parquet-derived compact JSON;
- serve through Next.js API routes;
- keep FastAPI runnable locally;
- deploy the frontend with deterministic demo artifacts.

## Deployment checklist

- `npm run build`;
- environment example;
- no secrets;
- bundled demo artifacts;
- public landing page;
- public dashboard;
- API health;
- correct CORS;
- valid links;
- disclaimer;
- GitHub repository;
- screenshot;
- demo video.

## Acceptance criteria

- public URL loads;
- no login required;
- dashboard works without external API availability;
- deployment matches local outputs;
- README includes exact deployment process;
- API or static fallback is documented.

## Codex execution prompt

```text
Complete Phase 13 from 13_DEPLOYMENT.md. Prepare Vercel configuration, bundle deterministic demo artifacts, deploy the frontend and lightweight API or documented fallback, verify the public URL, and update README with exact deployment steps.
```
