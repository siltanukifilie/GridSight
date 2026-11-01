#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -x .venv/bin/python ]]; then
  echo "First set up the Python environment using the instructions in README.md."
  exit 1
fi
if [[ ! -f models/forecast.joblib || ! -f reports/evaluation.json || ! -f data/synthetic_sites.csv ]]; then
  .venv/bin/python build.py
fi
if [[ ! -f data/load_shapes.json ]]; then
  .venv/bin/python build_profiles.py
fi
exec .venv/bin/python app.py
