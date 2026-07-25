# Universal Stage Update Prompt

Replace `[PHASE_FILE]` and `[PHASE_NUMBER]`.

```text
Audit the repository against [PHASE_FILE] and the current PROGRESS.md.

Do not begin the next phase.

For Phase [PHASE_NUMBER]:

1. Inspect every file created or changed.
2. Compare the implementation with every acceptance criterion.
3. Search for TODO, placeholder, mock, lorem, hardcoded KPI, fake metric, static response, broken route, false zero and missing disclosure.
4. Verify every displayed number comes from an artifact, API result or documented deterministic approximation.
5. Verify public, simulated and uploaded data labels.
6. Verify no completed Phase 3–10 artifact changed without a documented blocking defect.
7. Run relevant tests, notebook execution and production build.
8. Test every new route through direct navigation.
9. Test static fallback and local API modes where relevant.
10. Fix every missing P0 item.
11. Update PROGRESS.md with files, commands, results, route evidence, limitations and confirmation that the next phase was not started.

Return a concise completion report only after the phase passes.
```
