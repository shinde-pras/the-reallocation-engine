---
status: DRAFT
todos_open: 2
last_gate: null
attestation: null
recipe_version: 0.1.1
---
# PM/APM OPT-clock: sponsorship evidence and timeline check for large-company product roles

## Executive summary
What it does: for each Product Manager (PM) or Associate Product Manager (APM) role you are considering at a large company, this recipe checks two things. First, whether the sponsorship record shows that the company has sponsored PM-type job titles before, and at what level. Second, whether hiring can plausibly finish before your OPT unemployment window closes. It gives each role it can score a recommendation of Apply, Consider or Skip with every input labeled, and it lists separately the companies it cannot evaluate and the postings whose status is unknown. Then it stops and hands the decision to a person.

Who it is for: an international master's student graduating within a few months, on the F-1 OPT unemployment clock, applying to PM and APM roles at large tech companies. Committed files use a fictional persona with invented dates. Real dates and the real company list are supplied only at run time, from a location that git ignores.

What it decides: a recommendation, never a final decision. It cannot say that a company will sponsor you.

In this first version the strongest recommendation is Consider. The sponsorship record can show that a company has sponsored PM-type titles at some point, with the years undocumented, but not that it will sponsor this role now. Consider means: worth your tailoring hours, after you check the posting and the company's hiring window yourself.

Handoff condition: the run is complete when the human-readable report and the machine-readable log both exist, every candidate has exactly one status (scored, on hold, or cannot evaluate), and a person has read the report and recorded the decision in a run-log entry.

## Required reads
SNICKERDOODLE.md, DOMAIN.md (Known gaps), DATA_CONTRACT.md (Zero-Conditions), CONTRIBUTING.md, recipes/README.md, recipes/local-wage-adjustment.md (style reference), and the tier definitions in the book's Chapter 7.

## Purpose and source inventory
| Need | Path or command | Status | Label of values |
|---|---|---|---|
| Sponsorship history | data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv (columns company_name, Total Approvals, Total Denials, Approval_Rate, top_job_titles_sponsored) | exists, read-only | record |
| Name normalization | suffix list in scripts/ats/scrapers/common/config.py; function definition at scripts/ats/scrapers/common/normalize.py:22 | exists; importing the package needs requests, so the prototype loads the suffix list by file path and reproduces the short function | record (suffix list), model-judgment (matching) |
| Scoring | npm run score -- <roles.json> --profile <profile.json> --out-dir <dir> (scripts/score/role-scorer.mjs, used unchanged; exports nothing) | exists | as labeled per term |
| roles.json shape | data/examples/ch11-roles.json | exists | n/a |
| Liveness | npm run ats:liveness -- <url> (run by the person; results are entered as inputs; the prototype makes no network calls) | exists (needs Playwright Chromium) | record if from the command, your-input if checked by hand |
| Prototype | scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/pm_opt_clock.py (run command in the README in the same folder; offline tests in test_pm_opt_clock.py) | exists | n/a |
| Run logs | logs/runs/2026fa-shinde-pras-1.md (never edit logs/RUN_LOG.md) | exists (one entry, for the fictional persona run) | n/a |

Not used, and why: role_quality (scorer weight is 0.0 and the H-1B data has no SOC field); bls:local-wage (feeds no decision and fails on a fresh clone); Form D funding (not a scorer term; only 14 distinct sample companies match the CSV and only one has H-1B data).

## Proposed additions
None of these existed in the repo before this recipe. A1 to A4 are now built in the prototype and covered by offline tests. A5 and A6 are proposals only and remain open.
- A1: timeline factor computed from dates and a stated hiring lag (see the Timeline gate section). Built.
- A2: sponsorship probability and tier computed from the CSV by the rule in the Sponsorship rule section. Built.
- A3: mapping from a liveness result to a liveness factor, with unknown states held for a human. Built.
- A4: validation of the scorer's input files before the scorer runs (see the Workflow section). Built.
- A5: E-Verify participation check, relevant to a later STEM OPT extension. Not built in this version. [TODO: DATA SOURCE]
- A6: optional per-role application-window dates, supplied by the person, to make the timeline gate differ by role. Not built in v0.1. [TODO: DEV]

## Phase gates
Each gate is a hard stop. A gate that fails ends the run for the affected role or, where stated, the whole run.
- PG0, inputs present (whole run). Condition: test -f data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv and test -f scripts/score/role-scorer.mjs both succeed, and the candidates file, as-of date, OPT start, unemployment days, hiring-lag weeks and output folder were all supplied.
- PG1, liveness gate (per role; a gate, not a vote). A human sees the URL, the recorded result (active, expired, uncertain or none), when it was checked, and how (command or by hand). Condition: only roles with a recorded result of active (factor 1.0) or expired (factor 0.0) reach the scorer. Uncertain or none is HOLD until a human enters a result.
- PG2, timeline gate (a gate, not a vote). In v0.1 every role shares one factor, because its inputs are global. A human sees the as-of date, OPT start, unemployment days, hiring-lag weeks, the computed deadline and days available, and the arithmetic. Condition: days available must be positive and all dates must parse, otherwise the whole run stops with an error and no factor is invented.
- PG3, scorer input valid (whole run). Condition: validation (A4) reports zero errors before the scorer is called.
- PG4, human sign-off (whole run). A human reads the report and records the decision in the run-log entry. The tool never applies to anything.

## Workflow
1. Read the candidates file (your-input): role_id, company, title, optional url, fit (0 to 1), liveness_result, liveness_checked_at, liveness_source.
2. Check PG0. Normalize each company name and match it against the CSV.
3. Apply the sponsorship rule. Companies that cannot be scored are set aside with a reason.
4. Compute the timeline factor and map the liveness result using PG1.
5. Validate everything (A4). Reject: a probability outside 0 to 1, a value that is not a number, a source label other than record, model-judgment or your-input, a tier other than Likely or Unknown, a missing fit, a missing gate factor, and any override field. Then write roles.json and profile.json. The profile's authorization text is one fixed phrase, "F-1 OPT, needs H-1B sponsorship", because the scorer zeroes the sponsorship weight when that text contains any of: citizen, permanent, green, gc, pr at the end of a word, no-sponsor wording, or authorized. A test confirms the weight stays 0.35.
6. Run npm run score -- <roles.json> --profile <profile.json> --out-dir <dir>.
7. Join the scorer output back to the per-role detail by role_id (the scorer drops extra fields) and write the machine-readable log and the human-readable report.
8. Stop at PG4.

## Sponsorship rule v0.1
All constants below are v0.1 assumptions (model-judgment), not values derived from data. The facts they act on are records. Tier names follow the book's Chapter 7 (Proven, Likely, Unknown, Avoid), and this rule emits only Likely and Unknown. Proven is never emitted, because recent, strong filing history is not established when the years are undocumented. Avoid is never emitted, because nothing in the data shows that a company refuses to sponsor this kind of role, and the scorer treats an unfamiliar tier like Avoid the same as Proven. The scorer's code also knows a tier called Possible that the book does not define; it is not used.

| Situation in the CSV (record) | Result | Tier | p |
|---|---|---|---|
| company not in the CSV | cannot evaluate: not_in_csv | none | none |
| rows with the same normalized name but different figures | cannot evaluate: ambiguous_rows | none | none |
| row found but Total Approvals empty | cannot evaluate: no_h1b_data (no trace is not the same as not sponsoring) | none | none |
| approvals at least 50 and an entry-level PM title listed (Associate Product Manager, APM, Product Manager I, junior or new-grad wording) | scored | Likely | 0.70 |
| approvals at least 50 and a PM-family title with no level marker | scored | Likely | 0.50 |
| approvals at least 50 and PM-family titles only at senior levels (Senior, Staff, Principal, Group, Lead, Director, II or above) | scored | Likely | 0.30 |
| approvals below 50 and any PM-family title listed | scored | Likely | 0.20 |
| some approvals but no PM-family title listed | scored | Unknown | 0.15 |
| Total Approvals is zero or negative, is not a number, or the title list is non-empty but cannot be read | cannot evaluate: undefined_case (the table does not say what to do here, so the tool refuses to guess) | none | none |

Rows with identical normalized name and identical figures are collapsed to one. Approval counts are company-wide, and their years and petition categories are undocumented. The title list holds top titles only, so a missing PM title is not evidence of a no. Reading the book's Unknown ("no evidence either way") for a company that has filings but no listed PM title is a v0.1 interpretation, because the book's definition does not cover that case. The prototype never writes an override, so the strongest recommendation stays Consider.

How v0.1 reads titles (model-judgment). A title is PM-family if it contains "product manager" or "product management" in any case, or the whole word APM; Technical Program Manager and Project Manager do not count. Entry-level wording is: associate product manager, APM, Product Manager I (not II or higher), junior, new grad. Senior wording is: senior, sr, staff, principal, group, lead, director, head, VP, and Roman numerals II to X. A title with both kinds of wording counts as senior; across a company's titles, an entry-level title wins. Markers are matched as whole words anywhere in a PM title, so "Product Manager, Lead Generation" would be read as senior, and levels written as Arabic numerals or "Jr" are not read as markers, so those titles count as having no level. Both are known limitations, documented and tested, not fixed. Duplicate rows collapse only when approvals, denials, approval rate and the title list are all identical.

## Timeline gate v0.1
deadline = OPT start + unemployment days. days available = deadline minus as-of date. days needed = hiring-lag weeks times 7. factor = the smaller of 1 and (days available divided by days needed). Stop with an error if days available is zero or negative, if any date does not parse, or if hiring-lag weeks or unemployment days is not a positive number. The factor is labeled your-input because every input to it is. The scorer downgrades Apply to Consider below 0.6 and forces Skip at or below 0.05.

Known weakness, recorded before building: one linear number cannot represent hiring that runs in fixed cohorts, and in v0.1 all roles share it. It can change which recommendation a role reaches, but it cannot rank one role above another. Addition A6 is the intended fix.

## What it can and cannot verify
Can verify (record, or deterministic arithmetic on your-input): that a company row exists; the approval and denial figures and the title strings as stored; the date arithmetic; a liveness result as recorded by the command at a given time.

Cannot verify: that a company will sponsor this role, at this level, now; which fiscal years or petition types the counts cover; entry-level status beyond wording in a title string; that a name match is the right company (a brand and its legal entity can differ, and two unrelated companies can share a normalized name); hiring calendars or application windows; the H-1B lottery, recent rule changes, cap-exempt status, wage levels; E-Verify participation; STEM eligibility of any degree; anything legal. The person's school international office is the authority on dates and eligibility.

## Output contract
Files are written into the output folder the person chooses, never over a tracked file. A real run must use a folder that git ignores, such as private/pm-run/.
- roles.json and profile.json: scorer input.
- role-scores.json and role-scores.md: written by the scorer.
- run-log.json, for the agent: parameters, one record per candidate with status, tier, p, factors, reasons and warnings, and for every value its label (record, model-judgment or your-input) and source.
- report.md, for the person: a summary; scored roles with the arithmetic; the HOLD list; the cannot-evaluate list with reasons; what a human must check at each gate; and a limitations section.

One file cannot serve both audiences, so the two are always separate.

## Stop conditions and next action per result
Stop the whole run on: a missing input file or flag, a PG0 failure, a date error, a validation error, a non-zero scorer exit, or any value without a label.

Next action per result (this is where the recipe joins the 3-3-2 day):
- Consider: a role worth tailoring an application for, after checking the posting and the company's window yourself (the two hours).
- Skip: drop it.
- HOLD: open the posting, record the result, rerun.
- cannot evaluate, not_in_csv or no_h1b_data: look for a person to talk to at the company, or check sponsorship by hand (the networking three hours).
- cannot evaluate, ambiguous_rows: resolve the duplicate by hand, then rerun.

## Run-log template
For logs/runs/2026fa-shinde-pras-<n>.md:

```markdown
## YYYY-MM-DD — PM/APM OPT-clock run

- **Recipe:** shinde-pras-pm-apm-opt-clock
- **Inputs:** candidates file (fixture or private), as-of date, OPT start, unemployment days, hiring-lag weeks
- **Outputs:** files created in the output folder
- **Result:** counts of Consider / Skip / HOLD / cannot evaluate; what the human decided
- **Open issues:** what did not work or what is still missing
```

## Status note
Status as of 2026-10-02: DRAFT, with two open items (A5 and A6). Reached: the prototype runs on the shipped sample CSV with a fictional persona; its 50 offline tests pass on Python 3.9 and 3.11; the persona run reproduced identically in a fresh clone of the pushed branch; conformance passes. Why it stays DRAFT: SNICKERDOODLE.md moves a recipe to the next stage only when no open items remain, and A5 and A6 are proposals that the assignment asks to keep as typed to-dos. Not done: no live data was used (the tool reads the shipped CSV only), the tool itself runs no liveness check, and no named human has signed an attestation, so attestation stays null.

## Provenance
Builds on recipes/cases/2026su/case-opt-timeline-fit-company-targeting.md, a DRAFT skeleton in this repo. Reused: its purpose wording, its stop conditions, and its list of things it cannot verify. Changed: its placeholder inputs, gate tests and CLI commands are replaced with paths and commands that exist. The tool, thresholds and rule above are new. Drafted with Claude in a planning chat, with repo checks run by Claude Code; the student's own contribution is recorded in FRICTIONAL.md and SOURCES.md. The prototype, its tests and the evidence logs were produced with Claude Code and reviewed by the student; see SOURCES.md.
