# Promotion gate for self-improvement: method and pre-registration

License: CC BY 4.0. This file describes a method only. The gate's
implementation is not published.

## Contents
1. The problem the gate solves
2. Per-candidate promotion rule
3. Controls: placebo and decoy
4. Statistical tests
5. Verdicts
6. Pre-registration: does generation 2 beat generation 1?
7. What the published data shows today (2026-10-27)

## 1. The problem

The loop works like this. A *generator* (a prompt that writes candidate changes)
proposes edits to rules or agent instructions. Each candidate is compared with
its parent, and only winners are promoted. The recursive step is different: the
loop writes a *new generator* and checks whether that generator produces
winners more often than the old one.

There are two ways to fool yourself here. You can promote noise, and you can
declare a generator "worse" from a sample that cannot tell the two apart. The
gate is built to refuse both. It also refuses a third case: a verdict that
claims something was measured when it was not.

## 2. Per-candidate promotion rule (fail-closed)

A candidate is promoted only if **all** of these hold. Missing data on any
item means the candidate is NOT_MEASURED. It is never approved.

- Evidence is a **paired evaluation**: parent and candidate run on the same
  cases, with the same model held fixed for both in a given round. A
  comparison where the model changed between parent and child is refused.
- At least **100 evaluated cases**.
- Score delta of at least **+0.05** over the parent.
- In paired win/loss form, at least **5 discordant wins** and zero
  regressions. Under a one-sided sign test, 5 wins and 0 losses gives p = 1/32.
- At least **7 days** of post-evaluation observation, measured from a
  recorded start time. A summary that says "in trial" with no start time on
  record counts as NOT_MEASURED.
- Tier-1 (safety) targets are never promoted automatically. A change that
  only *adds* a prohibition can be approved automatically, but it still goes
  through review with a full test run. Loosening a rule is always a human
  decision.
- There is a kill switch that stops all automatic promotion.

## 3. Controls run every night

- **Placebo:** the parent is evaluated against an unchanged copy of itself.
  Its win rate is the evaluator's noise floor. A real candidate counts only if
  it wins more often than the placebo does.
- **Decoy:** a deliberately bad candidate. If the decoy is ever approved, the
  night stops.

Stopping rules:
- Decoy approved once: halt the run.
- Placebo winning as often as real candidates: suspend automatic promotion on
  that track.
- 8 weeks without improvement on a held-out set of real cases: switch that
  track off.

## 4. Statistical tests

- **Per candidate:** a one-sided sign test on discordant paired cases, with
  ties dropped.
- **Generator vs generator:** a one-sided Fisher exact test on promoted versus
  generated counts.
- **Power before verdict:** a sample size per arm is fixed in advance (normal
  approximation, alpha = 0.05 one-sided, power = 0.80). A comparison below that
  size can only be UNDERPOWERED.

## 5. Verdicts

| verdict | meaning |
|---|---|
| REACHED | pre-registered sample reached, and gen2 beats gen1 at one-sided p ≤ 0.05 |
| NOT_YET | pre-registered sample reached, and gen2 does not beat gen1 |
| UNDERPOWERED | sample below the pre-registered size. **No conclusion either way**, including "gen2 is worse" |

## 6. Pre-registration: does a second-generation generator beat the first?

Registered **2026-10-27**, before any new data collection. The numbers and the
rules are fixed here.

- **Baseline:** policy generator gen1 = 7 promoted of 619 generated (1.13%).
- **Effect to detect:** a doubling, from 1.13% to 2.26%.
- **n per arm:** **1,612 candidates**, all judged under the per-candidate rule
  in section 2. Candidates expired without measurement do not count toward n.
- **Test:** one-sided Fisher exact test, gen2 > gen1, alpha = 0.05.
- **Controls:** placebo and decoy every night. The comparison is void if
  the placebo win rate is not below the candidates' win rate over 4
  consecutive weeks.
- **Stopping:** stop when both arms reach n. A generator is not retired
  before its arm reaches n, except on a decoy approval.
- **Recursion resumes** only after 4 consecutive weeks of significant wins at
  least 5 percentage points above the placebo.

**Status on 2026-10-27:** the experiment is in progress, at its first step.
Since 2026-10-13 the loop has stopped writing new gen2 generators while the
measuring instrument is fixed. The first fix has been written and is under
review. It reports candidates without a trial clock as NOT_MEASURED instead of
"rejected on merit", and it sends pending instruction candidates to paired
evaluation. Data collection for this comparison has not started.

At the current throughput of 5 to 13 judged candidates per night, 1,612 per
arm would take about a year. That is why this repository asks for compute
(see README).

## 7. What the published data shows today

Run `python analysis/self_improvement.py` to reproduce these figures.

- 1,367 candidates since 2026-06-30: **11 promoted**, 1,262 rejected, 86
  pending, 8 awaiting the owner.
- Generators:
  - policy gen1: 7 of 619 (1.1%);
  - policy gen2: **0 of 125**;
  - instruction gen1: 0 of 357;
  - instruction gen2: **0 of 40**;
  - instruction paired gen0: 4 of 216.
- Gen2 vs gen1 (policy): under the gen1 rate, 1.41 winners were expected in
  125 tries. One-sided Fisher p for "gen2 worse" is 0.274, and for "gen2
  better" it is 1.0. Verdict: **UNDERPOWERED**. Both gen2 generators were
  retired before their arms had the power to show anything.
- The 7 promoted policy candidates had 218 to 1,534 evaluated cases. The 4
  promoted instruction candidates had only **5 to 6**, which is below the
  100-case floor in section 2. We report this as an inconsistency in our own
  gate.
- 397 candidates were never measured. 311 of them expired after 30 days and
  were recorded as "rejected", but they were never judged on merit.
- Controls (first 5 nights, 2026-W43 to W44): **the placebo won 4 of 5 nights,
  and the decoy won 0 of 5.** The decoy rule works. The placebo result means
  the paired evaluator on the instruction track cannot yet tell a real
  improvement from noise.
