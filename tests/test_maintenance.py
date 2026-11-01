"""INVENTED software fixtures only. These are NOT operator data or accuracy evidence.

Lifecycle tests deliberately exercise the operator *declaration* branch with
invented values. Passing proves plumbing, never source authenticity. All registry
writes and CLI inputs are confined to pytest tmp_path; no live registry is made.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from src import maintenance as m
from src.domain import ROOT
from src.statistical import confidence_study
from test_statistical import study_input


def request(version="fixture-v001", batch="A", declared_operator=False):
    body = study_input()
    replacements = {i: batch + i for group in ("fit_site_ids", "calibration_site_ids", "test_site_ids") for i in body["plan"][group]}
    for site in body["manifest"]["sites"]:
        site["site_id"] = replacements[site["site_id"]]
    for group in ("fit_site_ids", "calibration_site_ids", "test_site_ids"):
        body["plan"][group] = [replacements[i] for i in body["plan"][group]]
    lines = body["csv"].splitlines()
    for index in range(1, len(lines)):
        parts = lines[index].split(",")
        old_id = parts[0]
        parts[0] = replacements[old_id]
        # Hand-invented cohorts: wider calibration variability, comparable test demand.
        if old_id.startswith("CAL"):
            parts[2] = str(float(parts[2]) * (.5 if int(old_id[-1]) % 2 else 1.7))
        lines[index] = ",".join(parts)
    body["csv"] = "\n".join(lines) + "\n"
    body["release"] = {"version_id": version, "data_version": version + "-data",
                       "data_kind": "operator_metered" if declared_operator else "invented_test_fixture",
                       "prepared_by": "fixture-author", "change_note": "Invented software fixture ONLY, never field evidence"}
    # Deliberately permissive plumbing thresholds, NOT recommended acceptance criteria.
    body["policy"] = {"max_wape_pct": 10000, "max_abs_bias_pct": 10000, "min_site_coverage_pct": 80,
                      "max_mean_width_kwh": 1e10, "min_test_sites": 2, "min_test_sites_per_country": 1,
                      "max_wape_increase_vs_original_pp": 10000,
                      "max_abs_bias_increase_vs_original_pp": 10000,
                      "max_wape_increase_vs_previous_pp": 10000,
                      "max_country_share_shift_pp": 100, "max_input_mean_shift_pct": 10000}
    return body


def spec(body):
    return deepcopy({k: body[k] for k in ("release", "policy", "plan")})


@pytest.fixture(scope="module")
def computed():
    # Expensive scientific calculation runs once for storage/validation unit tests.
    p = request(declared_operator=True)
    return confidence_study({k: p[k] for k in ("manifest", "csv", "plan")})


@pytest.fixture
def fast_study(monkeypatch, computed):
    def fake(body):
        out = deepcopy(computed)
        ids = computed["plan"]["test_site_ids"]
        new = body["plan"]["test_site_ids"]
        mapping = dict(zip(ids, new))
        out["plan"] = deepcopy(body["plan"])
        out["by_site"] = {mapping[i]: v for i, v in out["by_site"].items()}
        for row in out["monthly_comparisons"]:
            row["site_id"] = mapping[row["site_id"]]
        return out
    monkeypatch.setattr(m, "confidence_study", fake)
    return computed


def staged(tmp_path, *, declared_operator=True):
    p = request(declared_operator=declared_operator)
    root = tmp_path / "private-registry"
    m.prepare(root, spec(p))
    return root, p, m.stage(root, p)


def approve(root, version):
    return m.review(root, version, reviewer="fixture-reviewer", decision="approve", reason="Invented workflow exercise only")


def promote(root, version):
    return m.promote(root, version, actor="fixture-release-role", reason="Invented local selection exercise")


def test_real_evaluation_reuses_algorithm_and_redacts_raw_observations(computed):
    p = request(declared_operator=True)
    before = deepcopy(p)
    result = m.evaluate_candidate(p)
    assert result["growth_model"] == computed["growth_model"]
    assert result["metrics"] == computed["test"]
    assert result["by_age"] == computed["by_stage"]
    assert result["by_country"] == computed["by_country"]
    assert result["performance_gates_passed"] is True
    assert result["review_eligible"] is False  # No actual local predeclaration.
    assert result["field_validation_complete"] is False
    assert result["serving_model_changed"] is False
    assert "NOT 20-input ML retraining" in result["method"]
    assert result["calibration"]["correction"] == computed["calibration"]["correction"]
    serialized = json.dumps(result)
    for sensitive in ("actual_kwh", "monthly_comparisons", "site_scores", "ATEST001", "input_evidence_reference"):
        assert sensitive not in serialized
    assert p == before


def test_actual_stage_integrates_complete_study_and_persists_no_raw_values(tmp_path):
    root, body, result = staged(tmp_path, declared_operator=False)
    assert result["performance_gates_passed"] is True
    assert result["review_eligible"] is False
    for path in root.rglob("*.json"):
        content = path.read_text()
        for sensitive in ("actual_kwh", "monthly_comparisons", "site_scores", "ATEST001", "input_evidence_reference"):
            assert sensitive not in content
    with pytest.raises(ValueError, match="invented fixtures"):
        approve(root, body["release"]["version_id"])


@pytest.mark.parametrize("missing", ["manifest", "csv", "plan", "release", "policy"])
def test_missing_body_fields_fail_closed(missing):
    p = request(); del p[missing]
    with pytest.raises(ValueError):
        m.evaluate_candidate(p)


@pytest.mark.parametrize("csv", [None, "", "  ", 42])
def test_no_data_no_synthetic_fallback(csv):
    p = request(); p["csv"] = csv
    with pytest.raises(ValueError, match="unavailable"):
        m.evaluate_candidate(p)


@pytest.mark.parametrize("value", [None, True, -1, float("nan"), float("inf"), "20"])
def test_invalid_thresholds(value):
    p = request(); p["policy"]["max_wape_pct"] = value
    with pytest.raises(ValueError):
        m.evaluate_candidate(p)


@pytest.mark.parametrize("change", [
    {"min_test_sites": 1}, {"min_test_sites": 2.5}, {"min_site_coverage_pct": 79},
    {"min_test_sites_per_country": 0}, {"unknown": 1}])
def test_invalid_gate_policy(change):
    p = request(); p["policy"].update(change)
    with pytest.raises(ValueError):
        m.evaluate_candidate(p)


@pytest.mark.parametrize("change", [
    {"data_kind": "synthetic"}, {"version_id": "../escape"}, {"prepared_by": ""},
    {"data_version": "../../data"}, {"change_note": ""}, {"unexpected": "x"}])
def test_invalid_release_metadata(change):
    p = request(); p["release"].update(change)
    with pytest.raises(ValueError):
        m.evaluate_candidate(p)


def test_invalid_plan_and_oversize_body():
    p = request(); p["plan"]["test_site_ids"] = None
    with pytest.raises(ValueError):
        m.evaluate_candidate(p)
    p = request(); p["csv"] = "x" * m.MAX_BODY_BYTES
    with pytest.raises(ValueError, match="256 KiB"):
        m.evaluate_candidate(p)


def test_readonly_status_never_creates_registry(tmp_path):
    root = tmp_path / "missing"
    result = m.status(root)
    assert result["available"] is False and result["active_version"] is None
    assert not root.exists()


@pytest.mark.parametrize("path", [".", "relative-registry", "/", "/tmp", str(Path.home()), str(ROOT),
                                 str(ROOT / "models" / "registry"), str(ROOT / "src" / "registry"),
                                 str(ROOT.parent / "sources" / "registry"), "/tmp/../tmp/registry"])
def test_unsafe_paths_refused(path):
    with pytest.raises(ValueError):
        m.prepare(path, spec(request()))


def test_symlink_and_nonempty_or_public_directory_refused(tmp_path):
    target = tmp_path / "target"; target.mkdir(mode=0o700)
    link = tmp_path / "link"; link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="symbolic"):
        m.prepare(link / "registry", spec(request()))
    (target / "keep.txt").write_text("user file")
    with pytest.raises(ValueError, match="nonempty"):
        m.prepare(target, spec(request()))
    assert (target / "keep.txt").read_text() == "user file"
    public = tmp_path / "public"; public.mkdir(mode=0o755)
    with pytest.raises(ValueError, match="owner-only"):
        m.prepare(public, spec(request()))


def test_prepare_freezes_no_data_and_duplicate_version_data_or_test_sites_refused(tmp_path):
    root = tmp_path / "registry"; p = request()
    receipt = m.prepare(root, spec(p))
    assert len(receipt["spec_sha256"]) == 64
    assert receipt["code"]["maintenance_sha256"]
    assert m.status(root)["candidates"] == []
    with pytest.raises(ValueError, match="already prepared"):
        m.prepare(root, spec(p))
    q = request("fixture-v002", batch="B"); q["release"]["data_version"] = p["release"]["data_version"]
    with pytest.raises(ValueError, match="Data version"):
        m.prepare(root, spec(q))
    q = request("fixture-v002", batch="A")
    with pytest.raises(ValueError, match="Reused test"):
        m.prepare(root, spec(q))
    q["plan"]["test_site_ids"] = [i.lower() for i in q["plan"]["test_site_ids"]]
    with pytest.raises(ValueError, match="Reused test"):
        m.prepare(root, spec(q))
    # A former fit site also cannot be called a new untouched test site.
    q = request("fixture-v002", batch="B")
    q["plan"]["test_site_ids"][0] = p["plan"]["fit_site_ids"][0]
    with pytest.raises(ValueError, match="Reused test"):
        m.prepare(root, spec(q))


@pytest.mark.parametrize("part", ["policy", "plan", "release", "code"])
def test_frozen_spec_or_code_changes_rejected_before_evaluation(tmp_path, monkeypatch, part):
    root = tmp_path / "registry"; p = request()
    m.prepare(root, spec(p))
    if part == "policy": p["policy"]["max_wape_pct"] -= 1
    elif part == "plan": p["plan"]["uncertainty"]["seed"] += 1
    elif part == "release": p["release"]["change_note"] += " changed"
    else:
        code = m._code(); code["maintenance_sha256"] = "0" * 64
        monkeypatch.setattr(m, "_code", lambda: code)
    with pytest.raises(ValueError, match="changed"):
        m.stage(root, p)
    assert len(m.status(root)["history"]) == 1


def test_invalid_measurements_audited_and_retry_cannot_retune_same_version(tmp_path):
    root = tmp_path / "registry"; p = request()
    m.prepare(root, spec(p))
    p["csv"] = "wrong,headers\n1,2\n"
    with pytest.raises(ValueError, match="Candidate evaluation failed"):
        m.stage(root, p)
    assert [e["kind"] for e in m.status(root)["history"]] == ["prepare", "evaluation_started", "evaluation_failed"]
    with pytest.raises(ValueError, match="already had"):
        m.stage(root, request())


def test_staging_is_immutable_no_automatic_promotion_and_review_is_explicit(tmp_path, fast_study):
    root, p, result = staged(tmp_path)
    assert result["review_eligible"] is True
    assert m.status(root)["active_version"] is None
    before = {f.name: f.read_bytes() for f in (root / "events").iterdir()}
    with pytest.raises(ValueError, match="already had"):
        m.stage(root, p)
    assert before == {f.name: f.read_bytes() for f in (root / "events").iterdir()}
    with pytest.raises(ValueError, match="explicitly approved"):
        promote(root, p["release"]["version_id"])
    with pytest.raises(ValueError, match="separate reviewer"):
        m.review(root, p["release"]["version_id"], reviewer="FIXTURE-AUTHOR", decision="approve", reason="Fixture only")
    approve(root, p["release"]["version_id"])
    assert m.status(root)["active_version"] is None
    promote(root, p["release"]["version_id"])
    assert m.status(root)["active_version"] == p["release"]["version_id"]
    assert not m.status(root)["serving_model_changed"]
    assert all((f.stat().st_mode & 0o777) == 0o400 for f in (root / "events").iterdir())


@pytest.mark.parametrize("threshold", ["max_wape_pct", "max_abs_bias_pct", "max_mean_width_kwh"])
def test_performance_failures_cannot_be_approved(tmp_path, fast_study, threshold):
    p = request(declared_operator=True); p["policy"][threshold] = 0
    root = tmp_path / "registry"; m.prepare(root, spec(p)); r = m.stage(root, p)
    assert not r["performance_gates_passed"]
    assert any(g["status"] == "fail" and threshold.removeprefix("max_") in g["name"] for g in r["gates"])
    with pytest.raises(ValueError, match="Cannot approve"):
        approve(root, p["release"]["version_id"])
    m.review(root, p["release"]["version_id"], reviewer="fixture-reviewer", decision="reject", reason="Failed invented fixture gates")
    with pytest.raises(ValueError, match="explicitly approved"):
        promote(root, p["release"]["version_id"])


@pytest.mark.parametrize("metric", ["wape_pct", "bias_pct"])
def test_undefined_accuracy_metric_fails_closed(monkeypatch, computed, metric):
    study = deepcopy(computed); study["test"]["growth_adjusted"][metric] = None
    monkeypatch.setattr(m, "confidence_study", lambda _: study)
    r = m.evaluate_candidate(request())
    assert not r["performance_gates_passed"]


def test_coverage_and_age_country_regression_failures(monkeypatch, computed):
    study = deepcopy(computed)
    study["test"]["site_path_coverage_pct"] = 50
    study["by_country"]["KE"]["growth_adjusted"]["wape_pct"] = 20000
    study["by_stage"]["Months 1–6"]["growth_adjusted"]["bias_pct"] = -20000
    monkeypatch.setattr(m, "confidence_study", lambda _: study)
    r = m.evaluate_candidate(request())
    failing = {g["name"] for g in r["gates"] if g["status"] == "fail"}
    assert "overall.site_path_coverage_pct" in failing
    assert "country.KE.wape_pct" in failing
    assert "age.Months 1–6.abs_bias_pct" in failing


def test_drift_previous_cohort_and_rollback_audited_without_serving_changes(tmp_path, fast_study):
    root, p, first = staged(tmp_path)
    approve(root, p["release"]["version_id"]); promote(root, p["release"]["version_id"])
    q = request("fixture-v002", batch="B", declared_operator=True)
    m.prepare(root, spec(q)); second = m.stage(root, q)
    assert second["drift"]["available"] is True
    assert second["drift"]["max_input_mean_shift_pct"] == 0
    assert second["baseline_version"] == p["release"]["version_id"]
    assert second["hashes"]["dataset_sha256"] != first["hashes"]["dataset_sha256"]
    approve(root, q["release"]["version_id"]); promote(root, q["release"]["version_id"])
    restored = m.rollback(root, p["release"]["version_id"], actor="fixture-release-role", reason="Invented rollback exercise")
    assert restored["previous_version"] == q["release"]["version_id"]
    assert m.status(root)["active_version"] == p["release"]["version_id"]
    assert m.status(root)["history"][-1]["kind"] == "rollback"
    assert not restored["serving_model_changed"]


def test_large_or_zero_baseline_drift_blocks_new_candidate(tmp_path, fast_study):
    root, p, _ = staged(tmp_path)
    approve(root, p["release"]["version_id"]); promote(root, p["release"]["version_id"])
    q = request("fixture-v002", batch="B", declared_operator=True)
    q["policy"]["max_input_mean_shift_pct"] = 1
    for site in q["manifest"]["sites"]:
        site["site"]["households"] *= 2
        site["detailed"]["new_connections_yearly"] = 5
    m.prepare(root, spec(q)); r = m.stage(root, q)
    assert r["drift"]["max_input_mean_shift_pct"] >= 100
    assert "new_connections_yearly" in r["drift"]["undefined_zero_baseline_features"]
    assert not r["review_eligible"]
    assert m.status(root)["active_version"] == p["release"]["version_id"]


def test_country_share_and_previous_error_drift_reporting(monkeypatch, computed):
    previous = m.evaluate_candidate(request())
    study = deepcopy(computed)
    study["test"]["growth_adjusted"]["wape_pct"] += 15
    monkeypatch.setattr(m, "confidence_study", lambda _: study)
    p = request(); p["policy"]["max_country_share_shift_pp"] = 5; p["policy"]["max_wape_increase_vs_previous_pp"] = 1
    for site in p["manifest"]["sites"]:
        site["country_code"] = "TZ"
    r = m.evaluate_candidate(p, prior_candidate=previous)
    assert r["drift"]["country_share_change_pp"] == {"KE": -100, "TZ": 100}
    failing = {g["name"] for g in r["gates"] if g["status"] == "fail"}
    assert "drift.max_country_share_shift_pp" in failing
    assert "previous_cohort.wape_change_pp" in failing


def test_history_overlap_never_fresh_even_in_pure_evaluation(fast_study):
    p = request(); r = m.evaluate_candidate(p, used_site_hashes=[m._token(p["plan"]["test_site_ids"][0])])
    assert not r["fresh_test_ids_in_this_registry"]
    assert r["reused_test_site_hashes"] and not r["review_eligible"]


def test_baseline_change_since_prepare_refused(tmp_path, fast_study):
    root, p, _ = staged(tmp_path)
    q = request("fixture-v002", batch="B", declared_operator=True)
    m.prepare(root, spec(q))
    approve(root, p["release"]["version_id"]); promote(root, p["release"]["version_id"])
    with pytest.raises(ValueError, match="baseline changed"):
        m.stage(root, q)


def test_code_changed_after_review_refuses_promotion(tmp_path, fast_study, monkeypatch):
    root, p, _ = staged(tmp_path); approve(root, p["release"]["version_id"])
    code = m._code(); code["maintenance_sha256"] = "0" * 64
    monkeypatch.setattr(m, "_code", lambda: code)
    with pytest.raises(ValueError, match="Code/runtime changed"):
        promote(root, p["release"]["version_id"])


def test_integrity_checks_detect_tamper_missing_event_and_symlink(tmp_path, fast_study):
    root, _, _ = staged(tmp_path)
    event = root / "events" / "000002.json"
    original = event.read_bytes(); event.chmod(0o600)
    changed = json.loads(original); changed["payload"]["request_sha256"] = "0" * 64
    event.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="integrity"):
        m.status(root)
    event.write_bytes(original); event.unlink()
    with pytest.raises(ValueError, match="integrity"):
        m.status(root)
    external = tmp_path / "external.json"; external.write_bytes(original)
    event.symlink_to(external)
    with pytest.raises(ValueError, match="safely read"):
        m.status(root)


def test_atomic_publish_never_overwrites_and_status_does_not_change_files(tmp_path, fast_study):
    root, _, _ = staged(tmp_path)
    event = root / "events" / "000001.json"; original = event.read_bytes()
    with pytest.raises(FileExistsError):
        m._atomic_new(event, {"overwrite": "not permitted"})
    assert event.read_bytes() == original
    before = {str(p): (p.stat().st_mtime_ns, p.read_bytes()) for p in root.rglob("*") if p.is_file()}
    m.status(root)
    assert before == {str(p): (p.stat().st_mtime_ns, p.read_bytes()) for p in root.rglob("*") if p.is_file()}
    assert not list((root / "events").glob(".pending-*"))


def test_lock_contention_fails_without_concurrent_write(tmp_path):
    import fcntl
    root = tmp_path / "registry"; m.prepare(root, spec(request()))
    with (root / ".lock").open("rb") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(ValueError, match="already running"):
            m.prepare(root, spec(request("fixture-v002", batch="B")))
    assert len(m.status(root)["history"]) == 1


def run_cli(*args):
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "update_real_data.py"), *args],
                          cwd=ROOT, capture_output=True, text=True, timeout=45)


def test_cli_prepare_status_missing_data_and_explicit_arguments(tmp_path):
    root = tmp_path / "registry"; p = request()
    source = tmp_path / "spec.json"; source.write_text(json.dumps(spec(p)))
    r = run_cli("prepare", "--registry", str(root), "--spec", str(source))
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["version_id"] == p["release"]["version_id"]
    r = run_cli("status", "--registry", str(root))
    assert r.returncode == 0 and json.loads(r.stdout)["active_version"] is None
    p["csv"] = ""
    source.write_text(json.dumps(p))
    r = run_cli("update", "--registry", str(root), "--request", str(source))
    assert r.returncode == 2 and "unavailable" in r.stderr
    assert len(m.status(root)["history"]) == 1
    assert run_cli("status").returncode == 2


def test_cli_duplicate_nonfinite_json_and_no_raw_logging(tmp_path):
    root = tmp_path / "registry"; source = tmp_path / "bad.json"
    source.write_text('{"release":1,"release":2}')
    r = run_cli("prepare", "--registry", str(root), "--spec", str(source))
    assert r.returncode == 2 and "Duplicate" in r.stderr and not root.exists()
    source.write_text('{"release":NaN}')
    r = run_cli("prepare", "--registry", str(root), "--spec", str(source))
    assert r.returncode == 2 and "finite" in r.stderr and not root.exists()
