# PM/APM OPT-clock prototype (shinde-pras, Fall 2026)

## Executive summary
This folder holds a small command-line tool and its tests. For a list of product-management roles you are considering, it checks the shipped sponsorship record and your OPT clock, hands the roles it can score to the engine's existing scorer, and writes one report for you and one log for an agent. It never decides for you, never applies to anything, and makes no network calls. Status: draft prototype (v0.1); its rules are assumptions, listed below, not facts from data.

## Run command (from the repo root)

```bash
python3 scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/pm_opt_clock.py --candidates <candidates.json> --as-of YYYY-MM-DD --opt-start YYYY-MM-DD --unemployment-days 90 --hiring-lag-weeks 10 --out-dir <folder>
```

Node 20 must be on PATH (for example `PATH=/opt/homebrew/opt/node@20/bin:$PATH`), because the tool calls `npm run score` when at least one role is scorable. Python 3.9 or later; standard library only.

| Flag | Meaning | Label |
|---|---|---|
| `--candidates` | JSON list of roles: `role_id`, `company`, `title`, optional `url`, `fit` (0 to 1), `liveness_result` (active, expired, uncertain, none), `liveness_checked_at`, `liveness_source` | your-input |
| `--as-of`, `--opt-start` | dates, strictly `YYYY-MM-DD` | your-input |
| `--unemployment-days` | allowed unemployment days, whole number above 0 | your-input |
| `--hiring-lag-weeks` | assumed weeks from application to start, above 0 | your-input |
| `--out-dir` | output folder. Real runs must use a gitignored folder such as `private/pm-run/`. The tool refuses to overwrite any tracked file. | your-input |
| `--csv` | defaults to the shipped `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv` | record |

Outputs in `--out-dir`: `roles.json`, `profile.json`, `role-scores.json`, `role-scores.md` (scorer, only when something is scorable), `run-log.json` (agent; every value carries a label and a source) and `report.md` (person). Exit code 0 on success, 2 on any input, date, validation, scorer or output-path error; on exit 2 nothing is written.

## Labels
- **record**: read from the CSV, or a liveness result whose `liveness_source` is exactly `ats:liveness`.
- **model-judgment**: the v0.1 rule constants (thresholds, p values, title patterns), the derived tier and status, and the scorer's own outputs.
- **your-input**: everything in the candidates file and on the command line, including the timeline factor computed from it, and liveness checked by hand.

## Rules (v0.1 assumptions, model-judgment)
Implements `recipes/cases/2026fa/shinde-pras-pm-apm-opt-clock.md`. Companies are matched by exact normalized name only (a local copy of `normalize_company_name`, `scripts/ats/scrapers/common/normalize.py:22`, with the suffix list loaded from `config.py` by file path). PM-family titles contain "product manager" or "product management", or the whole word APM. Entry-level markers: associate product manager, APM, "Product Manager I", junior, new grad. Senior markers: senior, sr, staff, principal, group, lead, director, head, vp, Roman numerals II and above. A title with both kinds of marker counts as senior. Situations the recipe's table does not cover (for example zero approvals, or an unreadable title list) are reported as "cannot evaluate: undefined_case".

## Limits
- Approval counts are company-wide; their years and petition types are undocumented.
- No aliases: a brand name and a legal name are different companies to this tool.
- One timeline factor is shared by every role; hiring cohorts and application windows are not modeled.
- The strongest recommendation it can produce is Consider; it only ever writes the tiers Likely and Unknown.
- Nothing here covers the H-1B lottery, cap-exempt status, wage levels, E-Verify, STEM eligibility, or anything legal.

## Known limitations
- Level markers match as whole words anywhere in a PM title, so "Product Manager, Lead Generation" is read as senior.
- Arabic-numeral levels ("Product Manager 2") and "Jr" are not read as level markers, so such titles count as no-level.
- Approvals are company-wide, and the years they cover are undocumented.
- Three situations the recipe's table does not cover are reported as "cannot evaluate: undefined_case", never guessed: approvals of 0 or below, approvals that are not a number, and a non-empty title list that cannot be parsed.

Tests named `test_known_limitation_*` pin the first two as current behavior, so any future fix shows up as a deliberate test change.

## Tests (offline, fixture only)

```bash
python3 scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/test_pm_opt_clock.py -v
```

The integration test runs the real scorer on the synthetic fixture and is skipped, with a message, if node or npm is not on PATH. `fixtures/fixture_80days.csv` uses invented company names; `fixtures/persona_candidates.json` is the fictional persona's role list (invented dates and placeholder URLs).
