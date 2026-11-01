"""Build an offline EAC place index from attributed public GeoNames country dumps.

Run: .venv/bin/python scripts/import_locations.py
No user data is transmitted. ZIP paths are never extracted.
"""
import hashlib
import io
import json
import math
import sys
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.context import COUNTRIES


def parse_dump(text, code):
    rows = []
    for line in text.splitlines():
        cols = line.split("\t")
        if len(cols) != 19 or cols[8] != code:
            continue
        feature = cols[7]
        if feature not in ("ADM1", "ADM2", "ADM3", "ADM4", "PPL", "PPLL"):
            continue  # excludes capitals, administrative seats, abandoned/historical places
        try:
            lat, lon, population = float(cols[4]), float(cols[5]), int(cols[14])
            if not math.isfinite(lat + lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180:
                continue
        except ValueError:
            continue
        rows.append({"id": cols[0], "name": cols[1], "latitude": lat, "longitude": lon,
                     "feature": feature, "codes": cols[10:14], "population": population or None,
                     "timezone": cols[17], "modified": cols[18]})
    return sorted(rows, key=lambda r: (r["name"].casefold(), r["id"]))


def fetch_country(code):
    url = f"https://download.geonames.org/export/dump/{code}.zip"
    with urllib.request.urlopen(url, timeout=45) as response:
        data = response.read(15_000_001)
    if len(data) > 15_000_000:
        raise ValueError(f"Oversize download: {code}")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        info = archive.getinfo(f"{code}.txt")
        if info.file_size > 80_000_000:
            raise ValueError(f"Oversize country text: {code}")
        rows = parse_dump(archive.read(info).decode("utf-8"), code)
    if not rows:
        raise ValueError(f"No usable country records: {code}")
    return code, {"country_code": code, "source": "GeoNames", "source_url": url,
                  "license": "CC BY 4.0", "fetched_at": datetime.now(timezone.utc).isoformat(),
                  "source_sha256": hashlib.sha256(data).hexdigest(), "records": rows}


def main():
    results = list(ThreadPoolExecutor(max_workers=4).map(fetch_country, COUNTRIES))
    directory = ROOT / "data/locations"
    directory.mkdir(exist_ok=True)
    for code, result in results:
        target = directory / f"{code}.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        temporary.replace(target)
        print(f"{code}: {len(result['records']):,} public place/admin records")


if __name__ == "__main__":
    main()
