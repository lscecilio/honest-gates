import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analysis"))
import self_improvement as si  # noqa: E402


def test_numbers_match_readme():
    s = si.summarize(si.load())
    assert s["total_candidates"] == 1367
    assert s["by_status"] == {"rejected": 1262, "promoted": 11, "pending": 86, "awaiting_owner": 8}
    assert s["generators"]["policy_mutator_gen1"]["promoted"] == 7
    assert s["generators"]["policy_mutator_gen1"]["candidates"] == 619
    assert s["gen2_vs_gen1"]["gen2"] == [0, 125]
    assert s["instruction_gen2_vs_gen1"] == [0, 40, 0, 357]
    assert s["gen2_vs_gen1"]["p_gen2_worse_one_sided"] == 0.274
    assert s["gen2_vs_gen1"]["n_per_arm_to_detect_doubling"] == 1612
    assert s["never_measured_rejected_by_expiry"] == 311
    assert s["controls"] == {"placebo": {"runs": 5, "won": 4}, "decoy": {"runs": 5, "won": 0}}
    assert s["promoted_eval_cases_range"] == {"policy": [218, 1534], "instruction": [5, 6]}
    assert s["verdict_level5"] == "UNDERPOWERED"


def test_fisher_against_known_value():
    # 2x2 table [[1, 9], [11, 3]]: classic one-sided p = 0.0014 (lady tasting tea style check)
    assert round(si.fisher_one_sided_less(1, 10, 11, 14), 4) == 0.0014


def test_sign_test():
    assert si.sign_test_one_sided(5, 0) == 1 / 32
    assert si.sign_test_one_sided(0, 0) is None


def test_selftest_verdict_refuses_underpowered_win():
    """The level-5 verdict must not say REACHED on a tiny sample even if gen2 'wins'."""
    rows = si.load()
    fake = [dict(r) for r in rows]
    for r in fake:
        if r["generator"] == "policy_mutator_gen2" and r["status"] == "rejected":
            r["status"] = "promoted"
            break
    assert si.summarize(fake)["verdict_level5"] == "UNDERPOWERED"


def test_empty_dataset_is_not_measured(tmp_path):
    p = tmp_path / "e.csv"
    p.write_text("generator,status\n")
    import pytest
    with pytest.raises(ValueError):
        si.load(str(p))
