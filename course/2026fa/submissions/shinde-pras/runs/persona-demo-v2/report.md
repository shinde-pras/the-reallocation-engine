# PM/APM OPT-clock report

## Executive summary

This report looks at 10 product-management roles you are considering and says, for each one, whether the shipped sponsorship record and your OPT clock support spending tailoring time on it.
6 role(s) were scored by the engine's existing scorer. Its recommendations: Consider 3, Skip 3.
1 role(s) are on hold because nobody has confirmed that the posting is still open. 3 role(s) cannot be evaluated from the shipped data; each one has a reason below.
In this version the strongest possible recommendation is Consider. The approval counts cover the whole company, the years they cover are undocumented, and nothing here says that a company will sponsor this role now. A person makes the decision.

## Run record

- as_of: 2027-07-01 [your-input]
- opt_start: 2027-06-01 [your-input]
- unemployment_days: 90 [your-input]
- hiring_lag_weeks: 10 [your-input]
- csv: default shipped CSV [your-input]
- timeline: deadline = 2027-06-01 + 90 days = 2027-08-30; days available = 2027-08-30 - 2027-07-01 = 60; days needed = 10 weeks x 7 = 70; factor = min(1, 60 / 70) = 0.8571 [your-input]
- recipe: recipes/cases/2026fa/shinde-pras-pm-apm-opt-clock.md v0.1.0; tool: pm_opt_clock 0.1.0

## Scored roles

| Role | Company | Sponsorship tier, p | Fit | Liveness | Timeline | Composite | Recommendation | Scorer arithmetic |
|---|---|---|---|---|---|---|---|---|
| r01-linkedin-apm | LinkedIn Corp | Likely, 0.7 [model-judgment] | 0.7 [your-input] | 1 [your-input] | 0.8571 [your-input] | 0.39 | Consider | (0.7·0.35 + 0.7·0.3) × 1 × 0.8571428571428571 = 0.390 |
| r02-stripe-pm | Stripe Inc | Likely, 0.5 [model-judgment] | 0.6 [your-input] | 1 [your-input] | 0.8571 [your-input] | 0.3043 | Consider | (0.5·0.35 + 0.6·0.3) × 1 × 0.8571428571428571 = 0.304 |
| r03-datadog-pm | Datadog Inc | Likely, 0.5 [model-judgment] | 0.5 [your-input] | 0 [your-input] | 0.8571 [your-input] | 0 | Skip | (0.5·0.35 + 0.5·0.3) × 0 × 0.8571428571428571 = 0.000 |
| r04-zscaler-pm | Zscaler Inc | Likely, 0.3 [model-judgment] | 0.55 [your-input] | 1 [your-input] | 0.8571 [your-input] | 0.2314 | Consider | (0.3·0.35 + 0.55·0.3) × 1 × 0.8571428571428571 = 0.231 |
| r05-flywire-pm | Flywire Corp | Likely, 0.2 [model-judgment] | 0.45 [your-input] | 1 [your-input] | 0.8571 [your-input] | 0.1757 | Skip | (0.2·0.35 + 0.45·0.3) × 1 × 0.8571428571428571 = 0.176 |
| r06-salesforce-apm | Salesforce.com, Inc. | Unknown, 0.15 [model-judgment] | 0.4 [your-input] | 1 [your-input] | 0.8571 [your-input] | 0.1479 | Skip | (0.15·0.35 + 0.4·0.3) × 1 × 0.8571428571428571 = 0.148 |

Sponsorship evidence behind each scored role (record, from the CSV):
- r01-linkedin-apm: rows LINKEDIN CORP; approvals 4962, denials 28.0; PM-family titles ['Associate Product Manager']; rule row: approvals at least 50 and an entry-level PM title listed
  - scorer reason: above threshold (0.390) but one soft spot: sponsorship tier "Likely"
- r02-stripe-pm: rows STRIPE INC; approvals 1250, denials 22.0; PM-family titles ['Product Manager']; rule row: approvals at least 50 and a PM-family title with no level marker
  - scorer reason: above threshold (0.304) but one soft spot: sponsorship tier "Likely"
- r03-datadog-pm: rows DATADOG INC; approvals 340, denials 0.0; PM-family titles ['PRODUCT MANAGER']; rule row: approvals at least 50 and a PM-family title with no level marker
  - scorer reason: gated: liveness ≈ 0.000 (a closed gate zeroes the composite regardless of votes)
- r04-zscaler-pm: rows ZSCALER INC; approvals 802, denials 12.0; PM-family titles ['Senior Product Manager']; rule row: approvals at least 50 and PM-family titles only at senior levels
  - scorer reason: composite 0.231 in the Consider band [0.2, 0.3)
- r05-flywire-pm: rows FLYWIRE CORP; approvals 36, denials 2.0; PM-family titles ['Product Manager']; rule row: approvals below 50 and any PM-family title listed
  - scorer reason: composite 0.176 < 0.2 — time is better spent elsewhere
- r06-salesforce-apm: rows SALESFORCE COM INC, SALESFORCECOM INC; approvals 66, denials 10.0; PM-family titles none listed; rule row: some approvals but no PM-family title listed
  - scorer reason: composite 0.148 < 0.2 — time is better spent elsewhere

## On hold (liveness not confirmed)

- r10-roku-pm: Roku Inc, Product Manager
  - URL: https://example.com/jobs/r10
  - liveness result: uncertain; checked at: 2027-06-28; source: by-hand (persona placeholder)
  - check it with `npm run ats:liveness -- https://example.com/jobs/r10`, record active or expired, and rerun.

## Cannot evaluate

- r07-alphabet-apm (Alphabet Inc.): cannot evaluate: no_h1b_data. row found but Total Approvals is empty (no trace is not the same as not sponsoring)
- r08-nanthealth-pm (NantHealth, Inc.): cannot evaluate: ambiguous_rows. 2 rows share the normalized name with different figures
- r09-northwind-apm (Northwind Product Labs): cannot evaluate: not_in_csv. no row with this normalized name (exact match only, no aliases)

## What a human must check at each gate

- PG0, inputs: the CSV and scorer named in the run record are the ones you meant, and every date and number above is yours.
- PG1, liveness: for every role scored with liveness from a hand check, open the posting yourself; resolve each role on hold.
- PG2, timeline: the deadline arithmetic in the run record matches your real OPT dates and allowed unemployment days.
- PG3, scorer input: validation passed before the scorer ran (it always does if this report exists).
- PG4, sign-off: read this report and record your decision in a run-log entry. The tool never applies to anything.

## Limitations

- Approval and denial counts are company-wide, not per role, and the years and petition types they cover are undocumented.
- A missing row or an empty approval field means no trace in this data, not that the company refuses to sponsor.
- Title lists hold top titles only; a missing PM title is not evidence of a no. Level is read from title wording only.
- Companies are matched by exact normalized name; brand names and legal names are not linked (for example a parent company and its product).
- The timeline factor is one linear number shared by every role; fixed hiring cohorts and application windows are not modeled.
- Nothing here covers the H-1B lottery, cap-exempt status, wage levels, E-Verify, STEM eligibility, or any legal question.
