# Phase 14 — Weekend Execution Plan

## Friday evening — Foundation

### Block 1: repository

- audit current 300-line prototype;
- preserve useful code;
- generate structure;
- configure Python and Next.js;
- create Makefile;
- run first build.

### Block 2: data

- build deterministic site simulation;
- ingest REPD;
- export map GeoJSON;
- prepare a cached public generation fixture;
- implement settlement utilities.

### Friday definition of done

- repository exists;
- at least 10 sites exist;
- 180 days of data exist;
- map data exists;
- DST tests pass;
- one notebook executes.

## Saturday morning — Site models

- feature generation;
- baselines;
- statistical model;
- ML point model;
- q10/q50/q90;
- rolling validation;
- model artifacts;
- model cards.

### Saturday midday definition of done

- every site has a forecast;
- metrics exist;
- quantile ordering holds;
- physical limits hold.

## Saturday afternoon — Portfolio and decisions

- bottom-up forecast;
- direct portfolio model;
- reconciliation;
- renewable matching;
- hedge policies;
- historical cost backtest;
- anomaly detection.

### Saturday definition of done

- portfolio artifact exists;
- matching artifact exists;
- hedge recommendations exist;
- alerts exist;
- four notebooks execute.

## Sunday morning — API and frontend

- FastAPI;
- landing;
- dashboard;
- map;
- site list;
- site detail;
- forecast lab;
- matching;
- market page;
- research page.

### Sunday midday definition of done

- full flow works locally;
- frontend consumes generated outputs;
- no blank P0 routes.

## Sunday afternoon — Polish and deployment

- tests;
- production build;
- loading/error states;
- visual polish;
- reports;
- documentation;
- deploy;
- record demo;
- prepare interview answers.

## Time-control rule

When behind schedule:

1. keep deterministic demo data;
2. keep site models;
3. keep portfolio forecast;
4. keep matching;
5. keep hedge simulator;
6. keep dashboard and site pages;
7. cut advanced live ingestion;
8. cut battery optimisation;
9. cut authentication;
10. cut deep learning.

## Final weekend definition of done

- live URL;
- GitHub repository;
- working model artifacts;
- executed notebooks;
- strong README;
- 90-second demo;
- interview talking points.
