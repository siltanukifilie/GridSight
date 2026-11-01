# Evaluation results

These tracked outputs belong to the **legacy synthetic reference model**:

- [evaluation.json](evaluation.json): baseline/model scores and synthetic interval coverage.
- [test_predictions.csv](test_predictions.csv): 100 held-out fictional sites,
  their synthetic targets, predictions and intervals.

They do not establish field accuracy. Measured-study results are in
[operational data](../data/operational/) and
[transfer evidence](../data/transfer_uncertainty/).

Generated HTML/ZIP review bundles and user-scenario exports stay local and are
ignored by Git. See the [script guide](../scripts/README.md) for regeneration.
Frozen JSON examples required by tests moved to [test fixtures](../tests/fixtures/).
