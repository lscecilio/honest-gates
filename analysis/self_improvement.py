"""Reproduce the self-improvement numbers in README.md from the aggregate CSV.

Pure standard library. Usage: python analysis/self_improvement.py [--json]
"""
import csv
import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "..", "data", "self_improvement_aggregate.csv")


def load(path=CSV_PATH):
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError("empty dataset: nothing measured")
    return rows


def fisher_one_sided_less(a, n1, c, n2):
    """P(X <= a) where X ~ Hypergeometric: a successes of n1 (arm 1), c of n2 (arm 2).

    Small p means arm 1's rate is lower than arm 2's.
    """
    k, n = a + c, n1 + n2
    total = math.comb(n, k)
    return sum(math.comb(n1, x) * math.comb(n2, k - x) for x in range(0, a + 1)) / total


def fisher_one_sided_greater(a, n1, c, n2):
    k, n = a + c, n1 + n2
    total = math.comb(n, k)
    return sum(math.comb(n1, x) * math.comb(n2, k - x) for x in range(a, min(n1, k) + 1)) / total


def n_per_arm(p1, p2, z_alpha=1.6449, z_beta=0.8416):
    """Normal-approximation sample size per arm, one-sided alpha=0.05, power=0.80."""
    pbar = (p1 + p2) / 2
    num = (z_alpha * math.sqrt(2 * pbar * (1 - pbar)) + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return math.ceil(num / (p2 - p1) ** 2)


def sign_test_one_sided(wins, losses):
    """P(W >= wins) under Binomial(wins+losses, 0.5); ties are dropped."""
    n = wins + losses
    return sum(math.comb(n, x) for x in range(wins, n + 1)) / 2 ** n if n else None


def summarize(rows):
    by_status = defaultdict(int)
    gen = defaultdict(lambda: {"candidates": 0, "promoted": 0})
    controls = defaultdict(lambda: {"runs": 0, "won": 0})
    for r in rows:
        n = int(r["n_candidates"])
        by_status[r["status"]] += n
        g = gen[r["generator"]]
        g["candidates"] += n
        if r["status"] == "promoted":
            g["promoted"] += n
        if r["control_arm"] != "none":
            c = controls[r["control_arm"]]
            c["runs"] += n
            c["won"] += n if r["won"] == "1" else 0
    never = sum(int(r["n_candidates"]) for r in rows if r["evidence"] == "never_measured")
    never_rejected = sum(int(r["n_candidates"]) for r in rows
                         if r["evidence"] == "never_measured" and r["status"] == "rejected")
    promoted_cases = sorted((int(r["eval_cases_min"]), int(r["eval_cases_max"]), r["generator"])
                            for r in rows if r["status"] == "promoted")
    p1g = gen["policy_mutator_gen1"]
    p2g = gen["policy_mutator_gen2"]
    base = p1g["promoted"] / p1g["candidates"]
    out = {
        "total_candidates": sum(by_status.values()),
        "by_status": dict(by_status),
        "generators": {k: dict(v, rate=round(v["promoted"] / v["candidates"], 4)) for k, v in gen.items()},
        "never_measured": never,
        "never_measured_rejected_by_expiry": never_rejected,
        "promoted_eval_cases_range": {
            "policy": [min(x[0] for x in promoted_cases if x[2].startswith("policy")),
                       max(x[1] for x in promoted_cases if x[2].startswith("policy"))],
            "instruction": [min(x[0] for x in promoted_cases if x[2].startswith("instruction")),
                            max(x[1] for x in promoted_cases if x[2].startswith("instruction"))],
        },
        "gen1_rate": round(base, 4),
        "gen2_vs_gen1": {
            "gen2": [p2g["promoted"], p2g["candidates"]],
            "gen1": [p1g["promoted"], p1g["candidates"]],
            "expected_wins_gen2_under_gen1_rate": round(base * p2g["candidates"], 2),
            "p_gen2_better_one_sided": round(fisher_one_sided_greater(p2g["promoted"], p2g["candidates"],
                                                                      p1g["promoted"], p1g["candidates"]), 3),
            "p_gen2_worse_one_sided": round(fisher_one_sided_less(p2g["promoted"], p2g["candidates"],
                                                                  p1g["promoted"], p1g["candidates"]), 3),
            "n_per_arm_to_detect_doubling": n_per_arm(base, 2 * base),
        },
        "instruction_gen2_vs_gen1": [gen["instruction_mutator_gen2"]["promoted"],
                                     gen["instruction_mutator_gen2"]["candidates"],
                                     gen["instruction_mutator_gen1"]["promoted"],
                                     gen["instruction_mutator_gen1"]["candidates"]],
        "controls": {k: dict(v) for k, v in controls.items()},
    }
    pv = out["gen2_vs_gen1"]
    if pv["gen2"][1] < pv["n_per_arm_to_detect_doubling"]:
        out["verdict_level5"] = "UNDERPOWERED"
    elif pv["p_gen2_better_one_sided"] <= 0.05:
        out["verdict_level5"] = "REACHED"
    else:
        out["verdict_level5"] = "NOT_YET"
    return out


if __name__ == "__main__":
    s = summarize(load())
    if "--json" in sys.argv:
        print(json.dumps(s, indent=2))
    else:
        for k, v in s.items():
            print("%s: %s" % (k, v))
