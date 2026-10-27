"""Score a checker against the false-green-bench cases.

Usage:
    python -m false_green_bench                      # built-in checkers
    python -m false_green_bench --checker pkg.mod:fn # your checker
    python -m false_green_bench --json
    python -m false_green_bench --export-prompts out.jsonl  # for model-based checkers

A checker is any callable taking the case "input" dict and returning one of
"PASS", "FAIL", "NOT_MEASURED". Anything else (including exceptions) is
recorded as an invalid answer and counted as PASS for the false-green rate,
because a checker that crashes and is ignored approves by omission.
"""
import argparse
import importlib
import json
import os
import sys

from . import FAIL, NOT_MEASURED, PASS, VERDICTS, baselines, reference

DEFAULT_CASES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "data", "cases.json")

BUILTIN = {
    "surface_status": baselines.surface_status,
    "coerce_null": baselines.coerce_null,
    "always_not_measured": baselines.always_not_measured,
    "tristate_reference": reference.check,
}


def load_cases(path=DEFAULT_CASES):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    cases = data["cases"]
    if not cases:
        raise ValueError("no cases loaded: refusing to score an empty benchmark")
    for c in cases:
        if c.get("expected") not in VERDICTS:
            raise ValueError("case %s has invalid expected verdict" % c.get("id"))
    return cases


def _answer(checker, case_input):
    try:
        out = checker(json.loads(json.dumps(case_input)))  # checker gets a copy
    except Exception as exc:  # noqa: BLE001
        return "INVALID", repr(exc)
    return (out, None) if out in VERDICTS else ("INVALID", repr(out))


def score(checker, cases):
    rows = []
    for c in cases:
        got, err = _answer(checker, c["input"])
        rows.append({"id": c["id"], "expected": c["expected"], "got": got, "error": err})
    neg = [r for r in rows if r["expected"] != PASS]
    pos = [r for r in rows if r["expected"] == PASS]
    as_pass = lambda r: r["got"] in (PASS, "INVALID")  # noqa: E731
    return {
        "cases": len(rows),
        "non_pass_cases": len(neg),
        "pass_cases": len(pos),
        "exact": sum(r["got"] == r["expected"] for r in rows),
        "false_green": sum(as_pass(r) for r in neg),
        "false_green_rate": round(sum(as_pass(r) for r in neg) / len(neg), 3) if neg else None,
        "false_red": sum(not as_pass(r) for r in pos),
        "false_red_rate": round(sum(not as_pass(r) for r in pos) / len(pos), 3) if pos else None,
        "fail_called_not_measured": sum(r["expected"] == FAIL and r["got"] == NOT_MEASURED for r in rows),
        "invalid": sum(r["got"] == "INVALID" for r in rows),
        "rows": rows,
    }


def _load_checker(spec):
    if spec in BUILTIN:
        return BUILTIN[spec]
    mod, _, fn = spec.partition(":")
    return getattr(importlib.import_module(mod), fn or "check")


def export_prompts(cases, path):
    with open(path, "w", encoding="utf-8") as fh:
        for c in cases:
            prompt = ("You are a merge/deploy gate. Given the signal below, answer with exactly one "
                      "word: PASS, FAIL or NOT_MEASURED. Missing or unreliable evidence is "
                      "NOT_MEASURED, never PASS.\n\n" + json.dumps(c["input"], indent=2))
            fh.write(json.dumps({"id": c["id"], "prompt": prompt}) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="false_green_bench")
    ap.add_argument("--cases", default=DEFAULT_CASES)
    ap.add_argument("--checker", action="append", help="builtin name or module:function")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--export-prompts", metavar="PATH")
    args = ap.parse_args(argv)
    cases = load_cases(args.cases)
    if args.export_prompts:
        export_prompts(cases, args.export_prompts)
        print("wrote %d prompts to %s" % (len(cases), args.export_prompts))
        return 0
    names = args.checker or list(BUILTIN)
    results = {n: score(_load_checker(n), cases) for n in names}
    if args.json:
        print(json.dumps({n: {k: v for k, v in r.items() if k != "rows"} for n, r in results.items()},
                         indent=2))
        return 0
    first = next(iter(results.values()))
    print("cases: %d (%d expected FAIL/NOT_MEASURED, %d expected PASS)"
          % (first["cases"], first["non_pass_cases"], first["pass_cases"]))
    print("%-22s %7s %13s %11s %8s" % ("checker", "exact", "false_green", "false_red", "invalid"))
    for n, r in results.items():
        print("%-22s %3d/%-3d %5d (%5.1f%%) %3d (%5.1f%%) %8d" % (
            n, r["exact"], r["cases"], r["false_green"], 100 * r["false_green_rate"],
            r["false_red"], 100 * r["false_red_rate"], r["invalid"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
