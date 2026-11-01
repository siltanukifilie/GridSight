"""Generate reproducible data and train the local forecasting model."""
import json
from src.synthetic import save_dataset
from src.model import train

if __name__ == "__main__":
    sites = save_dataset()
    report = train(sites)
    print(json.dumps({"sites": len(sites), "model": report["selected_model"], "test": report["test"]}, indent=2))
