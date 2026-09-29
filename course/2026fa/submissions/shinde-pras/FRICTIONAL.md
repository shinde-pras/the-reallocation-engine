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
