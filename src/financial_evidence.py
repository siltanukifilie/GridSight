"""Traceable planning evidence, never a bankability or causal savings certificate."""
from copy import deepcopy
from datetime import date
import hashlib
import json
import math

from .domain import ROOT

SCHEMA = "gridsight-financial-evidence-v1"
CATALOG = json.loads((ROOT / "data/financial_benchmarks.json").read_text())
KINDS = {"quotation", "invoice", "survey", "meter_log", "commitment", "tariff_approval"}


def signature(r):
    data = {k:r[k] for k in ("site", "context", "assumptions", "planning", "detailed", "connection")}
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def fields(r):
    """Explicit units; no automatic inference that a reference supports other values."""
    currency = r["context"]["currency"]
    out = {}
    for key in ("tariff", "variable_cost", "fixed_cost", "debt_payment", "collection_rate", "business_growth"):
        unit = currency+" / kWh" if key in ("tariff","variable_cost") else currency+" / month" if key in ("fixed_cost","debt_payment") else "fraction"
        out["assumptions."+key] = {"value":r["assumptions"][key],"unit":unit}
    for key in ("project_capex","capacity_capex","mill_support_cost","pump_support_cost","cold_room_support_cost","mill_monthly_cost","pump_monthly_cost","cold_room_monthly_cost"):
        out["planning."+key] = {"value":r["planning"][key],"unit":currency+(" / month" if key.endswith("monthly_cost") else "")}
    for key in ("shops","mills","pumps","cold_rooms","uptake"):
        out["site."+key] = {"value":r["site"][key],"unit":"fraction" if key=="uptake" else "count"}
    for key in ('household_basket_kwh', 'household_income_monthly', 'household_energy_budget_monthly',
                'household_fixed_fee_monthly', 'affordability_income_share'):
        if key in r['planning']:
            unit = 'kWh / household / month' if key=='household_basket_kwh' else 'fraction' if key=='affordability_income_share' else currency+' / household / month'
            out['planning.'+key] = {'value': r['planning'][key], 'unit': unit}
    for key in ("additional_mills","additional_pumps","additional_cold_rooms"):
        out["assumptions."+key] = {"value":r["assumptions"][key],"unit":"count"}
    if r["detailed"]["enabled"]:
        for equipment, values in r["detailed"]["equipment"].items():
            for key in ("power_kw","hours_per_day"):
                out[f"detailed.equipment.{equipment}.{key}"] = {"value":values[key],"unit":"kW / unit" if key=="power_kw" else "effective hours / calendar day"}
    return out


def template(r):
    return {"schema":SCHEMA,"project_signature":signature(r),"permission_confirmed":False,
            "no_personal_data":False,"records":[]}


def _text(value, label, limit=240):
    if not isinstance(value,str) or not 1<=len(value.strip())<=limit or any(ord(c)<32 for c in value):
        raise ValueError(f"{label} must be nonempty plain text (maximum {limit} characters).")
    return value.strip()


def _number(value, label, lo=0, hi=1e15):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not lo<=value<=hi:
        raise ValueError(f"{label} must be a finite number between {lo:g} and {hi:g}.")
    return float(value)


def _date(value):
    try:
        parsed=date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError("Evidence date must be YYYY-MM-DD.") from None
    if parsed.isoformat()!=value or parsed>date.today():
        raise ValueError("Evidence date cannot be in the future and must use YYYY-MM-DD.")
    return parsed


def review(r, raw=None):
    known=fields(r); accepted={}; packet=None; stale_project=False
    if raw is not None:
        keys={"schema","project_signature","permission_confirmed","no_personal_data","records"}
        if not isinstance(raw,dict) or set(raw)!=keys or raw["schema"]!=SCHEMA:
            raise ValueError("Use the financial evidence template with the supported fields.")
        if raw["permission_confirmed"] is not True or raw["no_personal_data"] is not True:
            raise ValueError("Confirm permission and removal of personal data before attaching evidence.")
        _text(raw["project_signature"],"Project signature",64)
        if not isinstance(raw["records"],list) or len(raw["records"])>50:
            raise ValueError("Attach at most 50 evidence records.")
        stale_project=raw["project_signature"]!=signature(r)
        if stale_project:
            cleared=review(r)
            cleared.update(stale_project=True, status="Inputs changed · evidence detached")
            return cleared
        for row in raw["records"]:
            if not isinstance(row,dict) or set(row)!={"field","value","unit","kind","source_reference","observed_on","sample_size"}:
                raise ValueError("Each evidence record needs field, value, unit, kind, source_reference, observed_on and sample_size.")
            path=row["field"]
            if not isinstance(path,str) or path not in known or path in accepted:
                raise ValueError("Evidence fields must be supported and unique.")
            if not isinstance(row["kind"],str) or row["kind"] not in KINDS:
                raise ValueError("Unsupported evidence kind.")
            value=_number(row["value"],"Evidence value",lo=-1)
            n=_number(row["sample_size"],"Sample size",1,1000000)
            if n!=int(n): raise ValueError("Sample size must be a whole number.")
            if row["unit"]!=known[path]["unit"]: raise ValueError("Evidence unit must match the input, including currency.")
            observed=_date(row["observed_on"])
            reference=_text(row["source_reference"],"Source reference")
            if not stale_project and (known[path]["value"] is None or value!=known[path]["value"]):
                raise ValueError("Evidence value differs from the applied input. Apply the input first and download a new template.")
            accepted[path]={**row,"source_reference":reference,"age_days":(date.today()-observed).days}
        packet=deepcopy(raw)
    rows=[]
    for path, item in known.items():
        record=accepted.get(path) if not stale_project else None
        status="missing" if item["value"] is None else "assumption"
        if record: status="review_due" if record["age_days"]>365 else "source_attached"
        rows.append({"field":path,**item,"status":status,"evidence":record})
    return {"schema":SCHEMA,"project_signature":signature(r),"packet":packet,"rows":rows,
            "source_attached":sum(x["status"]=="source_attached" for x in rows),"input_count":len(rows),
            "stale_project":stale_project,"independently_verified":False,"measured_capital_savings":None,
            "status":"Site inputs need evidence" if not accepted or stale_project else "Sources attached · review still required",
            "notice":"Attached sources are user-declared, not authenticated. Evidence never changes inputs. Review older-than-one-year sources; this is a workflow flag, not a universal expiry rule. No proven capital savings or lending approval.",
            "benchmarks":deepcopy(CATALOG)}


def benchmark_check(r, raw):
    required={"connections","local_currency_per_usd","fx_date","fx_reference","scope_confirmed"}
    if not isinstance(raw,dict) or set(raw)!=required or raw["scope_confirmed"] is not True:
        raise ValueError("Confirm cost and connection definitions and provide the benchmark comparison inputs.")
    count=_number(raw["connections"],"Metered connections",1,1000000)
    if count!=int(count): raise ValueError("Metered connections must be a whole number.")
    fx=_number(raw["local_currency_per_usd"],"Local currency per USD",1e-9,1e9)
    dated=_date(raw["fx_date"]); reference=_text(raw["fx_reference"],"Exchange-rate reference")
    expected=next(c for c in r["feasibility"]["scenarios"] if c["key"]=="expected")["years"][0]
    capex=r["planning"]["project_capex"]
    return {"project_signature":signature(r),"currency":r["context"]["currency"],"inputs":{**raw,"fx_reference":reference},
            "capex_usd_per_connection":None if capex is None else capex/fx/count,
            "opex_usd_per_connection_year":expected["operating_cost"]/fx/count,
            "benchmark_capex_usd_per_connection":1948,"benchmark_opex_usd_per_connection_year":26,
            "fx_review_due":(date.today()-dated).days>90,"costs_changed":False,
            "notice":"Comparison only: entered Year 1 costs divided by entered total metered connections. Regional historical averages are not site budgets. No inflation adjustment; check currency date, cost scope, connection timing and country comparability. Do not add the OPEX benchmark on top of existing operating costs."}


def productive_sensitivity(r):
    """Explicit use cases, NOT estimated business uptake probabilities."""
    from .domain import finance
    a=r["assumptions"]; base=finance(r["forecast"]["central"],a)["base"]
    margin=a["tariff"]*a["collection_rate"]-a["variable_cost"]
    rows=[]
    for option in r["feasibility"]["productive_options"]:
        for label, factor in (("No uptake",0),("Half assumed use",.5),("Assumed full use",1)):
            energy=option["extra_demand_kwh_month"]*factor
            served=finance(r["forecast"]["central"]+energy,a)["base"]["served_kwh"]-base["served_kwh"]
            cash=served*margin-option["extra_fixed_cost_amount_month"]
            rows.append({"option":option["label"],"case":label,"use_factor":factor,"extra_demand_kwh_month":energy,
                         "grid_contribution_amount_month":cash,"developer_support_cost_amount":option["developer_support_cost_amount"]})
    return {"rows":rows,"notice":"Usage stress cases, not uptake probabilities. Extra monthly support costs persist even with no uptake; sunk support capital is not recovered. No enterprise-profit, supply-upgrade or actual-savings claim."}
