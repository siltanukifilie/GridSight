"""Reproducible fictional sites, with latent uptake and consumption variation."""
import json
import numpy as np
import pandas as pd
from .domain import CONFIG, ROOT, SECTORS, DISTRICTS, baseline_components


def generate(seed=CONFIG["seed"], n_sites=CONFIG["sites"]):
    rng = np.random.default_rng(seed)
    sites, observations = [], []
    order = rng.permutation(n_sites)
    assignment = {int(idx): ("train" if j < int(n_sites * .6) else "calibration" if j < int(n_sites * .8) else "test") for j, idx in enumerate(order)}
    for index in range(n_sites):
        archetype = ["Residential", "Trading", "Agricultural"][index % 3]
        households = int(rng.integers(50, 801))
        shops = int(max(1, households * rng.uniform(.025, .12)))
        site = {"id": f"SYN-RW-{index + 1:04d}", "district": DISTRICTS[index % len(DISTRICTS)], "archetype": archetype, "households": households, "shops": shops, "schools": int(rng.integers(0, 4)), "clinics": int(rng.binomial(2, .35)), "mills": int(rng.integers(0, 4)) if archetype != "Residential" else 0, "pumps": int(rng.integers(0, 5)) if archetype == "Agricultural" else 0, "cold_rooms": int(rng.integers(0, 4)) if archetype == "Trading" else 0, "uptake": float(rng.uniform(.5, .98)), "appliance_index": float(rng.uniform(.6, 1.8)), "origin": "synthetic", "split": assignment[index]}
        parts = baseline_components(site)
        # Latent parameters remain generator internals, never prediction features.
        site_factor = rng.lognormal(-.5 * .13 ** 2, .13)
        sector_variation = rng.lognormal(-.5 * .1 ** 2, .1, len(SECTORS))
        adoption_factor = .65 + .35 * site["appliance_index"] + .18 * (shops / households) + .08 * site["uptake"]
        latent_growth = rng.uniform(.02, .18)
        year_one = []
        for month in range(1, CONFIG["months"] + 1):
            seasonal = 1 + (.12 if archetype == "Agricultural" else .05) * np.sin(2 * np.pi * (month - 1) / 12)
            # Year 1 is centered on one, later years reflect latent adoption growth.
            ramp = (1 + latent_growth) ** ((month - 6.5) / 12)
            noise = rng.lognormal(-.5 * .045 ** 2, .045)
            values = {k: float(parts[k] * site_factor * sector_variation[j] * adoption_factor * seasonal * ramp * noise) for j, k in enumerate(SECTORS)}
            total = sum(values.values())
            observations.append({"site_id": site["id"], "month": month, "split": site["split"], "origin": "synthetic", "demand_kwh": total, **{f"{k}_kwh": v for k, v in values.items()}})
            if month <= 12:
                year_one.append(total)
        site["target_kwh_month"] = float(np.mean(year_one))
        sites.append(site)
    return pd.DataFrame(sites), pd.DataFrame(observations)


def save_dataset():
    sites, monthly = generate()
    destination = ROOT / "data"
    destination.mkdir(exist_ok=True)
    sites.to_csv(destination / "synthetic_sites.csv", index=False)
    monthly.to_csv(destination / "synthetic_monthly.csv", index=False)
    metadata = {"version": CONFIG["version"], "seed": CONFIG["seed"], "origin": "synthetic", "sites": len(sites), "monthly_observations": len(monthly), "months_per_site": CONFIG["months"], "partitions": sites["split"].value_counts().to_dict(), "target": "First 12 months mean customer demand, kWh/month", "real_metered_sites": 0, "assumptions": CONFIG["note"]}
    (destination / "metadata.json").write_text(json.dumps(metadata, indent=2))
    return sites
