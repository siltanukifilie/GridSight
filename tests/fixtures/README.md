# Synthetic regression fixtures

These five JSON files are unchanged fictional analysis responses used by the
JavaScript tests. They preserve legacy behavior during upgrades; they are not
current live reports or field observations.

- `rw-demo-01.json`, `rw-demo-02.json`, `rw-demo-03.json`: fictional demo responses.
- `connection-ramp.json`: assumed post-connection scenario.
- `detailed-inputs.json`: detailed-input scenario with assumed finances.

They moved from `reports/examples/` during cleanup. Generating a new report
does not automatically overwrite these regression fixtures.
