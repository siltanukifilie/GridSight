"""Explicit, local growth/interval recalibration releases; never a serving-model updater.

Registry artifacts contain aggregate diagnostics, coefficients and hashes, NOT
the confidence study's raw observations, manifest, or per-site scores. Local
attestations and a hash chain cannot authenticate an operator or prevent an
owner rewriting the entire registry. See docs/REAL_DATA_UPDATES.md.
"""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
from importlib.metadata import version as package_version
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import uuid

from .domain import ROOT
from .detailed_validation import _exact, _identifier, model_fingerprint
from .statistical import _plan, confidence_study

SCHEMA = "gridsight-real-data-maintenance-v1"
MAX_BODY_BYTES = 256 * 1024
MAX_EVENTS = 1000
POLICY_LIMITS = {
    "max_wape_pct": (0, 10000),
    "max_abs_bias_pct": (0, 10000),
    "min_site_coverage_pct": (0, 100),
    "max_mean_width_kwh": (0, 1e10),
    "min_test_sites": (2, 30),
    "min_test_sites_per_country": (1, 30),
    "max_wape_increase_vs_original_pp": (0, 10000),
    "max_abs_bias_increase_vs_original_pp": (0, 10000),
    "max_wape_increase_vs_previous_pp": (0, 10000),
    "max_country_share_shift_pp": (0, 100),
    "max_input_mean_shift_pct": (0, 10000),
}
INPUT_FEATURES = ("households", "uptake", "shops", "mills", "pumps", "schools", "clinics", "cold_rooms")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _json(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError, OverflowError):
        raise ValueError("Use finite JSON values only.") from None


def _hash(value):
    return hashlib.sha256(value).hexdigest()


def _token(value):
    return _hash(_identifier(value).encode())


def _id(value, label="Version ID"):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{2,59}", value):
        raise ValueError(f"{label}: use 3–60 letters, digits, underscores or hyphens.")
    return value


def _text(value, label):
    if not isinstance(value, str) or not 3 <= len(value.strip()) <= 300 or any(ord(c) < 32 for c in value):
        raise ValueError(f"{label}: use 3–300 printable characters, without personal information.")
    return value.strip()


def blank_release():
    """Template only: missing values are deliberately not usable releases."""
    return {"version_id": "", "data_version": "", "data_kind": "operator_metered",
            "prepared_by": "", "change_note": ""}


def blank_policy():
    """No invented universal financial/lender acceptance thresholds."""
    return dict.fromkeys(POLICY_LIMITS)


def _code():
    result = model_fingerprint()
    cli = ROOT / "scripts" / "update_real_data.py"
    result = {**result, "maintenance_schema": SCHEMA,
              "cli_sha256": _hash(cli.read_bytes()) if cli.is_file() else None,
              "runtime": {"python": sys.version.split()[0],
                          **{k: package_version(k) for k in ("numpy", "scipy", "pandas")}}}
    result["maintenance_sha256"] = _hash(_json(result))
    return result


def _spec(raw):
    _exact(raw, ("release", "policy", "plan"), "Release specification")
    _exact(raw["release"], blank_release(), "Release metadata")
    release = deepcopy(raw["release"])
    for key in ("version_id", "data_version", "prepared_by"):
        _id(release[key], key)
    release["change_note"] = _text(release["change_note"], "Change note")
    if release["data_kind"] not in ("operator_metered", "invented_test_fixture"):
        raise ValueError("Declare operator_metered or invented_test_fixture data; no synthetic fallback.")
    _exact(raw["policy"], POLICY_LIMITS, "Frozen gate policy")
    policy = deepcopy(raw["policy"])
    for key, (lo, hi) in POLICY_LIMITS.items():
        v = policy[key]
        if type(v) not in (int, float) or not math.isfinite(v) or not lo <= v <= hi:
            raise ValueError(f"{key}: supply a finite number from {lo} to {hi}; missing is not zero.")
        if key.startswith("min_test_sites") and type(v) is not int:
            raise ValueError(f"{key}: use a whole number.")
    plan = raw["plan"]
    if not isinstance(plan, dict):
        raise ValueError("Supply a frozen study plan.")
    groups = ("fit_site_ids", "calibration_site_ids", "test_site_ids")
    if any(not isinstance(plan.get(k), list) for k in groups):
        raise ValueError("List every site split in the study plan.")
    ids = [_identifier(i) for k in groups for i in plan[k]]
    if len(ids) > 30:
        raise ValueError("A maintenance study supports at most 30 sites.")
    plan, _ = _plan(plan, ids)
    if policy["min_site_coverage_pct"] < 100 * plan["uncertainty"]["coverage"]:
        raise ValueError("The coverage gate must be at least the declared coverage target.")
    return {"release": release, "policy": policy, "plan": plan}


def _spec_hash(spec):
    return _hash(_json(spec))


def _splits(plan):
    return {k: sorted(_token(i) for i in plan[k])
            for k in ("fit_site_ids", "calibration_site_ids", "test_site_ids")}


def _validate_body(body):
    _exact(body, ("manifest", "csv", "plan", "release", "policy"), "Maintenance request")
    if len(_json(body)) > MAX_BODY_BYTES:
        raise ValueError("Maintenance request exceeds 256 KiB.")
    if not isinstance(body["csv"], str) or not body["csv"].strip():
        raise ValueError("Genuine monthly data is unavailable: supply a nonempty CSV; no fallback.")
    return _spec({k: body[k] for k in ("release", "policy", "plan")})


def _profile(body, study):
    sites = [s for s in body["manifest"]["sites"]
             if _identifier(s["site_id"]) in study["plan"]["test_site_ids"]]
    n = len(sites)
    means = {k: sum(s["site"][k] for s in sites) / n for k in INPUT_FEATURES}
    means.update({"appliance_adoption_rate": sum(s["detailed"]["appliance_adoption_rate"] for s in sites) / n,
                  "new_connections_yearly": sum(s["detailed"]["new_connections_yearly"] for s in sites) / n,
                  "business_growth": sum(s["assumptions"]["business_growth"] for s in sites) / n})
    return {"n_sites": n, "horizon_months": study["plan"]["horizon_months"],
            "input_means": means,
            "country_share_pct": {c: 100 * sum(s["country_code"] == c for s in sites) / n
                                  for c in sorted({s["country_code"] for s in sites})}}


def _drift(current, previous):
    if previous is None:
        return {"available": False, "reason": "No previously promoted local candidate; not evidence of stability."}
    prior = previous["test_profile"]
    countries = set(prior["country_share_pct"]) | set(current["country_share_pct"])
    shares = {c: current["country_share_pct"].get(c, 0) - prior["country_share_pct"].get(c, 0)
              for c in sorted(countries)}
    shifts, undefined = {}, []
    for k, now in current["input_means"].items():
        old = prior["input_means"][k]
        shifts[k] = 100 * abs(now - old) / abs(old) if old else (0 if now == 0 else None)
        if shifts[k] is None:
            undefined.append(k)
    return {"available": True, "previous_version": previous["release"]["version_id"],
            "same_horizon": current["horizon_months"] == prior["horizon_months"],
            "country_share_change_pp": shares, "input_mean_change_pct": shifts,
            "undefined_zero_baseline_features": undefined,
            "max_country_share_shift_pp": max(map(abs, shares.values()), default=0),
            "max_input_mean_shift_pct": max((v for v in shifts.values() if v is not None), default=0),
            "interpretation": "Descriptive changes between different test cohorts, not a causal improvement or a statistical drift test."}


def _gates(study, policy, drift, previous):
    gates = []

    def check(name, value, limit, minimum=False):
        finite = type(value) in (int, float) and math.isfinite(value)
        passed = finite and (value >= limit if minimum else value <= limit)
        gates.append({"name": name, "status": "pass" if passed else "fail", "value": value,
                      "operator": ">=" if minimum else "<=", "threshold": limit})

    def errors(prefix, summary):
        adjusted, original = summary["growth_adjusted"], summary["original"]
        check(prefix + ".wape_pct", adjusted["wape_pct"], policy["max_wape_pct"])
        check(prefix + ".abs_bias_pct", abs(adjusted["bias_pct"]) if adjusted["bias_pct"] is not None else None,
              policy["max_abs_bias_pct"])
        check(prefix + ".mean_width_kwh", summary["mean_width_kwh"], policy["max_mean_width_kwh"])
        for metric, key in (("wape_pct", "max_wape_increase_vs_original_pp"),
                            ("bias_pct", "max_abs_bias_increase_vs_original_pp")):
            a, o = adjusted[metric], original[metric]
            change = (abs(a) - abs(o)) if a is not None and o is not None else None
            check(prefix + "." + key, change, policy[key])

    errors("overall", study["test"])
    check("overall.test_sites", study["test"]["n_sites"], policy["min_test_sites"], True)
    check("overall.site_path_coverage_pct", study["test"]["site_path_coverage_pct"], policy["min_site_coverage_pct"], True)
    for country, group in study["by_country"].items():
        errors("country." + country, group)
        ids = {r["site_id"] for r in study["monthly_comparisons"] if r["country_code"] == country}
        covered = sum(study["by_site"][i]["whole_path_covered"] for i in ids)
        check(f"country.{country}.test_sites", len(ids), policy["min_test_sites_per_country"], True)
        check(f"country.{country}.site_path_coverage_pct", 100 * covered / len(ids), policy["min_site_coverage_pct"], True)
    for age, group in study["by_stage"].items():
        if group["growth_adjusted"]["n_months"]:
            errors("age." + age, group)
    check("country_transfer_warnings", len(study["transfer_warnings"]), 0)
    if previous is not None:
        check("drift.same_horizon", int(drift["same_horizon"]), 1, True)
        check("drift.undefined_zero_baselines", len(drift["undefined_zero_baseline_features"]), 0)
        for key in ("max_country_share_shift_pp", "max_input_mean_shift_pct"):
            check("drift." + key, drift[key], policy[key])
        a, b = study["test"]["growth_adjusted"]["wape_pct"], previous["metrics"]["growth_adjusted"]["wape_pct"]
        check("previous_cohort.wape_change_pp", a - b if a is not None and b is not None else None,
              policy["max_wape_increase_vs_previous_pp"])
    return gates


def evaluate_candidate(body, *, preparation=None, prior_candidate=None, used_site_hashes=()):
    """Pure evaluation; no storage and no promotion. Only stage() trusts a registry.

    Body: manifest, csv, plan, release, policy. A result without a registry-frozen
    preparation is exploratory and cannot qualify for review. Do not expose
    caller-supplied preparation/prior_candidate as a trusted HTTP boundary.
    """
    spec = _validate_body(body)
    code = _code()
    frozen = preparation is not None
    if frozen and (preparation["spec_sha256"] != _spec_hash(spec) or
                   preparation["code"]["maintenance_sha256"] != code["maintenance_sha256"]):
        raise ValueError("Prepared plan, policy, release or code/runtime changed; do not tune a frozen test.")
    reused = sorted(set(_splits(spec["plan"])["test_site_ids"]) & set(used_site_hashes))
    study = confidence_study({"manifest": body["manifest"], "csv": body["csv"], "plan": spec["plan"]})
    profile = _profile(body, study)
    drift = _drift(profile, prior_candidate)
    gates = _gates(study, spec["policy"], drift, prior_candidate)
    passed = all(g["status"] == "pass" for g in gates)
    declared_real = spec["release"]["data_kind"] == "operator_metered"
    hashes = {"manifest_sha256": _hash(_json(body["manifest"])), "csv_sha256": _hash(body["csv"].encode()),
              "plan_sha256": _hash(_json(spec["plan"])), "policy_sha256": _hash(_json(spec["policy"])),
              "code_sha256": code["maintenance_sha256"]}
    hashes["dataset_sha256"] = _hash(_json({k: hashes[k] for k in ("manifest_sha256", "csv_sha256")}))
    eligible = frozen and not reused and declared_real and passed
    return {"schema": SCHEMA, "status": "candidate_needs_review" if eligible else "candidate_not_eligible",
            "release": spec["release"], "policy": spec["policy"], "evaluated_at": _now(),
            "predeclared_in_registry": frozen, "performance_gates_passed": passed, "review_eligible": eligible,
            "field_validation_complete": False, "independently_verified": False, "serving_model_changed": False,
            "method": "Aggregate growth recalibration and site-block uncertainty calibration; NOT 20-input ML retraining",
            "hashes": hashes, "code": code, "site_hashes": _splits(spec["plan"]),
            "reused_test_site_hashes": reused, "fresh_test_ids_in_this_registry": not reused,
            "baseline_version": prior_candidate["release"]["version_id"] if prior_candidate else None,
            "growth_model": study["growth_model"],
            "calibration": {k: v for k, v in study["calibration"].items() if k != "site_scores"},
            "uncertainty_settings": spec["plan"]["uncertainty"],
            "metrics": study["test"], "by_country": study["by_country"], "by_age": study["by_stage"],
            "country_split_counts": study["country_split_counts"], "test_profile": profile, "drift": drift,
            "gates": gates, "transfer_warnings": study["transfer_warnings"],
            "limitations": [
                "No genuine dataset is bundled. Operator provenance, permissions and predeclaration are attestations, not independently authenticated evidence.",
                "No raw meter rows, source manifest, per-site outputs or per-site calibration scores are retained. Aggregate small-cohort metrics and hashed IDs remain sensitive.",
                "Fresh means no matching textual site ID in THIS registry's earlier prepared splits. Aliases, other registries and prior external use cannot be detected.",
                "Predeclaration is local and cannot prove outcomes were unseen. Never tune thresholds after seeing results, even for failed or abandoned candidates.",
                "Coverage is measured on whole sites; small-sample exact intervals remain wide. Gate passage is not field verification, country-wide accuracy, or lender approval.",
                "Previous-cohort differences are descriptive, not paired model comparisons. Drift flags require human investigation, not automatic retraining or relaxed thresholds.",
                "Local promotion/rollback changes only registry approval state, never the active dashboard, financial analysis or frozen reference model.",
            ]}


def _safe_root(value):
    if not isinstance(value, (str, Path)) or not str(value):
        raise ValueError("Explicitly choose an absolute private registry directory.")
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts or path == Path(path.anchor):
        raise ValueError("Choose an absolute, non-root directory without traversal.")
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError("Registry paths must not contain symbolic links.")
    path = path.resolve()
    project = ROOT.resolve()
    if path in (Path.home().resolve(), Path("/tmp"), project) or path in project.parents:
        raise ValueError("Do not use a home, temporary, workspace or application root as the registry.")
    forbidden = {"sources", "models", "data", "src", "scripts", "tests", "docs", "config", "static", "templates", ".git", ".codex", ".agents"}
    relative_parts = path.relative_to(project).parts if path.is_relative_to(project) else ()
    if "sources" in path.parts or any(p in forbidden for p in relative_parts):
        raise ValueError("Keep the private registry outside source, model, data and synced-reference directories.")
    return path


def _private_dir(path):
    try:
        info = path.lstat()
    except OSError as exc:
        raise ValueError("Registry directory is missing or unreadable.") from exc
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("Registry directories must be owner-only directories (mode 0700).")


def _read_json(path, limit=1024 * 1024):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as f:
            info = os.fstat(f.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_size > limit:
                raise ValueError("Unsafe registry file ownership, permissions, type or size.")
            data = f.read(limit + 1)
        value = json.loads(data, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON")))
        _json(value)
        return value
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"Cannot safely read registry file {path.name}.") from exc


def _atomic_new(path, value):
    """Publish a complete immutable file using an exclusive hard link, never replace."""
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(_json(value) + b"\n")
            f.flush()
            os.fchmod(f.fileno(), 0o400)
            os.fsync(f.fileno())
        os.link(temporary, path, follow_symlinks=False)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        os.unlink(temporary)


@contextmanager
def _locked(root, *, create=False):
    if not root.exists():
        if not create or not root.parent.is_dir():
            raise ValueError("Registry is missing; prepare it in an existing parent directory first.")
        root.mkdir(mode=0o700)
    _private_dir(root)
    if not (root / "registry.json").exists() and any(root.iterdir()):
        raise ValueError("Refuse a nonempty directory without a GridSight registry marker.")
    fd = os.open(root / ".lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_nlink != 1:
            raise ValueError("Unsafe registry lock file.")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Registry update already running; retry after it finishes.") from None
        if not (root / "registry.json").exists():
            if not create:
                raise ValueError("Registry has not been prepared.")
            (root / "events").mkdir(mode=0o700)
            _atomic_new(root / "registry.json", {"schema": SCHEMA, "registry_id": str(uuid.uuid4()), "created_at": _now()})
        yield
    finally:
        os.close(fd)


def _load(root):
    _private_dir(root)
    _private_dir(root / "events")
    marker = _read_json(root / "registry.json", 8192)
    _exact(marker, ("schema", "registry_id", "created_at"), "Registry marker")
    if marker["schema"] != SCHEMA:
        raise ValueError("Unsupported registry schema.")
    paths = sorted(p for p in (root / "events").iterdir() if not p.name.startswith(".pending-"))
    if len(paths) > MAX_EVENTS:
        raise ValueError("Registry event limit reached; archive with an independent audit before continuing.")
    events, previous = [], None
    for i, path in enumerate(paths, 1):
        if path.name != f"{i:06}.json":
            raise ValueError("Registry integrity failure: missing or unexpected event.")
        event = _read_json(path)
        _exact(event, ("sequence", "previous_sha256", "registry_id", "at", "kind", "payload", "sha256"), "Audit event")
        unsigned = {k: v for k, v in event.items() if k != "sha256"}
        if event["sequence"] != i or event["previous_sha256"] != previous or event["registry_id"] != marker["registry_id"] or event["sha256"] != _hash(_json(unsigned)):
            raise ValueError("Registry integrity failure: event hash or chain mismatch.")
        if event["kind"] not in ("prepare", "evaluation_started", "evaluation_failed", "candidate", "review", "promote", "rollback"):
            raise ValueError("Registry integrity failure: unsupported event kind.")
        events.append(event)
        previous = event["sha256"]
    return marker, events


def _append(root, marker, events, kind, payload):
    if len(events) >= MAX_EVENTS:
        raise ValueError("Registry event limit reached.")
    event = {"sequence": len(events) + 1, "previous_sha256": events[-1]["sha256"] if events else None,
             "registry_id": marker["registry_id"], "at": _now(), "kind": kind, "payload": payload}
    event["sha256"] = _hash(_json(event))
    _atomic_new(root / "events" / f"{event['sequence']:06}.json", event)
    events.append(event)
    return event


def _active(events):
    return next((e["payload"]["version_id"] for e in reversed(events) if e["kind"] in ("promote", "rollback")), None)


def _find(events, kind, version_id):
    return next((e["payload"] for e in events if e["kind"] == kind and
                 (e["payload"].get("version_id") or e["payload"].get("release", {}).get("version_id")) == version_id), None)


def _used(events, exclude_version=None):
    return {v for e in events if e["kind"] == "prepare" and e["payload"]["version_id"] != exclude_version
            for values in e["payload"]["site_hashes"].values() for v in values}


def prepare(registry_dir, specification):
    """Freeze plan/policy/code BEFORE evaluating outcomes; explicit local write."""
    spec = _spec(specification)
    root = _safe_root(registry_dir)
    with _locked(root, create=True):
        marker, events = _load(root)
        release = spec["release"]
        if _find(events, "prepare", release["version_id"]):
            raise ValueError("Version ID is immutable and already prepared.")
        if any(e["kind"] == "prepare" and e["payload"]["release"]["data_version"] == release["data_version"] for e in events):
            raise ValueError("Data version is already registered; assign a new documented input snapshot version.")
        splits = _splits(spec["plan"])
        if set(splits["test_site_ids"]) & _used(events):
            raise ValueError("Reused test site IDs cannot be fresh independent evidence; use new untouched sites.")
        receipt = {"version_id": release["version_id"], "release": release, "spec_sha256": _spec_hash(spec),
                   "plan_sha256": _hash(_json(spec["plan"])), "policy": spec["policy"],
                   "policy_sha256": _hash(_json(spec["policy"])), "code": _code(), "site_hashes": splits,
                   "baseline_version": _active(events), "prepared_at": _now()}
        _append(root, marker, events, "prepare", receipt)
        return receipt


def stage(registry_dir, body):
    """One evaluation attempt per frozen version; retain a redacted candidate only."""
    spec = _validate_body(body)
    root = _safe_root(registry_dir)
    with _locked(root):
        marker, events = _load(root)
        version_id = spec["release"]["version_id"]
        receipt = _find(events, "prepare", version_id)
        if receipt is None:
            raise ValueError("Prepare this exact version, plan and policy before staging data.")
        if _find(events, "evaluation_started", version_id):
            raise ValueError("This frozen version already had an evaluation attempt; results cannot be overwritten or retuned.")
        if receipt["baseline_version"] != _active(events):
            raise ValueError("Registry baseline changed since preparation; do not silently change the comparison.")
        if receipt["spec_sha256"] != _spec_hash(spec) or receipt["code"]["maintenance_sha256"] != _code()["maintenance_sha256"]:
            raise ValueError("Prepared plan, policy, release or code/runtime changed.")
        _append(root, marker, events, "evaluation_started", {"version_id": version_id,
                "request_sha256": _hash(_json(body)), "data_version": spec["release"]["data_version"]})
        try:
            previous = _find(events, "candidate", _active(events)) if _active(events) else None
            result = evaluate_candidate(body, preparation=receipt, prior_candidate=previous,
                                        used_site_hashes=_used(events, version_id))
        except (ValueError, TypeError, KeyError) as exc:
            _append(root, marker, events, "evaluation_failed", {"version_id": version_id,
                    "reason": "Input or study validation failed; no candidate or raw observations saved."})
            raise ValueError(f"Candidate evaluation failed: {exc}") from exc
        _append(root, marker, events, "candidate", result)
        return result


def review(registry_dir, version_id, *, reviewer, decision, reason):
    """Record a single manual review; usernames are declarations, not authentication."""
    _id(version_id)
    _id(reviewer, "Reviewer")
    reason = _text(reason, "Review reason")
    if decision not in ("approve", "reject"):
        raise ValueError("Review decision must be approve or reject.")
    root = _safe_root(registry_dir)
    with _locked(root):
        marker, events = _load(root)
        candidate = _find(events, "candidate", version_id)
        if candidate is None or _find(events, "review", version_id):
            raise ValueError("Review requires an unreviewed staged candidate.")
        if reviewer.casefold() == candidate["release"]["prepared_by"].casefold():
            raise ValueError("Use a separate reviewer from the preparer (local declaration, not verified identity).")
        if decision == "approve" and not candidate["review_eligible"]:
            raise ValueError("Cannot approve: failed gates, missing predeclaration, reused sites or invented fixtures.")
        value = {"version_id": version_id, "reviewer": reviewer, "decision": decision, "reason": reason}
        _append(root, marker, events, "review", value)
        return value


def _activate(registry_dir, version_id, actor, reason, rollback_requested):
    _id(version_id)
    _id(actor, "Actor")
    reason = _text(reason, "Decision reason")
    root = _safe_root(registry_dir)
    with _locked(root):
        marker, events = _load(root)
        candidate, reviewed = _find(events, "candidate", version_id), _find(events, "review", version_id)
        if candidate is None or reviewed is None or reviewed["decision"] != "approve" or not candidate["review_eligible"]:
            raise ValueError("Only an explicitly approved eligible candidate can be locally selected.")
        previous = _active(events)
        if previous == version_id:
            raise ValueError("Version is already the locally selected candidate.")
        if rollback_requested:
            if _find(events, "promote", version_id) is None:
                raise ValueError("Rollback target must have been promoted previously.")
        else:
            if _find(events, "promote", version_id):
                raise ValueError("Use explicit rollback to return to a previously promoted version.")
            if candidate["baseline_version"] != previous:
                raise ValueError("Baseline changed since evaluation; this candidate cannot be promoted against another baseline.")
            if candidate["hashes"]["code_sha256"] != _code()["maintenance_sha256"]:
                raise ValueError("Code/runtime changed after evaluation; do not promote an untested change.")
        value = {"version_id": version_id, "previous_version": previous, "actor": actor, "reason": reason,
                 "serving_model_changed": False}
        _append(root, marker, events, "rollback" if rollback_requested else "promote", value)
        return value


def promote(registry_dir, version_id, *, actor, reason):
    """Select an approved local candidate; DOES NOT deploy it to the dashboard."""
    return _activate(registry_dir, version_id, actor, reason, False)


def rollback(registry_dir, version_id, *, actor, reason):
    """Audit a return to a previously promoted local candidate, not serving code."""
    return _activate(registry_dir, version_id, actor, reason, True)


def status(registry_dir):
    """Read-only, integrity-checked summary. Does not create directories or locks."""
    root = _safe_root(registry_dir)
    if not root.exists():
        return {"schema": SCHEMA, "available": False, "active_version": None, "history": [], "candidates": [],
                "field_validation_complete": False, "serving_model_changed": False}
    marker, events = _load(root)
    return {"schema": SCHEMA, "available": True, "integrity": "hash_chain_ok_not_authenticated",
            "registry_id": marker["registry_id"], "active_version": _active(events),
            "field_validation_complete": False, "serving_model_changed": False,
            "audit_head_sha256": events[-1]["sha256"] if events else None,
            "history": [{"sequence": e["sequence"], "kind": e["kind"], "at": e["at"], "sha256": e["sha256"],
                         "version_id": e["payload"].get("version_id") or e["payload"].get("release", {}).get("version_id")}
                        for e in events],
            "candidates": [e["payload"] for e in events if e["kind"] == "candidate"],
            "preparations": [e["payload"] for e in events if e["kind"] == "prepare"]}
