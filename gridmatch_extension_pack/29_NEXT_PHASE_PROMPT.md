# Universal Next-Phase Prompt

Replace `[PHASE_FILE]` and `[PHASE_NUMBER]`.

```text
Read [PHASE_FILE], 17_EXTENSION_README.md and the current PROGRESS.md.

Implement only Phase [PHASE_NUMBER].

Preserve every completed previous phase and all quantitative artifacts. Do not begin the following phase.

Do not return only a plan. Inspect the repository, implement directly, run tests, fix failures, run the production build and update PROGRESS.md.

Before stopping:

1. Audit every P0 criterion.
2. Remove placeholders and false values.
3. Verify direct navigation for every new route.
4. Verify data-origin labelling.
5. Verify every KPI traces to an artifact, API result or documented deterministic approximation.
6. Confirm that no later phase was started.

Return commands, test results, changed files and limitations.
```
