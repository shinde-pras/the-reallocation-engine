# CHANGE-BRIEF: PM/APM OPT-clock recipe

Author: shinde-pras · Course: INFO 7375 · Written 2026-09-28, before any recipe or prototype code exists.
Branch: contrib/2026fa-shinde-pras-pm-apm-opt-clock · Slug: pm-apm-opt-clock

## Executive summary
This recipe helps an international student with a limited OPT unemployment window decide which large-company Product Manager (PM) and Associate Product Manager (APM) roles to apply to first. It checks two things against evidence: whether the company's sponsorship record includes PM-family titles and at what level, and whether hiring can finish before the OPT clock runs out. Every value is labeled record, model-judgment, or your-input, and a human clears two gates. It says nothing about the H-1B lottery or immigration eligibility.

## 1. Situation and engine layers
- Situation (persona P1, fictional; dates invented, not the author's): an international master's student on F-1, graduating in May 2027, OPT start estimated June 1 2027, 90-day unemployment allowance, targeting PM and APM roles at large tech companies.
- The author's real dates and real target list are never committed (DATA_CONTRACT Zero-Conditions). They are supplied only at run time from a local, gitignored path.
- Layers used: 80 Days to Stay (sponsorship), Job-Ops (liveness).
- Layers not used: Cognitive Pivot (the H-1B data has no SOC field, PM has no clean SOC code, and role_quality has weight 0.0 in the scorer). Form D (funding is not a scorer term; 15 of the 200 sample records match the CSV, which is 14 distinct companies, and only Databricks has H-1B data).

## 2. Reuse (exact paths) and proposed additions
Reuse:
- Sponsorship history: data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv (30,369 rows, 1,557 with H-1B data; columns Total Approvals, Total Denials, Approval_Rate, top_job_titles_sponsored). Read-only.
- Name normalization: scripts/ats/scrapers/common/config.py (COMPANY_SUFFIXES) and normalize.py:22 (normalize_company_name). Importing the module through its package runs scrapers/common/__init__.py, which imports requests (via retry.py), so the prototype loads the suffix list by file path.
- Scoring: scripts/score/role-scorer.mjs via npm run score -- <roles.json> --out-dir <own folder>. Used unchanged. It exports nothing, so the CLI is the only interface.
- roles.json shape: data/examples/ch11-roles.json.
- Liveness: npm run ats:liveness -- <url>. The prototype consumes results as inputs and makes no network calls.
- Precedent, cited: recipes/cases/2026su/case-opt-timeline-fit-company-targeting.md (DRAFT skeleton, 14 open TODOs). This recipe builds on its risk-class idea and its cannot-verify list, and replaces its placeholder inputs, gate tests and CLI commands with ones that exist.

Proposed additions (none exist in the repo today):
1. timeline.factor computed from dates and a stated hiring-lag. [TODO: DEV]
2. sponsorship p and tier computed from the CSV by a stated, level-aware rule. [TODO: DEV]
3. Mapping from liveness result to liveness.factor, with "uncertain" held for a human. [TODO: DEV]
4. Input validation before the scorer, because it accepts p outside 0..1, unknown source labels and any tier as Proven, and defaults a missing gate to 1. [TODO: DEV]
5. E-Verify participation check for later STEM OPT use. Proposed only, not built. [TODO: DATA SOURCE]

Facts that bite and how the recipe treats them:
- role_quality is not used, because its scorer weight is 0.0.
- bls:local-wage feeds nothing and is not used.
- The approval counts are company-wide. Their years and petition categories are undocumented, so they are evidence of "has sponsored", not of "will sponsor this role at this level now".
- A null in the CSV means "no trace", not "confirmed non-sponsor".
- The scorer zeroes the sponsorship weight if the authorization text contains words like "authorized". The profile must say the student needs H-1B sponsorship, and a test asserts the weight stays 0.35.
- The scorer silently drops a missing fit vote (weight 0.30). Without fit, Apply needs sponsorship p of about 0.857 or higher. The prototype therefore supplies fit for every role as a per-role student self-rating from 0 to 1, labeled your-input; the persona fixture uses fixed invented values.

## 3. Gates
- G1, Liveness (a gate, not a vote). A human sees the URL, the result (active, expired or uncertain), when it was checked, and the command used. Testable condition: an "uncertain" role never reaches the scorer; it appears only in a HOLD list until a human marks it live or not live.
- G2, Timeline (a gate, not a vote). A human sees the as-of date, OPT start, allowed unemployment days, hiring-lag assumption, computed latest start, and the arithmetic. Testable condition: a deadline before the as-of date, or an unparseable date, stops the run with an error instead of producing a factor.
- Final decision: the engine returns Apply / Consider / Skip with a trace and stops. The person decides.

## 4. Predicted failure cases (proposed by Claude from recon, accepted by the author)
- F1: company missing from the CSV. Expected: listed as "cannot evaluate", never Skip, never an invented p. Check: fixture test plus a real-CSV lookup.
- F2: name variants and duplicates (for example SALESFORCE COM INC vs SALESFORCECOM INC; Meta vs FACEBOOK INC). Expected: variants collapse by normalized name; brand/legal-name aliases are not guessed and are reported as unresolved. Check: unit test on normalized names.
- F3: company found, but PM titles only at senior level. Expected: not treated as entry-level evidence. Check: fixture with a senior-only title list.
- F4: OPT dates already past, or end before start. Expected: clear error, no factor. Check: boundary-date tests, including off-by-one on the last day.
- F5: posting 404s or liveness is uncertain. Expected: expired gives gate 0; uncertain goes to HOLD. Check: one fixture per state.
- F6 (added after the recon fact-check, not an original prediction): fit missing from roles.json. Expected: the prototype refuses to write a role without fit instead of letting the scorer drop it silently. Check: fixture test.

## 5. Predictions (original, frozen; later revisions go in section 7)
- P1 (first-pass miss), author's pick: the timeline factor will be too crude. Reason: a single hiring-lag number can't capture that APM cohorts and large-company hiring run on fixed calendars, so a smooth countdown will call some roles safe that are not, or the reverse.
- P2, author's number: of about 10 large tech companies tested privately, 5 will end up "cannot evaluate". Three of the names (Amazon, Adobe, Meta) had already been looked up in recon (two absent from the CSV, one present with no H-1B data) before this prediction was made, so only the remaining names are a real test.

## 6. Scope
Covered: sponsorship evidence by company and PM-family title level; timeline gate from a configurable unemployment-day allowance (so the same tool can run for a STEM OPT clock); liveness hold.
Not covered (will be repeated under "did not test"): H-1B lottery odds and recent rule changes, cap-exempt status, wage-level selection, E-Verify participation (proposed addition 5), STEM eligibility of any degree, and any legal or immigration conclusion. The author's DSO is the authority on dates and eligibility.

## 7. Revisions
- 2026-09-28, before the first commit: after a fact-check against the repo, corrected the Form D count (15 records, 14 distinct companies) and the requests-import wording, and added the fit fact and failure case F6. Sections 5 and 6 were not changed.
- 2026-09-30, during the prototype build (CP3): (a) The prototype found three situations the recipe's sponsorship table does not cover: Total Approvals of 0 (5 rows in the real CSV), a non-numeric Total Approvals, and a non-empty title list that cannot be parsed. It reports them as "cannot evaluate: undefined_case" and does not guess; the recipe text will be updated at a later checkpoint. (b) Failure case F4 says "end before start". The recipe has no OPT end input, only unemployment days, so the implemented check is days available of zero or less, or an unparseable date; an as-of date before OPT start is allowed because the clock has not started. (c) Known limitation found in review: level markers match anywhere in a PM title, so "Product Manager, Lead Generation" would be read as senior, and arabic-numeral levels are not read as markers. Documented, not fixed in v0.1. Sections 5 and 6 were not changed.
- 2026-09-30, before the first persona demo run and before any real run. Predictions (author's, as stated): P3, persona demo: of the six roles that reach the scorer, 3 will be Skip; reasoning given: Datadog is expired, and any role scoring under 0.20 is a Skip. P4, real list, run privately: at least half of the real roles that can be scored will be Skip; reasoning given: postings do not stay live for long and scores will be under 0.20. Noted with it: an expired posting only counts if the author checks and enters it, and uncertain results are held, not skipped, so what actually produces the Skips is to be observed. Hand calculation from the recipe formula (done by Claude in the planning chat before the run): timeline factor 60/70 = 0.857; expected scores LinkedIn 0.390, Stripe 0.304, Datadog 0, Zscaler 0.231, Flywire 0.176, Salesforce 0.148; expected verdicts Consider, Consider, Skip, Consider, Skip, Skip; expected: 0 Apply, 3 cannot evaluate (Alphabet, NantHealth, Northwind Product Labs), 1 on hold (Roku). Sections 5 and 6 were not changed.
- (append later dated entries; do not rewrite sections 5 or 6)

## 8. Who did what
Drafted in a planning chat with Claude from the author's answers and a read-only recon of the repo done by Claude Code. Predictions P1 and P2 are the author's choices. Failure cases F1 to F5 were proposed by Claude and accepted by the author; F6 came from Claude Code's recon.
