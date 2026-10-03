# Domain justification: PM/APM OPT-clock (shinde-pras)

## Executive summary
This recipe helps an international student on a short OPT clock decide which large-company Product Manager roles deserve tailoring time, by putting the sponsorship record and the days left on the clock side by side, with every value labeled.

## Who uses it, and in what situation
An international master's student on an F-1 visa, graduating within a few months, who will start OPT soon after and then has 90 days of allowed unemployment. They are applying for Product Manager (PM) and Associate Product Manager (APM) roles at large technology companies and will need an H-1B sponsor. Hiring cycles are not modeled or verified. The committed persona uses invented dates.

## The information asymmetry
From the outside this student cannot easily see whether a company has ever sponsored PM-titled roles, at what level, or whether the days left on the clock are enough for a hiring process. The recipe puts the record (the company's row in the 80 Days file: approvals, denials, listed titles) beside the clock arithmetic and labels each value record, model-judgment or your-input.

## Engine layers
80 Days to Stay (sponsorship history) and Job-Ops (posting liveness, as a gate fed by hand or by the liveness command). Not used: Form D funding (not a scorer term) and The Cognitive Pivot (no PM occupation code in the data; role quality has weight 0.0).

## Where it fits the 3-3-2 day
It takes over the first part of the two research-and-apply hours: looking up sponsorship history and doing the clock arithmetic for each role before deciding whether to tailor an application. Checking one company by hand takes me about 10 minutes, and I would check about 25 companies a week, so the tool could take over around 4 hours of research a week. This is my estimate, not a measurement. It feeds the networking three hours: companies that cannot be evaluated are the ones to ask a person about instead of guessing.

## Failure modes
1. Wrong or missing company match. Companies are matched by exact normalized name. A company whose filings sit under a different legal name looks absent (false absence), and an unrelated company with the same normalized name looks like evidence (false match). In a private run on 11 real companies, 8 could not be evaluated; one appeared to be filed under a different legal name (unconfirmed) and one match was a different company. The tool cannot tell either case apart, and the report shows the matched CSV name only for scored roles (the run log records it for all), so a student new to US corporate naming would find this hardest to catch.
2. Company-wide counts read as role-level evidence. A company with thousands of approvals, mostly for engineers, may list a PM title once, or only at senior level. A new graduate can read "sponsors PMs" as "sponsors APMs". The tool lowers the probability for senior-only titles but cannot see counts per title or year, and the years are undocumented. The new graduate who treats the number as role-specific would find this hardest to catch.
