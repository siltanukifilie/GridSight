"""Opt-in public context, bounded requests and timestamped, in-memory snapshots."""
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import threading
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from .context import country, validate_context

INDICATORS = {"SP.POP.TOTL": ("Population", "people"), "EG.ELC.ACCS.ZS": ("Electricity access", "% of population")}


class PublicDataUnavailable(Exception):
    pass


def fetch_json(url):
    # URLs are constructed from fixed HTTPS hosts, not supplied by clients.
    try:
        with urlopen(Request(url, headers={"User-Agent": "GridSight-local-prototype/1.2", "Accept": "application/json"}), timeout=12) as response:
            raw = response.read(500_001)
        if len(raw) > 500_000:
            raise ValueError("Oversized response")
        return json.loads(raw)
    except Exception as exc:
        raise PublicDataUnavailable("Public source unavailable. Retry later, or enter coordinates manually; your forecast is unchanged.") from exc


class PublicDataService:
    def __init__(self, fetcher=fetch_json):
        self.fetcher = fetcher
        self.cache = OrderedDict()
        self.snapshots = OrderedDict()
        self.lock = threading.Lock()

    def cached(self, key, loader):
        # One lock also prevents concurrent duplicate requests in this local prototype.
        with self.lock:
            cached = self.cache.get(key)
            if cached and time.monotonic() - cached[0] < 86400:
                return deepcopy(cached[1])
            result = loader()
            self.cache[key] = (time.monotonic(), result)
            self.cache.move_to_end(key)
            while len(self.cache) > 128:
                self.cache.popitem(last=False)
            return deepcopy(result)

    def locations(self, query, code):
        country(code)
        if not isinstance(query, str) or not 2 <= len(query.strip()) <= 100:
            raise ValueError("Enter 2–100 characters to search for a place.")
        query = query.strip()
        def load():
            url = "https://geocoding-api.open-meteo.com/v1/search?" + urlencode({"name": query, "countryCode": code, "count": 8, "language": "en", "format": "json"})
            body = self.fetcher(url)
            if not isinstance(body, dict) or body.get("error") or not isinstance(body.get("results", []), list):
                raise PublicDataUnavailable("The location source returned an invalid response.")
            places = []
            for row in body.get("results", []):
                if not isinstance(row, dict) or row.get("country_code") != code:
                    continue
                try:
                    location = {"label": ", ".join(str(row[k]) for k in ("name", "admin1") if row.get(k))[:120], "latitude": row["latitude"], "longitude": row["longitude"], "country_code": code, "source": "Open-Meteo / GeoNames"}
                    places.append(validate_context({"country_code": code, "location": location})["location"])
                except (KeyError, ValueError):
                    continue
            return {"locations": places, "fetched_at": datetime.now(timezone.utc).isoformat(), "source": "Open-Meteo / GeoNames", "source_url": url, "license": "CC BY 4.0; hosted free endpoint for non-commercial prototyping", "notice": "Place names and coordinates, not verified mini-grid projects. Results may be cached for 24 hours."}
        return self.cached(("places", code, query.casefold()), load)

    def public_context(self, code):
        profile = country(code)
        def load():
            url = f"https://api.worldbank.org/v2/country/{code}/indicator/" + ";".join(INDICATORS) + "?source=2&format=json&mrnev=1&per_page=100"
            body = self.fetcher(url)
            if not isinstance(body, list) or len(body) != 2 or not isinstance(body[1], list):
                raise PublicDataUnavailable("World Bank data unavailable. No national values have been substituted.")
            latest = {}
            for row in body[1]:
                if not isinstance(row, dict):
                    continue
                if not isinstance(row.get("indicator"), dict) or not isinstance(row.get("country"), dict):
                    continue
                key = row["indicator"].get("id")
                value = row.get("value")
                year = str(row.get("date", ""))
                if key not in INDICATORS or row.get("country", {}).get("id") != code or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 or not year.isdigit():
                    continue
                if key == "EG.ELC.ACCS.ZS" and value > 100:
                    continue
                if key in latest and latest[key]["year"] >= int(year):
                    continue
                label, unit = INDICATORS[key]
                latest[key] = {"indicator": key, "label": label, "value": value, "unit": unit, "year": int(year), "source_url": "https://data.worldbank.org/indicator/" + key, "attribution": "World Bank, World Development Indicators", "license": "CC BY 4.0"}
            if not latest:
                raise PublicDataUnavailable("No usable national observations returned. No values have been invented.")
            result = {"country_code": code, "country": profile["name"], "scope": "National context only; not local demand, model inputs or consumption validation", "fetched_at": datetime.now(timezone.utc).isoformat(), "source_url": url, "indicators": list(latest.values()), "missing_indicators": [k for k in INDICATORS if k not in latest], "transformation": "Latest non-null observation per indicator; values unchanged. Years may differ."}
            result["id"] = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()[:24]
            self.snapshots[result["id"]] = result
            while len(self.snapshots) > 128:
                self.snapshots.popitem(last=False)
            return result
        return self.cached(("national", code), load)

    def snapshot(self, identifier, code):
        with self.lock:
            result = self.snapshots.get(identifier)
            return deepcopy(result) if result and result["country_code"] == code else None
