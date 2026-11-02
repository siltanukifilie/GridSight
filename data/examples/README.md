# Juru examination dataset

Developed by the GridSight Team. **Synthetic test data, not meter readings.**

Open **Locations → Load Juru test case**. Both customer roles use the same project.
The starting screen also offers this button without requiring cell selection.

[The complete input preset](juru_synthetic_project.json) contains all 20 requested
features, eight appliance types, six equipment/service types, 12 agricultural
factors and all financial planning inputs. Currency is RWF; amounts are test
assumptions, not verified tariffs, incomes or equipment quotes.

## Scope

This is a 300-household demo service area associated with Juru, not Juru's entire
sector or an actual surveyed cell. No coordinates or real cell are invented.
Juru's 8,508 census households remain separate public sector context. Unknown
equipment totals and meter labels in the public source table remain unavailable.

The initial connection share is 65% (195 households); 36 connections/year are
added, capped at 300. Appliance adoption is 8%/year and business growth is
10%/year. Additional productive equipment is assumed from Year 2. All are
synthetic assumptions. Seasonality may produce monthly declines even when
annual consumption increases. The date January 2027 is a demonstration start,
not an actual commissioning date.

## Download and examine

- `GET /api/demo-cases/juru` returns the metadata and complete original project.
- `GET /api/demo-cases/juru/download` returns a ZIP with the 20-feature table,
  all editable inputs, 36 monthly low/expected/high scenarios, a 24-hour profile,
  daily/weekly/monthly/yearly equivalents, financial stress scenarios, a report,
  and separate public-sector context and sources.
- **Export report** includes `juru_test_case/` with the **currently edited**
  inputs and results. The dedicated test download always returns the preset.

Scenario tables are generated deterministically by the existing engineering
calculator. No random or measured meter targets are added. This case is not
inserted into training, calibration, held-out validation or sector rankings.
Low/high remain scenarios, not statistical confidence limits.

## Checks

To produce an offline examination pack, run
`.venv/bin/python scripts/export_juru_test_case.py`.
It writes the ZIP, individual CSVs, JSON inputs and report to the ignored
`exports/juru-examination/` directory. Use `--output /absolute/directory` to choose
another destination. Existing generated files in that destination are replaced.

Run `.venv/bin/python -m pytest -q tests/test_demo_cases.py`, then
`node --test tests/demo-cases.test.cjs` from the repository root. These check
completeness, arithmetic, exports, preservation of public evidence, both roles,
and safe loading/error behavior; they do not establish field accuracy.
