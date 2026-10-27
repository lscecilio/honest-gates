import copy
import json
import os
import tempfile

import pytest

from false_green_bench import FAIL, NOT_MEASURED, PASS, baselines, reference
from false_green_bench.runner import load_cases, score

CASES = load_cases()


def test_case_ids_unique_and_balanced():
    ids = [c["id"] for c in CASES]
    assert len(ids) == len(set(ids)) == 30
    assert sum(c["expected"] != PASS for c in CASES) == 24


def test_reference_checker_scores_all_cases():
    r = score(reference.check, CASES)
    assert (r["exact"], r["false_green"], r["false_red"]) == (30, 0, 0)


def test_baseline_numbers_match_readme():
    s = score(baselines.surface_status, CASES)
    c = score(baselines.coerce_null, CASES)
    a = score(baselines.always_not_measured, CASES)
    assert (s["exact"], s["false_green"], s["false_red"]) == (6, 23, 1)
    assert (c["exact"], c["false_green"], c["false_red"]) == (14, 11, 0)
    assert (a["exact"], a["false_green"], a["false_red"]) == (16, 0, 6)


@pytest.mark.parametrize("field,bad", [
    ("value", None), ("provenance", "cached"), ("executed", False),
    ("measured_on", "something_else"), ("n_required", 10_000),
])
def test_selftest_reference_must_refuse_each_defect(field, bad):
    """Every check is born with a case it has to refuse: break one field of a PASS control."""
    ctrl = copy.deepcopy(next(c for c in CASES if c["id"] == "CTRL-02")["input"])
    assert reference.check(ctrl) == PASS
    ctrl["evidence"][0][field] = bad
    assert reference.check(ctrl) == NOT_MEASURED


def test_selftest_empty_evidence_is_not_approval():
    assert reference.check({"evidence": []}) == NOT_MEASURED
    assert reference.check({}) == NOT_MEASURED


def test_measured_failure_beats_unmeasured():
    inp = {"evidence": [
        {"value": 0, "op": ">=", "threshold": 1, "provenance": "measured",
         "measured_on": "x", "about": "x", "executed": True},
        {"value": None, "op": ">=", "threshold": 1, "provenance": "measured",
         "measured_on": "x", "about": "x", "executed": True},
    ]}
    assert reference.check(inp) == FAIL


def test_crashing_checker_counts_as_false_green():
    def boom(_):
        raise RuntimeError("x")
    r = score(boom, CASES)
    assert r["invalid"] == 30 and r["false_green"] == 24


def test_checker_cannot_mutate_cases():
    def vandal(inp):
        inp["evidence"] = []
        return PASS
    before = json.dumps(CASES, sort_keys=True)
    score(vandal, CASES)
    assert json.dumps(CASES, sort_keys=True) == before


def test_runner_refuses_empty_benchmark():
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump({"cases": []}, fh)
    try:
        with pytest.raises(ValueError):
            load_cases(fh.name)
    finally:
        os.unlink(fh.name)


def test_readme_states_the_measured_numbers():
    readme = open(os.path.join(os.path.dirname(__file__), "..", "README.md"), encoding="utf-8").read()
    for s in ("23/24 (95.8%)", "11/24 (45.8%)", "6/6 (100%)", "| 30/30 | 0/24 | 0/6 |",
              "0 out of 125", "1,612 candidates per arm", "0.274", "placebo won 4 of 5"):
        assert s in readme, s
