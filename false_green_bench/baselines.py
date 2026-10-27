"""Baseline checkers that reproduce common ways a green is accepted."""
import operator as _op

from . import FAIL, NOT_MEASURED, PASS

_OK = {"success", "ok", "green", "passed", "approved", "200", "won", "promoted", "completed"}
_OPS = {"<": _op.lt, "<=": _op.le, ">": _op.gt, ">=": _op.ge, "==": _op.eq}


def surface_status(case_input):
    """Trust the status field a dashboard shows (no failure shown = pass)."""
    status = str((case_input.get("surface") or {}).get("status", "")).lower()
    return PASS if status in _OK else FAIL


def coerce_null(case_input):
    """Evaluate the rules, but treat null as 0 and ignore provenance and subject.

    This is what `Number(null) === 0` or an error path returning a default does.
    An empty evidence list is read as "nothing failed".
    """
    for m in case_input.get("evidence") or []:
        value = m.get("value")
        value = 0 if value is None else value
        if not _OPS[m["op"]](value, m["threshold"]):
            return FAIL
    return PASS


def always_not_measured(case_input):
    """Degenerate checker: never says PASS. Zero false greens, useless otherwise."""
    return NOT_MEASURED
