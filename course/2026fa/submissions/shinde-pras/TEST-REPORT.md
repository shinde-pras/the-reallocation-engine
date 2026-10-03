# TEST-REPORT: PM/APM OPT-clock prototype (shinde-pras)

## Executive summary
This report records how the prototype was tested: what was run, what was seen, and what is still untested. All 50 offline tests pass on two Python versions, the fictional-persona run reproduced identically in a fresh clone of the pushed branch, and three of four deliberate break attempts behaved as expected; the fourth exposed a gap. Testing and review found three problems in total (a held posting did not show its link, some numbers were stored as text, and one undefined case had no test); all three are fixed. Nothing here covers real job postings, real hiring calendars or any legal question. Real company data was used only in a private run, which is reported as counts.

## Environment
- One Mac. Node v20.20.2, npm 10.8.2, Python 3.9.6 (the python3 on this machine) and Python 3.11.16. Playwright Chromium was installed once for a smoke test.
- Branch contrib/2026fa-shinde-pras-pm-apm-opt-clock. The fresh-clone run used commit 9b82a34. The prototype program file has not changed since that commit, which was checked with git; later commits add one test, evidence and documents.
- Commit at the time of writing: c879f38.

## Toolchain baseline, before and after
The fresh clone was checked before running the prototype and again after. Full output is in evidence-sanitized/clean-checkout/ (doctor: B3a and B6a; verify as is: B3b and B6b; verify with PyYAML: B3c and B6c).
- npm run doctor: exit code 0 before and after; SUMMARY lines "environment: ✓ runnable", "recipes: 33/33 carry lifecycle frontmatter — all tracked", "next: continue"; the before and after output is identical (diff of B3a-doctor.log and B6a-doctor-after.log is empty).
```
RECIPES (33)
  with lifecycle frontmatter: 33   missing: 0
  by status: DRAFT 28 · RUNNABLE-SAMPLE 4 · RUNNABLE-LIVE  # DRAFT | SPECIFIED | RUNNABLE-SAMPLE | RUNNABLE-LIVE | VERIFIED 1
  open TODOs: 318 declared (in frontmatter) · 318 [TODO markers in bodies

SUMMARY
  environment: ✓ runnable
  recipes: 33/33 carry lifecycle frontmatter — all tracked
  next: continue
```
- npm run verify, run as is: exit code 1 before and after; error line "ModuleNotFoundError: No module named 'yaml'". This is an environment gap: the continuous-integration setup installs PyYAML and this Mac does not have it.
```

> the-reallocation-engine@1.0.0 verify
> node scripts/conformance.mjs && node scripts/manifest-check.mjs

conformance: 164 files (88 md · 38 py · 30 js · 4 json · 4 sh)
✓ all conform (machine half of P4). Adequacy is still the human gate.
MANIFEST CHECK — The Reallocation Engine
==========================================
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'yaml'

ERROR (1):
  E1 .ai/manifest.yaml does not parse: Error: Command failed: python3 -c "import yaml,json;print(json.dumps(yaml.safe_load(open('.ai/manifest.yaml'))))"

✗ manifest check FAILED (1 error)
```
- npm run verify, run in a throwaway environment with PyYAML (continuous-integration parity): exit code 0, "✓ manifest check passed (3 warnings)", before and after.
```

> the-reallocation-engine@1.0.0 verify
> node scripts/conformance.mjs && node scripts/manifest-check.mjs

conformance: 164 files (88 md · 38 py · 30 js · 4 json · 4 sh)
✓ all conform (machine half of P4). Adequacy is still the human gate.
MANIFEST CHECK — The Reallocation Engine
==========================================

WARN (3):
  W1 ignore path not in .gitignore: archive/
  W2 private path not gitignored (PII/secret risk): private/
  W2 private path not gitignored (PII/secret risk): data/ats/

✓ manifest check passed (3 warnings)
```

## Sample run and its output
The fictional persona, run with the command in the prototype README. Counts: 10 candidates, 6 scored (Consider 3, Skip 3), 1 on hold, 3 cannot evaluate.
```
$ python3 scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/pm_opt_clock.py --candidates scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/fixtures/persona_candidates.json --as-of 2027-07-01 --opt-start 2027-06-01 --unemployment-days 90 --hiring-lag-weeks 10 --out-dir course/2026fa/submissions/shinde-pras/runs/persona-demo-v2
# python3: Python 3.9.6 · node: v20.20.2 · commit: 0b0d042 + uncommitted CP4b changes to pm_opt_clock.py · run at 2026-10-01T20:09:12Z
pm_opt_clock: 10 candidates -> cannot_evaluate 3, hold 1, scored 6; scorer called; wrote roles.json, profile.json, run-log.json, report.md, role-scores.json, role-scores.md to course/2026fa/submissions/shinde-pras/runs/persona-demo-v2
exit_code: 0
```
Unit tests, Python 3.11 (last lines):
```
$ PYTHONDONTWRITEBYTECODE=1 python3.11 scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/test_pm_opt_clock.py -v 2>&1 | tail -n 4
----------------------------------------------------------------------
Ran 50 tests in 0.390s

OK
```

## Failure cases exercised
| Case | What should happen | Covering tests | Also seen in |
|---|---|---|---|
| F1 company not in the CSV | cannot evaluate: not_in_csv; never Skip; no invented value | test_row1_not_in_csv, test_nothing_scorable_skips_scorer | persona run: one role |
| F2 name variants and duplicates | identical rows collapse; differing rows are ambiguous; no alias guessing | test_row2_ambiguous_rows, test_salesforce_spellings_collapse, test_identical_duplicate_rows_collapse, test_differing_duplicate_rows_are_ambiguous, test_no_alias_matching | persona run: spellings collapsed, differing rows ambiguous. Not detected by the tool: a legal-name mismatch, or a different company with the same normalized name (both seen in the private run, counts only) |
| F3 PM titles only at senior level | lower probability; not treated as entry-level evidence | test_row6_senior_only, test_entry_level_title_wins_over_senior, test_title_with_senior_and_entry_markers_counts_as_senior | persona run: one role |
| F4 dates past or unparseable | exit 2, no outputs, no factor | test_zero_days_available_errors, test_past_deadline_errors, test_unparseable_dates_error, test_non_positive_numbers_error, test_error_leaves_no_partial_outputs | break attempt (a). "End before start" is not implemented, because there is no OPT end-date input |
| F5 posting expired or unknown | expired scores 0; unknown is held and never reaches the scorer | test_mapping, test_nothing_scorable_skips_scorer, test_hold_with_url_shows_url_and_liveness_command, test_hold_without_url_says_none_and_warns, test_integration_real_scorer_keeps_sponsorship_weight | persona run: one expired role scored 0 and Skip, one held; break attempt (d) |
| F6 missing fit | refused | test_missing_fit, test_candidates_file_rejections | not in the persona run. Break attempt (c) used an out-of-range value, not a missing one |
| Approvals zero or negative | cannot evaluate: undefined_case | test_zero_approvals_is_undefined_case | not in the persona run (5 rows in the real CSV have 0 approvals) |
| Approvals not a number | cannot evaluate: undefined_case | test_nonnumeric_approvals_is_undefined_case | not in the persona run. This test was added in commit 2ce53de, after the fresh-clone review found it missing |
| Title list unreadable | cannot evaluate: undefined_case | test_unparseable_titles_is_undefined_case | not in the persona run |
Also tested: refusal to overwrite a tracked file; the fixed profile phrase never matches the scorer's sponsorship-zeroing pattern; an integration test runs the real scorer and checks the sponsorship weight stays 0.35.

## Break attempts (output is in the worked run)
| Attempt | Exit | Seen |
|---|---|---|
| (a) as-of date after the deadline | 2 | no time left: deadline 2027-08-30 is not after as-of 2027-09-01 (days available = -2); no outputs written |
| (b) output folder that holds a tracked file | 2 | refusing to overwrite tracked file(s): data/examples/role-scores.json, data/examples/role-scores.md; no tracked file changed |
| (c) fit value of 1.5 | 2 | candidates file is invalid: candidate 'r01-linkedin-apm': fit must be a number from 0 to 1, got 1.5; no outputs written |
| (d) held role with its link removed | 0 | 10 candidates -> cannot_evaluate 3, hold 2, scored 5; the role was held and never reached the scorer. Before the fix, the held list did not show the link at all |

## Namespace check
Taken at the commit named above, before this report and the two other documents were added. All three are under course/2026fa/submissions/shinde-pras/, inside my namespace.
```
$ git diff --stat upstream/main...HEAD
 .../2026fa/submissions/shinde-pras/CHANGE-BRIEF.md |   68 +
 .../2026fa/submissions/shinde-pras/FRICTIONAL.md   |   45 +
 course/2026fa/submissions/shinde-pras/SOURCES.md   |   51 +
 .../shinde-pras/evidence-sanitized/01-doctor.log   |   64 +
 .../shinde-pras/evidence-sanitized/01-doctor.meta  |    5 +
 .../shinde-pras/evidence-sanitized/02-verify.log   |   16 +
 .../shinde-pras/evidence-sanitized/02-verify.meta  |    5 +
 .../02b-verify-CI-parity-pyyaml.log                |   15 +
 .../02b-verify-CI-parity-pyyaml.meta               |    6 +
 .../evidence-sanitized/03-ats-scan-dry-run.log     |    5 +
 .../evidence-sanitized/03-ats-scan-dry-run.meta    |    5 +
 .../evidence-sanitized/04-score-ch11.log           |    6 +
 .../evidence-sanitized/04-score-ch11.meta          |    5 +
 .../evidence-sanitized/05-ats-liveness-example.log |   10 +
 .../05-ats-liveness-example.meta                   |    5 +
 .../evidence-sanitized/06-fact7-bls-local-wage.log |    7 +
 .../06-fact7-bls-local-wage.meta                   |    5 +
 .../07-fact7-validate-h1b-join-sample.log          |   13 +
 .../07-fact7-validate-h1b-join-sample.meta         |    5 +
 .../08-pii-scan-working-tree.log                   |    6 +
 .../08-pii-scan-working-tree.meta                  |    5 +
 .../evidence-sanitized/09a-ci-shukla-harness.log   |   14 +
 .../evidence-sanitized/09a-ci-shukla-harness.meta  |    5 +
 .../evidence-sanitized/09b-ci-fuzz-invariants.log  |   14 +
 .../evidence-sanitized/09b-ci-fuzz-invariants.meta |    5 +
 .../evidence-sanitized/09c-ci-tapkir-harness.log   |   11 +
 .../evidence-sanitized/09c-ci-tapkir-harness.meta  |    5 +
 .../09d-ci-dhamija-gate-harness.log                |   63 +
 .../09d-ci-dhamija-gate-harness.meta               |    5 +
 .../09e-ci-yuqing-gate-harness.log                 |   14 +
 .../09e-ci-yuqing-gate-harness.meta                |    5 +
 .../09f-ci-ma-scorer-harness.log                   |   14 +
 .../09f-ci-ma-scorer-harness.meta                  |    5 +
 .../evidence-sanitized/10a-output-linter-test.log  |   14 +
 .../evidence-sanitized/10a-output-linter-test.meta |    5 +
 .../evidence-sanitized/10b-skill-demand-test.log   |   89 ++
 .../evidence-sanitized/10b-skill-demand-test.meta  |    5 +
 .../clean-checkout/B2-lockfile-numstat.txt         |    1 +
 .../clean-checkout/B2-npm-install.log              |   16 +
 .../clean-checkout/B2-npm-install.meta             |    5 +
 .../clean-checkout/B3a-doctor.log                  |   64 +
 .../clean-checkout/B3a-doctor.meta                 |    5 +
 .../clean-checkout/B3b-verify-as-is.log            |   16 +
 .../clean-checkout/B3b-verify-as-is.meta           |    5 +
 .../clean-checkout/B3c-verify-CI-parity.log        |   15 +
 .../clean-checkout/B3c-verify-CI-parity.meta       |    5 +
 .../clean-checkout/B4a-tests-python3.log           |   54 +
 .../clean-checkout/B4a-tests-python3.meta          |    5 +
 .../clean-checkout/B4b-tests-python3.11.log        |   54 +
 .../clean-checkout/B4b-tests-python3.11.meta       |    5 +
 .../clean-checkout/B4c-unittest-m-repo-root.log    |    5 +
 .../clean-checkout/B4c-unittest-m-repo-root.meta   |    5 +
 .../clean-checkout/B4d-unittest-m-in-folder.log    |   54 +
 .../clean-checkout/B4d-unittest-m-in-folder.meta   |    5 +
 .../clean-checkout/B5-compare.txt                  |   11 +
 .../clean-checkout/B5-persona-demo-clean.log       |    4 +
 .../clean-checkout/B6a-doctor-after.log            |   64 +
 .../clean-checkout/B6a-doctor-after.meta           |    5 +
 .../clean-checkout/B6b-verify-as-is-after.log      |   16 +
 .../clean-checkout/B6b-verify-as-is-after.meta     |    5 +
 .../clean-checkout/B6c-verify-CI-parity-after.log  |   15 +
 .../clean-checkout/B6c-verify-CI-parity-after.meta |    5 +
 .../clean-checkout/B6d-pii-scan.log                |    6 +
 .../clean-checkout/B6d-pii-scan.meta               |    5 +
 .../clean-checkout/B6e-conformance-prototype.log   |    2 +
 .../clean-checkout/B6e-conformance-prototype.meta  |    5 +
 .../clean-checkout/B6f-git-status.log              |   16 +
 .../clean-checkout/B7-upstream-diff.log            |  141 ++
 .../clean-checkout/B8-traceability-grep.txt        |   38 +
 .../shinde-pras/runs/break-attempts-terminal.log   |   31 +
 .../shinde-pras/runs/persona-demo-terminal.log     |    4 +
 .../shinde-pras/runs/persona-demo-v2-terminal.log  |    4 +
 .../shinde-pras/runs/persona-demo-v2/profile.json  |    3 +
 .../shinde-pras/runs/persona-demo-v2/report.md     |   73 +
 .../runs/persona-demo-v2/role-scores.json          |  281 ++++
 .../runs/persona-demo-v2/role-scores.md            |   16 +
 .../shinde-pras/runs/persona-demo-v2/roles.json    |  134 ++
 .../shinde-pras/runs/persona-demo-v2/run-log.json  | 1605 ++++++++++++++++++++
 .../shinde-pras/runs/persona-demo/profile.json     |    3 +
 .../shinde-pras/runs/persona-demo/report.md        |   70 +
 .../shinde-pras/runs/persona-demo/role-scores.json |  281 ++++
 .../shinde-pras/runs/persona-demo/role-scores.md   |   16 +
 .../shinde-pras/runs/persona-demo/roles.json       |  134 ++
 .../shinde-pras/runs/persona-demo/run-log.json     | 1604 +++++++++++++++++++
 .../submissions/shinde-pras/runs/role-scores.json  |  241 +++
 .../submissions/shinde-pras/runs/role-scores.md    |   15 +
 logs/runs/2026fa-shinde-pras-1.md                  |    7 +
 .../2026fa/shinde-pras-pm-apm-opt-clock.card.md    |   40 +
 .../cases/2026fa/shinde-pras-pm-apm-opt-clock.md   |  129 ++
 .../2026fa/shinde-pras-pm-apm-opt-clock/README.md  |   54 +
 .../fixtures/fixture_80days.csv                    |   18 +
 .../fixtures/persona_candidates.json               |   32 +
 .../shinde-pras-pm-apm-opt-clock/pm_opt_clock.py   |  783 ++++++++++
 .../test_pm_opt_clock.py                           |  425 ++++++
 94 files changed, 7285 insertions(+)
```
Any path outside the namespaces: none. Protected paths touched: none.

## What the gates need a person to judge
- Liveness: open each held posting and record whether it is active or expired. The tool never opens a page itself.
- Timeline: check the OPT dates and the allowed unemployment days with the school's international office. The tool only does arithmetic on what it is given.
- Company match: read the matched company name in the report. The tool cannot tell a brand from its legal entity, or two unrelated companies with the same normalized name.
- Fit: the fit values are the person's own rating; nothing verifies them.
- Sign-off: read the report and record the decision. The tool never applies to anything.

## Known issues not fixed
- Timestamps in run-log.json are local time without a zone, while the terminal logs use UTC.
- npm run verify fails as is on this Mac without PyYAML (environment gap); it passes with it.
- python3 -m unittest run from the repository root finds 0 tests and reports OK; the README command must be used.
- The earlier fresh-clone traceability snapshot (evidence-sanitized/clean-checkout/B8-traceability-grep.txt) predates the non-numeric-approvals test; the table above is current.
- The upstream repository's own checks were already failing on the commit this branch started from (four harness scripts that its workflow calls do not exist, and its PII scan flags an address inside package-lock.json), as read from its run logs on the first day. This branch touches none of those paths. Checks on the pull request have not run yet.
- The report shows the matched company name only for scored roles. For held and cannot-evaluate roles it prints the name the person typed, and the matched CSV row is only in run-log.json (csv.matched_rows). The card's failure-mode bullet says to check the matched name in the report; that is accurate only for scored roles.
