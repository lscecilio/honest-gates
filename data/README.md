# Data dictionary

License: CC BY 4.0 (see `../LICENSE-DATA`). Exported 2026-10-27 09:29 UTC.

## `cases.json`

The false-green-bench cases. The schema is described inside the file. 24 cases
come from failure patterns we saw in our own operations (May to October 2026),
rewritten as minimal generic scenarios. 6 are synthetic controls whose correct
answer is PASS, or FAIL for a true red, so a checker cannot score well just by
never saying PASS. Numbers inside a case illustrate the pattern. They are not
readings from any live system.

## `self_improvement_aggregate.csv`

This is an aggregate of the decision log of an automated self-improvement loop that
has been running in production since 2026-06-30. Every candidate change the loop
generated is counted once. Rows are grouped by ISO week and by the categorical
fields below. The file holds no prompts, no candidate text, no identifiers and
no file names.

| column | meaning |
|---|---|
| generator | which generator produced the candidate. `policy_*` = generators that mutate rule/policy files, `instruction_*` = generators that mutate agent instruction files, `gen1`/`gen2` = generation (gen2 was written by the loop to improve gen1), `instruction_paired_generator_gen0` = a generator scored by paired evaluation from the start, `control` = placebo and decoy arms |
| target_kind | policy or instruction |
| risk_tier | tier1_safety, tier2_accuracy, tier3_goal. Tier 1 is never promoted automatically |
| status | promoted, rejected, pending, awaiting_owner (passed the automatic gate, waiting for a human decision) |
| evidence | `paired_eval` = parent and candidate run on the same cases; `fixed_benchmark` = scored on a fixed benchmark (an older method, retired); `never_measured` = no measurement ever happened |
| created_iso_week | ISO week the candidate was created |
| observation_window_started | 1 if the post-evaluation observation period was started |
| control_arm | none, placebo (parent against an unchanged copy of itself), decoy (a deliberately bad candidate) |
| won / tied / regressed | paired-evaluation outcome flags (`na` when not paired) |
| n_candidates | number of candidates in the group |
| eval_cases_min / max / sum | evaluated cases per candidate |
| delta_min / max / mean | candidate score minus parent score. Units depend on `evidence`: percentage points on `fixed_benchmark`, points on `paired_eval`. Do not compare across evidence types |

`python analysis/self_improvement.py` reproduces every number in the README
from this file.
