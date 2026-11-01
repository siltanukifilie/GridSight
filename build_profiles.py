"""Use the installed RAMP library to build cached, normalized daily shapes.

RAMP is EUPL-1.2-or-later. This adapter contains original scenario definitions;
the upstream simulator is used as a dependency, not copied into this project.
Shapes describe timing only and are scaled to GridSight's monthly forecasts.
"""
import importlib.metadata
import json
import os
import random
import numpy as np
from src.domain import ROOT, CONFIG

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
from ramp import User, UseCase

# name, watts, number, daily minutes, allowed operating windows in minutes
APPLIANCES = {
    "households": [("LED lighting", 8, 3, 240, [[300, 420], [1080, 1440]]), ("Television", 40, 1, 180, [[1020, 1380]]), ("Phone charging", 5, 2, 120, [[360, 480], [1080, 1380]])],
    "shops": [("Shop services", 180, 1, 360, [[480, 1200]]), ("Shop lighting", 12, 3, 180, [[1020, 1320]])],
    "schools": [("School services", 600, 1, 300, [[420, 1020]])],
    "clinics": [("Clinic base services", 120, 1, 1200, [[0, 1440]]), ("Clinical equipment", 500, 1, 300, [[420, 1140]])],
    "mills": [("Grain milling", 5000, 1, 240, [[480, 1080]])],
    "pumps": [("Irrigation", 1500, 1, 240, [[360, 660], [900, 1080]])],
    "cold_rooms": [("Refrigeration compressor", 1200, 1, 720, [[0, 1440]])],
}


def generate_shapes():
    random.seed(CONFIG["seed"])
    np.random.seed(CONFIG["seed"])
    shapes = {}
    for sector, appliances in APPLIANCES.items():
        user = User(user_name=sector, num_users=12)
        for name, watts, count, minutes, windows in appliances:
            appliance = user.add_appliance(name=name, number=count, power=watts, num_windows=len(windows), func_time=minutes, func_cycle=15, time_fraction_random_variability=.12)
            appliance.windows(**{f"window_{i+1}": w for i, w in enumerate(windows)}, random_var_w=.08)
        use_case = UseCase(name=f"GridSight {sector} shape", users=[user], date_start="2026-01-05", date_end="2026-01-11")
        minute_watts = use_case.generate_daily_load_profiles(verbose=False)
        hourly = np.asarray(minute_watts).reshape(7, 24, 60).mean(axis=(0, 2))
        if not np.all(np.isfinite(hourly)) or hourly.sum() <= 0:
            raise ValueError(f"RAMP produced an invalid profile for {sector}")
        shapes[sector] = (hourly / hourly.sum()).tolist()
    return {"engine": f"RAMP {importlib.metadata.version('rampdemand')} · normalized 7-day appliance simulation", "seed": CONFIG["seed"], "origin": "synthetic", "license": "EUPL-1.2-or-later", "source": "https://rampdemand.org/", "purpose": "Hourly energy shares only. Monthly demand and training labels come from the separate GridSight generator.", "templates": APPLIANCES, "shapes": shapes}


if __name__ == "__main__":
    output = generate_shapes()
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data/load_shapes.json").write_text(json.dumps(output, indent=2))
    print(f"Generated {len(output['shapes'])} normalized sector shapes using {output['engine']}")
