# GridSight forecasting model

Version 1.0.0 predicts first-year average monthly customer demand in kWh/month. All model training, calibration, and evaluation use synthetic data.

The model uses seven customer-group counts, expected household uptake, and an appliance index. It excludes district names, site IDs, future monthly outcomes, latent generator parameters, and realized growth.

## Point estimator

A transparent engineering baseline sums documented sector assumptions. A gradient-boosting regressor predicts the multiplicative correction to that baseline. It has 120 estimators, depth 2, learning rate 0.04, minimum leaf size 15, and the fixed project seed. The baseline and trained model are compared on an internal holdout of the training sites. The lower-MAE option becomes the point estimator.

The selected estimator is gradient boosting. Zero baseline demand always produces zero point demand and zero bounds. Point corrections are constrained to 0.05–4 to keep application outputs finite and positive; this is a numerical guard, not evidence that out-of-range inputs are reliable.

## Prediction interval

Separate 10th- and 90th-percentile gradient-boosting regressors fit the target-to-baseline ratio. Initial bounds are nonnegative and expanded if necessary to contain the point estimate. Calibration scores are the nonnegative outside-interval error divided by the baseline. A finite-sample quantile of the scores from 100 separate calibration sites widens the bounds. The same interval construction is used in evaluation and the application.

The nominal interval target is 80%. Observed coverage on the test set is reported separately. Any exchangeability-based coverage interpretation is confined to comparable data; it is not a guarantee for unseen real populations. See the [scikit-learn quantile example](https://scikit-learn.org/stable/auto_examples/ensemble/plot_gradient_boosting_quantile.html) for the underlying quantile regression approach. The calibration code is in `src/model.py`.

## Recorded evaluation

| Metric | Held-out synthetic result |
|---|---:|
| Test sites | 100 |
| Mean absolute error | 1,294.73 kWh/month |
| Root mean squared error | 1,843.21 kWh/month |
| Weighted absolute percentage error | 10.55% |
| Nominal interval coverage | 80% |
| Observed interval coverage | 91% |
| Mean interval width | 5,090.70 kWh/month |
| Baseline mean absolute error | 2,236.26 kWh/month |

These values are drawn from `reports/evaluation.json`; tests independently recompute the error and coverage from the saved test predictions. The point model reduces MAE by approximately 42% versus the baseline on this synthetic test set. This comparison does not establish an improvement on real mini-grids.

When all synthetic test outcomes are increased by 25% without changing inputs, weighted error rises to 22.49% and interval coverage falls to 36%. This deliberately simple shift illustrates why local operator data is needed.

## Explanation and limits

The interface shows the transparent baseline's sector breakdown and one-input-at-a-time sensitivities of the selected point estimator. These are distinct explanations; baseline shares are not claimed to explain the trained model exactly. Different sensitivity increments should not be read as a global importance ranking.

The hourly profile is an illustrative distribution of daily energy using RAMP shapes. Its peak is not a measured annual maximum. Growth curves apply explicit scenario assumptions to Year 1; their bands propagate initial uncertainty under the same assumptions and are not independently calibrated growth intervals. Financial outputs are deterministic scenario calculations, not a lender recommendation.

Future validation should use permissioned site-level data with consistent metering periods, outage and service context, tariffs, connection dates, and pre-construction features. Keep sites and relevant regions separate when evaluating transfer, assess calibration and subgroup errors, and retain a real-site holdout untouched during model selection.
