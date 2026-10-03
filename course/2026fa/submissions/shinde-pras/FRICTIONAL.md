# FRICTIONAL — Reallocation Engine Recipe Design (shinde-pras)

Entries are in date order. Each one separates what I did and decided from what an AI did.

## Entry 1 — Setup, recon, and CHANGE-BRIEF (2026-09-28)

I read the terminal reports and the CHANGE-BRIEF text myself before anything was committed.

**I tried / expected**
I tried to fork the engine, get it running, and write my predictions before building anything. I expected the brief's commands (doctor, verify, score, ats:scan, ats:liveness) to run on a fresh clone the way the assignment describes.

**What happened**
- Fork, clone and npm install worked. npm install rewrote package-lock.json (36 deleted "libc" lines). I restored it and did not commit it.
- npm run verify failed with ModuleNotFoundError: No module named 'yaml'. CI installs pyyaml and my Mac does not have it. I kept that failure on record. A separate run in a throwaway venv with PyYAML passed (exit 0, 3 warnings I have not explained).
- npm run ats:scan -- --dry-run failed because portals.yml does not exist (only the example does). It stopped before any network call.
- npm run ats:liveness against https://example.com/job/123 returned expired (HTTP 404) after I approved installing Chromium (about 95 MiB). That is a smoke test only. It says nothing about how the classifier does on real career pages.
- npm run score on data/examples/ch11-roles.json (with --out-dir) scored 5 roles: Apply 2, Consider 1, Skip 2. The tracked example output did not change.
- Fact 6 in the brief is out of date: the repo already has 4 RUNNABLE-SAMPLE recipes and 1 RUNNABLE-LIVE.
- The upstream repo's own CI is red on the commit I forked from (015843d): four harness files that CI calls do not exist, and the PII scan flags an email address inside package-lock.json. No PR has ever been opened upstream, so the PR-only checks have never run.
- Data: only 1,557 of 30,369 companies in the 80 Days CSV have any H-1B data, and the file has no SOC column. Amazon and Adobe are not in it. Alphabet and Meta (as FACEBOOK INC) have rows with no H-1B data. Salesforce appears twice under two spellings. Company-wide approval counts do not say which roles were sponsored or at what level.
- The scorer does no input checking. It accepted p = 1.5, dropped a missing fit vote silently, passed any source label through, and treated an unknown tier like "Avoid" as Proven. A profile containing the word "authorized" turns sponsorship weight to 0.
- My saved terminal logs contained my home-folder path, which the repo's PII scanner does not check. I committed sanitized copies only and moved the raw logs outside the repo.
- The first commit had my university email as author. That would have been public on push. It was caught before pushing, and the commit was rewritten with my GitHub noreply address.

**What I did**
- Approved the fork, the Chromium install, the PyYAML venv and the scratch-only changes, and chose to sanitize the evidence and to use the noreply address.
- Chose the situation (PM/APM at large companies). My real graduation date and company list are kept private; the committed persona uses invented dates.
- Made prediction P1 (the timeline factor will be too crude) and P2 (about 5 of 10 tested companies end up "cannot evaluate"). I gave no reason for P1, and the wording of its reason was drafted by Claude and accepted by me. I also answered "no idea" for a second failure case, so F1 to F5 came from recon, not from me.
- Chose to cover H-1B and STEM OPT scope only as far as the repo's data allows.

**What Claude or another person contributed**
- Claude Code (terminal) did the fork check, installs, all command runs, the data inventory, the scorer probes, the sanitizing, the fact-check of the brief against the repo, and the commit and push. It also refused to save the brief while placeholders were still in it, and it stopped before pushing when it saw my real email in the commit.
- Claude in the planning chat drafted the CHANGE-BRIEF structure, failure cases F1 to F5 and the wording above, and reviewed the terminal reports. It made two mistakes that Claude Code caught: a prompt that contained the literal text <PATH-TO-BRIEF> instead of a path, and a Form D count stated as 14 of 200 records when the measured figure is 15 records (14 distinct companies).
- The commit trailer names Claude as co-author.

**What I understand now / still do not understand**
- Understand: the approval counts are company-wide, and a null in the CSV means "no trace", not "does not sponsor". The scorer trusts whatever it is given, so my prototype has to validate its own input. Gates multiply, votes add.
- Do not understand yet: which fiscal years and petition types the CSV counts cover (the repo says undocumented); why manifest-check warns about private/ and data/ats/ although .gitignore lists them; whether the maintainer already knows the upstream CI is red and how a PR will be treated.
I reread CHANGE-BRIEF.md and can explain each section to a TA.

**Evidence and next step**
- Commit 22511c2c702edf43ecf2a843700347a0337b1486 on contrib/2026fa-shinde-pras-pm-apm-opt-clock. (An earlier local commit, 46daa12, was rewritten before the first push and never existed on GitHub.)
- Files: CHANGE-BRIEF.md; evidence-sanitized/ (34 files: 17 logs and 17 metadata files); runs/role-scores.json and role-scores.md from the reference score run.
- Raw, unsanitized logs are kept outside the repository and are not committed.
- Next: write the recipe and its card (RUNNABLE-SAMPLE at most), then the prototype and its offline test.

## Entry 2 — Recipe, prototype, runs and documents (2026-09-29 to 2026-10-02)

I read JUSTIFICATION.md, WORKED-RUN.md and TEST-REPORT.md in full, and I can explain each statement in them.

**I tried / expected**
I tried to turn my predictions into a recipe, a small prototype with offline tests, a fictional-persona run and the required documents. I expected the recipe's rules to become code without surprises. My predictions were: P1, the timeline factor would be too crude; P2, about 5 of about 10 companies could not be evaluated; P3, 3 of the 6 persona roles that reach the scorer would be Skip; P4, at least half of my real scored roles would be Skip.

**What happened**
- Recipe and card (CP2, 0cec16a). Claude Code's fact-check disagreed with the first draft in several places: a tier name the book does not define, an executive summary that broke the repository's own rule, an incomplete list of words that zero the sponsorship weight, a run-log template that differed from the shared one, and a table that would not render. All were fixed before the commit. One of the checks written in the planning chat was too narrow (it did not allow the code-fence label to match the shared template); Claude Code stopped instead of deciding, and a one-line fix was authorized.
- Prototype (CP3, 1537085). It found three situations the recipe's table did not cover (approvals of zero, a non-numeric approvals value, an unreadable title list); it reports them as cannot evaluate and does not guess. One real company was replaced in the persona so it would not overlap my private list. Two limitations (level words matched anywhere in a title; Arabic-numeral levels not read) were documented and pinned by tests, not fixed.
- Persona run. My predictions and a hand calculation were committed first (db62589), and the demo ran 15 seconds after that commit. P3 was right: 3 of 6 were Skip, and all six scores matched the hand calculation to three decimals. That checks the code against the recipe's formula, not the formula against reality.
- Break attempts. Three behaved as expected. The fourth (a held role with its link removed) showed that the held list did not show the link at all. The source cross-check in the same round found that some numbers were stored as text. Fixed in 9b82a34 with every score unchanged; run 1 stays in the repository (0b0d042) beside run 2.
- Fresh clone. The pushed branch reproduced run 2 identically. The review also found that no test covered a non-numeric approvals value; added in 2ce53de (50 tests now, on Python 3.9 and 3.11).
- Private run (my own company list, first level only). I replaced neutral placeholder fit values with random ones, so they are not real assessments. Of 11 companies, 8 could not be evaluated, 3 were held, and none was scored. P2 was too low. One match was a different company with the same normalized name; one company appears to be filed under a different legal name (not confirmed). P1 and P4 could not be tested (the timeline factor was 1.0 because my clock has not started, and nothing was scored). I did not do the second level (checking real postings) for lack of time.
- Documents (CP6, CP7). Before the last documents were committed, Claude Code checked them against the evidence and stopped because three statements were unsupported: "four break attempts behaved as expected", "the report prints the matched name" (true only for scored roles), and a harness mistake attributed to me that was Claude Code's, and because the justification was over the 500-word limit. All four problems were fixed before the commit.
- Known imperfections I am leaving: CHANGE-BRIEF.md (CP1) and FRICTIONAL.md entry 1 (CP1b) name three large public companies (in the brief's examples and P2 note, and in entry 1's account of the data), although the brief says my real list is never committed (the scan is clean and the names are public; I did not re-cut the branch); the card committed in CP6 told readers to check the matched name in the report, which is true only for scored roles (corrected in the commit that adds this entry); the upstream repository's own checks were already failing before my first commit.

**What I did**
- Chose DRAFT for the recipe's status, not RUNNABLE-SAMPLE, which Claude had recommended, because it is the safest honest claim.
- Kept the default sponsorship rule and a single hiring-lag number, and told Claude that my target companies run fixed application windows.
- Made P3 (3 of 6) and P4, with their reasons, and the P2 number, before the runs. The explanation of why I guessed 5 was written after the private run. I had asked Claude Code the same question first; its answer offered three known misses plus a margin of about two, and I confirmed that matched my reasoning and adopted it, along with a drafted clause about what I assumed.
- Supplied my own company list and dates for the private run, replaced the placeholder fit values with random ones, and agreed, on Claude's suggestion, to skip the second level for lack of time.
- Kept all real dates and my company list out of every committed file; the private run's outputs stay in a folder git ignores.

**What Claude or another person contributed**
- Claude Code (terminal): ran every command, wrote the prototype, tests and fixtures, sanitized the logs, ran the checks, made every commit and push, and stopped when a check disagreed with the text or the repository.
- Claude (planning chat): drafted CHANGE-BRIEF, the recipe, the card, the run-log entry, SOURCES, TEST-REPORT, JUSTIFICATION, WORKED-RUN and these entries; computed the hand calculation and kept it sealed until I gave my count; made the drafting errors listed above.
- No other person or student.

**What I understand now / still do not understand**
Understand: a gate multiplies and a vote adds; cannot evaluate is not Skip, because a missing row means no trace, not a no; exact-name matching can give both a false absence and a false match, and the tool cannot tell; a hand calculation that matches tests the code, not reality. Still do not understand: what years and petition types the approval counts cover; why the manifest check warns about private/ and data/ats/ although .gitignore lists them; whether the maintainer already knows the upstream checks are failing.

**Evidence and next step**
- Commits on contrib/2026fa-shinde-pras-pm-apm-opt-clock: 22511c2 (CP1), 504073d (CP1b), 0cec16a (CP2), 1537085 (CP3), db62589 (CP3b), 0b0d042 (CP4a), 9b82a34 (CP4b), 2ce53de (CP5), c879f38 (CP6), 3d57631 (CP7).
- Files: CHANGE-BRIEF.md, TEST-REPORT.md, JUSTIFICATION.md, WORKED-RUN.md, SOURCES.md and runs/ in course/2026fa/submissions/shinde-pras/; the recipe and card in recipes/cases/2026fa/; the prototype in scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/; logs/runs/2026fa-shinde-pras-1.md.
- Next: open the pull request, build the Canvas ZIP and SUBMISSION.md, rehearse the demo.
