# Deploy GridSight

This repository serves the full Python planning dashboard, not a static Pages
copy. GitHub stores the source; Render runs calculations and report generation.
The green brand, both audience roles, eight-country selectors, Rwanda public
proxies and all planning/report features are retained.

## Free Render demo

1. In Render, choose **New → Blueprint** and connect
   **siltanukifilie/GridSight**, branch **main**.
2. Review the single web service in `render.yaml`: **Free**, Frankfurt,
   Python 3.14.4, no databases, disks or paid services.
3. Confirm creation. If asked for new GitHub permissions, restrict the
   integration to this repository. Review any terms yourself.
4. Wait for the build and health check. Open the assigned HTTPS URL; check both
   roles, a Rwanda location, the forecast and the downloadable deliverables.
5. Later pushes deploy only after the GitHub checks pass. Do not enable a paid
   service or overage billing without the account owner's approval.

If creating a Web Service manually, copy these settings:

- Build: `pip install -r requirements-web.txt`
- Start: `gunicorn --config gunicorn.conf.py 'app:create_app()'`
- Health check: `/health`
- Python: `3.14.4`
- Environment: `GRIDSIGHT_PUBLIC_DEMO=1`, `GRIDSIGHT_LOW_MEMORY=1`,
  `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `PYTHONUNBUFFERED=1`.
- Plan: **Free**; region: **Frankfurt**; branch: **main**.

The free service can sleep after 15 minutes idle and take about a minute to
wake. Free usage is limited; existing payment methods can permit bandwidth or
build overage charges. Review the workspace's usage/spend controls. No database
or persistent disk is needed: saved projects live in the browser, and reports
download to the user's device. Server filesystem changes are ephemeral.

## Public-data and privacy boundaries

- The public demo accepts **non-confidential planning scenarios only**. Inputs
  are processed on Render, not solely on the visitor's computer.
- There are no secure operator accounts. The audience switch is not access
  control. Four meter-validation/recalibration POST routes return 403 before
  parsing data, and their upload forms are disabled on the public demo.
  Templates, protocols and synthetic evidence remain downloadable.
- The complete validation/recalibration tools remain available locally without
  `GRIDSIGHT_PUBLIC_DEMO=1`. Do not turn that flag off on a public service
  until authentication, approved transfer/storage, retention, rate limits and
  security review are implemented.
- No operator records, private registries, credentials or local export bundles
  belong in this repository. Request bodies are not written to application
  logs. Render's own infrastructure/logging has separate privacy terms.
- `data/rwanda/electricity.json` is intentionally excluded: public-query
  access does not establish redistribution rights. The public app displays
  that historical layer as unavailable; grid status remains unknown.
- Public GeoNames, Open Buildings, geoBoundaries and the independent OSM extract
  retain their provenance/licence notices. See `THIRD_PARTY_NOTICES.md`.
- No real metered-site validation, calibrated real-world confidence or proven
  investment return is claimed by hosting the app.

## Reproduction and updates

The pretrained model, synthetic data and profile snapshots are committed.
Do **not** regenerate them during deployment. Runtime packages are pinned in
`requirements-web.txt`; optional rebuilding dependencies remain in the
original requirements files.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-web.txt pytest==9.2.0
.venv/bin/python -m pytest -q
node --test tests/*.test.cjs
GRIDSIGHT_PUBLIC_DEMO=1 GRIDSIGHT_LOW_MEMORY=1 PORT=8050 .venv/bin/gunicorn --config gunicorn.conf.py 'app:create_app()'
```

One synchronous worker avoids duplicate large source indexes. The low-memory
lookup uses bounded latitude filtering followed by the same spherical-distance
test as the local tree; it does not change the 500 m catchment or forecast.
Keep source snapshots and their hashes versioned when deliberately refreshing.
Real-data updates still use the private, reviewed workflow in
`REAL_DATA_UPDATES.md`, not an automatic public retraining endpoint.

References: [Render Flask hosting](https://render.com/docs/deploy-flask),
[free service limitations](https://render.com/docs/free),
[Blueprint settings](https://render.com/docs/blueprint-spec).
