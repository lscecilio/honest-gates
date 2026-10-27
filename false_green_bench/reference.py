"""Minimal tri-state reference checker. Rule: missing data is never approval."""
import operator as _op

from . import FAIL, NOT_MEASURED, PASS

_OPS = {"<": _op.lt, "<=": _op.le, ">": _op.gt, ">=": _op.ge, "==": _op.eq}


def _unmeasured(m):
    return (m.get("value") is None or m.get("provenance") != "measured"
            or m.get("executed") is not True or m.get("measured_on") != m.get("about")
            or (m.get("n_required") is not None and (m.get("n") or 0) < m["n_required"]))


def check(case_input):
    evidence = case_input.get("evidence") or []
    if not evidence:
        return NOT_MEASURED
    measured = [m for m in evidence if not _unmeasured(m)]
    if any(not _OPS[m["op"]](m["value"], m["threshold"]) for m in measured):
        return FAIL
    return PASS if len(measured) == len(evidence) else NOT_MEASURED
