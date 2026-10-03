# Card: PM/APM OPT-clock (shinde-pras-pm-apm-opt-clock)

## Purpose
Given a list of PM or APM roles at large companies, show which are worth tailoring an application for, which need a manual check, and which cannot be evaluated from the shipped data, using the 80 Days sponsorship record and your own OPT dates. Status DRAFT (two proposals still open); a prototype runs on sample data.

## What it can verify
- A company row exists in the 80 Days CSV, and what its approval, denial and title fields say (record).
- The date arithmetic behind the timeline factor (deterministic, from your-input).
- A liveness result as recorded by npm run ats:liveness at a stated time (record).

## What it cannot verify
- That a company will sponsor this role, at this level, now. The counts are company-wide, and their years and categories are undocumented.
- Hiring calendars and application windows (addition A6, not built).
- Lottery odds, rule changes, cap-exempt status, wage levels, E-Verify, STEM eligibility, anything legal.
- That a name match is the right company. A brand and its legal entity can differ, and two unrelated companies can share a normalized name.

## Dependencies
Node 20 or later, Python 3, the shipped CSV, scripts/score/role-scorer.mjs, and (only for checking liveness by hand) Playwright Chromium. The prototype needs nothing beyond the standard library.

## Annotated commands
- npm run score -- <roles.json> --profile <profile.json> --out-dir <dir> : the existing scorer, used unchanged. Always pass --out-dir.
- npm run ats:liveness -- <url> : run by you; enter its result in the candidates file.
- python3 scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/pm_opt_clock.py --candidates <json> --as-of YYYY-MM-DD --opt-start YYYY-MM-DD --unemployment-days N --hiring-lag-weeks N --out-dir <dir> : the prototype; see its README. Use a git-ignored --out-dir for any real run.
- python3 scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/test_pm_opt_clock.py -v : the offline tests.

## What it produces
roles.json, profile.json, role-scores.json and role-scores.md, run-log.json (for the agent) and report.md (for you), in an output folder you choose. Real runs go to a folder that git ignores.

## Named failure modes
- Company missing from the CSV, or present with no H-1B data: cannot evaluate, never Skip.
- Name variants and duplicate rows: collapsed only when the figures are identical, otherwise ambiguous.
- PM titles found only at senior level: lower p, not treated as entry-level evidence.
- OPT dates past, unparseable or out of order: stops with an error, no factor.
- Posting expired or unknown: expired scores zero; unknown is held for a human.
- Missing fit vote: refused, because the scorer would silently drop it.
- Profile text containing citizen, permanent, green, gc, pr at the end of a word, no-sponsor wording, or authorized: the scorer would zero the sponsorship weight, so the profile uses one fixed phrase and a test checks the weight stays 0.35.
- A tier the scorer does not treat as soft (Proven, Avoid, or any unfamiliar value): could let a role reach Apply, so only Likely and Unknown are ever written.
- The timeline factor is one linear number shared by all roles; fixed hiring cohorts will make it wrong for some roles (predicted, not yet observed).
- Approvals of zero, a non-numeric approvals value, or an unreadable title list: cannot evaluate (undefined_case), never guessed.
- A name that matches the wrong company, or a company listed under a different legal name: exact matching cannot tell either; a person must check the matched name in the report.
