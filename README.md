# honest-gates

**A benchmark of false greens.** It collects cases where a CI check, a
dashboard or an AI agent's own report says "passed" although nothing was
measured. It also publishes an honest negative result from a self-improvement
loop that has been running in production.

All numbers are dated **2026-10-27** unless stated otherwise.

> Code: Apache-2.0 (`LICENSE`). Data and text: CC BY 4.0
> (`LICENSE-DATA`). Questions and collaboration: contact via
> [lsc-lab.com](https://lsc-lab.com).

## Why this exists

LSC-Lab is a one-person company in Brazil. Its founder, Leandro, is a
49-year-old business administrator from Brazil who does not write or read code. Everything
the company runs was built by AI agents that he directs in plain Portuguese,
the way he would direct managers. The agents report back in business terms
(cost, risk, return), and he approves or refuses.

That arrangement only works if the machine tells the truth. An owner who
cannot inspect code depends entirely on the signals he is shown. When a check
says "green", it has to mean that something was measured. If it was not, the
check should say **"not measured"**. The false green is the most expensive
failure we have: nobody reviews a green, so it gets passed along as if it were
a fact.

This repository publishes the failure patterns we found in our own operations,
in a form anyone can use to test a checker, whether that checker is a script, a
CI gate or an LLM acting as a reviewer.

## What is here

| part | what it is | license |
|---|---|---|
| `data/cases.json` | 30 cases. 24 are minimal generic rewrites of false greens (and one false red) seen in real operations from May to October 2026. 6 are controls | CC BY 4.0 |
| `false_green_bench/` | runner that scores any checker; 3 baseline checkers; a minimal tri-state reference checker (PASS / FAIL / NOT_MEASURED) | Apache-2.0 |
| `data/self_improvement_aggregate.csv` | aggregate, numbers-only decision log of a self-improvement loop (1,367 candidates, 2026-06-30 to 2026-10-27) | CC BY 4.0 |
| `analysis/self_improvement.py` | reproduces every self-improvement number below | Apache-2.0 |
| `docs/METHOD.md` | the promotion-gate method (pre-registration, placebo, decoy, one-sided tests) and the pre-registration of our next experiment | CC BY 4.0 |

The implementation of our own gates, agents and infrastructure is **not**
published. This repository contains only the benchmark, the scorer and the
method.

## The rule

**Absence of data is a failure, never an approval.** For every measurement a
checker should be able to answer:

1. **Was a value obtained?** null, a timeout or a default is not a value.
2. **Was it measured, or was it cached, self-reported or projected?**
3. **Did the measuring step actually run?** A step that was skipped does not
   count.
4. **Is the thing measured the thing the claim is about?** Watch for a
   different commit, a copy, or a state that has changed since.
5. **Is the sample at least the size fixed in advance?**

If any answer is no, the verdict is `NOT_MEASURED`. If a real measurement
breaks its rule, the verdict is `FAIL`. Only when every measurement passes all
five questions is the verdict `PASS`.

There is also a rule for the checks themselves: **every check is born with a
case it must fail.** A check that has never been seen to fail may have been
broken for months. The tests in `tests/` include these self-tests.

## Results (reproduce: `python -m false_green_bench`)

30 cases: 24 whose correct verdict is FAIL or NOT_MEASURED, and 6 whose
correct verdict is PASS. A *false green* is a PASS (or a crash, which also
counts as a PASS) on a case that should not pass. A *false red* is a non-PASS
on a case that should pass.

| checker | exact | false greens | false reds |
|---|---|---|---|
| `surface_status`: trusts the status shown on the dashboard | 6/30 | **23/24 (95.8%)** | 1/6 |
| `coerce_null`: evaluates the rules, but null becomes 0 and empty means nothing failed | 14/30 | **11/24 (45.8%)** | 0/6 |
| `always_not_measured`: never says PASS | 16/30 | 0/24 | **6/6 (100%)** |
| `tristate_reference`: the ~20-line checker in `false_green_bench/reference.py` | 30/30 | 0/24 | 0/6 |

**Read this table honestly.** The reference checker scores 30/30 **by
construction**. We wrote the case schema (`value`, `provenance`, `executed`,
`measured_on`/`about`, `n`/`n_required`) together with the checker, so it shows
that the rule is consistent. It does not show that the rule is hard to follow.
The open question, which this benchmark is built to answer, is this: **does a
model-based checker reach the right verdict when it reads the case the way a
reviewer would, from the claim and the surface text plus the raw evidence?**
`python -m false_green_bench --export-prompts prompts.jsonl` writes one prompt
per case for that test. **We have not yet run any model on it**, because this
release was made at zero cost.

## Self-improvement: a measured negative result (reproduce: `python analysis/self_improvement.py`)

Since 2026-06-30 an automated loop has proposed changes to rules and agent
instructions. Candidates are compared with their parents, and only winners are
promoted. The recursive step is a *second-generation* generator, written by the
loop, that produces winners more often than the first. It **has not been
reached**.

- 1,367 candidates in total: **11 promoted**, 1,262 rejected, 86 pending, 8
  waiting for the owner.
- First-generation policy generator: 7 winners out of 619 candidates (**1.1%**).
- Second-generation generators: **0 out of 125** (policy) and **0 out of 40**
  (instructions).
- **0 out of 125 does not show that generation 2 is worse.** At generation 1's
  rate, 1.41 winners were expected. The one-sided Fisher p-value is 0.274 for
  "worse" and 1.0 for "better". To detect even a doubling of the rate takes
  about **1,612 candidates per arm**. Both second-generation generators were
  retired before their samples had that power. Verdict: **UNDERPOWERED**.
- The 7 promoted policy changes were tested on 218 to 1,534 cases each. The 4
  promoted instruction changes were tested on only **5 to 6**, which is below
  our own written floor of 100. That is an inconsistency in our own gate, and
  we are publishing it.
- 311 candidates were recorded as "rejected" after expiring without ever being
  measured.
- Controls in the first 5 nights: the **placebo won 4 of 5** (the parent
  against an unchanged copy of itself), and the **decoy won 0 of 5**. The
  decoy rule works. The placebo result means the instruction-track evaluator
  cannot yet tell a real improvement from noise.

The method and the pre-registration of the next experiment are in
`docs/METHOD.md`. It was registered on 2026-10-27 and is in progress, at its
first step, which is fixing the measuring instrument. Data collection has not
started.

## What this does NOT measure

- **No model has been evaluated yet.** None of the numbers above comes from an
  LLM.
- The cases come from **one company's operations** and were rewritten by us.
  Their mix of patterns reflects what we ran into, not how often these patterns
  occur in the wild.
- 30 cases is small. The case numbers are illustrations. They are not readings
  from live systems.
- The self-improvement dataset is an aggregate. It cannot be used to audit an
  individual candidate, and it contains no prompts or candidate text.
- `delta` units differ by evidence type (see `data/README.md`). Do not average
  them across types.

## Reproduce

```bash
python -m pytest              # 19 tests, standard library + pytest
python -m false_green_bench   # the results table above
python -m false_green_bench --checker yourmodule:your_check
python analysis/self_improvement.py
```

Python 3.8 or later. No dependencies beyond `pytest`, which is needed only for
the tests.

## Who we are

LSC-Lab ([lsc-lab.com](https://lsc-lab.com)) is a one-person company in Brazil,
operated by AI agents and run by a founder who does not code. Contact is
through the website.

## License

- Code: [Apache License 2.0](LICENSE).
- Data and documentation: [CC BY 4.0](LICENSE-DATA).
- Required notice: see [NOTICE](NOTICE).

Questions, collaboration or commercial support: lsc-lab.com.
