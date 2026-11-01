# Contributing to GridSight

Developed and maintained by the **GridSight Team**.

## Before changing the app

1. Follow the [local setup](README.md#run-locally).
2. Read the [architecture](docs/ARCHITECTURE.md) and [data catalogue](data/README.md).
3. Keep the two user workspaces and public meter-upload protections intact.
4. Do not regenerate frozen data/models as part of an ordinary UI or documentation
   change. Never label synthetic observations as measured or proxies as surveys.

## Before proposing a change

Run the checks in the [README](README.md#test). Include the purpose, affected
inputs/outputs, verification performed and known limitations in your change
description. New behavior needs focused tests plus the existing regression suite.

For data updates, retain source, rights, collection/release date, unit, geographic
scope, missing-value policy and checksum inventory. Keep train/calibration/test
separation and source labels explicit. Review a change to an evidence snapshot
before updating its expected checksum. Do not weaken tests merely to accept
different model results.

## Files that do not belong in Git

- Secrets, access tokens, `.env` values or private keys.
- Customer identifiers, private meter traces, operator uploads or local registries.
- Generated user reports, export ZIPs, caches, virtual environments and raw
  downloads with unknown or incompatible redistribution terms.

Generated examples remain local under ignored report/export directories. Test
fixtures are explicitly fictional and belong in `tests/fixtures/`. Do not add
real customer data to reproduce a bug.

No blanket software licence is currently declared. See [reuse](docs/REUSE.md).
