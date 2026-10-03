# Worked run: PM/APM OPT-clock (shinde-pras)

## Executive summary
I ran the prototype on a fictional persona and checked the result in four ways: a hand calculation made before the run, a comparison of two rows with the source data file, 50 offline tests, and a rerun in a fresh clone of the pushed branch. I also tried four ways to break it. One attempt exposed a real gap (a posting on hold did not show its link), which I fixed and reran without changing any score. A separate private run on my own company list is reported only as counts. Nothing here says that any company will sponsor a visa.

## Inputs
- Persona (fictional, invented dates): an international master's student on F-1; as-of date 2027-07-01; OPT start 2027-06-01; 90 allowed unemployment days; hiring lag 10 weeks (an assumption, labeled your-input).
- Candidates: scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/fixtures/persona_candidates.json, 10 roles. The fit values were fixed in the committed file (commit 1537085) before the first run; the liveness results are invented placeholders labeled your-input.
- Data: data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv, the real file shipped with the repository, read only.
- Expected results, with a hand calculation, were committed (db62589) before the first run.

## Commands and real output
The toolchain baseline is in TEST-REPORT.md.

Unit tests:
```
$ PYTHONDONTWRITEBYTECODE=1 python3 scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/test_pm_opt_clock.py -v 2>&1
test_denials_and_rate_are_numbers_when_they_parse (__main__.CliTest) ... ok
test_error_leaves_no_partial_outputs (__main__.CliTest) ... ok
test_hold_with_url_shows_url_and_liveness_command (__main__.CliTest) ... ok
test_hold_without_url_says_none_and_warns (__main__.CliTest) ... ok
test_integration_real_scorer_keeps_sponsorship_weight (__main__.CliTest) ... ok
test_nonnumeric_approvals_is_undefined_case (__main__.CliTest) ... ok
test_nothing_scorable_skips_scorer (__main__.CliTest) ... ok
test_refuses_to_overwrite_tracked_file (__main__.CliTest) ... ok
test_mapping (__main__.LivenessTest) ... ok
test_differing_duplicate_rows_are_ambiguous (__main__.NormalizationTest) ... ok
test_identical_duplicate_rows_collapse (__main__.NormalizationTest) ... ok
test_no_alias_matching (__main__.NormalizationTest) ... ok
test_salesforce_spellings_collapse (__main__.NormalizationTest) ... ok
test_profile_phrase_never_matches_scorer_regex (__main__.ProfileTest) ... ok
test_regex_copies_match_scorer_source (__main__.ProfileTest) ... ok
test_apm_whole_word_is_entry_level (__main__.SponsorshipTableTest) ... ok
test_entry_level_title_wins_over_senior (__main__.SponsorshipTableTest) ... ok
test_row1_not_in_csv (__main__.SponsorshipTableTest) ... ok
test_row2_ambiguous_rows (__main__.SponsorshipTableTest) ... ok
test_row3_no_h1b_data (__main__.SponsorshipTableTest) ... ok
test_row4_entry_level_title (__main__.SponsorshipTableTest) ... ok
test_row5_pm_title_no_level (__main__.SponsorshipTableTest) ... ok
test_row6_senior_only (__main__.SponsorshipTableTest) ... ok
test_row7_under_50_with_pm_title (__main__.SponsorshipTableTest) ... ok
test_row8_some_approvals_no_pm_title (__main__.SponsorshipTableTest) ... ok
test_title_with_senior_and_entry_markers_counts_as_senior (__main__.SponsorshipTableTest) ... ok
test_truncated_title_list_uses_regex_fallback (__main__.SponsorshipTableTest) ... ok
test_unparseable_titles_is_undefined_case (__main__.SponsorshipTableTest) ... ok
test_zero_approvals_is_undefined_case (__main__.SponsorshipTableTest) ... ok
test_exactly_enough_days_gives_one (__main__.TimelineTest) ... ok
test_more_than_enough_is_capped_at_one (__main__.TimelineTest) ... ok
test_non_positive_numbers_error (__main__.TimelineTest) ... ok
test_one_day_gives_one_seventieth (__main__.TimelineTest) ... ok
test_past_deadline_errors (__main__.TimelineTest) ... ok
test_unparseable_dates_error (__main__.TimelineTest) ... ok
test_zero_days_available_errors (__main__.TimelineTest) ... ok
test_known_limitation_arabic_numerals_and_jr_not_markers (__main__.TitleRulesTest) ... ok
test_known_limitation_marker_anywhere_in_title (__main__.TitleRulesTest) ... ok
test_levels (__main__.TitleRulesTest) ... ok
test_pm_family (__main__.TitleRulesTest) ... ok
test_bad_source_label (__main__.ValidationTest) ... ok
test_candidates_file_rejections (__main__.ValidationTest) ... ok
test_good_role_passes (__main__.ValidationTest) ... ok
test_missing_fit (__main__.ValidationTest) ... ok
test_missing_gate_factor (__main__.ValidationTest) ... ok
test_override_present (__main__.ValidationTest) ... ok
test_p_above_one (__main__.ValidationTest) ... ok
test_p_not_a_number (__main__.ValidationTest) ... ok
test_tier_avoid (__main__.ValidationTest) ... ok
test_tier_proven (__main__.ValidationTest) ... ok

----------------------------------------------------------------------
Ran 50 tests in 0.390s

OK
```

Persona run (second run, after the fix):
```
$ python3 scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/pm_opt_clock.py --candidates scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/fixtures/persona_candidates.json --as-of 2027-07-01 --opt-start 2027-06-01 --unemployment-days 90 --hiring-lag-weeks 10 --out-dir course/2026fa/submissions/shinde-pras/runs/persona-demo-v2
# python3: Python 3.9.6 · node: v20.20.2 · commit: 0b0d042 + uncommitted CP4b changes to pm_opt_clock.py · run at 2026-10-01T20:09:12Z
pm_opt_clock: 10 candidates -> cannot_evaluate 3, hold 1, scored 6; scorer called; wrote roles.json, profile.json, run-log.json, report.md, role-scores.json, role-scores.md to course/2026fa/submissions/shinde-pras/runs/persona-demo-v2
exit_code: 0
```

The scorer's own table:
```
# Role Scorer report — 2026-10-01

*Bayesian Role Scorer (Ch.11). Weights: sponsorship 0.35, fit 0.3, role_quality 0 [role_quality weight is **[VERIFY]** — not pinned by the chapter]. Threshold 0.3. Profile requires sponsorship.*

**Summary:** 6 roles → Apply 0 · Consider 3 · Skip 3. **Skip rate 50%** (healthy — a good run skips at least half).

| Role | Composite | Rec | Why | Audit (term · value · weight · source) |
|---|---|---|---|---|
| LinkedIn Corp — Associate Product Manager | 0.390 | **Consider** | above threshold (0.390) but one soft spot: sponsorship tier "Likely" | sponsorship 0.7·0.35 [model-judgment]; fit 0.7·0.3 [your-input] × liveness 1[your-input]×timeline 0.8571428571428571[your-input] |
| Stripe Inc — Product Manager | 0.304 | **Consider** | above threshold (0.304) but one soft spot: sponsorship tier "Likely" | sponsorship 0.5·0.35 [model-judgment]; fit 0.6·0.3 [your-input] × liveness 1[your-input]×timeline 0.8571428571428571[your-input] |
| Zscaler Inc — Product Manager | 0.231 | **Consider** | composite 0.231 in the Consider band [0.2, 0.3) | sponsorship 0.3·0.35 [model-judgment]; fit 0.55·0.3 [your-input] × liveness 1[your-input]×timeline 0.8571428571428571[your-input] |
| Flywire Corp — Product Manager | 0.176 | **Skip** | composite 0.176 < 0.2 — time is better spent elsewhere | sponsorship 0.2·0.35 [model-judgment]; fit 0.45·0.3 [your-input] × liveness 1[your-input]×timeline 0.8571428571428571[your-input] |
| Salesforce.com, Inc. — Associate Product Manager | 0.148 | **Skip** | composite 0.148 < 0.2 — time is better spent elsewhere | sponsorship 0.15·0.35 [model-judgment]; fit 0.4·0.3 [your-input] × liveness 1[your-input]×timeline 0.8571428571428571[your-input] |
| Datadog Inc — Product Manager | 0.000 | **Skip** | gated: liveness ≈ 0.000 (a closed gate zeroes the composite regardless of votes) | sponsorship 0.5·0.35 [model-judgment]; fit 0.5·0.3 [your-input] × liveness 0[your-input]×timeline 0.8571428571428571[your-input] |

*Every term traces to its source. If you cannot explain a row term-by-term, distrust the recommendation before your confusion (Ch.11).*
```

Deliberate break attempts (commands and output):
```
### a) as-of after the 2027-08-30 deadline
$ python3 scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/pm_opt_clock.py --opt-start 2027-06-01 --unemployment-days 90 --hiring-lag-weeks 10 --candidates scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/fixtures/persona_candidates.json --as-of 2027-09-01 --out-dir <scratch>/out-a
pm_opt_clock: error: no time left: deadline 2027-08-30 is not after as-of 2027-09-01 (days available = -2)
No outputs were written.
exit_code: 2
out-dir exists: no (no files written)

### b) out-dir data/examples (role-scores.json there is tracked)
$ python3 scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/pm_opt_clock.py --opt-start 2027-06-01 --unemployment-days 90 --hiring-lag-weeks 10 --candidates scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/fixtures/persona_candidates.json --as-of 2027-07-01 --out-dir data/examples
pm_opt_clock: error: refusing to overwrite tracked file(s): data/examples/role-scores.json, data/examples/role-scores.md
No outputs were written.
exit_code: 2
tracked changes (git status --porcelain --untracked-files=no): ''
checksum: data/examples/role-scores.json: OK
checksum: data/examples/role-scores.md: OK
untracked files in data/examples: ''

### c) persona copy, r01 fit = 1.5
$ python3 scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/pm_opt_clock.py --opt-start 2027-06-01 --unemployment-days 90 --hiring-lag-weeks 10 --candidates <scratch>/persona-fit15.json --as-of 2027-07-01 --out-dir <scratch>/out-c
pm_opt_clock: error: candidates file is invalid:
  - candidate 'r01-linkedin-apm': fit must be a number from 0 to 1, got 1.5
No outputs were written.
exit_code: 2
out-dir exists: no (no files written)

### d) persona copy, r02 liveness_result uncertain + url removed
$ python3 scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/pm_opt_clock.py --opt-start 2027-06-01 --unemployment-days 90 --hiring-lag-weeks 10 --candidates <scratch>/persona-uncertain-nourl.json --as-of 2027-07-01 --out-dir <scratch>/out-d
pm_opt_clock: 10 candidates -> cannot_evaluate 3, hold 2, scored 5; scorer called; wrote roles.json, profile.json, run-log.json, report.md, role-scores.json, role-scores.md to <scratch>/out-d
exit_code: 0
files in out-dir: profile.json report.md role-scores.json role-scores.md roles.json run-log.json 

```

## Verified versus inferred
Built from run-log.json for four of the ten roles, one per outcome (scored and Consider, scored and Skip, on hold, cannot evaluate). Each row shows the value and the label exactly as stored.
Role r02-stripe-pm (scored, Consider):

| Field | Value | Stored label |
|---|---|---|
| role_id | r02-stripe-pm | your-input |
| company | Stripe Inc | your-input |
| title | Product Manager | your-input |
| url | https://example.com/jobs/r02 | your-input |
| fit | 0.6 | your-input |
| status | scored | model-judgment |
| reason | scorable | model-judgment |
| csv.normalized_name | stripe | model-judgment |
| csv.matched_rows | ["STRIPE INC"] | record |
| csv.total_approvals | 1250.0 | record |
| csv.total_denials | 22.0 | record |
| csv.approval_rate | 98.27044025157232 | record |
| csv.titles | ["Software Engineer", "Backend Engineer", "Risk Strategist", "Product Manager", "Engineering Manager"] | record |
| csv.pm_titles | ["Product Manager"] | model-judgment |
| sponsorship.tier | Likely | model-judgment |
| sponsorship.p | 0.5 | model-judgment |
| sponsorship.rule_row | approvals at least 50 and a PM-family title with no level marker | model-judgment |
| sponsorship.detail | "" | model-judgment |
| liveness.result | active | your-input |
| liveness.factor | 1.0 | your-input |
| liveness.checked_at | 2027-06-28 | your-input |
| liveness.source | by-hand (persona placeholder) | your-input |
| timeline_factor | 0.8571428571428571 | your-input |
| scorer.composite | 0.3043 | model-judgment |
| scorer.recommendation | Consider | model-judgment |
| scorer.machine_recommendation | Consider | model-judgment |
| scorer.reason | above threshold (0.304) but one soft spot: sponsorship tier "Likely" | model-judgment |
| scorer.arithmetic | (0.5·0.35 + 0.6·0.3) × 1 × 0.8571428571428571 = 0.304 | model-judgment |

Role r05-flywire-pm (scored, Skip):

| Field | Value | Stored label |
|---|---|---|
| role_id | r05-flywire-pm | your-input |
| company | Flywire Corp | your-input |
| title | Product Manager | your-input |
| url | https://example.com/jobs/r05 | your-input |
| fit | 0.45 | your-input |
| status | scored | model-judgment |
| reason | scorable | model-judgment |
| csv.normalized_name | flywire | model-judgment |
| csv.matched_rows | ["FLYWIRE CORP"] | record |
| csv.total_approvals | 36.0 | record |
| csv.total_denials | 2.0 | record |
| csv.approval_rate | 94.73684210526316 | record |
| csv.titles | ["Digital Marketing Specialist", "Product Manager", "Application Security Engineer", "Senior Technical Support Engineer II"] | record |
| csv.pm_titles | ["Product Manager"] | model-judgment |
| sponsorship.tier | Likely | model-judgment |
| sponsorship.p | 0.2 | model-judgment |
| sponsorship.rule_row | approvals below 50 and any PM-family title listed | model-judgment |
| sponsorship.detail | "" | model-judgment |
| liveness.result | active | your-input |
| liveness.factor | 1.0 | your-input |
| liveness.checked_at | 2027-06-28 | your-input |
| liveness.source | by-hand (persona placeholder) | your-input |
| timeline_factor | 0.8571428571428571 | your-input |
| scorer.composite | 0.1757 | model-judgment |
| scorer.recommendation | Skip | model-judgment |
| scorer.machine_recommendation | Skip | model-judgment |
| scorer.reason | composite 0.176 < 0.2 — time is better spent elsewhere | model-judgment |
| scorer.arithmetic | (0.2·0.35 + 0.45·0.3) × 1 × 0.8571428571428571 = 0.176 | model-judgment |

Role r10-roku-pm (on hold):

| Field | Value | Stored label |
|---|---|---|
| role_id | r10-roku-pm | your-input |
| company | Roku Inc | your-input |
| title | Product Manager | your-input |
| url | https://example.com/jobs/r10 | your-input |
| fit | 0.8 | your-input |
| status | hold | model-judgment |
| reason | HOLD: liveness uncertain | model-judgment |
| csv.normalized_name | roku | model-judgment |
| csv.matched_rows | ["ROKU INC"] | record |
| csv.total_approvals | 654.0 | record |
| csv.total_denials | 4.0 | record |
| csv.approval_rate | 99.3920972644377 | record |
| csv.titles | ["Senior Software Engineer", "Senior Data Scientist", "Software Engineer", "Product Manager", "Senior Data Engineer"] | record |
| csv.pm_titles | ["Product Manager"] | model-judgment |
| sponsorship.tier | Likely | model-judgment |
| sponsorship.p | 0.5 | model-judgment |
| sponsorship.rule_row | approvals at least 50 and a PM-family title with no level marker | model-judgment |
| sponsorship.detail | "" | model-judgment |
| liveness.result | uncertain | your-input |
| liveness.factor | null | your-input |
| liveness.checked_at | 2027-06-28 | your-input |
| liveness.source | by-hand (persona placeholder) | your-input |
| timeline_factor | null | your-input |

Role r07-alphabet-apm (cannot evaluate):

| Field | Value | Stored label |
|---|---|---|
| role_id | r07-alphabet-apm | your-input |
| company | Alphabet Inc. | your-input |
| title | Associate Product Manager | your-input |
| url | https://example.com/jobs/r07 | your-input |
| fit | 0.65 | your-input |
| status | cannot_evaluate | model-judgment |
| reason | cannot evaluate: no_h1b_data | model-judgment |
| csv.normalized_name | alphabet | model-judgment |
| csv.matched_rows | ["ALPHABET INC"] | record |
| csv.total_approvals | null | record |
| csv.total_denials | null | record |
| csv.approval_rate | null | record |
| csv.titles | null | record |
| csv.pm_titles | null | model-judgment |
| sponsorship.tier | null | model-judgment |
| sponsorship.p | null | model-judgment |
| sponsorship.rule_row | null | model-judgment |
| sponsorship.detail | row found but Total Approvals is empty (no trace is not the same as not sponsoring) | model-judgment |
| liveness.result | active | your-input |
| liveness.factor | 1.0 | your-input |
| liveness.checked_at | 2027-06-28 | your-input |
| liveness.source | by-hand (persona placeholder) | your-input |
| timeline_factor | null | your-input |
In plain words:
- record: the company row, approvals, denials and title strings, as read from the CSV file.
- model-judgment: which titles count as PM-family and at what level, the sponsorship tier and probability (constants I and the AI chose for version 0.1, not derived from data), each role's status, and the scorer's recommendation.
- your-input: the dates, the hiring lag, the fit values and the liveness results (all invented for the persona), and the timeline factor, which is arithmetic on those inputs.
- Not verified by the tool: that any company will sponsor this role now, what years or petition types the counts cover, hiring calendars, and whether a name match is the right company.

## Verification
1. Hand calculation before the run: all six scores and verdicts matched to three decimals. This checks the code against the recipe's formula, not the formula against reality.
2. Two rows cross-checked by hand against the source file:
```
$ python3 -c "import csv,json; r={x[\"company_name\"]:x for x in csv.DictReader(open(\"data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv\",newline=\"\",encoding=\"utf-8-sig\"))}; L={c[\"role_id\"][\"value\"]:c[\"csv\"] for c in json.load(open(\"course/2026fa/submissions/shinde-pras/runs/persona-demo-v2/run-log.json\"))[\"candidates\"]}; [print(\"CSV     \",n,\"|\",r[n][\"Total Approvals\"],\"|\",r[n][\"Total Denials\"],\"|\",r[n][\"top_job_titles_sponsored\"]) or print(\"RUN-LOG \",*[k+\"=\"+repr(L[i][k][\"value\"])+\" [\"+L[i][k][\"label\"]+\"]\" for k in (\"matched_rows\",\"total_approvals\",\"total_denials\",\"titles\")]) for n,i in ((\"STRIPE INC\",\"r02-stripe-pm\"),(\"FLYWIRE CORP\",\"r05-flywire-pm\"))]"
CSV      STRIPE INC | 1250.0 | 22.0 | ['Software Engineer', 'Backend Engineer', 'Risk Strategist', 'Product Manager', 'Engineering Manager']
RUN-LOG  matched_rows=['STRIPE INC'] [record] total_approvals=1250.0 [record] total_denials=22.0 [record] titles=['Software Engineer', 'Backend Engineer', 'Risk Strategist', 'Product Manager', 'Engineering Manager'] [record]
CSV      FLYWIRE CORP | 36.0 | 2.0 | ['Digital Marketing Specialist', 'Product Manager', 'Application Security Engineer', 'Senior Technical Support Engineer II']
RUN-LOG  matched_rows=['FLYWIRE CORP'] [record] total_approvals=36.0 [record] total_denials=2.0 [record] titles=['Digital Marketing Specialist', 'Product Manager', 'Application Security Engineer', 'Senior Technical Support Engineer II'] [record]
```
3. 50 offline tests (output above).
4. A fresh clone of the pushed branch (commit 9b82a34) reproduced the second run: role-scores.json, roles.json, profile.json, run-log.json (ignoring the timestamp), report.md and role-scores.md were identical (evidence-sanitized/clean-checkout/B5-compare.txt).
5. Four deliberate break attempts (output above).

Private run, counts only. I ran the same program on my own company list with no postings checked, so nothing could be scored. Of 11 companies, 8 were cannot evaluate (7 not found by exact name; 1 matched a different company that has no H-1B data) and 3 were on hold. I had predicted about 5 of about 10 cannot evaluate, so the prediction was too low. Level 2 (checking real postings by hand) was not done, so my prediction about the share of Skip on my real list is untested. Names and dates are not recorded here.

## Reflection
What worked:
- The tool refused to guess: three of ten candidates came out as cannot evaluate with a reason, and none was silently skipped.
- The hand calculation made before the run matched; because it was committed first, the match is evidence about the code and not a story told afterward.
- The fresh-clone rerun was identical, so the result does not depend on my working folder.

What it got wrong or missed:
- A held posting did not show its link, and a held role without a link was accepted silently. Break attempt (d) found it; fixed in commit 9b82a34 with the scores unchanged.
- Some numbers were stored as text; fixed in the same commit.
- A test for a non-numeric approvals value was missing until the fresh-clone review found it; added in commit 2ce53de.
- Exact-name matching cannot tell a false absence or a false match (private run).
- The timeline factor is one number shared by every role, so it cannot rank them. Because my own clock has not started it was 1.0 for every real role, so my prediction that it would be too crude could not show up in the numbers.
- The report lists results but not the next action for each, which the recipe defines.

I predicted 5 of about 10 because I already knew three misses from my first look at the data and added a margin of about two for the rest. I assumed most of the other large companies would be in the data. In fact 5 of the other 8 were not found by exact name, and at least one of those appears to be listed under a different legal name, so "not found" did not always mean "absent". My prediction was too low (8 of 11 could not be evaluated).

The next improvement I would make: let me supply an alias list (brand name to legal name), labeled your-input, and show the matched company name prominently in the report, because the private run showed both a false absence and a false match that the tool cannot detect on its own.

## Attestation
- Recipe: PM/APM OPT-clock (shinde-pras-pm-apm-opt-clock) v0.1.1, status DRAFT, attestation field null
- By: Prasad Shinde (shinde-pras) · 2026-10-02
- Run by: Claude Code in the author's terminal; the author reviewed each output below.

### Tested
| Ran | Saw | Expected |
|---|---|---|
| python3 test command from the README, under Python 3.9.6 and 3.11.16 | 50 tests, OK on both | all pass |
| Persona run with the README command | 6 scored (Consider 3, Skip 3), 1 on hold, 3 cannot evaluate; scores 0.390, 0.304, 0, 0.231, 0.176, 0.148 | the same, from a hand calculation made before the run |
| The same run in a fresh clone of commit 9b82a34 | all outputs identical | identical |
| Break attempt (a): as-of date after the deadline | exit 2, a clear message, no files written | refuse |
| Break attempt (b): output folder holding a tracked file | exit 2, refused, no tracked file changed | refuse |
| Break attempt (c): a fit value of 1.5 | exit 2, no files written | refuse |
| Break attempt (d): a held role with its link removed | exit 0; the role was held and never scored; the link was missing from the report | a clear note that no link was supplied (not met; see the next section) |
| Private run on a real company list (counts only) | 8 of 11 cannot evaluate, 3 held, 0 scored | about 5 of about 10 cannot evaluate (too low) |

### Did not test
- Whether my prediction that at least half of the scored roles on my real list would be Skip (not tested: nothing was scored; Level 2 was skipped for lack of time).
- The liveness command on real postings. It was run once, on a reserved example address, as a smoke test, and says nothing about its accuracy on real career pages.
- Real hiring calendars and application windows (addition A6 is not built).
- E-Verify participation (addition A5 is not built).
- Any machine other than this Mac, and the checks that run on the pull request.
- Whether a name match is the right company, which the tool cannot tell.
- The H-1B lottery, wage levels, cap-exempt status, STEM eligibility, and anything legal.
- What the approval counts cover (years and petition types are undocumented).

### Broke during testing, fixed
- The held list did not show a posting's link, and a held role without a link was accepted silently. Found by break attempt (d). Fixed in commit 9b82a34; every score, verdict and count was unchanged.
- Numbers were stored as text in run-log.json. Fixed in the same commit.
- No test covered a non-numeric approvals value. Found in the fresh-clone review. Test added in commit 2ce53de.
- Claude Code's first script for the break attempts failed because of how the shell split a variable (exit 127; the prototype never ran). That was a mistake in the test harness, not in the prototype; Claude Code reran it under bash, and the table above is from the rerun.
