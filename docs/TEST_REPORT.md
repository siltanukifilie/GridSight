# Verification record

## v1.13 local release checks — 2 November 2026

- **728 Python tests and all 13 JavaScript test files passed** from the extracted
  handover source snapshot, without ignored local datasets or report folders.
- Added the complete Juru examination preset, both-role calculations, CSV/JSON
  and HTML exports, saved-label compatibility, and exact Juru administrative
  selection tests. Same-named locations elsewhere do not load the preset.
- The Juru public-proxy screen remains separately available. Tests preserve
  unknown public meter fields, synthetic provenance and unmodified public
  sector evidence. No financial output is clamped to a positive value.
- Dashboard wording is shorter; source notes, scenario limitations, grid-arrival
  warnings and export provenance remain accessible.
- These results cover the local release candidate, not proof of a completed
  Render deployment or visual browser acceptance. Check the live `/health`
  endpoint and GitHub workflow for the deployed release status.

## Released v1.12 — 1 November 2026

- **653 Python tests and all 12 JavaScript test files passed** before the
  repository cleanup. GitHub run
  [41304943272](https://github.com/siltanukifilie/GridSight/actions/runs/41304943272)
  passed for release commit `facdbb8`.
- Live endpoint checks completed at **13:20 UTC / 15:20 Kigali** against
  [GridSight on Render](https://gridsight-0al3.onrender.com/).
- `/health` reported feature version **1.12**, model version **1.0.0**, status OK.
  The model version describes the unchanged legacy synthetic artifact, not the
  dashboard release or separate measured experiments.
- Verified homepage/screening assets, all 15 Bugesera sectors and rankings,
  measured-study availability, 1,540 hourly feature rows, 4,216 prediction rows,
  four evidence ZIPs and included checksum inventories.
- Both roles passed using fictional demo inputs. The 36-month scenario remained
  separate from empirical operational ranges; field validation remained pending.
- All four public meter-upload/recalibration routes returned HTTP 403. No
  confidential inputs were transmitted.

These are endpoint/calculation/download checks, **not visual browser QA**.
Recent browser access was blocked by its security-verification service; no bypass
or new visual acceptance is claimed. Earlier desktop checks are preserved in
[verification history](archive/VERIFICATION_HISTORY.md).

## Repository cleanup verification

- **698 Python tests and all 12 JavaScript test files passed**, including 45 new
  repository-packaging checks. Gunicorn's production configuration check passed
  with the release environment. Diff whitespace checks passed.
- The same full suite and Gunicorn configuration check passed from an isolated
  export of the staged Git tree using the web release environment. No ignored
  local report, private layer or virtual environment was included in that export.
- New checks cover judge-facing relative links, catalogue row/column counts,
  canonical features against source values, missing labels, portable metadata,
  SVG accessibility, fixture paths and private/generated-file exclusions.
- The green README SVG was rendered locally and visually inspected. This is a
  documentation-asset check, not a new dashboard/browser acceptance claim.
  GitHub's Markdown API accepted the README headings, tables and diagram markup;
  this does not claim a browser-rendered Mermaid screenshot.
- Five unchanged fictional JSON responses moved into `tests/fixtures/`. Seven
  reproducible HTML/ZIP/summary exports were removed from Git tracking; copies
  remain locally and previous commits retain them. Private and generated review
  bundles stay ignored. No required runtime source/model asset was removed.
- The 15-row public-context review table and metadata were added, with a portable
  repository-relative source path. No observed value, model, forecast equation,
  measured-study checksum or public-upload setting was changed.

## Reproduce

Run the [README test commands](../README.md#test). GitHub Actions also runs
Gunicorn's configuration check on a fresh checkout with committed data, not
local-only reports. JavaScript tests use logic/DOM doubles, not browser automation.

Tests cover numerical scenarios, units, role consistency, source integrity,
missing data, escaping, reports/archives and upload guards. Software tests do not
establish forecasting accuracy or independent partner review.

## Still open

Current-model real-site validation, calibrated Rwanda uncertainty, measured
post-connection growth, full mobile/accessibility/print acceptance, secure hosted
operator-data access and independent capital-saving/customer evidence.
