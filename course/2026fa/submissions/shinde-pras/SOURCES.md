# SOURCES: PM/APM OPT-clock recipe (shinde-pras)

I read this file and every statement about my own actions is true.

## Executive summary
This file credits what the work builds on and says who did what. The recipe, prototype, tests and documents were produced with AI help: Claude in a planning chat and Claude Code in a terminal. The decisions, predictions, approvals and checks listed under "What I decided" are mine; the drafting, command running and code writing listed under "What the AI did" were done by the AI.

## Repository and governing documents
- nikbearbrown/the-reallocation-engine, via my fork shinde-pras/the-reallocation-engine, starting from commit 015843d.
- SNICKERDOODLE.md, DOMAIN.md, DATA_CONTRACT.md, CONTRIBUTING.md, recipes/README.md and recipes/_shared.md (run-log template).
- recipes/local-wage-adjustment.md and its card, used only as a style reference.
- The assignment brief "The Reallocation Engine — Recipe Design Assignment" (INFO 7375, Fall 2026) and the Course AI Policy.
- Book chapter 07 (sponsorship tiers, lines 59 to 64) and data/examples/ch11-roles.json (the roles.json shape).

## Data
- data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv, shipped with the repo, read-only.
- The Form D samples and the BLS compact table were inspected during recon but are not used by the prototype.
- Tests use a synthetic fixture CSV with invented company names.

## Existing code used unchanged or reproduced
- scripts/score/role-scorer.mjs, run through npm run score and never modified.
- The company-name suffix list in scripts/ats/scrapers/common/config.py, loaded by file path; normalize_company_name is reproduced locally from scripts/ats/scrapers/common/normalize.py:22.

## Precedent
- recipes/cases/2026su/case-opt-timeline-fit-company-targeting.md, a DRAFT skeleton in the instructor's repo. Reused: its purpose wording, its stop conditions and its list of things it cannot verify. Changed: its placeholder inputs, gate tests and commands were replaced; the sponsorship rule, timeline gate, validation and prototype are new.

## Tools
Claude (claude.ai planning chat), Claude Code, Python 3.9 and 3.11 (standard library only), Node 20, Playwright Chromium (installed for one liveness smoke test), git, GitHub and the gh command line.

## Collaborators
None. I did not read or copy any other student's work.

## What the AI did
- Claude (planning chat): drafted the text and structure of CHANGE-BRIEF.md, the recipe, the card and the first FRICTIONAL.md entry; wrote the prompts for Claude Code; computed expected scores by hand before the persona run; reviewed each terminal report and raised problems (for example, a tier name that did not match the book, and a word in the profile text that would silently zero the sponsorship weight).
- Claude Code (terminal): forked and cloned, ran every command, wrote the prototype, tests and fixtures, sanitized the evidence logs, ran the checks, and made the commits and pushes. Commits carry a Co-Authored-By trailer for Claude.
- Mistakes the AI made that were caught and fixed: a prompt containing a placeholder path instead of a real one; a Form D count stated as 14 when the measured figure was 15 records (14 distinct companies); a recipe tier name the book does not define; a check that was too narrow for the run-log template; a wrong expectation about which commits count as unpushed; wrong dates in an early schedule.

## What I decided, checked, changed or rejected
Decided:
- The situation (PM and APM roles at large companies, graduating within a few months) and to keep my real dates and company list out of every committed file.
- To keep the default sponsorship rule and a single hiring-lag number, and I told the AI that my target companies run fixed application windows.
- My predictions P1 to P4 in CHANGE-BRIEF.md. I made the P1 choice and the numbers; the wording of P1's reason was drafted by Claude and accepted by me.
- To use my GitHub noreply address after the commit-email problem was found, to approve the Chromium install and the PyYAML environment, and to keep my graduation date out of FRICTIONAL.md.
- To keep the recipe at DRAFT as the safest honest claim, and not to do the optional second level of the private run (checking real postings by hand) for lack of time.

Checked:
- I read the terminal reports after each step and compared the persona run with my prediction (3 Skip) and with the hand calculation.
- I ran a private first-level run on my own company list, using placeholder fit values that are not real assessments, and compared the count of companies that could not be evaluated with my P2 prediction. Only counts are committed.

Changed or rejected:
- I did not follow Claude's recommendation to mark the recipe RUNNABLE-SAMPLE with two open items. I chose to keep it at DRAFT because that was the safest honest claim.
