"""Baseline comparison, trained correction model, and held-out calibration."""
import json
import math
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from .domain import ROOT, CONFIG, FEATURES, baseline


def inputs(frame):
    return frame[FEATURES].to_numpy(dtype=float)


def bases(frame):
    return np.array([baseline(row) for row in frame.to_dict("records")])


def metrics(actual, predicted, lower, upper):
    return {"n_sites": len(actual), "mae_kwh": float(mean_absolute_error(actual, predicted)), "rmse_kwh": float(np.sqrt(mean_squared_error(actual, predicted))), "wape_pct": float(100 * np.abs(actual - predicted).sum() / np.abs(actual).sum()) if np.abs(actual).sum() else None, "coverage_pct": float(100 * np.mean((actual >= lower) & (actual <= upper))), "mean_interval_width_kwh": float(np.mean(upper - lower))}


class Forecaster:
    def __init__(self, bundle):
        self.bundle = bundle

    def predict_frame(self, frame):
        b = bases(frame)
        x = inputs(frame)
        factor = self.bundle["point"].predict(x) if self.bundle["selected"] == "gradient_boosting" else np.ones(len(frame))
        central = b * np.clip(factor, .05, 4)
        lower = np.minimum(central, b * np.maximum(0, self.bundle["lower"].predict(x) - self.bundle["expansion"]))
        upper = np.maximum(central, b * np.maximum(0, self.bundle["upper"].predict(x) + self.bundle["expansion"]))
        return central, lower, upper

    def predict(self, site):
        central, lower, upper = self.predict_frame(pd.DataFrame([site]))
        return {"central": float(central[0]), "lower": float(lower[0]), "upper": float(upper[0]), "baseline": baseline(site), "interval_level": .8, "method": self.bundle["selected"], "version": CONFIG["version"]}


def train(sites):
    train_frame = sites[sites["split"] == "train"].copy()
    calibration = sites[sites["split"] == "calibration"].copy()
    test = sites[sites["split"] == "test"].copy()
    fit, select = train_test_split(train_frame, test_size=.2, random_state=CONFIG["seed"])

    def regressor(loss="squared_error", alpha=.9):
        return GradientBoostingRegressor(loss=loss, alpha=alpha, n_estimators=120, max_depth=2, learning_rate=.04, min_samples_leaf=15, random_state=CONFIG["seed"])

    candidate = regressor().fit(inputs(fit), fit["target_kwh_month"].to_numpy() / bases(fit))
    select_y = select["target_kwh_month"].to_numpy()
    model_mae = mean_absolute_error(select_y, bases(select) * candidate.predict(inputs(select)))
    baseline_mae = mean_absolute_error(select_y, bases(select))
    selected = "gradient_boosting" if model_mae < baseline_mae else "baseline"
    x, ratio = inputs(train_frame), train_frame["target_kwh_month"].to_numpy() / bases(train_frame)
    point = regressor().fit(x, ratio)
    lower = regressor("quantile", .1).fit(x, ratio)
    upper = regressor("quantile", .9).fit(x, ratio)
    bundle = {"point": point, "lower": lower, "upper": upper, "selected": selected, "expansion": 0.0, "version": CONFIG["version"], "training_bounds": {key: [float(train_frame[key].min()), float(train_frame[key].max())] for key in FEATURES}}
    forecaster = Forecaster(bundle)
    _, lo, hi = forecaster.predict_frame(calibration)
    ycal, bcal = calibration["target_kwh_month"].to_numpy(), bases(calibration)
    scores = np.maximum.reduce([(lo - ycal) / bcal, (ycal - hi) / bcal, np.zeros(len(calibration))])
    q = min(1, math.ceil((len(scores) + 1) * .8) / len(scores))
    bundle["expansion"] = float(np.quantile(scores, q, method="higher"))
    predictions, lo, hi = forecaster.predict_frame(test)
    y = test["target_kwh_month"].to_numpy()
    report = {"version": CONFIG["version"], "data_origin": "synthetic", "selected_model": selected, "split": {"train": len(train_frame), "calibration": len(calibration), "test": len(test)}, "selection": {"source": "60-site internal holdout inside the 300 training sites", "baseline_mae": float(baseline_mae), "model_mae": float(model_mae)}, "test": metrics(y, predictions, lo, hi), "baseline_test_mae": float(mean_absolute_error(y, bases(test))), "nominal_coverage_pct": 80, "interval_method": "10th/90th quantile regressors with nonnegative normalized split-conformal expansion; point included in bounds before calibration and evaluation.", "calibration_expansion": bundle["expansion"], "groups": {}, "stress_test": {"description": "Synthetic held-out outcomes increased by 25%; inputs unchanged. Illustrates sensitivity to generator shift.", **metrics(y * 1.25, predictions, lo, hi)}, "limitations": ["No real metered sites were used.", "Test sites come from the same synthetic generator; field accuracy is unknown.", "Growth and finance are conditional scenarios, not validated forecasts.", "Nominal coverage applies under distributional assumptions, not arbitrary new communities."]}
    for archetype in test["archetype"].unique():
        mask = (test["archetype"] == archetype).to_numpy()
        report["groups"][archetype] = metrics(y[mask], predictions[mask], lo[mask], hi[mask])
    (ROOT / "models").mkdir(exist_ok=True)
    (ROOT / "reports").mkdir(exist_ok=True)
    joblib.dump(bundle, ROOT / "models/forecast.joblib")
    (ROOT / "reports/evaluation.json").write_text(json.dumps(report, indent=2))
    output = test[["id", "archetype", "target_kwh_month"]].copy()
    output["prediction_kwh"] = predictions
    output["lower_kwh"] = lo
    output["upper_kwh"] = hi
    output.to_csv(ROOT / "reports/test_predictions.csv", index=False)
    return report


def load():
    # Only our own local artifact is loaded; there is no uploaded-model endpoint.
    return Forecaster(joblib.load(ROOT / "models/forecast.joblib"))
