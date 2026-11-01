GRIDSIGHT — PUBLIC HOURLY TRAINING DATA AND MODEL RESULTS

This is a reviewed subset of GridSight_Model_Comparison_20261101, not a live
model service. All numeric CSVs are unchanged experiment snapshots. Files are
checksum-pinned; missing or changed files make the section unavailable rather
than substituting examples. Hashes detect drift, not an untrusted sender's identity.

operational_features.csv: 1,540 real qualified hourly examples with 20 candidate
calendar/past-power features, site IDs, chronological splits and a target in kW.
Missing historical features stay blank. Training-only imputation/scaling is
documented in the original preparation pack, not new measured observations.
predictions.csv: 4,216 validation/test predictions across eight approaches.
The predictions are model outputs; actual_power_kw is the observed hourly target.
metrics.csv: 48 site/model/split score records, with MAE/RMSE/bias in kW and WAPE
in percent. WAPE is error and must not be converted to an accuracy percentage.
selected_models_test.csv: validation-selected model scores on later test hours.
split_summary.csv: 1,013 training, 267 validation and 260 test rows across three
separately fitted sites. Use per-site chronology; do not pool these as a global
chronological deployment test. Earlier observed test hours enter later lags.
protocol, run summary, selection lock and verification record the completed
experiment. Source manifests, feature definitions and quality notes are included.

Rwanda ECOS is not Bugesera. Congo Idjwi is in DR Congo. Haiti Beaumont is outside
East Africa. None of these observations is joined to the 15 Bugesera sectors.
Results test later hours, NOT entirely held-out sites. They do not validate the
app's monthly engineering calculation, confidence bands, capacity or growth.
Recorded campaigns were previously inspected and are short (about 18–36 days).
All displayed model choices were selected by validation MAE before test scoring.

This app bundles data/results, not executable models, preprocessing matrices or
the entire training toolchain. The original full training ZIP retains those.
Do not infer that new model inference or a production release has occurred.
The original source notes/RESULTS describe the full upstream experiment, and
any paths there refer to that pack rather than this compact app download.

Attribution: Luh, Matthias; Phipps, Kaleb; Britto, Anthony; Wolf, Matthias;
Lutz, Marek; Kraft, Johann. High-Resolution Real-World Electricity Data from Three
Microgrids in the Global South. KIT / RADAR4KIT, https://doi.org/10.35097/1305.
CC BY 4.0, https://creativecommons.org/licenses/by/4.0/. Accessed 2026-11-01.
Hourly features, model outputs and metrics are GridSight transformations,
not author-endorsed products. No confidential operator records are included.
