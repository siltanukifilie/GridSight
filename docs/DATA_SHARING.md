# Proposed operator data integration

The current MVP uses generated data and contains no customer meter records. The next evidence phase should obtain explicit operator permission and agree on purpose, permitted users, retention, and publication of aggregate results.

Start with site-level monthly or hourly aggregates, stable anonymous site identifiers, connection date, customer-group totals, pre-construction surveys, service availability, metering coverage, and documented units. Preserve a distinction between observed energy and estimated unserved demand.

Remove direct identifiers and precise customer locations before transfer. Assess whether small groups or unusual time patterns could still identify a customer; aggregate further or suppress such groups. Removing names alone does not make data anonymous.

Keep raw data under controlled access with retention limits and an audit trail. Validate ranges, missing periods, units, outages, and duplicate sites before ingestion. Publish only permitted aggregate evaluation metrics. Keep the public synthetic dataset and restricted operator data in separate locations and manifests.

A future input adapter can map operator records into the documented schema. Refit the model and recalibrate intervals using appropriate real data, retaining untouched sites for evaluation. Do not mix the same site's monthly history across training and test partitions. Document whether a forecast uses only information available before construction.

Feature v1.7 implements a local, in-memory monthly aggregate importer and paired input-manifest checks; see [Monthly validation](MONTHLY_VALIDATION.md). It does not implement raw-meter ingestion, operator integration, user accounts or a protected data repository. Uploads are user-attested, not independently verified. Public-source candidates and their access/fitness limitations are recorded separately from validation outcomes.

Feature v1.8 adds a separate observed-growth and confidence study: [protocol](CONFIDENCE_AND_GROWTH.md). Allocate fresh whole sites to fitting, calibration and untouched testing before reviewing outcomes. Freeze input uncertainty settings and retain the protocol reference. Test histories cannot be reused to select growth parameters or confidence widths. Total energy does not identify connection/appliance/business drivers; any additional panels require the same authority and disclosure safeguards. Studies remain local and are not automatically deployed as regional forecasting models.

The v1.10 **Evidence → Download deliverables** pack includes the full proposal and a blank `operator_handover.json` worksheet: purpose, operator permission reference, permitted fields, recipient roles, disclosure review, approved transfer method, retention deadline, deletion owner, publication review, incident contact role and revocation process. Complete it outside the prototype under the operator's process. It is not authorization, a contract, a compliance certificate or an implemented security control. The exported meter CSV contains a header only. Uploaded study results are not automatically included in project deliverables.
